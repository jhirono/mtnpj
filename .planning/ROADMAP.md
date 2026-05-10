# Roadmap — Mountain Project Climbing Search

## Milestones

- ✅ **v1.0 Full-Stack Refactor** — Phase 01 (shipped 2026-05-09)
- 🔄 **v1.1 Coverage & Tagging** — Phases 02–03 (in progress)

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

**Goal:** Scrape Yosemite NP tick comments via Selenium, then benchmark and upgrade the tagging pipeline.

**Requirements:** 8 mapped | 0 unmapped ✓

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|-----------------|
| 2 | Tick Comments | Scrape Yosemite NP routes + tick comments via Selenium | TICK-01, TICK-02, TICK-03 | 4 |
| 3 | Tagging Upgrade | Benchmark models, improve prompts with tick data, audit + re-run | TAG-01–05 | 4 |

---

### Phase 02: Tick Comments (Yosemite NP)

**Goal:** Scrape Yosemite NP routes via async scraper, import into D1, then collect tick comments via Selenium authenticated session.

**Requirements:** TICK-01, TICK-02, TICK-03

**Plans:** 4 plans

Plans:
- [x] 02-01-PLAN.md — Schema migration (comments CHECK constraint + 'tick') + test scaffold
- [x] 02-02-PLAN.md — login_mp() implementation + parse_stats() updated to return list[dict]
- [ ] 02-03-PLAN.md — collect_ticks.py standalone tick collection orchestrator
- [ ] 02-04-PLAN.md — El Cap validation run + go/no-go gate + full Yosemite NP scrape/import/ticks

**Success criteria:**
1. Selenium login session authenticated and stable — MP authenticated pages load without redirect
2. Yosemite NP routes scraped and imported into D1 — route_ids available for tick comment collection
3. Tick comments scraped for Yosemite NP routes
4. Tick comments stored in D1 `comments` table and joinable to routes via route_id

**Build notes:**
- Scrape Yosemite NP area using existing async scraper (scrape_async.py) — no pre-imported CA data
- Import scraped routes into D1 using existing pipeline (chunked batches, FK-safe PRAGMA foreign_keys=0)
- MP login credentials via env vars — Selenium session kept alive across tick page requests
- `comments` table schema migration required: CHECK constraint must add 'tick' (Wave 0 blocker)
- Start with El Cap sub-area to validate the Selenium + tick flow before full Yosemite run
- Dedup guard: use route_id as key, INSERT OR IGNORE for tick comments

---

### Phase 03: Tagging Pipeline Upgrade

**Goal:** Benchmark Grok 4.3 vs GPT-5.5 Instant on a sample, migrate to the winning model, improve prompts to incorporate tick comment context, audit accuracy, and re-run on all D1 routes.

**Requirements:** TAG-01, TAG-02, TAG-03, TAG-04, TAG-05

**Success criteria:**
1. Grok 4.3 and GPT-5.5 Instant both evaluated on ≥50 sample routes — winner selected on accuracy vs cost
2. Tagging pipeline (`route_area_tagging.py`) migrated to winning model
3. Prompts include tick comment text as context where available
4. Before/after accuracy audit on ≥50 routes shows measurable tag quality improvement
5. All routes in D1 have tags applied and synced via `d1_tag_sync.py`

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
| 02 Tick Comments | v1.1 | 4/4 | Planned | — |
| 03 Tagging Upgrade | v1.1 | 0/? | Pending | — |
