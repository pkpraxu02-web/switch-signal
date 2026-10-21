# Ticmint — Growth Lead Assignment

**Candidate:** Ananya · **Date:** 20 Oct 2026
**Build:** Track 2, Review-Site Sentiment Agent ("SwitchSignal") → see `README.md`, code in this repo.

> **Evidence rules I followed.** Anything marked **[observed]** I fetched from a live page on 20 Oct 2026. **[estimate]** is my
> arithmetic with the assumption stated. **[hypothesis]** is a claim I could not verify. My Ahrefs access returned "Insufficient plan"
> on every endpoint (Site Explorer, Keywords Explorer, Brand Radar), so **I have no traffic, ranking or AI-citation numbers for
> Ticmint**, and nothing below pretends otherwise. Sections marked **[YOU FILL]** need your own real work; I have not invented any.

---

## 0. What I found in the first hour (the "what you notice" part)

1. **Ticmint's marketing site contradicts itself on its own core claim (fees), and answer engines will quote the contradiction.** [observed]
   - Pricing page: Starter 5%, Growth 2% (plus $19/mo or $15/mo annual).
   - White-label FAQ: "platform fee of 1.5–7% per transaction".
   - Homepage: "fees from 2%" and "Free to start". The 2% only applies on the paid plan.
   - Competitor fees quoted three ways on the homepage alone: "5–8%+" (table), "3.5–8%+" (FAQ), "8–15%" (ownership section). White-label FAQ adds "35–60% lower fees" with no source.
