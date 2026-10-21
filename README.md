# SwitchSignal — Review-Site Sentiment Agent for Ticmint (Track 2)

Finds **event organisers** who are publicly unhappy with a competing ticketing platform, extracts the *specific* complaint,
scores the lead, and drafts outreach that answers that exact complaint using **only fact-checked Ticmint claims**.
Results land in a Google Sheet that refreshes itself every 6 hours.

**What is proven vs not (read this first)**

| Piece | Status |
|---|---|
| Classifier, scoring, drafter, fact-check, dedupe | Tested: `pytest` 7/7, run twice end-to-end (2nd run adds 0 rows) |
| Custom MCP server over stdio, driven by a real MCP client | Tested (`tests/test_agent.py::test_end_to_end_via_mcp`) |
| CSV output | Tested |
| **Google Sheets sync** | **Written, NOT run.** Needs your service-account creds; I had none. First run on your side is the real test |
| **Live Trustpilot collector** | **Written, NOT run.** The build sandbox's proxy returned 403 on trustpilot.com. The failure path is tested (error surfaces in the `Runs` tab, run continues) |
| G2 / Capterra | CSV import only, deliberately (see "Where it breaks") |
| Data in the demo | `fixtures/reviews_sample.json` = **10 synthetic reviews**, flagged `SYNTHETIC FIXTURE` in the sheet. Not real people |

## Architecture

```
GitHub Actions cron (every 6h)           Claude Desktop / Claude Code (human, ad hoc)
        |                                          |
   run.py  (MCP client)  ------------------>  ticmint-intel  (custom MCP server, stdio)
        |                                          |  tools: ingest_reviews, analyze_pending, draft_pending,
        |                                          |         list_leads, get_lead, explain_review,
        |                                          |         competitor_complaint_summary, set_lead_status, export_rows
        |                                          |  owns: SQLite store, taxonomy.yaml, scoring, ticmint_facts.yaml fact-check
        v                                          v
   sheets.py --> Google Sheet: Leads | Trends | Runs
```

* **Why the MCP server is not decorative:** it owns state and every guardrail. The scheduler and a human in Claude
  Desktop call the *same* tools, so an ad-hoc "draft me an email for lead X" cannot bypass the fact-check.
* **Where the LLM sits:** optional. Rules (`config/taxonomy.yaml`) classify first, free and deterministic. If
  `LLM_BASE_URL` + `LLM_MODEL` are set (any OpenAI-compatible endpoint, e.g. local Ollama = $0) the LLM may *add*
  categories and a quote, but its quote must be a verbatim substring of the review or it is dropped (`verify_llm`).
  The drafter is templates + a claims file, **not** free-form generation, so it cannot invent a price.
* **What triggers a run:** cron (`.github/workflows/refresh.yml`) or `python run.py` or `workflow_dispatch`.
* **Sheet design:** machine columns overwritten each run; `status / owner / notes` columns are never touched, so the
  Sheet is the sales team's working CRM. `Runs` tab gets one row per run = visible proof it refreshes itself.

## Setup

```bash
pip install -r requirements.txt        # note: mcp pinned <2 (v2 renamed FastMCP; see below)
python -m pytest -q                    # 7 passed
python run.py --source fixtures        # offline demo -> output/leads.csv, trends.csv, runs.csv
```

Google Sheet (free):
1. Google Cloud → create project → enable **Google Sheets API** → create **service account** → download JSON key.
2. Create a Sheet, share it (Editor) with the service account's email.
3. Repo secrets: `SHEET_ID` (from the Sheet URL), `GOOGLE_SERVICE_ACCOUNT_JSON` (whole JSON). Optional var `SENDER_NAME`.
4. Put a licensed G2/Capterra export at `exports/reviews.csv` (columns: `source,competitor,rating,title,text,dislikes,author,role,company_size,industry,country,date,url`; `competitor` and `text` required).
5. Actions → refresh-leads → Run workflow. Check the `Runs` tab; it should gain a row every 6 hours.

