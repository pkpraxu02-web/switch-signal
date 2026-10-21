import asyncio
import json
import os
import sys
from datetime import date

import pytest

from switchsignal import analyze as an, draft as dr, score as sc
from switchsignal.models import Review, load_yaml

TAX = load_yaml("taxonomy.yaml")
TODAY = date(2026, 10, 20)


def rv(**kw):
    base = dict(source="g2", competitor="Eventbrite", text="", rating=2, date="2026-10-10", country="IN",
                role="Founder", company_size="11-50 employees")
    base.update(kw)
    return Review(**base)


def test_attendee_is_not_a_lead():
    r = rv(text="I bought two tickets and the event was fake. They wouldn't refund me. Scam.", role="", rating=1)
    a = an.analyze(r, TAX, use_llm=False)
    assert a.persona == "attendee"
    s = sc.score_lead(r, a, TODAY)
    assert s["score"] <= 15 and s["tier"] == "C"
    assert dr.draft(r, a, s["tier"]) is None


def test_organizer_fee_complaint_scores_and_drafts():
    r = rv(dislikes="As an organizer, the fees are way too high and cut into our margins. We are looking for an alternative.")
    a = an.analyze(r, TAX, use_llm=False)
    assert a.persona == "organizer" and a.primary == "fees_pricing" and a.switch_intent
    s = sc.score_lead(r, a, TODAY)
    assert s["tier"] in ("A", "B")
    d = dr.draft(r, a, s["tier"])
    assert d and d["check"] == "ok"
    assert "2%" in d["body"] and "₹249" in d["body"]          # India price line chosen by country
    assert "5%" in d["body"]                                   # honest qualifier about Starter fee
    assert "way too high" not in d["body"]                     # reviewer quote is never pasted into outreach


def test_quote_is_verbatim_substring():
    text = "Setup was easy. The payout was on hold for weeks and our cash flow suffered. Support was fine."
    a = an.analyze(rv(dislikes=text), TAX, use_llm=False)
    assert a.quote and a.quote in text


def test_llm_hallucinated_quote_is_dropped(monkeypatch):
    text = "We can't export our attendee data and cannot retarget buyers."
    monkeypatch.setattr(an.llm, "extract", lambda t, c: {"categories": ["data_ownership", "made_up_cat"],
                                                          "quote": "This quote does not exist in the review"})
    cats, quote = an.verify_llm(an.llm.extract(text, []), text, TAX)
    assert cats == ["data_ownership"] and quote == ""


def test_draft_flags_unsupported_number(monkeypatch):
    r = rv(dislikes="As an organizer the fees are too high and cut into our margins.")
    a = an.analyze(r, TAX, use_llm=False)
    facts = load_yaml("ticmint_facts.yaml")
    facts["claims"]["fee_growth"]["text"] = "On Growth the fee is 1.5%, plus gateway charges"  # number not in `numbers`
    monkeypatch.setattr(dr, "load_yaml", lambda name: facts)
    d = dr.draft(r, a, "A")
    assert d["unsupported"] == ["1.5%"] and d["check"].startswith("NEEDS_FIX")


def test_recency_and_enrichment():
    assert sc.recency("2026-10-10", TODAY) == 1.0 and sc.recency("2024-01-01", TODAY) == 0.1
    e, meta = sc.enrichment(rv(), load_yaml("competitors.yaml")["markets"])
    assert meta["segment"] == "mid_market" or meta["segment"] == "self_serve"
    assert meta["market"] == "India"


def test_end_to_end_via_mcp(tmp_path):
    """Spawns the real MCP server over stdio and drives it like run.py does."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from run import unwrap

    env = dict(os.environ, SWITCHSIGNAL_DB=str(tmp_path / "t.db"))

    async def go():
        params = StdioServerParameters(command=sys.executable, args=["-m", "switchsignal.mcp_server"], env=env)
        async with stdio_client(params) as (r, w):
            async with ClientSession(r, w) as s:
                await s.initialize()
                tools = {t.name for t in (await s.list_tools()).tools}
                ing = unwrap(await s.call_tool("ingest_reviews", {"source": "fixtures"}))
                ing2 = unwrap(await s.call_tool("ingest_reviews", {"source": "fixtures"}))  # idempotent
                await s.call_tool("analyze_pending", {})
                dp = unwrap(await s.call_tool("draft_pending", {}))
                top = unwrap(await s.call_tool("list_leads", {"limit": 3}))
                ex = unwrap(await s.call_tool("export_rows", {}))
                bad = await s.call_tool("ingest_reviews", {"source": "csv", "path": "/nope.csv"})
                return tools, ing, ing2, dp, top, ex, unwrap(bad)

    tools, ing, ing2, dp, top, ex, bad = asyncio.run(go())
    assert {"ingest_reviews", "analyze_pending", "draft_pending", "list_leads", "export_rows"} <= tools
    assert ing["new"] == 10 and ing2["new"] == 0
    assert dp["scored"] == 10 and dp["flagged_needs_fix"] == 0
    assert top[0]["score"] >= top[-1]["score"]
    assert all(len(row) == len(ex["leads_header"]) for row in ex["leads"])
    assert bad["errors"] and bad["fetched"] == 0   # failing source reports, does not crash
