"""Review collectors. Each returns list[Review] and raises CollectorError with a plain reason.

Honest scope:
  * fixtures  - synthetic sample rows (clearly flagged synthetic) so the pipeline is demoable offline
  * csv       - G2 / Capterra exports or manual copy. Scraping those sites breaks their ToS and is blocked
                by bot protection, so the compliant free route is a CSV you are entitled to export.
  * trustpilot- best-effort public pages (robots.txt checked, 3s delay, identifying UA). Mostly ticket
                BUYERS, so the persona filter does most of the work here.
"""
from __future__ import annotations

import csv
import json
import time
import urllib.robotparser

import requests
from bs4 import BeautifulSoup

from .models import ROOT, Review

UA = "SwitchSignalBot/0.1 (+research; contact: set-your-email@example.com)"


class CollectorError(Exception):
    pass


def from_fixtures(path: str = "") -> list[Review]:
    p = ROOT / (path or "fixtures/reviews_sample.json")
    return [Review(synthetic=True, **row) for row in json.loads(p.read_text(encoding="utf-8"))]


def from_csv(path: str) -> list[Review]:
    cols = {"source", "competitor", "rating", "title", "text", "dislikes", "author", "role",
            "company_size", "industry", "country", "date", "url"}
    try:
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    except OSError as e:
        raise CollectorError(f"cannot read {path}: {e}") from e
    if rows and not {"competitor", "text"} <= set(rows[0]):
        raise CollectorError("csv needs at least columns: competitor, text")
    out = []
    for r in rows:
        r = {k: (v or "") for k, v in r.items() if k in cols}
        r["rating"] = float(r["rating"]) if r.get("rating") else None
        r.setdefault("source", "csv")
        out.append(Review(**r))
    return out


def from_trustpilot(domain: str, competitor: str, pages: int = 2, delay: float = 3.0) -> list[Review]:
    rp = urllib.robotparser.RobotFileParser("https://www.trustpilot.com/robots.txt")
    try:
        rp.read()
    except Exception as e:
        raise CollectorError(f"trustpilot robots.txt unreachable: {e}") from e
    out: list[Review] = []
    for page in range(1, pages + 1):
        url = f"https://www.trustpilot.com/review/{domain}?stars=1&stars=2&stars=3&page={page}"
        if not rp.can_fetch(UA, url):
            raise CollectorError("trustpilot robots.txt disallows this path")
        try:
            resp = requests.get(url, headers={"User-Agent": UA}, timeout=20)
        except requests.RequestException as e:
            raise CollectorError(f"trustpilot request failed: {e}") from e
        if resp.status_code != 200:
            raise CollectorError(f"trustpilot HTTP {resp.status_code} (blocked or rate limited)")
        tag = BeautifulSoup(resp.text, "html.parser").find("script", id="__NEXT_DATA__")
        if not tag:
            raise CollectorError("trustpilot page layout changed: __NEXT_DATA__ not found")
        try:
            items = json.loads(tag.string)["props"]["pageProps"]["reviews"]
        except (KeyError, TypeError, json.JSONDecodeError) as e:
            raise CollectorError(f"trustpilot JSON shape changed: {e}") from e
        for it in items:
            out.append(Review(
                source="trustpilot", competitor=competitor, text=it.get("text", ""), title=it.get("title", ""),
                rating=float(it["rating"]) if it.get("rating") else None,
                author=(it.get("consumer") or {}).get("displayName", ""),
                country=(it.get("consumer") or {}).get("countryCode", ""),
                date=((it.get("dates") or {}).get("publishedDate") or "")[:10],
                url=f"https://www.trustpilot.com/reviews/{it.get('id', '')}"))
        time.sleep(delay)
    return out