Optional free LLM: `ollama pull llama3.2`, then `LLM_BASE_URL=http://localhost:11434/v1 LLM_MODEL=llama3.2`.

Use from Claude Desktop (`claude_desktop_config.json`):
```json
{"mcpServers": {"ticmint-intel": {"command": "python", "args": ["-m", "switchsignal.mcp_server"],
  "cwd": "/path/to/switch-signal"}}}
```
Then ask: *"List tier A leads whose main complaint is payouts, and show the draft for the first."*

## How a lead is scored (all visible in the `score_rationale` column)

`score = 100 × (0.35·severity + 0.25·ticmint_fit + 0.15·recency + 0.15·organizer_persona + 0.10·enrichment)`
Tier A ≥ 70, B ≥ 50, C below. **Attendee-voice reviews and reviews with no complaint are capped at 15.**
The key observation behind the design: review sites are mostly ticket *buyers* ("event was fake", "refund"), who are
not leads. In the fixtures 2 of 10 are attendee voices and 1 more has no complaint at all; all three are capped at 15.
The persona gate is the highest-leverage rule.
`ticmint_fit` is how directly Ticmint's own pages answer the complaint (white-label/data ownership = 1.0,
support quality = 0.6 because Ticmint has no support advantage to claim).

## Where it breaks (known, ranked by how much it worries me)

1. **Data access.** G2 and Capterra prohibit scraping and sit behind bot protection; I did not build scrapers for them.
   The compliant free route is CSV export. At scale: a licensed data source (G2 buyer-intent, or an actor marketplace),
   roughly $300–1,500/month, quote needed. Trustpilot's page JSON (`__NEXT_DATA__`) can change without notice; the collector
   raises `CollectorError("layout changed")` instead of returning silently empty.
2. **No contact data.** Reviews give a first name, role, company size. I do **not** enrich to an email: reviewer names are
   personal data (GDPR / UK GDPR / India DPDP). A human finds a professional contact, and never messages through the review
   platform (against their rules). Drafts open with "Hi {first name}" and contain no reviewer quote.
3. **Classifier recall.** Regex misses sarcasm, other languages, and novel phrasing. Fixture-level tests prove behaviour, not accuracy.
   I have **no labelled real data**, so I cannot quote precision/recall. Next step is hand-labelling ~200 real reviews.
4. **Stale reviews look hot.** Recency decays in 5 steps; a 10-month-old review can still reach tier A on severity alone (one fixture does).
5. **Claims drift.** `ticmint_facts.yaml` is a snapshot of Ticmint's site on 2026-10-20 and the site contradicts itself
   (fee "1.5–7%" vs 5%/2%; Conversions API "available" vs "Coming Soon"). The drafter uses the pricing page and refuses the contested claims.
   If pricing changes, drafts go stale until someone edits the YAML.
6. **Cost at scale.** Rules path: $0. With a hosted LLM on ~5k reviews/month at ~500 tokens each: single-digit dollars on a small model. The cost is the data licence, not the model.
7. **Auth expiry.** Service-account keys don't expire but can be revoked; a failed sync falls back to CSV and the error shows in the run log (not yet alerting).
8. **mcp library churn.** `mcp` 2.x renamed `FastMCP`; I pinned `<2`. Migrating is a small change but untested.

## What I'd build next (one more week)

1. Hand-label 200 real reviews; report precision/recall per category; tune patterns.
2. Pull `status` back from the Sheet so tier thresholds learn from which leads actually reply (closed loop).
3. Slack alert for new tier-A leads and any failed run (today a failure is only a row in `Runs`).
4. Reddit / forum listener (Track 1) feeding the *same* store; one server, two signal types.
5. Company enrichment from the reviewer's company name via a free registry/LinkedIn-compliant route, behind a consent-aware allowlist.
6. Migrate to `mcp` 2.x; add per-claim `last_verified` and a weekly job that re-fetches ticmint.com/pricing and diffs the YAML.