2. **Feature claims conflict.** Homepage says Meta Pixel, GA4 and Conversions API are "connected natively". Pricing page lists Meta Conversion API and advanced automation as **Coming Soon**. The white-label FAQ says Conversions API is available on Growth. [observed]
3. **Tracking hygiene problem on Ticmint's own funnel.** The nav CTA links use `utm_source=webiste-nav` (typo), and other CTAs use `web-home`, `website`, `pricing-page-us`, `mobile-menu`, `industry-White-Label-LP`: six naming schemes, mixed case, `utm_campaign` on one link only. Source reports in GA4 will fragment. [observed in link hrefs]
4. **Dead and broken links on money pages.** "Watch Demo" and "See full feature comparison" on the homepage point to `#`. Four vertical cards on the white-label page ("See Sports Platform" etc.) point to `#` even though the `/industries/` pages exist. The homepage's Basketball Federation case-study title links to the TEDx case study. [observed]
5. **Typos replicated sitewide.** Footer "Popular Searches" (on every page) contains "Whitelabel **evnet** Ticketing software". White-label page says "never see **Timint**". Growth plan card reuses Starter's tagline "Perfect for testing the waters". [observed]
6. **Content strategy is volume-led.** Blog index has 56 archive pages (≈ 600+ posts [estimate: 56 × ~12/page]); 10 posts published 5–19 Oct. [observed] The post list shows clusters of near-duplicate targets (6+ posts titled "Event Management Enterprise Software…", 10+ on DTCM permits, 3 "Unlocking Success: How to Choose the Best Event Ticketing Platform" with `-2` slugs, ~25 NFT/blockchain posts from the 2023–24 era). That is a cannibalisation and "scaled content" risk. [observed list; impact = hypothesis]
7. **The DTCM permit content is probably the most defensible organic asset.** It matches a product (permit.ticmint.com), a narrow high-intent query set and a compliance moat. [hypothesis: I can't see traffic] It should be protected and upgraded, not diluted by 600 generic posts.
8. **Review-site presence is thin relative to who is cited.** G2/Capterra/GetApp listings exist (G2 summary present; no ratings visible in what I retrieved, so verify). Eventbrite shows ~5,700 Capterra and ~900 G2 reviews. [observed] LLMs weight review and listicle sources heavily [hypothesis].
9. **The "best ticketing platform in India" results are vendor-authored.** The pages I saw (Dreamcast, KonfHub, Wowsly) each rank themselves first; Ticmint did not appear in the snippets I retrieved. [observed] Answer engines learn from those pages.
10. **There is a platform-builder customer hiding in the case studies.** Caribtix built a white-label marketplace *on* Ticmint: 100+ organisers, 30+ events/month, 100K+ tickets/month. [observed] One deal, many organisers. See D1/D2.

---

# PART A — The Build

Track 2, Review-Site Sentiment Agent. Everything is in `README.md` (setup, architecture, where it breaks, next week).
**Honest status:** tested on 10 clearly-labelled synthetic reviews; Google Sheets sync and live Trustpilot collection are written but not run (no credentials; sandbox network blocked trustpilot.com). I would rather say that here than have you discover it on your first run.

**Decision I'd defend:** the persona gate. Review sites are mostly ticket *buyers*. Treating "event was fake, no refund" as a lead would flood the sheet with people who will never buy white-label ticketing. Capping attendee voices at 15/100 made the top of the list organisers only.
**Decision I'm unsure about:** weighting `ticmint_fit` at 25%. It encodes my reading of Ticmint's pitch (white-label/data = 1.0, support = 0.6). If sales finds fee-complainers convert better than branding-complainers, I'd be wrong, and only reply data can tell me. That's why next-week item #2 is pulling Sheet status back into scoring.

---

# PART B — The Other Three (written)

### Track 1 — Internet Listener
- **Signal / source:** public posts where organisers complain about a platform. Free sources: Reddit (OAuth, free tier is non-commercial, so check terms before commercial use), Hacker News Algolia API, Google Alerts RSS on "eventbrite fees" / "alternative to eventbrite", YouTube comments, Quora. X is paid; LinkedIn forbids scraping.
- **Decides:** same persona gate as Part A (organiser vs attendee), plus a *buying-moment* classifier: "planning a festival", "need ticketing for…", "switching from…" outranks plain venting. Score = intent × recency × reachability (can a human reply helpfully?).
- **Action:** drops rows in the same store/Sheet. **Human approves everything.** Public replies in forums are where brands get banned for self-promotion, so the agent drafts a *useful, non-salesy answer* (e.g. a fee calculation) and a human posts or skips.
- **Worst failure:** reputational. A tone-deaf reply, or replying where the community forbids promotion, burns the channel. Also mis-reading sarcasm.
- **Cost/month:** infra $0 (Actions); classifier $0 with a local model or ~$5–20 hosted for ~2k posts/day [estimate: ~400 tokens each on a small model]. Human time dominates.

### Track 3 — Multi-Tool Orchestration
- **Signal:** a person asking in plain language ("what did we spend last week and what did it produce?") plus a nightly sync. Sources: Google Ads, Meta Ads, GA4, Ticmint's own order data (via the Enterprise REST API/webhooks), CRM or the Part A Sheet.
- **Decides:** which sources a question needs, and how to join them. The hard part is **metric definitions**, so the MCP server holds a metrics dictionary (spend in one currency, one attribution window, "qualified signup" defined once) and the model may only call defined queries, read-only.
- **Action:** answers with the numbers *and* the definition used; flags anomalies (spend up, signups flat). It **never changes budgets**; any spend change is a human click.
- **Worst failure:** a confidently wrong answer from mismatched definitions (INR vs USD, Meta 7-day-click vs GA4 last-click). Mitigation: every answer prints its definitions; reconcile each source to its platform total weekly and alarm on >5% drift.
- **Cost/month:** connectors are free APIs; BigQuery/DuckDB free tier; LLM ~$10–40 [estimate: a few hundred queries]. Looker Studio free for the visual layer.

### Track 4 — Funnel Measurement Agent
- **Signal:** scheduled synthetic journeys (Playwright, free on Actions) through ticmint.com → `app.ticmint.com` signup → first event published, plus GA4 BigQuery export and GTM container diffs.
- **Decides:** for each step, did the expected GA4/Meta/GTM events fire, were UTMs preserved across the domain hop, did consent mode block them? Severity = funnel stage × spend exposed (a broken `pricing-page` source during a paid push is red; a blog page is amber). It would have caught finding #3 (the `webiste-nav` UTM) on day one.
- **Action:** opens a ticket and Slack alert with the exact failing step and a screenshot. It fixes nothing automatically (changing a tag in production without review is how you create the next break).
- **Worst failure:** synthetic tests pass while real users fail (different browsers, ad blockers, consent states), giving false comfort. Mitigation: compare synthetic vs real event counts per step weekly.
- **Cost/month:** ~$0 (Actions + BigQuery free tier); LLM only to summarise diffs, <$5. The scarce resource is a person who owns the tracking plan.

---

# PART C — The Organic Visibility Agent

## C1. Fundamentals

**My model of the three surfaces**
- **SEO:** earn a ranked blue link. Unit of competition = a *page* versus other pages for a query. Levers: intent match, content depth, internal links, authority (links), technical health. You measure rank, clicks, CTR.
- **AEO (answer engines):** the engine resolves the query itself (featured snippets, AI Overviews, "People also ask", voice, and chat-style answers with citations). Unit of competition = a *passage* (a self-contained, extractable answer) versus other passages. Levers: question-shaped headings, a direct 40–60-word answer first, tables, FAQ/HowTo structure, schema, and being on sources the engine already trusts. You measure *citation* and *answer inclusion*, not rank.
- **GEO (generative engines):** the model *recommends* brands in free-form answers ("which ticketing platform should I use for a marathon in India?"). Unit of competition = the **brand/entity** in the model's memory plus whatever it retrieves live. Levers: consistent facts about you across many independent sources (reviews, Reddit, listicles, press, your own site), clear entity definition ("Ticmint = white-label event ticketing"), comparison content, and a positive, accurate review footprint. You measure *mention rate, position in the answer, sentiment, factual accuracy*, and results are probabilistic: the same prompt gives different answers.
- **What changes operationally:** SEO is page-by-page and deterministic-ish. AEO/GEO are *source-footprint* games, so a single claim repeated inconsistently across your own pages (fees!) becomes an error the models repeat.

**My hands-on work on this channel — [YOU FILL, with real facts only]**
> Suggested structure: *what site/client, what I owned (strategy / briefs / on-page / technical / links), constraints, what I'd do differently.* Your profile says 11 years in marketing and performance work scaling university applications while cutting paid spend; if you have organic work at ClassFull or inside the institutions, write it here. If you have little hands-on SEO, say that plainly and lead with the Part A/C artefacts as evidence you can build the system. The evaluators said "don't throw numbers in the air"; a candid scope beats an inflated one.

**Outcome — [YOU FILL]** (before/after, window, source such as GSC export, and what else changed that period.)

**Audit of ticmint.com** — method: live fetch of home, pricing, white-label, blog index, `robots.txt`, `sitemap.xml`, `llms.txt`, plus search-result snapshots for competitor/category queries. **Not done:** rankings, traffic, backlinks, Core Web Vitals, JSON-LD validation, AI-citation tracking (no tool access). Those are the first things I'd run with access.

| # | Finding | Evidence | Why it matters | Fix (priority) |
|---|---|---|---|---|
| 1 | Fee claims contradict (1.5–7% / 5% / 2% / competitor 3.5–15%) | home, pricing, white-label FAQ | Engines and prospects quote whichever they find; erodes trust | One canonical fee table, one competitor-fee sourcing rule; remove "35–60%" unless sourced (**P0**) |
| 2 | Feature claims conflict (Conversions API) | home vs pricing "Coming Soon" | Over-promise risk; same engine-misquote problem | Align copy to what's live (**P0**) |
| 3 | Sitewide footer "Popular Searches" keyword block with typo "evnet" | every page | Low-value, spam-adjacent, typo repeated on every URL | Delete block or turn into real links to hub pages (**P1**) |
| 4 | Dead `#` links on money pages; wrong case-study link | home, white-label | Lost internal links on highest-authority pages; broken UX | Point to `/industries/*`, build `/compare/` (**P0, 1 hour**) |
| 5 | UTM fragmentation (`webiste-nav` etc.) | link hrefs | Attribution for every campaign is polluted | UTM convention + lint in GTM/CI (**P0**) |
| 6 | Cannibalising/duplicate content clusters; `-2/-3` slugs; stale-year titles ("2024", "2025 Updated") | blog list / llms.txt | Splits signals; scaled-content risk; looks templated ("N Powerful…") | Content inventory → merge/redirect/prune; keep one canonical per intent (**P0 audit, P1 execution**) |
| 7 | ~25 NFT/blockchain posts vs a product that is now white-label ticketing | blog list | Dilutes topical focus; entity confusion for engines | Consolidate to 1–2 pillar pages or noindex/prune (**P2**) |
| 8 | `llms.txt` is auto-generated and lists hundreds of posts with no curation | `/llms.txt` | A flat dump signals nothing; and no major vendor has confirmed it influences answers, so expect small effect | Curate to ~15 defining URLs (pricing, white-label, case studies, comparisons, DTCM guide); keep cheap (**P2**) |
| 9 | `robots.txt` allows all agents (good) and has no AI-bot rules; sitemap index is healthy (post/page/case-studies/industries) | robots.txt, sitemap | AI crawlers can reach you. Do **not** block them | Keep open; log AI-bot hits (**P1**) |
| 10 | `og:type=article` on home and pricing | page meta | Minor; should be `website` | Fix in AIOSEO (**P3**) |
| 11 | Comparison pages exist for ~15 rivals but are unlinked from nav and the homepage compare link is dead; several rivals (Ticketmaster, StubHub, Live Nation) aren't real alternatives | blog list | The best BOFU assets are hidden; mismatched rivals look like keyword bait | `/compare/` hub; keep real rivals (Eventbrite, Ticket Tailor, Townscript, Eventzilla, Humanitix, vivenu, Weezevent); add "when NOT to choose Ticmint" (**P0**) |
| 12 | Third-party footprint: review counts apparently small; vendor-authored "best X" lists dominate category results and Ticmint is absent from those I saw | G2/Capterra, SERP snapshots | GEO runs on independent corroboration | Review-collection programme from live customers (they're real: BAI, BFI, Caribtix); listicle outreach to *independent* publishers (**P0**) |
| 13 | Strong assets under-used: SOC 2 + ISO 27001 badges (images), case studies with real numbers, press logos (Entrepreneur UK, Khaleej Times, Indian Express, Gulf News, India Today) | home | These are entity-trust signals | Add a `/trust/` page with certificate details and an `Organization` + `Review` schema; the FAQ's "ISO-grade security" wording is weaker than the badge, so align (**P1**) |
| 14 | Unverified: structured data (my fetch strips JSON-LD), Core Web Vitals on Elementor pages, indexation of tag/author sitemaps | n/a | Could be fine or a real problem | Run Rich Results Test, PageSpeed, GSC coverage (**first task**) |

**Recommendation in one line:** before producing anything new, spend two weeks making the existing site *consistent and linked* (findings 1, 2, 4, 5, 6, 11, 12), because every future AEO/GEO gain is multiplied or cancelled by whether the facts agree.

## C2. The agent — "Visibility Loop"

**Signals read (and from where)**
| Signal | Source |
|---|---|
| Queries, pages, impressions, position | Google Search Console API (free) |
| Landing pages and AI-referrer sessions (`chatgpt.com`, `perplexity.ai`, `gemini.google.com`, `copilot.microsoft.com`, `claude.ai`) | GA4 / BigQuery export |
| AI-crawler hits (GPTBot, OAI-SearchBot, ChatGPT-User, PerplexityBot, ClaudeBot, Google-Extended) | CDN / server logs |
| Prompt-panel results: ~100 buyer-intent prompts × 4 engines × 2–3 geos × 3 repeats | API calls to each engine (or a tool such as Ahrefs Brand Radar) |
| SERP features and who is cited | SERP API / manual sample |
| Third-party footprint: review counts/ratings, Reddit threads, listicle inclusion | G2/Capterra pages, Reddit API |
| Brand-fact accuracy: what engines *say* about Ticmint's price/features | same panel, graded against `ticmint_facts.yaml` |
| Product truth: pricing and feature pages | weekly fetch + diff |

**Prioritisation logic (not a list of inputs)**

```
priority(task) = value × winnability × speed ÷ effort

value       = intent_weight (switch/compare 1.0 · "best X" 0.7 · how-to 0.3)
              × market_weight (IN, UAE, UK, US per revenue target)
              × volume_proxy  (GSC impressions or tool volume; for prompts: panel frequency)
winnability = the gap to the leader, adjusted for whether a citable source exists
              (if engines cite G2/Reddit for this prompt and we have no presence there, the task is "get on G2",
               not "write a post")
speed       = 1.0 if edit to existing page · 0.6 new page · 0.3 needs third-party action
effort      = hours, estimated from task type
override    = any NEEDS_FIX on a *brand-fact* error jumps to the top (a wrong price outranks any growth task)
```
Worked example: prompt cluster "eventbrite alternative with lower fees" (value 1.0×1.0×high), where the panel shows Ticket Tailor and a vendor listicle cited and Ticmint not mentioned (winnability high, gap is large). Cheapest lever is existing page + consistent fee table (speed 1.0), so the agent queues "rewrite /compare/eventbrite with a canonical fee table and a 50-word answer block" ahead of "write five new posts".

**What it produces / does**
Weekly queue of ranked tasks, each with a brief, the evidence, and the predicted lever; PRs for metadata/internal-link/schema fixes; a brand-fact error ticket when an engine misstates Ticmint; review/listing outreach targets; a monthly report tying visibility to demos.

**Where the human sits, and why there**
1. **Approves the queue** (strategy and trade-offs).
2. **Approves any page that states a price, fee, feature, security or legal claim.** Wrong claims here create customer and regulatory risk, and models spread them.
3. **Does not review** schema validation, broken links, internal-link suggestions or stale-year fixes (agent opens PRs; human skims diffs).

## C3. Autonomous publishing

**Would I let it? Not on money or claim pages, and not in the first quarter anywhere.**

- **Never autonomous:** pricing, comparison, white-label, security/compliance, case studies, anything naming a competitor. A mistake is a legal/brand event and gets amplified by engines.
- **Allowed after proof:** narrow, templated, data-sourced, reversible classes. E.g. "events on Ticmint this month" listing pages built from Ticmint's own events data; a DTCM fee table that updates from the official source *with a diff alert*. These are generated from structured truth, not model prose.
- **Everything else:** agent drafts → automated fact-check against `ticmint_facts.yaml` → human editor 5-minute checklist (claims verified, one original contribution such as a customer quote, data or screenshot, no near-duplicate of an existing page) → publish.

**What must be true to move the line**
- 90 days with ≥95% automated fact-check pass and human edit distance <10% on the class in question.
- A duplicate/cannibalisation check that blocks publishing when an existing URL targets the intent.
- One-click rollback (<1 hour) and a canary: 5 posts, wait 3–4 weeks, watch indexation and engagement before widening.
- Zero Google policy flags in that window.

**Damage if wrong, and how fast I'd know**
- *Factual error* (wrong fee on a live page): visible within hours via claim-diff monitoring and the brand-fact probe; cost = sales confusion, possibly a mis-sold deal.
- *Scaled low-value content* (Google's scaled content abuse policy; an algorithmic or manual hit): slow, 2–8 weeks, shows as sitewide impressions decline in the blog cluster, rising "crawled — not indexed", and falling average position. It can drag the whole domain, including pricing. This is not hypothetical here: finding #6 already looks like this pattern.

## C4. Measurement (the hard part)

**Principle:** there is no rank, often no click, no referrer. So measure at three layers and never rely on one.

| Layer | What | How collected | Cadence |
|---|---|---|---|
| **1. Presence** | Mention rate, citation rate, position-in-answer, sentiment, share of voice vs 4 named rivals on a fixed prompt panel | API runs, 3 repeats per prompt (outputs are non-deterministic), panel frozen and versioned; report as a rate with a confidence interval, not a point | Weekly |
| **2. Accuracy** | % of brand-prompt answers whose price/feature claims match `ticmint_facts.yaml` | same panel, auto-graded + 10% human spot-check | Weekly |
| **3. Demand proxies** | Branded search impressions (GSC), direct/unattributed landings on `/pricing` and `/compare/*`, AI-referrer sessions (GA4 regex), AI-bot crawl frequency (logs) | GSC, GA4 BigQuery, CDN logs | Daily collect, weekly read |
| **4. Business** | "How did you hear about us?" free-text on signup and demo form with an "AI assistant (ChatGPT, Perplexity…)" option; sales-call tagging; assisted signups | form field + CRM | Monthly |

**Attribution:** treat prompt clusters as test vs control. Ship an intervention (e.g. canonical fee table + answer blocks) on half of matched clusters, stagger the rest, and compare mention-rate change (difference-in-differences). This is what separates "we published, and the line went up" from "the line went up."

**Cost note:** panel of ~100 prompts × 4 engines × 2 geos × 3 repeats ≈ 2,400 calls/week. At roughly $0.01–0.05 per call [estimate, vendor pricing varies] that is ~$100–500/month, or buy a tool.

**Numbers that tell me to shut it down** (pre-registered, so I can't talk myself out of them)
1. After **two full quarters**, bottom-funnel prompt mention rate is within ±3 percentage points of baseline *and* control clusters moved the same → no causal effect.
2. Cost per qualified signup attributable (self-reported + AI-referrer + assisted) exceeds **1.5× blended CAC** for two consecutive quarters.
3. **Safety kill (immediate):** more than **10%** of brand-prompt answers state a wrong fee or feature and the source can't be fixed within 14 days, or any manual action notice.

## C5. Failure modes (the three that worry me most)

1. **Content flood → quality demotion and claim drift.** Detect with: indexed-vs-published ratio on `/blog`, cluster-level GSC impressions/position trend, weekly duplicate-intent detector, and the claim-diff check on every publish. Build the detector *before* the generator.
2. **Measurement mirage.** Non-deterministic outputs, geo/personalisation effects and prompt-wording sensitivity make noise look like progress. Detect with: fixed versioned panel, repeats, control clusters, CI bands; an alarm if week-on-week swing on *untouched* control prompts exceeds the effect size I'm claiming.
3. **Misinformation about Ticmint propagates** (wrong fees/features) from its own inconsistent pages or a competitor listicle. Detect with: weekly brand-fact probe versus the facts file, source tracing (which cited URL taught the engine the wrong thing), auto-ticket to correct that source. Fix the root pages first (audit #1, #2).

---

# PART D — Growth Strategy

## D1. ICP

**Segments:** (1) small self-serve organisers (workshops, dance academies, community); (2) **professional independent organisers/promoters** (festivals, experiential, club/music, clubs & leagues; recurring events); (3) enterprise sports federations, stadiums and venues; (4) corporate/B2B conferences and associations; (5) colleges and universities; (6) event agencies and platform-builders who resell (Caribtix pattern); (7) permit-seekers in Dubai (DTCM) as a top-of-funnel pool.

### Primary ICP: professional independent organisers (mid-market)
- **Profile:** 4+ ticketed events a year or ~$100K–$5M annual ticket value [assumption], currently on Eventbrite, Ticket Tailor, Townscript or BookMyShow, in India, UAE, UK, US. 5–50 staff.
- **Buyers:** founder/MD (decides), marketing or ops lead (runs it), finance (cares about payout and fees).
- **Core pain:** fees on every ticket, no ownership of buyers (can't re-market), their brand hidden behind the marketplace, slow payouts.
- **Trigger events:** fee/pricing change by the incumbent (Eventbrite removed its free tier for >25-ticket events in late 2023 per third-party coverage, and acquirers/ratings changes are natural switching windows), a platform payout hold, launching a second or third edition, expanding to a new city/country, a failed on-sale.
- **Why primary:** urgency is high and quantifiable (fees are a P&L line); budget exists because they already pay a platform; sales cycle is short (days to weeks) so the machinery in Part A has data to learn from; expansion is *more events and higher volume* on the same account.

### Secondary ICP: enterprise sports federations, leagues and venues
- **Profile:** national federations, leagues, stadium operators, large annual festivals (BAI, BFI, Times Group-type).
- **Buyers:** secretary-general/CEO, commercial head, IT/security, procurement.
- **Pain:** zero or fragmented digital ticketing, need for audit trails and custom integrations, a major event on a hard date.
- **Trigger:** a confirmed fixture/season (the BFI case: onboarded in 24 hours for FIBA qualifiers), tender/RFP, a bad on-sale on a rival.
- **Why secondary, not primary:** the biggest accounts and the best proof (BAI +27% revenue, BFI 66,500+ tickets), but cycles of months, relationship-led, and you can't growth-hack them. Treat as founder-led plus case-study-fuelled ABM of ~50 named accounts.

**Third, opportunistic:** colleges and universities (fests, alumni events, convocations). If you've worked inside institutions for five years, this is a network advantage Ticmint's cold outreach lacks, and `/industries/university-college/` already exists. Keep it in the plan **only if** you can name real contacts; otherwise cut it.

**Platform-builders/agencies (Caribtix pattern)** are my best *expansion* hypothesis (one customer = 100+ organisers), but I have one data point, so I treat it as a partner experiment, not an ICP.

## D2. Channel prioritisation

**Available:** SEO/AEO/GEO · review sites · outbound email + LinkedIn · paid search · paid social · partnerships/agencies · referral (Ticmint already has "Refer & Earn up to $3000") · PR/trade press · communities (Reddit etc.) · YouTube/webinars · WhatsApp · trade shows · affiliates · marketplaces/app directories.

**Chosen for next two quarters**

1. **Signal-led outbound** (job: pipeline).
   - *Why it fits:* professional organisers are findable and the pain is public (reviews, posts); short cycle means fast learning. Fuelled by the Part A agent.
   - *90-day success:* 600 contacted (human-approved), ≥8% reply, ≥25 qualified conversations, ≥8 demos, ≥3 paying organisers.
2. **Bottom-funnel search + AEO/GEO** (job: trust + pipeline). *Not* "more blog posts": fix consistency, build the `/compare/` hub, protect the DTCM moat, and earn review/listicle footprint.
   - *90-day success:* audit P0s done; panel baselined; mention rate on switch/compare prompts up measurably vs control; 40+ real G2/Capterra reviews collected from live customers; demos with `/compare` or `/pricing` as first landing page >5/month.
3. **Referral + partner channel** (job: trust + expansion). Existing referral programme plus agencies and venues who bring many organisers.
   - *90-day success:* 5 active partners, 2 referral-sourced paying organisers, one agency pilot with a written volume commitment.

**Explicitly not doing, and why**
- **Paid social at scale:** organisers don't browse Meta looking for ticketing software; CAC will be poor until positioning is proven. (A small paid-*search* test on "eventbrite alternative" for measurement only.)
- **Trade shows and sponsorships:** long feedback loops, high fixed cost, can't attribute at this stage.
- **Thought-leadership/brand content on LinkedIn:** slow; outbound is already doing the targeted version.
- **More NFT/web3 and event-listing content:** off-ICP and diluting.
- **Marketplace/discovery listing:** Ticmint's pitch is *not* being a marketplace; building one contradicts the positioning.
- **Reddit/community replies:** one-person, high-risk, small upside; revisit via Track 1 listener once there is capacity.

## D3. Cold outreach motion (primary ICP)

- **Channel and sequence:** email-first with LinkedIn touches, 4 touches over 14 days. T1 (day 0): the specific complaint/trigger + one relevant fact + an offer to run their numbers. T2 (day 3, LinkedIn): connection, no pitch. T3 (day 7): a micro-asset (a fee calculation for *their* event type or a short teardown of their checkout). T4 (day 14): graceful close. Replies within 24h by a human. Max 3 touches per person; hard suppression list.
- **Worth contacting vs ignoring:** tier A/B from Part A (organiser voice, strong complaint, fit ≥0.7, in-market country, recent) **or** a live trigger (new event announced on a competitor's platform). Ignore: attendee voices, no complaint, no identifiable business, outside the four markets, or already a customer.
- **Personalisation at volume without mail-merge theatre:** the agent supplies *what* the specific problem is and the *facts allowed to be said*; a human supplies the contact and adds one line only they can write. The email never quotes the reviewer; it references the public review and asks for volume so the reply is a calculation, not a pitch. That offer is the personalisation.
- **Connection to Part A:** it's the engine. Sheet row → human finds a professional contact off-platform → sends from their own inbox → marks `status`. Fed back to re-weight `ticmint_fit` after ~100 sends.
- **Measure:** reply rate, positive-reply rate, meeting rate, qualified-opp rate, bounce/unsubscribe/spam-complaint rate; cost per qualified conversation.
- **Kill number:** after 300 sends per segment, **<3% reply or >2% spam complaints or >5% bounce** → stop and fix targeting/domain before sending more. (Complaints and bounces protect the domain that also sends product email.)
- **Tools:** the Part A repo + Sheet; Apollo/Hunter free tiers or manual LinkedIn for contacts; Instantly/Smartlead or Gmail with a dedicated sending domain (SPF, DKIM, DMARC, warm-up); Calendly.
- **Compliance:** B2B legitimate-interest basis in UK/EU with an opt-out in every email; India DPDP and UAE rules need review by counsel; I am not a lawyer.

## D4. Funnel & qualification

| Stage | Meaning for Ticmint | Primary channels | The action that matters | Metric | Biggest drop-off risk |
|---|---|---|---|---|---|
| **TOFU** | Organiser realises their platform is costing them | search/AEO, outbound, referral | Reads a compare/pricing page or replies | Qualified visits to `/compare`, `/pricing`; reply rate | Inconsistent fee claims make them distrust the page |
| **MOFU** | Evaluating Ticmint vs incumbent | demo, fee calculator, case studies | Starts a free event, or shares ticket volume for the numbers | Signup→published-event rate; calculator submissions | Setup friction; needing a sales call for what should be self-serve |
| **BOFU** | Commits real events | demo, migration support, pricing | First paid ticket sold on their own domain | Time-to-first-paid-ticket; demo→win | Gateway/domain setup stalls before the on-sale date |

- **Sales-ready:** published an event *or* shared volume; ≥$100K annual ticket value (or ≥4 events/yr); in a served market; decision-maker or influencer engaged; a dated event within 90 days.
- **Nurture:** right profile but no dated event, or happy with incumbent now. Trigger-based follow-ups (a new event announced, an incumbent fee change).
- **Disqualify early:** one-off personal events, free-only events with no growth, event types Ticmint can't serve, countries it doesn't operate in, and anyone needing a marketplace's discovery audience (they will churn).

## D5. Metrics

**North star:** **Monthly GMV from organisers who sold on their own Ticmint domain and ran ≥2 events** ("repeat white-label GMV").
*Why now (not in two years):* Ticmint's revenue is take-rate × volume, and its entire thesis is *ownership*; organisers who return for a second event on their own domain prove the thesis and carry the expansion. Sign-ups would reward the free tier; GMV alone would reward one-off giant events. In two years, net revenue retention or a margin metric may be better.

**Leading (each changes a decision)**
1. *Activation:* % of new organisers who publish an event and sell a ticket within 14 days. → if low, fix onboarding before buying traffic.
2. *Qualified conversations/week from outbound.* → tune the Part A weights and send volume.
3. *Share on custom domain.* → if free-tier users never convert to domain, repackage Growth.
4. *Demo→qualified-opportunity rate.* → tightens or loosens the ICP gate.
5. *Mention rate on switch/compare prompts (panel).* → decides continued investment in the C-agent.

**Lagging**
1. *Repeat white-label GMV, take-rate realised.* → whether pricing (2% vs 5%) is leaving money or conversion on the table.
2. *12-month organiser retention / events per organiser.* → whether the channel brings keepers.
3. *CAC payback by channel.* → where to move the next dollar.

## D6. Risks & trade-offs

**Biggest assumptions**
- Organisers feel the fee/ownership pain enough to *migrate* (not just complain). Complaining is public; migration is rare and event-calendar-bound.
- Mid-market organisers will self-serve or accept a light-touch sale.
- Ticmint's claims (2%, T+3 settlement, features) are accurate and consistent; I verified only what's on its website.

**Most likely to go wrong in six months**
1. **Reply rate is fine, conversion is weak** because of migration friction (historical data, scheduled events live on another platform). *Response:* migration offer for the *next* event, not an in-flight one.
2. **Trust leaks from inconsistent claims** (the audit's #1/#2) as sales and engines quote conflicting numbers. *Response:* fix first; it's cheap.
3. **Content volume drags organic down** instead of lifting it. *Response:* the C3 gates and an inventory-prune before any new publishing.

**If early signals come back flat (say 6 weeks, outbound <3% reply):** change the audience before the copy. Check list quality, then trigger (switch to people with a dated upcoming event), then the offer (numbers vs deck). Don't increase volume to compensate.

**What I'm knowingly trading away:** brand-awareness investment and the enterprise pipeline's speed in exchange for fast, attributable learning from the mid-market; breadth of channels for depth in three; and a vanity traffic story (the blog's volume) for a smaller, more trustworthy footprint.

---

# PART E — Proof of Work — [YOU FILL; I can't supply this]

I have no access to your pages or account data, and the brief explicitly says not to throw numbers in the air. Here is a structure that answers what they asked, with the fields only you can fill.

**1. WordPress + Elementor** — 2–4 live URLs. For each: *what was mine / what was briefed to others; constraints (theme, speed budget, brand); what I'd change now; before/after with the source (GSC, GA4, Hotjar), and the date range.* They will check the page is live and built by you.

**2. Campaigns I ran**
- *Platforms used for B2B SaaS performance marketing:* list only ones you've personally run. Your profile shows Google Ads and Meta, mostly for education institutions; **if you haven't run B2B SaaS, say that and frame education admissions (a considered, high-ticket, multi-stakeholder funnel) as the closest analogue.** Don't relabel.
- *Max ROAS and the average you maintained:* give the number, the account, the period, the spend level, and what ROAS was measured against (platform-reported vs CRM-closed). A 12× ROAS on £2k spend and 4× on £200k are different claims; state which.

**3. Anything else I've built:** this repo (Part A) and the Part C audit; add ClassFull's own automations, dashboards or skills (e.g. your education-copy framework as a Claude skill) if you can show them.

---

# AI-USE NOTE (half a page; **edit this with your own overrides**)

*Draft written by the AI that helped build this. Replace/extend with what you actually overrode.*

- **Where AI did the work:** research synthesis, the first version of all code (collectors, taxonomy, scoring, drafter, MCP server, tests), the audit findings and the written Parts B–D.
- **Where I (human) must override or have overridden — [YOU FILL]:** at minimum, the scoring weights (the 35/25/15/15/10 split is my reasoning, not data), the ICP choice, the channel cuts, and anything in Part E.
- **Where the AI was wrong or hit limits during this build (real events):**
  1. First test run failed because the sandbox installed `mcp` 2.x, which renamed the `FastMCP` class my code used. Fixed by pinning `mcp<2`, and documented as a risk.
  2. I assumed Ahrefs would supply traffic and AI-visibility data. Every endpoint returned "Insufficient plan", so the audit is crawl-based and says so rather than guessing numbers.
  3. The sandbox blocked trustpilot.com, so the live collector has never fetched real data, and Google Sheets sync has never run against Google. The README says so at the top.
  4. A README sentence claimed "3 of 10 fixtures are attendee reviews"; the actual run showed 2 attendee + 1 no-complaint. Caught on re-reading the output and corrected.
- **Confidently-wrong risks I'd watch for in your hands:** the AI will happily write plausible ROAS, traffic or ranking numbers. None appear here for that reason. Keep it that way.

---

*Video (5–8 min) is yours to record; a suggested running order is in `VIDEO_SCRIPT.md`.*
