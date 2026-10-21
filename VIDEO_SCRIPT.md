# Walkthrough video, 6-7 minutes

1. **0:00 The problem (30s).** Review sites are full of unhappy organisers, but most reviewers are ticket buyers, not leads.
2. **0:30 Run it live (90s).** `python -m pytest -q` (7 pass) → `python run.py --source fixtures`. Show the JSON run record.
3. **2:00 The sheet (90s).** Open the Google Sheet (after you've done the 5-minute setup in README). Show Leads, Trends, and the Runs tab. Trigger the Action manually; show a new Runs row appear. Tab-to-tab: edit a `status` cell, re-run, show it survived.
4. **3:30 The MCP server (90s).** In Claude Desktop ask: "tier A leads whose main complaint is payouts" then "explain this review" with pasted text. Point out: same tools the scheduler uses, so the fact-check can't be bypassed.
5. **5:00 One decision I'd defend (45s).** The persona gate. Show an attendee row capped at 15 and a draft that contains no reviewer quote.
6. **5:45 One I'm unsure about (45s).** The 25% `ticmint_fit` weight: it's my opinion, not data; only reply data will settle it.
7. **6:30 Where it breaks (30s).** G2/Capterra are CSV by design; no contact enrichment on purpose; live Trustpilot untested in my sandbox.

Be upfront that the demo data is synthetic and flagged as such in the sheet.
