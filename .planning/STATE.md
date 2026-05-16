---
status: complete
phase: "04-specialty-grade-sort"
last_activity: 2026-05-16
milestone: v1.2
---

# Project State

**Project:** Mountain Project Climbing Search
**Milestone:** v1.1 Coverage & Tagging — Washington data import in progress
**Current Focus:** Washington routes imported + tagged; tick collection running in background

## Current Position

Phase 03 — Tagging Pipeline Upgrade: **ALL 6 PLANS COMPLETE**
Production: https://climbing-search.pages.dev (live, all fixes deployed)

---

## What Was Shipped This Session (2026-05-10)

### Phase 03 Plans (all 6 complete)

| Plan | What | Status |
|------|------|--------|
| 03-01 | `enrich_ticks.py` — merge D1 tick comments into route JSON (190/2966 enriched) | ✅ |
| 03-02 | Model benchmark — gpt-4o-mini won (50/50 valid, 5.1 avg tags) | ✅ |
| 03-03 | `TAGGING_MODEL = "gpt-4o-mini"` constant added | ✅ |
| 03-04 | Full Yosemite tagging run (2,216 routes updated in D1) | ✅ |
| 03-05 | Nevada + Washington re-import with tag clearing (non-Yosemite coverage maintained) | ✅ |
| 03-06 | 6-category ALLOWED_TAGS restructure; area tagging pipeline removed | ✅ |

### UI + API Bug Fixes (shipped post-phase)

| Fix | Files |
|-----|-------|
| FilterPanel rewrite — 7 accordion sections, static tag definitions, badge counts | `FilterPanel.tsx` |
| Area names clickable → Mountain Project (`area_url` added to SQL + `RouteApi`) | `RouteCard.tsx`, `queries.ts`, `routes.ts`, `types.ts` |
| Area search: slugify query, search `path` column — "el-capitan" now finds results | `queries.ts` |
| Grade filter: replace `GRADE_ORDER.indexOf` with `gradeToNumeric()` (5.10a → 10.1) | `App.tsx` |
| API 500: D1 rejects LIKE on long slugs; replaced with pre-resolved `INSTR(path, ?)=1` | `queries.ts`, `routes.ts` |
| Route count: show `X+` when `hasMore`; no longer claims loaded batch = total | `App.tsx` |
| "No areas selected" false-positive: suppressed when any filter is active | `App.tsx` |
| Tag filter auto-load: when tag filter is sparse, auto-fetch next API page | `App.tsx` |

---

## Production State

| Service | URL | State |
|---------|-----|-------|
| Frontend | https://climbing-search.pages.dev | ✅ Live (latest build) |
| Worker API | https://climbing-search-api.jumpei-hirono.workers.dev | ✅ Live |
| D1 Database | climbing-search (4183c756) | ✅ 15,746 routes (Yosemite + Washington) |

**Route coverage:**
- Yosemite NP: 2,966 routes
- Washington: 12,780 routes (fresh scrape 2026-05-10)
- Nevada: removed (was stale data)

**Tag coverage:**
- Yosemite NP: 2,216 routes tagged (6 categories)
- Washington: 12,070 of 12,780 routes tagged (6 categories, gpt-4o-mini)

**Comment coverage:**
- Yosemite: 4,209 tick comments across 174 routes (synced to remote D1 2026-05-10)
- Washington: tick collection running in background (PID 47856, ~10,951 routes, log: /tmp/wa_ticks.log)
- Note: remote comments table was missing 'tick' type in CHECK constraint — migrated 2026-05-10

---

## Decisions Made This Phase

| ID | Decision |
|----|----------|
| D-15 | Area tagging pipeline deleted (create_area_batch_requests, inherit_approach_tags removed) |
| D-16 | multi_pitch/single_pitch replaces short_multipitch/long_multipitch |
| D-17 | Rope length rules: route_length_meter / 2 = min rappel rope (≤30m→60m, 31–35m→70m, 35–40m→80m) |
| D-18 | Boulder routes: tags cleared to empty (rope tag system doesn't apply) |
| D-19 | 6-category tag taxonomy (Route Style, Crack Climbing, Movement, Logistics, Safety, Quality) |
| D-20 | gpt-4o-mini selected as tagging model (benchmark: 50/50 valid vs gpt-5 models failing) |
| D-21 | D1 LIKE complexity limit: use INSTR(path, prefix)=1 for area path prefix matching |

---

## Known Limitations / Tech Debt

- Washington tick collection still in progress — will need to sync local→remote after complete
- Remote D1 comments schema migrated 2026-05-10 (added 'tick' to CHECK constraint via table rename)
- Local D1 has 10,951 Washington routes (pre-fresh-scrape); remote has 12,780 — ~1,829 new routes will miss tick collection this pass
- El Capitan is not scraped as a standalone area row — users must pick a sub-area (Southwest Face, etc.)
- Area search returns sub-areas of El Capitan, not a single "El Capitan" parent entry
- Service worker `autoUpdate` — users on old cached JS need hard-reload (Cmd+Shift+R) after deploys
- Route count shows loaded batch size + `+` when hasMore, not true DB total (no COUNT(*) in API)

---

## Candidate Next Actions (Phase 04)

Ranked by user value:

1. **Sync Washington ticks to remote** — after background collection completes, export local→remote D1 (same process as Yosemite sync done 2026-05-10)
2. **Add more regions** — Red Rock Canyon NV, Tuolumne, Joshua Tree, Smith Rock (scrape + tag)
3. **Area hierarchy navigation** — El Capitan parent area missing from DB; add or synthesize from path
4. **FTS area search** — area search uses LIKE; upgrade to FTS5 for speed and better relevance
5. **Total route count in API** — add `COUNT(*) OVER()` or separate count query so UI shows real total
6. **Mobile layout pass** — route cards are functional but not optimized for one-handed mobile use

---

## Project Reference

See: `.planning/PROJECT.md`

**Core value:** Fast, comprehensive climbing route discovery across all route types, zero-cost edge stack
