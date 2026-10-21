"""Outreach drafter. Speaks to the reviewer's specific complaint, using ONLY claims in ticmint_facts.yaml.

Safety rails, all enforced in code (not in a prompt):
  * every number in the draft must come from a claim the draft uses -> else flagged `unsupported`
  * no reviewer quote is pasted into the email (the quote stays in the sheet for the human)
  * never drafts for attendees or leads without a complaint
Drafts are NEVER sent. A human finds the contact off-platform and approves (status column).
"""
from __future__ import annotations

import os
import re

from .models import Analysis, Review, load_yaml

ISSUE = {
    "fees_pricing": "fees stacking up on every ticket",
    "payout_cashflow": "how long it takes to get paid out after an event",
    "branding_whitelabel": "limited control over how your event page and checkout look",
    "data_ownership": "not owning your attendee data and audience",
    "local_payments": "payment options that don't match how your buyers pay",
    "support_quality": "getting stuck without responsive support",
    "feature_gaps": "features you needed that weren't there",
    "reliability_checkin": "problems on event day",
}
FACTS_FOR = {
    "fees_pricing": ["fee_growth", "@price"], "payout_cashflow": ["payout_t3"],
    "branding_whitelabel": ["white_label"], "data_ownership": ["data_owner"],
    "local_payments": ["payments_local", "@price"], "support_quality": ["support_channels"],
    "feature_gaps": ["features_core"], "reliability_checkin": ["access_control"],
}
QUALIFIER = {
    "fees_pricing": "fee_starter",
    "payout_cashflow": None,
}
NUM = re.compile(r"(?:[$£₹]|AED\s?)\d[\d,.]*|\d+(?:\.\d+)?%|T\+\d")
PRICE_BY_COUNTRY = {"IN": "price_in", "GB": "price_uk", "AE": "price_ae"}


def first_name(author: str) -> str:
    tok = (author or "").split()
    return tok[0].capitalize() if tok and tok[0].isalpha() and len(tok[0]) > 1 else "there"


def _claim(facts: dict, key: str, country: str) -> tuple[str, dict]:
    if key == "@price":
        key = PRICE_BY_COUNTRY.get(country.upper(), "growth_price_usd")
    return key, facts["claims"][key]


def draft(review: Review, a: Analysis, tier: str) -> dict | None:
    if tier == "C" or a.persona == "attendee" or not a.primary:
        return None
    facts = load_yaml("ticmint_facts.yaml")
    used, lines = [], []
    for key in FACTS_FOR[a.primary]:
        k, c = _claim(facts, key, review.country)
        used.append(k)
        lines.append(c["text"][0].upper() + c["text"][1:])
    q = QUALIFIER.get(a.primary)
    if q:  # honest qualifier: the headline number has a catch, say it up front
        used.append(q)
        lines.append("For context, " + facts["claims"][q]["text"])
    sender = os.getenv("SENDER_NAME", "{{sender}}")
    body = (
        f"Hi {first_name(review.author)},\n\n"
        f"I came across your public {review.source.capitalize()} review of {review.competitor}, "
        f"where you raised {ISSUE[a.primary]}. That is the exact problem Ticmint was built around.\n\n"
        + ". ".join(l.rstrip(".") for l in lines) + ".\n\n"
        "If you tell me roughly how many tickets you sell per event and your average ticket price, "
        "I will work out what the fees would look like on Ticmint versus your current setup. "
        "Just the numbers, no deck.\n\n"
        f"{sender}"
    )
    allowed = {n for k in used for n in facts["claims"][k]["numbers"]}
    unsupported = sorted({n for n in NUM.findall(body) if n not in allowed})
    return {
        "subject": f"{ISSUE[a.primary].capitalize()} at {review.competitor}",
        "body": body,
        "claims_used": used,
        "unsupported": unsupported,
        "check": "ok" if not unsupported else "NEEDS_FIX: " + ", ".join(unsupported),
    }
