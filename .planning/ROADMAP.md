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
- [x] 02-03-PLAN.md — collect_ticks.py standalone tick collection orchestrator
- [x] 02-04-PLAN.md — El Cap validation run + go/no-go gate + full Yosemite NP scrape/import/ticks

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

**Goal:** Benchmark gpt-4o-mini vs gpt-5-nano vs gpt-5-mini on a 50-route sample, migrate to the winning model, improve prompts to incorporate D1 tick comment context, audit tag quality, and re-run on all 2,966 Yosemite NP routes.

**Requirements:** TAG-01, TAG-02, TAG-03, TAG-04, TAG-05

**Plans:** 5 plans

Plans:
- [ ] 03-01-PLAN.md — D1 tick enrichment: export tick comments from local D1, merge into Yosemite route JSON as route_tick_comments (TAG-03)
- [ ] 03-02-PLAN.md — LLM benchmark: run gpt-4o-mini, gpt-5-nano, gpt-5-mini on 50-route sample; user checkpoint for model selection (TAG-01, TAG-04)
- [ ] 03-03-PLAN.md — Pipeline migration: add TAGGING_MODEL constant, replace both hardcoded model strings at line 192 + line 449 (TAG-02, TAG-03)
- [ ] 03-04-PLAN.md — Full Yosemite run: tag all 2,966 routes with upgraded pipeline; user spot-check audit before D1 sync (TAG-04, TAG-05)
- [ ] 03-05-PLAN.md — Remote D1 sync: push Yosemite data to Cloudflare D1; delete Washington data; user verifies UI (TAG-05)

**Success criteria:**
1. gpt-4o-mini, gpt-5-nano, and gpt-5-mini evaluated on 50-route sample — winner selected on accuracy vs cost (D-03)
2. Tagging pipeline (`route_area_tagging.py`) migrated to winning model — TAGGING_MODEL constant replaces both hardcoded strings (line 192 + line 449)
3. Prompts include D1 tick comment text as context where available (174 routes enriched via enrich_ticks.py)
4. User manually reviews 50-route benchmark output before full run (D-10/D-11)
5. All 2,966 Yosemite routes tagged and synced to Cloudflare remote D1; Washington data deleted from production

**Build notes:**
- All models use same OpenAI Batch API client — model string swap only (D-01)
- gpt-5-mini batch may return 403 PermissionDeniedError for some projects — benchmark handles gracefully
- Dual model hardcode in route_area_tagging.py: line 192 (route tagging) AND line 449 (area tagging) — both must be updated
- Enrichment step uses direct sqlite3 on local D1 (not wrangler) — avoids batch-mode PRAGMA bug from Phase 02
- Remote D1 delete targets Washington only (path LIKE '/washington/%') — Nevada was never pushed to remote D1

---

## Progress

| Phase | Milestone | Plans | Status | Completed |
|-------|-----------|-------|--------|-----------|
| 01 Full-Stack Refactor | v1.0 | 5/5 | Complete | 2026-05-09 |
| 02 Tick Comments | v1.1 | 4/4 | Complete | 2026-05-10 |
| 03 Tagging Upgrade | v1.1 | 5/5 | Pending | — |
