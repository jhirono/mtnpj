---
status: in_progress
phase: 01-refactor
last_activity: 2026-05-08
current_wave: 2_complete_pending_checkpoint
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
| 01-03 | checkpoint | T01–T03 done (Hono API + vitest, 20/20 pass); T04 awaits wrangler login + d1 create |
| 01-04 | pending | Frontend migration (depends on 01-03 T04 worker URL) |
| 01-05 | complete | d1_tag_sync.py, 11 tests pass, handles LLM + logic-based tags |

## Decisions

- Async HTTP via httpx + Semaphore for non-JS pages; Selenium kept for login-gated comment scraping
- Stable route_id from MP URL numeric segment (regex /route/(\d+)/)
- D1 SQLite schema: areas, routes, comments, FTS5 virtual table
- 9 boolean type columns: is_sport, is_trad, is_aid, is_ice, is_alpine, is_mixed, is_tr, is_boulder, is_snow
- Import batching ≤100KB per D1 statement; materialized path from URL slugs
- Hono Worker API on Cloudflare Workers — name: climbing-search-api
- type parameter whitelisted before column interpolation (SQL injection blocked)
- tagging pipeline: scrape → import_to_d1 → route_area_tagging → d1_tag_sync (LLM + logic-based tags)
- Frontend migrates from static JSON to Worker API REST calls (Wave 3)

## Open Checkpoints

- 01-01 T03: Yosemite NP smoke test — run scrape, verify Areas≥50 / Routes≥1000 / Aid≥50 / UUID4==0
- 01-03 T04: wrangler login + d1 create climbing-search → fill database_id in worker-api/wrangler.toml → deploy
