"""ticmint-intel: the custom MCP server at the centre of SwitchSignal.

It is not a thin wrapper. It OWNS the SQLite store, the complaint taxonomy, scoring and the fact-checked
drafter. Two clients use it:
  1. run.py, the scheduled pipeline, calls ingest -> analyze -> draft -> export over stdio.
  2. A human in Claude Desktop / Claude Code asks "which payout-complaint leads in India are tier A?"
Same tools, same guardrails, so ad-hoc questions can never bypass the fact-check.

Run:  python -m switchsignal.mcp_server        (stdio)
"""
from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from . import collectors
from .analyze import analyze
from .draft import draft
from .models import Review, load_yaml
from .score import score_lead
from .store import Store

mcp = FastMCP("ticmint-intel")
_store: Store | None = None

LEAD_HEADER = ["lead_id", "tier", "score", "competitor", "source", "review_date", "rating", "persona",
               "primary_complaint", "switch_intent", "reviewer", "role", "company_size", "industry", "country",
               "segment", "evidence_quote", "review_url", "score_rationale", "draft_subject", "draft_body",
               "draft_check", "data_origin", "last_updated"]
HUMAN_HEADER = ["status", "owner", "notes"]  # humans edit these in the Sheet; the sync never overwrites them
TREND_HEADER = ["competitor", "category", "organizer_complaints", "avg_severity", "switch_signals"]


def store() -> Store:
    global _store
    if _store is None:
        _store = Store()
    return _store


@mcp.tool()
def ingest_reviews(source: str = "fixtures", path: str = "", competitors: str = "", pages: int = 2) -> dict:
    """Collect reviews into the store. source: fixtures | csv | trustpilot.
    csv needs `path`. trustpilot reads config/competitors.yaml (optionally filter with comma-separated `competitors`).
    Returns counts and per-source errors; one failing source never aborts the run."""
    errors, fetched = [], 0
    reviews: list[Review] = []
    try:
        if source == "fixtures":
            reviews = collectors.from_fixtures(path)
        elif source == "csv":
            reviews = collectors.from_csv(path)
        elif source == "trustpilot":
            want = {c.strip().lower() for c in competitors.split(",") if c.strip()}
            for c in load_yaml("competitors.yaml")["competitors"]:
                if want and c["name"].lower() not in want:
                    continue
                try:
                    reviews += collectors.from_trustpilot(c["trustpilot"], c["name"], pages=pages)
                except collectors.CollectorError as e:
                    errors.append(f"{c['name']}: {e}")
        else:
            errors.append(f"unknown source '{source}'")
    except collectors.CollectorError as e:
        errors.append(str(e))
    fetched = len(reviews)
    return {"source": source, "fetched": fetched, "new": store().add_reviews(reviews), "errors": errors}


@mcp.tool()
def analyze_pending() -> dict:
    """Classify every unanalyzed review (persona, complaint categories, severity, verbatim evidence quote),
    then score it as a lead. Attendee-voice reviews are kept but capped as non-leads."""
    s, n = store(), 0
    for r in s.pending_analysis():
        s.save_analysis(r.id, analyze(r))
        n += 1
    return {"analyzed": n}


@mcp.tool()
def draft_pending() -> dict:
    """Score analyzed reviews and draft outreach for tier A/B organizer leads. Drafts are never sent.
    Any number not backed by config/ticmint_facts.yaml flags the draft NEEDS_FIX."""
    s, drafted, flagged, total = store(), 0, 0, 0
    for r, a in s.analyzed_without_lead():
        sc = score_lead(r, a)
        d = draft(r, a, sc["tier"])
        s.save_lead(r.id, sc, d)
        total += 1
        drafted += bool(d)
        flagged += bool(d and d["unsupported"])
    return {"scored": total, "drafted": drafted, "flagged_needs_fix": flagged}


@mcp.tool()
def list_leads(tier: str = "", category: str = "", competitor: str = "", limit: int = 10) -> list[dict]:
    """Top leads by score. Filter by tier (A/B/C), complaint category id, or competitor name."""
    out = []
    for r in store().leads(tier, category, competitor, limit):
        out.append({k: r[k] for k in ("review_id", "tier", "score", "competitor", "source", "role", "country",
                                      "primary_cat", "switch_intent", "quote", "status")})
    return out


@mcp.tool()
def get_lead(lead_id: str) -> dict:
    """Full detail for one lead: score rationale, evidence, and the draft with its fact-check result."""
    rows = [r for r in store().leads(limit=1000) if r["review_id"] == lead_id]
    return rows[0] if rows else {"error": f"no lead {lead_id}"}


@mcp.tool()
def explain_review(text: str, competitor: str = "Eventbrite", rating: float = 0, role: str = "",
                   country: str = "") -> dict:
    """Ad-hoc: analyze pasted review text WITHOUT saving it. Useful to sanity-check the classifier."""
    r = Review(source="adhoc", competitor=competitor, text=text, rating=rating or None, role=role, country=country,
               date="")
    a = analyze(r)
    return {"persona": a.persona, "categories": a.categories, "primary": a.primary, "severity": a.severity,
            "switch_intent": a.switch_intent, "quote": a.quote, "method": a.method}


@mcp.tool()
def competitor_complaint_summary(days: int = 90) -> list[dict]:
    """Which complaint themes dominate each competitor's organizer reviews (attendees excluded)."""
    return store().trends(days)


@mcp.tool()
def set_lead_status(lead_id: str, status: str) -> dict:
    """Update lead status: new | contacted | replied | meeting | won | lost | disqualified."""
    return {"ok": store().set_status(lead_id, status)}


@mcp.tool()
def export_rows() -> dict:
    """Rows for the Google Sheet: Leads (machine cols + human cols), Trends. Sync preserves human columns."""
    leads = []
    for r in store().leads(limit=5000):
        leads.append([r["review_id"], r["tier"], r["score"], r["competitor"], r["source"], r["date"], r["rating"],
                      r["persona"], r["primary_cat"], "yes" if r["switch_intent"] else "", r["author"], r["role"],
                      r["company_size"], r["industry"], r["country"], r["segment"], r["quote"], r["url"],
                      r["rationale"], r["subject"], r["body"], r["draft_check"],
                      "SYNTHETIC FIXTURE" if r["synthetic"] else "live", r["updated_at"]])
    trends = [[t["competitor"], t["category"], t["n"], t["avg_severity"], t["switch_signals"]]
              for t in store().trends(365)]
    return {"leads_header": LEAD_HEADER, "human_header": HUMAN_HEADER, "leads": leads,
            "trends_header": TREND_HEADER, "trends": trends}


@mcp.resource("ticmint://facts")
def facts() -> str:
    """The verified Ticmint claims the drafter is allowed to use, with source URLs."""
    return json.dumps(load_yaml("ticmint_facts.yaml"), indent=2, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()
