# Phase 1: Full-Stack Refactor — Context

**Gathered:** 2026-05-08
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase covers three tightly coupled refactors:
1. **Scraper overhaul** — capture all route types (including aid, ice, alpine, mixed, TR, boulder) across Western US, with incremental update support and a post-scrape LLM tagging pass.
2. **Data model normalization** — replace nested JSON (area contains routes[]) with a fully normalized relational schema: `areas`, `routes`, `comments`, and `hierarchy` tables.
3. **Cloud DB migration** — migrate from static JSON file loading to Cloudflare D1, served via a Cloudflare Worker (Hono), with the frontend migrated to Cloudflare Pages.

</domain>

<decisions>
## Implementation Decisions

### Scraper Coverage
- **D-01:** Capture ALL route types — Sport, Trad, Aid, Ice, Alpine, Mixed, TR, Boulder, Snow. No filtering at scrape time; filtering happens in the app/UI.
- **D-02:** Geographic scope: Western US first (CA, CO, UT, WA, OR, NV, AZ, WY). Existing tagged JSON files in `data/` are the starting point. Expand to full US in a later phase.
- **D-03:** The current scraper only captures `*_sport_trad.json` files. The `DataService.ts` filename convention must be updated to remove the `_sport_trad` suffix.

### Scraper Architecture
- **D-04:** Use **async HTTP (httpx/aiohttp)** for bulk area/route scraping. Keep Selenium only for login-gated comment scraping. This is a hybrid approach — much faster than all-Selenium, avoids rewriting comment logic.
- **D-05:** Scraper must handle deep sub-area hierarchies correctly (Yosemite NP → walls → formations → routes). Fix `get_sub_area_links` detection logic to handle all nav patterns, not just the specific CSS class.
- **D-06:** Support **incremental/diff-based updates**: re-scrape known area pages, compare route lists against DB by `route_id`, only fetch full details for new/changed routes.

### LLM Tagging Pipeline
- **D-07:** Tagging is a **post-scrape step**, separate from scraping. Pipeline: scrape → store raw data → run LLM tagger → update DB with tags. The existing `tagging/` scripts become a pipeline stage, not inline.
- **D-08:** Raw route data is stored in D1 first (untagged). A second pass updates the `route_tags` JSON column. This decouples scrape cost from LLM cost.

### Cloud Database
- **D-09:** Use **Cloudflare D1** (SQLite at the edge). Rationale: already using Cloudflare R2, free tier covers the dataset (5GB storage, 25M reads/day), edge-native for global performance.
- **D-10:** **Migrate frontend to Cloudflare Pages** + Cloudflare Worker API. Full CF stack: Pages (Vite app) + Worker (Hono API) + D1 (database) + R2 (static assets). Removes Fly.io dependency for the web app.
- **D-11:** Retire the Firebase WIP (`firebase-climbing-search/`). The Firebase partial implementation is not carried forward.

### Search & Filtering
- **D-12:** **Server-side SQL filtering via Worker API** (WHERE clauses, ORDER BY, pagination). Use D1's FTS5 for text search on route names/descriptions. No external search service needed initially.

### Data Model — Schema
- **D-13:** **Fully normalized schema** with 4 tables:
  - `areas` — area_id, parent_id (adjacency list), area_name, area_url, area_gps, area_description, area_getting_there, area_access_issues, area_page_views, area_shared_on, path (materialized path string e.g. `/CA/Yosemite/El-Cap/`)
  - `routes` — route_id, area_id (FK), route_name, route_url, route_lr, route_grade, route_grade_numeric (indexed), route_protection_grading, route_stars (indexed), route_votes, is_sport, is_trad, is_aid, is_ice, is_alpine, is_mixed, is_tr, is_boulder, is_snow (boolean columns, indexed), route_pitches, route_length_ft, route_length_meter, route_fa, route_description, route_location, route_protection, route_page_views, route_shared_on, route_tags (JSON column), route_suggested_ratings (JSON column), route_tick_comments
  - `comments` — comment_id, parent_id (route_id or area_id), parent_type (enum: 'route'|'area'), comment_author, comment_text, comment_time
  - `area_hierarchy` — kept as `parent_id` + `path` columns on `areas` table (adjacency list + materialized path), NOT a separate table
- **D-14:** Route types stored as **boolean columns** (`is_sport`, `is_trad`, `is_aid`, etc.) for fast indexed filtering. Tags stored as **JSON column** (`route_tags`). No separate tags join table.
- **D-15:** Area hierarchy: **adjacency list** (`parent_id` on `areas`) plus a **materialized path** string column for efficient ancestor/descendant queries. No closure table needed.

