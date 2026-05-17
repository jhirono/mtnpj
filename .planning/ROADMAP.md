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

### Phase 04: Specialty Grade Sort

**Goal:** Add discipline-specific sort options (Aid Grade, Ice Grade, Mixed Grade) to the Sort By dropdown so aid/ice/mixed climbers can order routes by their relevant grade system instead of YDS only.

**Requirements:** SORT-01, SORT-02, SORT-03

**Plans:** 1 plan

Plans:

- [x] 04-01-PLAN.md — Parse A/C, WI/AI, M grades from route_grade; add sort options to UI

**Success criteria:**

1. Aid routes can be sorted A0→A6+/C0→C6+ (or reverse) — grade extracted from combined route_grade string
2. Ice routes can be sorted WI1→WI7+/AI1→AI5+ (or reverse)
3. Mixed routes can be sorted M1→M12+ (or reverse) — extracted from route_grade or route_protection_grading
4. Routes without a relevant specialty grade sort to the end (not interleaved as 0)
5. Sort options appear in the dropdown and work in both ascending and descending direction

**Build notes:**

- No API changes — all sorting is client-side (existing pattern)
- route_grade stores combined strings: "5.9 A3", "WI4", "5.8 C2", "5.9 A3+", "WI3-4"
- Aid grade also appears in route_protection_grading: "A3+", "A2+", "A0"
- Mixed M-grade in route_protection_grading: "M4", "M5-", "M6+"
- A grades and C grades share the same numeric scale (C2 ≈ A2 in difficulty, just gear style differs)
- WI and AI share the same numeric scale (AI is alpine ice, WI is waterfall ice)
- Routes missing a grade for the selected sort dimension sort to the bottom (null last)

---

### Phase 05: Grade System Picker

**Goal:** Replace specialty sort options (Aid/Ice/Mixed/Boulder) in Sort By with a unified grade system picker row. Picker controls active grade system (YDS/V/Aid/Ice/Mixed), drives grade filter options and "Sort by Grade" behavior. Requires frontend + backend API changes for server-side grade filtering.

**Requirements:** D-01 through D-20 (from 05-CONTEXT.md)

**Plans:** 5 plans

Plans:

- [ ] 05-01-PLAN.md — Type contracts + test scaffold: GradeSystem type, GRADE_LISTS, RouteFilters/SortOption/ApiFilters updates, aid/mixed fixtures, grade_system integration tests
- [ ] 05-02-PLAN.md — Backend implementation: Zod schema extension (grade_system enum, grade_list validation), LIKE-based OR clause filtering in buildRoutesQuery
- [ ] 05-03-PLAN.md — FilterPanel UI: grade system picker row (5 segmented buttons), system-aware grade filter selects, trimmed Sort By select
- [ ] 05-04-PLAN.md — App.tsx wiring: gradeSystem initial state, filtersToApi grade_list expansion, polymorphic grade sort switch, specialty case removal
- [ ] 05-05-PLAN.md — Deploy + human verification checkpoint

**Success criteria:**

1. Grade system picker (segmented buttons: YDS | V | Aid | Ice | Mixed) visible as top-level row in FilterPanel
2. Selecting a grade system updates grade filter min/max options to that system's grade list
3. "Sort by Grade" sorts by the active grade system — V-scale for Boulder, A-scale for Aid, etc.
4. Specialty sort options (aid_grade, ice_grade, mixed_grade, boulder_grade) removed from Sort By dropdown
5. Non-YDS grade filtering is server-side via LIKE prefix matching on route_grade + route_protection_grading

---

## Progress

| Phase | Milestone | Plans | Status | Completed |
|-------|-----------|-------|--------|-----------|
| 01 Full-Stack Refactor | v1.0 | 5/5 | Complete | 2026-05-09 |
| 02 Tick Comments | v1.1 | 4/4 | Complete | 2026-05-10 |
| 03 Tagging Upgrade | v1.1 | 5/5 | Pending | — |
| 04 Specialty Grade Sort | v1.2 | 1/1 | Complete | 2026-05-16 |
| 05 Grade System Picker | v1.2 | 5/5 | Pending | — |
