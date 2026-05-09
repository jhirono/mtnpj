# Roadmap — Mountain Project Climbing Search Refactor

## Phase 1 — Full Scraper Coverage
**Goal:** Fix scraper to capture all route types (aid, ice, alpine, mixed, TR, boulder) across all area hierarchy levels including large parks like Yosemite NP.
**Status:** in_progress

| Plan | Status | Artifacts |
|------|--------|-----------|
| 01-01 | checkpoint | scrape_async.py (httpx + Semaphore); awaiting Yosemite smoke test |
| 01-02 | complete | import_to_d1.py, schema.sql, 13 tests pass |
| 01-03 | pending | Hono Worker API |
| 01-04 | pending | Frontend migration |
| 01-05 | complete | d1_tag_sync.py — 11 tests, 89,467 route updates across 6 states |

## Phase 2 — Data Model Normalization
**Goal:** Replace nested JSON (area contains routes[]) with normalized relational tables (areas table, routes table, comments table, hierarchy table).
**Status:** planning

## Phase 3 — Cloud Database Migration
**Goal:** Migrate from static JSON file loading to a cloud database. Evaluate and implement best-ROI solution (Cloudflare D1, Firebase, Supabase, Turso, etc.).
**Status:** planning
