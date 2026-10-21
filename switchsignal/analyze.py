"""Complaint extraction. Rules first (free, deterministic, auditable); LLM optional and guarded."""
from __future__ import annotations

import re

from . import llm
from .models import Analysis, Review, load_yaml

MONEY = re.compile(r"[$£€₹]\s?\d|\d+\s?%")
RATING_SEV = {1: 0.9, 2: 0.75, 3: 0.5, 4: 0.25, 5: 0.1}


def _count(patterns: list[str], text: str) -> int:
    return sum(1 for p in patterns if re.search(p, text, re.I))


def detect_persona(review: Review, tax: dict) -> tuple[str, int]:
    """Review sites are mostly ticket BUYERS. Only organizer voices are sales leads."""
    text = review.all_text()
    org = _count(tax["persona"]["organizer"], text)
    att = _count(tax["persona"]["attendee"], text)
    role = review.role.lower()
    if role and any(r in role for r in tax["persona"]["organizer_roles"]):
        org += 2
    score = org - att
    if score >= 1:
        return "organizer", score
    if score <= -1:
        return "attendee", score
    return "unknown", score


def classify_rules(text: str, tax: dict) -> list[dict]:
    found = []
    for cat, spec in tax["categories"].items():
        hits = _count(spec["patterns"], text)
        strong = _count(spec.get("strong", []), text)
        if hits or strong:
            found.append({"cat": cat, "hits": hits, "strong": strong})
    found.sort(key=lambda c: (c["strong"], c["hits"]), reverse=True)
    return found


def best_quote(text: str, cats: list[dict], tax: dict) -> str:
    """Return the most complaint-dense sentence. Always a verbatim substring of `text`."""
    if not cats:
        return ""
    pats = [p for c in cats[:2] for p in tax["categories"][c["cat"]]["patterns"]]
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]
    if not sentences:
        return ""
    best = max(sentences, key=lambda s: (_count(pats, s), -len(s)))
    return best[:300]


def has_switch_intent(text: str, tax: dict) -> bool:
    return _count(tax["switch_intent"], text) > 0


def severity(rating: float | None, cats: list[dict], text: str, switch: bool) -> float:
    base = RATING_SEV.get(int(round(rating)), 0.5) if rating else 0.5
    strong = sum(c["strong"] for c in cats)
    hits = sum(c["hits"] for c in cats)
    intensity = min(1.0, 0.45 * strong + 0.12 * hits + (0.15 if MONEY.search(text) else 0))
    return round(min(1.0, 0.5 * base + 0.3 * intensity + 0.2 * (1.0 if switch else 0.0)), 3)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def verify_llm(result: dict | None, text: str, tax: dict) -> tuple[list[str], str]:
    """Hallucination guard: keep only known categories and a quote that really appears in the review."""
    if not result:
        return [], ""
    cats = [c for c in result.get("categories", []) if c in tax["categories"]]
    quote = result.get("quote", "") or ""
    if quote and _norm(quote) not in _norm(text):
        quote = ""
    return cats, quote


def analyze(review: Review, tax: dict | None = None, use_llm: bool | None = None) -> Analysis:
    tax = tax or load_yaml("taxonomy.yaml")
    persona, org_score = detect_persona(review, tax)
    text = review.complaint_text()
    cats = classify_rules(text, tax)
    switch = has_switch_intent(review.all_text(), tax)
    method = "rules"
    quote = best_quote(text, cats, tax)

    want_llm = llm.configured() if use_llm is None else use_llm
    if want_llm and persona != "attendee":
        extra, llm_quote = verify_llm(llm.extract(text, list(tax["categories"])), text, tax)
        known = {c["cat"] for c in cats}
        for c in extra:
            if c not in known:
                cats.append({"cat": c, "hits": 1, "strong": 0})
                method = "rules+llm"
        if llm_quote and not quote:
            quote = llm_quote
            method = "rules+llm"

    sev = severity(review.rating, cats, text, switch)
    return Analysis(persona=persona, organizer_score=org_score, categories=cats,
                    primary=cats[0]["cat"] if cats else "", severity=sev,
                    quote=quote, switch_intent=switch, method=method)
