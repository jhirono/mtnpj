---
status: in_progress
phase: 01-refactor
last_activity: 2026-05-08
current_wave: 1_complete_pending_checkpoint
---

# Project State

**Project:** Mountain Project Climbing Search
**Milestone:** Full-Stack Refactor
**Current Phase:** 01 — Full Scraper Coverage

## Phase 1 Progress

| Plan | Status | Notes |
|------|--------|-------|
| 01-01 | checkpoint | T01+T02 done; T03 (Yosemite smoke test) awaits human approval |
| 01-02 | complete | D1 schema + import_to_d1.py, 13 tests pass |
| 01-03 | pending | Hono Worker API (depends on 01-02) |
| 01-04 | pending | Frontend migration (depends on 01-03) |
| 01-05 | complete | d1_tag_sync.py — 11 tests pass, nevada smoke: 6407 route updates |

## Decisions

- Async HTTP via httpx + Semaphore for non-JS pages; Selenium kept for login-gated comment scraping
- Stable route_id from MP URL numeric segment (regex /route/(\d+)/)
- D1 SQLite schema: areas, routes, comments, FTS5 virtual table
- 9 boolean type columns: is_sport, is_trad, is_aid, is_ice, is_alpine, is_mixed, is_tr, is_boulder, is_snow
- Import batching ≤100KB per D1 statement; materialized path from URL slugs
- Hono Worker API on Cloudflare Workers (Wave 2)
- Frontend migrates from static JSON to Worker API REST calls (Wave 3)
- CASE-WHEN bulk UPDATE for d1_tag_sync.py batch efficiency (one statement per chunk, hundreds of routes)
- URL-derived stable MP ID resolution: numeric route_id passes through, legacy uuid4 falls back to URL extraction

## Open Checkpoints

- 01-01 T03: Yosemite NP smoke test — run scrape, verify Areas≥50 / Routes≥1000 / Aid≥50 / UUID4==0
