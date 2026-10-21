"""Lead scoring. Every component is explainable and shown in the sheet's `rationale` column."""
from __future__ import annotations

import re
from datetime import date, datetime

from .models import Analysis, Review, load_yaml

SENIOR = re.compile(r"founder|owner|ceo|director|head|vp|president|producer|promoter", re.I)
MID = re.compile(r"manager|coordinator|lead|organi[sz]er", re.I)
PERSONA_W = {"organizer": 1.0, "unknown": 0.5, "attendee": 0.0}


def recency(date_str: str, today: date | None = None) -> float:
    today = today or date.today()
    try:
        d = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
    except ValueError:
        return 0.3
    days = (today - d).days
    for limit, w in ((30, 1.0), (90, 0.8), (180, 0.5), (365, 0.25)):
        if days <= limit:
            return w
    return 0.1


def enrichment(review: Review, markets: dict) -> tuple[float, dict]:
    role = review.role or ""
    seniority = 1.0 if SENIOR.search(role) else 0.7 if MID.search(role) else 0.3 if role else 0.2
    size = review.company_size
    n = int(re.findall(r"\d+", size)[0]) if re.findall(r"\d+", size) else None
    segment = "unknown" if n is None else "self_serve" if n <= 50 else "mid_market" if n <= 500 else "enterprise"
    in_market = review.country.upper() in markets
    region = 1.0 if in_market else 0.4
    return round(0.5 * seniority + 0.5 * region, 3), {
        "segment": segment, "market": markets.get(review.country.upper(), review.country or "unknown")}


def score_lead(review: Review, a: Analysis, today: date | None = None) -> dict:
    tax = load_yaml("taxonomy.yaml")
    markets = load_yaml("competitors.yaml")["markets"]
    fit = tax["categories"][a.primary]["ticmint_fit"] if a.primary else 0.0
    rec = recency(review.date, today)
    enr, meta = enrichment(review, markets)
    persona_w = PERSONA_W[a.persona]
    raw = 100 * (0.35 * a.severity + 0.25 * fit + 0.15 * rec + 0.15 * persona_w + 0.10 * enr)
    if a.persona == "attendee" or not a.primary:
        raw = min(raw, 15)  # not a sales lead: a ticket buyer, or no complaint found
    score = round(raw, 1)
    tier = "A" if score >= 70 else "B" if score >= 50 else "C"
    rationale = (f"severity {a.severity:.2f} | fit {fit:.2f} ({a.primary or 'none'}) | recency {rec:.2f} | "
                 f"persona {a.persona} | enrichment {enr:.2f} ({meta['segment']}, {meta['market']})"
                 + (" | stated switch intent" if a.switch_intent else ""))
    return {"score": score, "tier": tier, "rationale": rationale, **meta}