### API Layer
- **D-16:** Cloudflare Worker API using **Hono framework** — purpose-built for Workers, TypeScript-first, lightweight. REST endpoints: `GET /routes`, `GET /areas`, `GET /routes/:id`, `GET /areas/:id/routes`.
- **D-17:** Standard filtering params: `?grade=5.10&type=aid&region=california&stars_min=3&page=1&limit=50`.

### Data Sync
- **D-18:** **Monthly scrape cadence**. Scraper exports JSON files (same as current workflow). A separate import script transforms JSON → D1 schema and loads via Cloudflare D1 HTTP API or `wrangler d1 execute`. Diff logic skips unchanged routes.
- **D-19:** Scraper continues to run locally (or via GitHub Actions). No hosted scraper service needed.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Codebase
- `scraping/scrape_mtnpj_final.py` — Current scraper; `get_sub_area_links`, `is_lowest_level_area`, `get_routes`, `get_route_details` are the key functions to refactor
- `climbing-search/src/utils/DataService.ts` — Current data loading; `getRegionRoutes` hardcodes `_sport_trad` filename suffix — must be generalized
- `climbing-search/src/types/index.ts` — Current TypeScript types for Area, Route, Comment, AreaHierarchy; new schema will produce new types
- `climbing-search/src/utils/loadData.ts` — Current entry point for data loading; will be replaced by Worker API client
- `firebase-climbing-search/src/firebase.ts` — WIP Firebase implementation; read for patterns to avoid repeating, then retire
- `tagging/` — LLM tagging scripts; understand pipeline before redesigning as post-scrape step
- `data/` — Existing tagged JSON files (arizona, colorado, nevada, oregon, utah, washington); input for initial D1 import
- `r2_config.py`, `upload_all_to_r2.py` — Existing R2 upload scripts; understand for CF integration pattern

### Cloudflare Platform
- No external specs yet — researcher should investigate Cloudflare D1 docs, Hono docs, and Cloudflare Pages docs during research phase

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `climbing-search/src/components/` — All React components (RouteCard, RouteList, AreaSearch, filters) are reusable; only the data-fetching layer changes
- `climbing-search/src/types/index.ts` — Type definitions will need updating for new schema but component props can stay similar
- `tagging/` scripts — LLM tagging logic is reusable as a pipeline stage

### Established Patterns
- Scraper uses disk-based caching (7-day TTL, `data/cache/`) — keep this pattern for incremental scraping
- `DataService.ts` uses a deduplication pattern for concurrent fetches (`dataLoadPromises`) — reuse in the Worker API client
- Firebase WIP shows what NOT to do (NoSQL document model doesn't fit relational route/area queries well)

### Integration Points
- `DataService.ts` → replace `fetch('/data/*.json')` calls with `fetch('/api/routes?...')` Worker API calls
- `loadData.ts` → replace with a `routeApi.ts` client that talks to the Hono Worker
- `main.tsx` / `App.tsx` — no structural changes needed; only data-fetching layer changes
- Cloudflare Pages deploys Vite apps natively — `vite.config.ts` needs minimal changes (output dir)

### Known Issues in Scraper
- `get_sub_area_links` uses `class_='max-height max-height-md-0 max-height-xs-400'` — brittle CSS class targeting; needs a more robust selector or fallback
- `left-nav-route-table` selector may miss routes in paginated views for large areas
- `DataService.ts` `getRegionRoutes` hardcodes `_sport_trad` in filename — filters out all non-sport/trad routes before they reach the UI

</code_context>

<specifics>
## Specific Ideas

- User confirmed: Yosemite NP (`https://www.mountainproject.com/area/105833381/yosemite-national-park`) is the primary test case for deep hierarchy and aid route coverage
- Full Cloudflare stack is the target: Pages + Workers + D1 + R2
- Monthly scrape is acceptable cadence — data doesn't change that frequently
- LLM tagging pipeline already exists in `tagging/` — wire it in as a post-scrape step rather than rebuilding

</specifics>

<deferred>
## Deferred Ideas

- Full US coverage (all 50 states) — deferred to Phase 2 after Western US is working
- External search service (Algolia, Meilisearch) — D1 FTS5 is sufficient for now; add if text search quality becomes an issue
- On-demand admin-triggered scraping — monthly batch is sufficient; no hosted scraper service needed yet
- Mobile app — out of scope for this refactor
- User accounts / ticks / wishlists — out of scope for this refactor

</deferred>

---

*Phase: 01-refactor*
*Context gathered: 2026-05-08*
