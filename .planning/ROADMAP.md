# Roadmap — Mountain Project Climbing Search

## Milestones

- ✅ **v1.0 Full-Stack Refactor** — Phase 01 (shipped 2026-05-09)
- 🔄 **v1.1 Coverage & Tagging** — Phases 02–04 (in progress)

## Phases

<details>
<summary>✅ v1.0 Full-Stack Refactor (Phase 01) — SHIPPED 2026-05-09</summary>

- [x] Phase 01-01: Async scraper (5/5 plans) — completed 2026-05-09
- [x] Phase 01-02: D1 schema + import pipeline (5/5 plans) — completed 2026-05-09
- [x] Phase 01-03: Hono Worker API (5/5 plans) — completed 2026-05-09
- [x] Phase 01-04: Frontend migration to Worker API (5/5 plans) — completed 2026-05-09
- [x] Phase 01-05: Tagging pipeline (5/5 plans) — completed 2026-05-09

Full archive: `.planning/milestones/v1.0-ROADMAP.md`

</details>

## v1.1 Coverage & Tagging

**Goal:** Import all pre-tagged state data into D1, collect tick comments for Yosemite NP via Selenium, then benchmark and upgrade the tagging pipeline.

**Requirements:** 10 mapped | 0 unmapped ✓

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|-----------------|
| 2 | Data Import | Import AZ/CA/CO/OR/UT pre-tagged JSON into D1 | IMPORT-01, IMPORT-02 | 3 |
| 3 | Tick Comments | Collect Yosemite NP tick comments via Selenium (routes already in D1) | TICK-01, TICK-02, TICK-03 | 4 |
| 4 | Tagging Upgrade | Benchmark models, improve prompts with tick data, audit + re-run | TAG-01–05 | 4 |

---

### Phase 02: Data Import

**Goal:** Import all 5 pre-tagged state datasets (AZ, CA, CO, OR, UT) into D1 with integrity validation.

**Requirements:** IMPORT-01, IMPORT-02

**Success criteria:**
1. AZ, CA, CO, OR, UT routes visible and queryable via the Worker API
2. Total D1 route count increases by the expected amount per state (no silent data loss)
3. Post-import validation confirms: no duplicate route_ids, all required fields populated

**Build notes:**
- CA file is at `data/old/california_routes_tagged.json` (131MB) — includes Yosemite NP routes
- CO file is at `data/colorado_routes_tagged.json` (100MB)
- AZ, OR, UT files are in `data/` at 38MB, 16MB, 58MB respectively
- NV + WA already imported — skip those
- Use existing import pipeline (chunked batches, FK-safe PRAGMA foreign_keys=0)
- Yosemite NP routes are in CA data — Phase 3 tick comment collection will use these route_ids

---

### Phase 03: Tick Comments (Yosemite NP)

**Goal:** Collect tick comments for Yosemite NP routes via Selenium authenticated session. Route records already in D1 from CA import — no route data re-import.

**Requirements:** TICK-01, TICK-02, TICK-03

**Success criteria:**
1. Selenium login session authenticated and stable — MP authenticated pages load without redirect
2. Yosemite NP route_ids looked up from D1 (from CA import) — no duplicate route records created
3. Tick comments scraped for Yosemite NP routes
4. Tick comments stored in D1 `comments` table and joinable to routes via route_id

**Build notes:**
- Query D1 for existing Yosemite NP route_ids before scraping (filter by area hierarchy)
- MP login credentials via env vars — Selenium session kept alive across tick page requests
- `comments` table exists in D1 schema — verify column fit for tick comment structure
- Start with El Cap sub-area (~261K already scraped) to validate the Selenium + tick flow
- Dedup guard: use route_id as key, INSERT OR IGNORE for tick comments

---

### Phase 04: Tagging Pipeline Upgrade

**Goal:** Benchmark Grok 4.3 vs GPT-5.5 Instant on a sample, migrate to the winning model, improve prompts to incorporate tick comment context, audit accuracy, and re-run on all newly imported data.

**Requirements:** TAG-01, TAG-02, TAG-03, TAG-04, TAG-05

**Success criteria:**
1. Grok 4.3 and GPT-5.5 Instant both evaluated on ≥50 sample routes — winner selected on accuracy vs cost
2. Tagging pipeline (`route_area_tagging.py`) migrated to winning model
3. Prompts include tick comment text as context where available
4. Before/after accuracy audit on ≥50 routes shows measurable tag quality improvement
5. All AZ, CA, CO, OR, UT routes have tags applied and synced to D1 via `d1_tag_sync.py`

**Build notes:**
- Grok 4.3 batch: $0.625/$1.25 per 1M tokens — strong reasoning, 2M context
- GPT-5.5 Instant batch: $2.50/$15 per 1M tokens — highest accuracy, 52.5% fewer hallucinations
- Current pipeline uses OpenAI batch API — Grok API may require client swap
- Tick comments from Phase 3 feed as additional context field in prompt
- Audit methodology: manually score sample, compare pre- vs post-prompt-improvement tags

---

## Progress

| Phase | Milestone | Plans | Status | Completed |
|-------|-----------|-------|--------|-----------|
| 01 Full-Stack Refactor | v1.0 | 5/5 | Complete | 2026-05-09 |
| 02 Data Import | v1.1 | 0/? | Pending | — |
| 03 Tick Comments | v1.1 | 0/? | Pending | — |
| 04 Tagging Upgrade | v1.1 | 0/? | Pending | — |
