# Phase 1: Full-Stack Refactor — Research

**Researched:** 2026-05-08
**Domain:** Python async scraping, Cloudflare D1 + Worker (Hono) + Pages, data model normalization
**Confidence:** HIGH (codebase verified by direct inspection; Cloudflare/Hono docs fetched from official sources)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Capture ALL route types — Sport, Trad, Aid, Ice, Alpine, Mixed, TR, Boulder, Snow. No filtering at scrape time.
- **D-02:** Geographic scope: Western US first (CA, CO, UT, WA, OR, NV, AZ, WY). Existing tagged JSON in `data/` is the starting point. Full US in a later phase.
- **D-03:** `DataService.ts` filename convention must be updated to remove the `_sport_trad` suffix.
- **D-04:** Use **async HTTP (httpx/aiohttp)** for bulk scraping; keep Selenium only for login-gated comment scraping.
- **D-05:** Fix `get_sub_area_links` to handle all nav patterns, not just the brittle CSS class.
- **D-06:** Support **incremental/diff-based updates**: re-scrape known areas, compare route lists vs. DB by `route_id`, fetch full details only for new/changed routes.
- **D-07:** Tagging is a **post-scrape step** — pipeline: scrape → store raw → LLM tag → update DB.
- **D-08:** Raw route data stored in D1 first (untagged); second pass updates `route_tags` JSON column.
- **D-09:** Use **Cloudflare D1** (SQLite at edge).
- **D-10:** Migrate frontend to **Cloudflare Pages** + Cloudflare Worker API. Full CF stack: Pages + Worker + D1 + R2. Remove Fly.io.
- **D-11:** Retire `firebase-climbing-search/`. Not carried forward.
- **D-12:** Server-side SQL filtering via Worker API (WHERE clauses, ORDER BY, pagination). D1 FTS5 for text search.
- **D-13:** Normalized schema: `areas` (area_id, parent_id, area_name, area_url, area_gps, area_description, area_getting_there, area_access_issues, area_page_views, area_shared_on, path), `routes` (route_id, area_id FK, all route fields, boolean type columns, route_tags JSON), `comments` (comment_id, parent_id, parent_type, comment_author, comment_text, comment_time). Area hierarchy via `parent_id` + `path` on `areas` table.
- **D-14:** Route types as boolean columns (`is_sport`, `is_trad`, `is_aid`, etc.), indexed. Tags as JSON column (`route_tags`).
- **D-15:** Adjacency list (`parent_id`) + materialized path (`path` string) on `areas`. No closure table.
- **D-16:** Worker API using **Hono framework**. REST endpoints: `GET /routes`, `GET /areas`, `GET /routes/:id`, `GET /areas/:id/routes`.
- **D-17:** Filtering params: `?grade=5.10&type=aid&region=california&stars_min=3&page=1&limit=50`.
- **D-18:** Monthly scrape cadence. Scraper exports JSON. Import script transforms JSON → D1 via `wrangler d1 execute`. Diff logic skips unchanged routes.
- **D-19:** Scraper continues to run locally or via GitHub Actions.

### Deferred Ideas (OUT OF SCOPE)
- Full US coverage (all 50 states)
- External search service (Algolia, Meilisearch)
- On-demand admin-triggered scraping
- Mobile app
- User accounts / ticks / wishlists
</user_constraints>

---

## Summary

Phase 1 is a three-layer refactor executed in parallel tracks: (1) the Python scraper is converted from synchronous requests+Selenium-only to a hybrid httpx-async (areas/routes) + Selenium (comments/stats) architecture with incremental update logic; (2) the existing nested JSON data model is normalized into a four-concept relational D1 schema with boolean route-type columns and a materialized-path area hierarchy; (3) the hosting stack is migrated from Fly.io static JSON serving to a full Cloudflare stack (Pages + Worker + D1 + R2).

The existing codebase has been directly inspected. Key findings: the scraper already has disk-based caching and a clean function boundary (`get_sub_area_links`, `is_lowest_level_area`, `get_routes`, `get_route_details`), making the async rewrite surgical. The tagged JSON files for 6 states exist with 89,467 routes total — these are the input for the initial D1 import. The front-end React components (RouteCard, RouteList, AreaSearch, FilterPanel) are fully reusable; only the data-fetching layer changes from JSON file fetches to Worker API calls. The venv already contains httpx 0.28.1, aiohttp 3.11.13, and all other required Python packages.

Cloudflare D1 supports SQLite 3.x semantics with FTS5 for full-text search and JSON functions. Hono 4.12.18 is purpose-built for Workers with a clean D1 binding pattern (`c.env.DB.prepare(...).bind(...).run()`). wrangler 4.90.0 handles both Worker deployment and D1 SQL execution via `wrangler d1 execute --file=schema.sql`.

**Primary recommendation:** Implement the three tracks serially in this order — (1) async scraper refactor and data import pipeline, (2) D1 schema + import, (3) Hono Worker API + Pages deployment — because each track's output is consumed by the next.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Route/area search and filtering | API / Backend (Worker) | — | SQL WHERE clauses on D1; client receives filtered pages |
| Full-text search (route names/descriptions) | API / Backend (Worker) | — | D1 FTS5 virtual table; Worker translates `?q=` to MATCH query |
| Area hierarchy navigation | API / Backend (Worker) | Frontend (React) | Worker serves adjacency-list tree; React renders it |
| UI filtering / sort (client-side) | Frontend (React) | — | Grade normalization, tag filtering, sort already in `filters.ts` |
| Data loading / pagination | API / Backend (Worker) | Frontend (React) | Worker paginates; React implements infinite scroll |
| LLM tagging pipeline | Scraper (local/CI) | — | Post-scrape Python step; outputs JSON → D1 update |
| Static asset hosting | CDN / Static (CF Pages) | R2 | Pages serves the Vite dist; R2 available for large assets |
| Authentication (comments) | Scraper (local) | — | Selenium login only; no user auth in the web app |
| D1 bulk import | Local CLI (wrangler) | — | `wrangler d1 execute --file=` runs SQL import offline |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| httpx | 0.28.1 | Async HTTP client for scraper | Already in venv; async-first, HTTPX 1.x API stable, supports timeout/retry natively |
| aiohttp | 3.11.13 | Alternative async HTTP (available if needed) | Already in venv; slightly higher throughput for pure-async workloads |
| BeautifulSoup4 | 4.13.3 | HTML parsing | Already in use; lxml parser backend for performance |
| Selenium | 4.28.1 | Browser automation for login-gated pages (comments, stats) | Already in use; only needed for dynamic/JS-rendered content |
| Hono | 4.12.18 | Web framework for Cloudflare Worker API | Purpose-built for Workers, TypeScript-first, minimal bundle, D1 binding pattern is idiomatic |
| Wrangler | 4.90.0 | CF Worker/Pages deploy + D1 CLI | Official Cloudflare tool; `wrangler d1 execute` is the import mechanism |
| @cloudflare/workers-types | 4.20260508.1 | TypeScript types for CF bindings | Required for `D1Database`, `R2Bucket` type safety |

[VERIFIED: venv/lib/python*/site-packages/ for Python packages; `npm view` for JS packages]

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @hono/zod-validator | latest | Query param validation in Worker routes | All `GET /routes` query params; prevents SQL injection via untyped bind |
| zod | latest | Schema definition | Paired with zod-validator for type-safe query parsing |
| asyncio.Semaphore | stdlib | Concurrency throttle for async scraper | Limit to ~10 concurrent requests to avoid MP rate-limiting |
| openai | 1.63.2 | OpenAI Batch API for LLM tagging | Already in venv; existing tagging pipeline uses it |

[VERIFIED: npm registry for Hono packages; venv for openai]

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| httpx | aiohttp | aiohttp is marginally faster at scale; httpx has cleaner API, sync+async in one lib |
| Hono | itty-router | Hono has built-in zod-validator, TypeScript generics for bindings; itty-router is smaller but less ergonomic |
| wrangler d1 execute | D1 HTTP API | HTTP API requires auth token management; wrangler CLI is simpler for local import |
| D1 FTS5 | LIKE search | LIKE is simpler; FTS5 returns ranked results and is indexed for large tables |

**Installation (Worker):**
```bash
npm create hono@latest worker-api -- --template cloudflare-workers
npm install @hono/zod-validator zod @cloudflare/workers-types
```

**Installation (Python scraper):**
```bash
# Already in venv; activate and verify:
source venv/bin/activate
pip install httpx[asyncio] aiohttp asyncio
```

---

## Architecture Patterns

### System Architecture Diagram

```
[MountainProject.com]
        |
        | HTTP (httpx async, semaphore-throttled)
        v
[scraper/scrape_async.py]  <-- async area/route scraping
        |  (Selenium only for comments/stats)
        |
        v
[data/*.json]  <-- raw JSON output (per-state files)
        |
        | python import_to_d1.py  →  SQL file generation
        v
[wrangler d1 execute --file=import.sql --remote]
        |
        v
[Cloudflare D1]  <-- normalized: areas, routes, comments
        |
        | D1 binding (c.env.DB)
        v
[Cloudflare Worker (Hono)]  <-- REST API: GET /routes, GET /areas, etc.
        |
        | fetch('/api/routes?...')
        v
[Cloudflare Pages]  <-- Vite React build (dist/)
  [React components]  <-- RouteCard, FilterPanel, AreaSearch (reused as-is)

[LLM Tagging pipeline]  (separate step)
  data/*.json → tagging/route_area_tagging.py → updates route_tags in D1
```

### Recommended Project Structure

```
scraping/
├── scrape_async.py          # New async scraper (replaces scrape_mtnpj_final.py)
├── scrape_mtnpj_final.py    # Kept for Selenium comment/stats functions (reused)
└── import_to_d1.py          # JSON → SQL transform + wrangler d1 execute wrapper

worker-api/                  # New: Hono Worker
├── src/
│   ├── index.ts             # App entry, Hono app, route mounting
│   ├── routes/
│   │   ├── routes.ts        # GET /routes, GET /routes/:id
│   │   └── areas.ts         # GET /areas, GET /areas/:id/routes
│   └── db/
│       └── queries.ts       # SQL query builders
├── schema.sql               # D1 schema definition (CREATE TABLE, CREATE INDEX, FTS5)
└── wrangler.toml            # D1 binding, compatibility_date

climbing-search/             # Existing Vite React app (minimal changes)
├── src/
│   ├── api/
│   │   └── routeApi.ts      # NEW: replaces DataService.ts + loadData.ts
│   ├── components/          # REUSED AS-IS: RouteCard, FilterPanel, AreaSearch
│   ├── types/               # UPDATED: route.ts, area.ts for new schema
│   └── App.tsx              # UPDATED: uses routeApi.ts instead of loadData
└── vite.config.ts           # UPDATED: remove PWA offline data caching for JSON files
```

### Pattern 1: Async HTTP Scraper with Semaphore Throttle

**What:** Replace synchronous `requests.get()` in scraping loops with `httpx.AsyncClient` + `asyncio.Semaphore`.
**When to use:** Any bulk page fetch that doesn't require JS rendering.

```python
# Source: verified pattern from httpx docs + asyncio stdlib
import httpx
import asyncio
from bs4 import BeautifulSoup

CONCURRENCY_LIMIT = 10  # tune based on MP rate-limit response
DELAY_BETWEEN_BATCHES = 0.5  # seconds

async def fetch_page(client: httpx.AsyncClient, sem: asyncio.Semaphore, url: str) -> str:
    async with sem:
        headers = {"User-Agent": "Mozilla/5.0 (compatible)"}
        response = await client.get(url, headers=headers, timeout=15.0)
        response.raise_for_status()
        await asyncio.sleep(DELAY_BETWEEN_BATCHES)
        return response.text

async def scrape_area_urls(urls: list[str]) -> list[BeautifulSoup]:
    sem = asyncio.Semaphore(CONCURRENCY_LIMIT)
    async with httpx.AsyncClient(follow_redirects=True) as client:
        tasks = [fetch_page(client, sem, url) for url in urls]
        pages = await asyncio.gather(*tasks, return_exceptions=True)
    return [BeautifulSoup(p, 'lxml') for p in pages if isinstance(p, str)]
```

### Pattern 2: D1 Schema with Boolean Type Columns and FTS5

**What:** D1 SQLite schema matching the decided data model.
**When to use:** The `schema.sql` file run via `wrangler d1 execute`.

```sql
-- Source: [CITED: developers.cloudflare.com/d1/sql-api/sql-statements/]
-- areas table with adjacency list + materialized path
CREATE TABLE IF NOT EXISTS areas (
  area_id TEXT PRIMARY KEY,
  parent_id TEXT REFERENCES areas(area_id),
  area_name TEXT NOT NULL,
  area_url TEXT UNIQUE NOT NULL,
  area_gps TEXT,
  area_description TEXT,
  area_getting_there TEXT,
  area_access_issues TEXT,
  area_page_views INTEGER,
  area_shared_on TEXT,
  path TEXT NOT NULL  -- e.g. '/California/Yosemite/El-Cap/'
);

CREATE INDEX IF NOT EXISTS idx_areas_parent ON areas(parent_id);
CREATE INDEX IF NOT EXISTS idx_areas_path ON areas(path);

-- routes table with boolean type columns
CREATE TABLE IF NOT EXISTS routes (
  route_id TEXT PRIMARY KEY,
  area_id TEXT NOT NULL REFERENCES areas(area_id),
  route_name TEXT NOT NULL,
  route_url TEXT UNIQUE NOT NULL,
  route_lr INTEGER,
  route_grade TEXT,
  route_grade_numeric REAL,  -- for numeric sort/filter
  route_protection_grading TEXT,
  route_stars REAL,
  route_votes INTEGER,
  -- boolean type columns (0/1)
  is_sport INTEGER DEFAULT 0,
  is_trad INTEGER DEFAULT 0,
  is_aid INTEGER DEFAULT 0,
  is_ice INTEGER DEFAULT 0,
  is_alpine INTEGER DEFAULT 0,
  is_mixed INTEGER DEFAULT 0,
  is_tr INTEGER DEFAULT 0,
  is_boulder INTEGER DEFAULT 0,
  is_snow INTEGER DEFAULT 0,
  route_pitches INTEGER,
  route_length_ft INTEGER,
  route_length_meter INTEGER,
  route_fa TEXT,
  route_description TEXT,
  route_location TEXT,
  route_protection TEXT,
  route_page_views INTEGER,
  route_shared_on TEXT,
  route_tags TEXT,              -- JSON string
  route_suggested_ratings TEXT, -- JSON string
  route_tick_comments TEXT
);

CREATE INDEX IF NOT EXISTS idx_routes_area ON routes(area_id);
CREATE INDEX IF NOT EXISTS idx_routes_grade ON routes(route_grade_numeric);
CREATE INDEX IF NOT EXISTS idx_routes_stars ON routes(route_stars);
CREATE INDEX IF NOT EXISTS idx_routes_votes ON routes(route_votes);
CREATE INDEX IF NOT EXISTS idx_routes_sport ON routes(is_sport);
CREATE INDEX IF NOT EXISTS idx_routes_trad ON routes(is_trad);
CREATE INDEX IF NOT EXISTS idx_routes_aid ON routes(is_aid);
CREATE INDEX IF NOT EXISTS idx_routes_boulder ON routes(is_boulder);

-- FTS5 virtual table for text search
-- [CITED: developers.cloudflare.com/d1/sql-api/sql-statements/ - FTS5 supported]
CREATE VIRTUAL TABLE IF NOT EXISTS routes_fts USING fts5(
  route_name,
  route_description,
  content='routes',
  content_rowid='rowid'
);

-- comments table
CREATE TABLE IF NOT EXISTS comments (
  comment_id TEXT PRIMARY KEY,
  parent_id TEXT NOT NULL,
  parent_type TEXT NOT NULL CHECK(parent_type IN ('route', 'area')),
  comment_author TEXT,
  comment_text TEXT,
  comment_time TEXT
);

CREATE INDEX IF NOT EXISTS idx_comments_parent ON comments(parent_id, parent_type);
```

### Pattern 3: Hono Worker with D1 Binding

**What:** Hono app structure for the Worker API.
**When to use:** `worker-api/src/index.ts`

```typescript
// Source: [CITED: developers.cloudflare.com/d1/examples/d1-and-hono/]
import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { zValidator } from '@hono/zod-validator'
import { z } from 'zod'

type Bindings = {
  DB: D1Database
}

const app = new Hono<{ Bindings: Bindings }>()

// CORS must be registered before routes
app.use('/api/*', cors({
  origin: ['https://your-app.pages.dev', 'http://localhost:5173'],
}))

const routeQuerySchema = z.object({
  grade: z.string().optional(),
  type: z.string().optional(),      // e.g. 'aid', 'trad'
  region: z.string().optional(),    // area path prefix
  stars_min: z.coerce.number().optional(),
  page: z.coerce.number().default(1),
  limit: z.coerce.number().default(50),
  q: z.string().optional(),         // FTS5 search
})

app.get('/api/routes', zValidator('query', routeQuerySchema), async (c) => {
  const { grade, type, region, stars_min, page, limit, q } = c.req.valid('query')
  const offset = (page - 1) * limit

  let sql = `SELECT r.*, a.path FROM routes r JOIN areas a ON r.area_id = a.area_id WHERE 1=1`
  const params: unknown[] = []

  if (grade) { sql += ` AND r.route_grade = ?`; params.push(grade) }
  if (type) { sql += ` AND r.is_${type} = 1` }  // parameterized column name not possible; validate type enum
  if (stars_min) { sql += ` AND r.route_stars >= ?`; params.push(stars_min) }
  if (region) { sql += ` AND a.path LIKE ?`; params.push(`/${region}/%`) }
  if (q) { sql += ` AND r.rowid IN (SELECT rowid FROM routes_fts WHERE routes_fts MATCH ?)`;  params.push(q) }

  sql += ` ORDER BY r.route_votes DESC LIMIT ? OFFSET ?`
  params.push(limit, offset)

  const { results } = await c.env.DB.prepare(sql).bind(...params).run()
  return c.json({ routes: results, page, limit })
})

export default app
```

**CAUTION:** The `is_${type}` pattern for boolean column selection requires server-side type validation against a whitelist before interpolation. Validate `type` against `['sport','trad','aid','ice','alpine','mixed','tr','boulder','snow']` before use.

### Pattern 4: Cloudflare Pages + Worker wrangler.toml

**What:** wrangler.toml for the Worker that backs the Pages app.
**When to use:** `worker-api/wrangler.toml`

```toml
# Source: [CITED: developers.cloudflare.com/workers/wrangler/configuration/]
name = "climbing-search-api"
main = "src/index.ts"
compatibility_date = "2025-01-01"

[[d1_databases]]
binding = "DB"
database_name = "climbing-search"
database_id = "<obtained from wrangler d1 create>"
```

**Pages deployment** — no wrangler.toml needed for Pages itself; deploy with:
```bash
npm run build          # generates climbing-search/dist/
npx wrangler pages deploy dist --project-name climbing-search
```

### Anti-Patterns to Avoid

- **Synchronous scraping loop:** Calling `requests.get()` sequentially for 89k routes is the existing bottleneck. The async refactor uses `asyncio.gather()` with a semaphore.
- **CSS class string matching for nav detection:** `soup.find('div', class_='max-height max-height-md-0 max-height-xs-400')` is brittle. Use structural selectors (e.g., find links within `#left-nav` area containers) or multiple fallback strategies.
- **Filtering in the scraper:** Current `App.tsx` has `EXCLUDED_TYPES = ['Aid', 'Boulder', 'Ice', 'Mixed', 'Snow']`. The new API surfaces all types; filtering is purely UI-side or via query params.
- **Hardcoding `_sport_trad` in filenames:** `DataService.ts` line 77 (`const filename = \`${region.toLowerCase()}_sport_trad.json\``) — this must be removed. The new `routeApi.ts` talks to the Worker, not static JSON.
- **Large single INSERT in SQL import:** D1 throws "Statement too long" for single INSERT with thousands of rows. Split into INSERT batches of 100-500 rows per statement.
- **Column name interpolation without whitelist:** Never do `WHERE r.is_${type} = 1` without validating `type` against a known set of column names.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Query param validation in Worker | Manual string checks | `@hono/zod-validator` + `zod` | Type-safe, auto-400 on invalid input, works with Hono's `c.req.valid()` |
| FTS5 search ranking | LIKE % matching | D1 FTS5 `MATCH` operator | Indexed, relevance-ranked, handles tokenization |
| Async HTTP with retries | Custom retry loop | `httpx` with `httpx.Retry` transport or `tenacity` | Edge cases around connection reset, timeout vs. HTTP error |
| Concurrency throttling | Sleep loops | `asyncio.Semaphore` | Correct backpressure; sleep loops are imprecise |
| SQL import from Python | D1 REST API calls | `wrangler d1 execute --file=` CLI | Handles auth, chunking, and error reporting; no custom HTTP client needed |
| LLM tagging | New OpenAI client | existing `tagging/route_area_tagging.py` | Already handles batch splitting, retry, validation, manual tag merging |

---

## Current Codebase — Verified Facts

### What the scraper actually does (verified by reading `scraping/scrape_mtnpj_final.py`)

- `get_sub_area_links(soup)` — line 131: finds nav div by exact class string `'max-height max-height-md-0 max-height-xs-400'`, then finds all `<a href containing '/area/'>` within it. **Brittle:** class name change breaks navigation entirely.
- `is_lowest_level_area(soup, sub_areas)` — line 139: checks for `<table id="left-nav-route-table">`. Returns True if has routes AND no sub-areas. **Known gap:** large areas may paginate route tables, causing routes to be missed.
- `get_routes(area_url)` — line 614: synchronous `requests.get()`. Extracts area metadata, then iterates `<tr>` in `#left-nav-route-table` and calls `get_route_details()` per route. Uses disk cache (7-day TTL, MD5-keyed).
- `get_route_details(route_url)` — line 460: synchronous `requests.get()`. Extracts grade (`.rateYDS, .route-type.Ice`), stars (`#starsWithAvgText`), type/length (string `'Type:'`), FA (`'FA:'`), description (`.fr-view` after h2 tags). Calls `get_comments()` and `get_route_stats()` via Selenium.
- `get_comments()` / `get_route_stats()` — lines 295, 420: Selenium only. These functions are already well-isolated. **Keep them.**
- The `route_type` field is a comma-separated string, e.g., `"Trad, 10 pitches, 2800 ft"` or `"Sport, 80 ft"`. The import script must parse this into boolean columns.

### Existing data JSON structure (verified by inspection)

Area-level keys: `area_id, area_url, area_name, area_gps, area_description, area_getting_there, area_tags, area_hierarchy, area_access_issues, area_page_views, area_shared_on, area_comments, routes, manual_tags`

Route-level keys: `route_name, route_url, route_lr, route_grade, route_protection_grading, route_stars, route_votes, route_type, route_pitches, route_length_ft, route_length_meter, route_fa, route_description, route_location, route_protection, route_page_views, route_shared_on, route_id, route_tags, route_composite_tags, route_comments, route_suggested_ratings, route_tick_comments, manual_tags`

`route_tags` is a `dict[str, list[str]]` (category → tag list). e.g.:
```json
{"Rope Length": ["rope_60m"], "Multi-Pitch, Anchors & Descent": ["single_pitch"]}
```

`area_hierarchy` is a list of `{level, area_hierarchy_name, area_hierarchy_url}` — deepest observed hierarchy is 11 levels deep (Arizona Cochise Stronghold bouldering areas).

**Route type distribution across 6 existing states (89,467 routes):**
Sport: 32,508 | Trad: 28,447 | Boulder: 27,475 | TR: 5,603 | Alpine: 3,949 | Ice: 1,505 | Aid: 1,184 | Mixed: 969 | Snow: 441

**Note:** `route_type` strings also contain "Grade II", "Grade III" etc. (Alpine route grades) and whitespace-mangled strings with fixed hardware counts. The import transformer must handle all variants.

### DataService.ts — API surface the Worker must replicate (verified by reading source)

Current calls made by the frontend:
1. `GET /data/index.json` → `string[]` (list of filenames) — replaced by Worker not needed as file listing
2. `GET /data/{filename}` → `Area[]` (area with nested routes) — replaced by `GET /api/routes?region=...&page=...`

The `App.tsx` `loadAreas` effect (line 263) iterates `dataFiles`, fetches each, maps routes to add `area_name` and `area_hierarchy`. The new `routeApi.ts` must join this data server-side or return it in the route object.

The route type filter in `App.tsx` (line 14) currently excludes Aid/Boulder/Ice/Mixed/Snow. These exclusions must be removed and replaced with UI filter checkboxes wired to the `?type=` API param.

### React components: what changes vs. what stays

| Component | Change Required |
|-----------|----------------|
| `RouteCard.tsx` | None — reads `route.*` fields which map directly to new schema |
| `FilterPanel.tsx` | Add Aid, Ice, Alpine, Mixed, Boulder, Snow type checkboxes; wire to API params |
| `AreaSearch.tsx` | Replace local in-memory search over `areas[]` with `GET /api/areas?q=` Worker call |
| `App.tsx` | Replace `loadAreas()` with `routeApi.fetchRoutes(filters, page)` + remove EXCLUDED_TYPES |
| `DataService.ts` | Delete (replaced by `routeApi.ts`) |
| `loadData.ts` | Delete (replaced by `routeApi.ts`) |
| `registerSW.ts` | Keep PWA registration; update cached URL patterns (no more `/data/*.json`) |
| `vite.config.ts` | Remove `data/*.json` from workbox `globPatterns`; update runtime caching to `/api/*` |

---

## Common Pitfalls

### Pitfall 1: Route Type String Parsing During Import
**What goes wrong:** `route_type = "Trad, Aid, 3 pitches, 350 ft"` — the import script naively splits on comma and tries to match against type names, but pitch count and length share the same field.
**Why it happens:** The scraper extracts the raw "Type:" table cell which mixes type names with stats.
**How to avoid:** The import transformer already exists conceptually in `get_route_details()` lines 522-559 which separates types, pitches, and length. Port that logic to the import script.
**Warning signs:** `is_aid = 0` for routes you expect to be aid.

### Pitfall 2: `get_sub_area_links` Missing Sub-Areas
**What goes wrong:** Yosemite NP has deep hierarchies. If the CSS class selector misses the nav div, the scraper treats it as a leaf node with no routes instead of traversing into walls/formations.
**Why it happens:** `soup.find('div', class_='max-height max-height-md-0 max-height-xs-400')` is an exact class match — if MP adds or changes classes, it returns `None`.
**How to avoid:** Add fallback selectors. Possible alternatives: find all `<a href="/area/...">` within `#left-nav`, or find the div by looking for `<a>` elements with `/area/` hrefs in any left-nav container div.
**Warning signs:** Area count is suspiciously low; no aid/alpine routes found in large parks.

### Pitfall 3: FTS5 Table and Import Order
**What goes wrong:** FTS5 virtual table `routes_fts` must be populated separately from `routes`. `wrangler d1 execute` running CREATE VIRTUAL TABLE before populating `routes` content, then later INSERT INTO `routes` doesn't auto-populate FTS.
**Why it happens:** FTS5 with `content='routes'` is a "content table" configuration — it reads from `routes` but FTS index is not automatically updated by subsequent inserts.
**How to avoid:** Either use FTS5 triggers to keep index in sync, or rebuild FTS after bulk import with `INSERT INTO routes_fts(routes_fts) VALUES('rebuild')`.
**Warning signs:** MATCH queries return 0 results when `routes` table has data.

### Pitfall 4: D1 "Statement too long" on Bulk Import
**What goes wrong:** Generating one giant `INSERT INTO routes VALUES (...), (...), ...` for 89k routes produces a SQL statement exceeding D1's 100KB limit.
**Why it happens:** D1 limits SQL statement length to 100,000 bytes (verified from docs).
**How to avoid:** Generate INSERT batches of 100-200 rows per statement in the import script.
**Warning signs:** `wrangler d1 execute` fails with "Statement too long" error.

### Pitfall 5: CORS Not Registered Before Routes in Hono
**What goes wrong:** The Pages frontend's `fetch('/api/routes')` gets blocked by CORS policy.
**Why it happens:** Hono's `app.use()` middleware ordering is sequential — registering CORS after routes means preflight OPTIONS requests hit the route handler, not the CORS middleware.
**How to avoid:** Always register `app.use('/api/*', cors(...))` before route definitions.
**Warning signs:** Browser console shows `CORS error` or `No 'Access-Control-Allow-Origin' header`.

### Pitfall 6: `route_id` Collisions Between States
**What goes wrong:** The current scraper generates `route_id = str(uuid.uuid4())` — a new UUID on each scrape run. If re-scraped, the same MP route gets a different `route_id`, breaking diff logic.
**Why it happens:** `get_route_details()` line 595: `route_details['route_id'] = str(uuid.uuid4())`.
**How to avoid:** Derive `route_id` from the MP URL (e.g., the numeric ID embedded in `/route/105733804/...`) rather than generating a fresh UUID. This makes IDs stable across scrape runs.
**Warning signs:** Diff import inserts every route as "new" on each run.

### Pitfall 7: Materialized Path Construction from Existing `area_hierarchy`
**What goes wrong:** The existing JSON has `area_hierarchy` as a flat list of `{level, area_hierarchy_name, area_hierarchy_url}`. Building a materialized path string requires joining these names in a stable, URL-safe way — but names contain spaces and special characters.
**Why it happens:** `area_hierarchy_name` values like "El Capitan / Yosemite" contain `/` which conflicts with path delimiter.
**How to avoid:** Derive path from `area_hierarchy_url` segments (the URL slug is already URL-safe) rather than from area names.
**Warning signs:** Path queries like `WHERE path LIKE '/California/%'` return no results.

---

## Code Examples

### Import Script: route_type → Boolean Columns

```python
# Source: [VERIFIED: based on scraper logic at scraping/scrape_mtnpj_final.py line 522-559]
ROUTE_TYPE_KEYWORDS = {
    'is_sport': ['sport'],
    'is_trad': ['trad'],
    'is_aid': ['aid'],
    'is_ice': ['ice'],
    'is_alpine': ['alpine'],
    'is_mixed': ['mixed'],
    'is_tr': ['tr', 'top rope'],
    'is_boulder': ['boulder'],
    'is_snow': ['snow'],
}

def parse_route_type_booleans(route_type_str: str) -> dict:
    """Convert 'Trad, Aid, 3 pitches, 350 ft' → {is_trad: 1, is_aid: 1, ...}"""
    lower = (route_type_str or '').lower()
    result = {col: 0 for col in ROUTE_TYPE_KEYWORDS}
    for col, keywords in ROUTE_TYPE_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            result[col] = 1
    return result
```

### Import Script: Area Hierarchy → Materialized Path

```python
# Source: [ASSUMED - derived from URL pattern inspection]
def build_materialized_path(area_hierarchy: list[dict]) -> str:
    """Build path from URL slugs: '/california/yosemite-national-park/el-capitan/'"""
    segments = []
    for h in area_hierarchy:
        url = h.get('area_hierarchy_url', '')
        slug = url.rstrip('/').split('/')[-1]
        if slug and slug != 'route-guide':
            segments.append(slug)
    return '/' + '/'.join(segments) + '/' if segments else '/'
```

### Incremental Diff Logic

```python
# Source: [ASSUMED - pattern consistent with D-06 decision]
async def get_existing_route_ids(db_client) -> set[str]:
    """Query D1 HTTP API for known route IDs from MP URL"""
    # Derive stable ID from MP URL: /route/105733804/name -> '105733804'
    pass

def extract_mp_route_id(route_url: str) -> str:
    """Extract the numeric Mountain Project route ID from URL"""
    import re
    m = re.search(r'/route/(\d+)/', route_url)
    return m.group(1) if m else route_url
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Selenium for all scraping | httpx async for HTML + Selenium for JS-only | Ongoing shift 2023-2025 | 10x throughput for non-JS pages |
| Static JSON file serving | Cloudflare D1 + Worker API | 2024+ for CF stack adoption | SQL filtering, pagination, no full-dataset download |
| Flat JSON data model | Normalized relational schema | This phase | Efficient boolean filtering, ancestor queries via path |
| Client-side filtering of all data | Server-side SQL with pagination | This phase | Eliminates downloading entire dataset per region |

**Deprecated in this project:**
- `DataService.ts` `getRegionRoutes()` with `_sport_trad` suffix — delete, replace with `routeApi.ts`
- `loadData.ts` — delete, inline API calls in `App.tsx` or new hook
- `firebase-climbing-search/` — entire directory, per D-11

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Materialized path built from URL slugs rather than area names avoids delimiter collision | Code Examples | Path queries may return wrong results; alternative is URL-encoding names |
| A2 | MP stable route numeric ID (from URL) can serve as `route_id` for diff logic | Pitfall 6 | If MP changes URL structure, diff breaks; fallback is URL-normalized hash |
| A3 | FTS5 content table requires manual `INSERT INTO routes_fts(routes_fts) VALUES('rebuild')` after bulk import | Schema Pattern | If D1 handles auto-sync, the rebuild step is unnecessary but harmless |
| A4 | `asyncio.Semaphore(10)` is sufficient to avoid Mountain Project rate-limiting | Async Scraper Pattern | MP may rate-limit at lower concurrency; tune during testing |
| A5 | The `type` whitelist validation in the Worker is sufficient SQL injection prevention for boolean column name interpolation | Hono Pattern | If whitelist is missing or incomplete, SQL injection is possible; use parameterized subquery as stronger alternative |

---

## Open Questions (RESOLVED)

1. **What is the MP rate limit policy?**
   - What we know: Current scraper uses synchronous requests with no explicit throttle (relies on sequential latency as natural throttle)
   - What's unclear: Whether MP enforces IP-based rate limiting and at what threshold
   - Recommendation: Start with `asyncio.Semaphore(5)` during Yosemite test case and observe; increase conservatively
   - **RESOLVED:** Plan 01-01 sets `CONCURRENCY_LIMIT = 5` with `asyncio.Semaphore(5)` and 0.4s per-request delay. The Yosemite smoke test (T03) empirically validates this threshold before full Western US scrape proceeds.

2. **Does D1 FTS5 content table auto-sync on INSERT or require manual trigger?**
   - What we know: Standard SQLite FTS5 content tables do NOT auto-sync — triggers required [CITED: SQLite FTS5 docs]
   - What's unclear: Whether Cloudflare D1's implementation adds auto-trigger behavior
   - Recommendation: Assume manual rebuild required; add `INSERT INTO routes_fts(routes_fts) VALUES('rebuild')` at end of import SQL
   - **RESOLVED:** Plan 01-02 adopts manual rebuild. `import_to_d1.py` appends `INSERT INTO routes_fts(routes_fts) VALUES('rebuild')` as the final statement in every generated SQL file. Verified by acceptance criteria in T03.

3. **Where does the Worker API live relative to the Pages app?**
   - What we know: Two deployment options: (a) separate Worker service with Pages calling it via external URL, (b) Pages Functions (`functions/` directory) which colocate API with the Pages project
   - What's unclear: Which pattern is easier to manage with wrangler for this use case
   - Recommendation: Use separate Worker service (option a) — simpler wrangler.toml per project, easier to develop and deploy independently; Pages calls `https://climbing-search-api.{account}.workers.dev/api/...`
   - **RESOLVED:** Plan 01-03 uses separate Worker service deployed from `worker-api/` with its own `wrangler.toml`. Pages app (Plan 01-04) calls the Worker via external URL configured in `VITE_API_BASE_URL`.

4. **How to handle the 6 existing state JSON files that lack California?**
   - What we know: CA was excluded from existing tagged data because it exceeded OpenAI batch limits (force_split logic in tagging script). The data directory has: AZ, CO, NV, OR, UT, WA.
   - What's unclear: Whether a CA scrape needs to happen before the D1 import, or if CA is added in a follow-up run.
   - Recommendation: Import the 6 existing states first to validate the pipeline; treat CA as the first new scrape using the async scraper.
   - **RESOLVED:** Plan 01-02 T04 generates import SQL for the 6 existing states only (AZ, CO, NV, OR, UT, WA). CA is explicitly deferred — it will be the first new scrape run using the async scraper from Plan 01-01, consistent with D-02 ("existing tagged JSON files in `data/` are the starting point").

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3 | Scraper, import script, tagging | ✓ | 3.13.3 | — |
| httpx | Async scraper | ✓ (in venv) | 0.28.1 | aiohttp (also in venv) |
| aiohttp | Async scraper alternative | ✓ (in venv) | 3.11.13 | httpx |
| BeautifulSoup4 | HTML parsing | ✓ (in venv) | 4.13.3 | — |
| Selenium | Comment/stats scraping | ✓ (in venv) | 4.28.1 | — |
| openai | LLM tagging | ✓ (in venv) | 1.63.2 | — |
| Node.js | Worker build, wrangler | ✓ | 23.11.0 | — |
| npm | Package management | ✓ | 10.9.2 | — |
| wrangler (npx) | D1 CLI, Worker deploy | ✓ via npx | 4.90.0 | — |
| Chrome/ChromeDriver | Selenium headless | ✓ (macOS path configured) | varies | — |

**Missing dependencies with no fallback:** None blocking.

**Note:** wrangler is available via `npx wrangler` but not in `$PATH`. All wrangler commands should use `npx wrangler` prefix.

---

## Validation Architecture

No `config.json` found in `.planning/`; treating nyquist_validation as enabled.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (Python scraper/import), Vitest (Worker TypeScript) |
| Config file | None — Wave 0 gap |
| Quick run command | `source venv/bin/activate && pytest scraping/tests/ -x -q` |
| Full suite command | `pytest scraping/tests/ && cd worker-api && npm test` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| D-05 | `get_sub_area_links` finds sub-areas via fallback selectors | unit | `pytest scraping/tests/test_scraper.py::test_get_sub_area_links -x` | ❌ Wave 0 |
| D-06 | Incremental diff skips unchanged routes by stable MP ID | unit | `pytest scraping/tests/test_import.py::test_diff_logic -x` | ❌ Wave 0 |
| D-14 | route_type string parsed correctly into boolean columns | unit | `pytest scraping/tests/test_import.py::test_parse_route_type -x` | ❌ Wave 0 |
| D-12 | Worker GET /routes returns filtered results | integration | `cd worker-api && npm test -- routes.test.ts` | ❌ Wave 0 |
| D-12 | FTS5 MATCH query returns relevant routes | integration | `cd worker-api && npm test -- fts.test.ts` | ❌ Wave 0 |
| D-17 | All filter params (grade, type, region, stars_min) work | integration | `cd worker-api && npm test -- routes.test.ts` | ❌ Wave 0 |

### Wave 0 Gaps

- [ ] `scraping/tests/test_scraper.py` — covers D-05 sub-area link detection
- [ ] `scraping/tests/test_import.py` — covers D-06 diff logic, D-14 boolean parsing
- [ ] `worker-api/src/routes/routes.test.ts` — covers D-12, D-17
- [ ] `worker-api/vitest.config.ts` — test config
- [ ] Install: `cd worker-api && npm install -D vitest @cloudflare/vitest-pool-workers`

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No user auth in this phase |
| V3 Session Management | No | Stateless API |
| V4 Access Control | No | Public read-only API |
| V5 Input Validation | Yes | `@hono/zod-validator` + zod schemas on all query params |
| V6 Cryptography | No | No secrets transmitted in routes |

### Known Threat Patterns for Hono + D1

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| SQL injection via `?type=` parameter | Tampering | Validate `type` against whitelist enum before interpolating into column name; all other params use parameterized `?` placeholders |
| Route enumeration via `/routes/:id` | Information Disclosure | Acceptable for public climbing data; no private data |
| Abuse of open API (scraping the scraper) | DoS | Cloudflare rate limiting at the edge (CF dashboard WAF rule) — not an app-level concern |

---

## Sources

### Primary (HIGH confidence)

- Direct codebase inspection: `scraping/scrape_mtnpj_final.py`, `climbing-search/src/utils/DataService.ts`, `climbing-search/src/App.tsx`, `climbing-search/src/types/*.ts`, `tagging/route_area_tagging.py`, `r2_config.py` — all read in this session
- Direct data inspection: `data/arizona_routes_tagged.json` — schema and statistics verified programmatically
- [Cloudflare D1 Limits](https://developers.cloudflare.com/d1/platform/limits/) — row size 2MB, SQL statement 100KB, FTS5 supported
- [Cloudflare D1 SQL Statements](https://developers.cloudflare.com/d1/sql-api/sql-statements/) — FTS5 module confirmed, JSON extension confirmed
- [D1 + Hono example](https://developers.cloudflare.com/d1/examples/d1-and-hono/) — `c.env.DB.prepare().bind().run()` pattern
- [Hono docs — Bindings](https://hono.dev/llms-full.txt) — `Hono<{ Bindings: Bindings }>` pattern
- [Wrangler configuration](https://developers.cloudflare.com/workers/wrangler/configuration/) — `[[d1_databases]]` section

### Secondary (MEDIUM confidence)

- [npm view outputs] — hono 4.12.18, wrangler 4.90.0, @cloudflare/workers-types 4.20260508.1 (verified this session)
- [Cloudflare D1 import/export](https://developers.cloudflare.com/d1/best-practices/import-export-data/) — `wrangler d1 execute --file=` pattern, batch INSERT splitting requirement
- WebSearch: httpx asyncio semaphore pattern — cross-verified with httpx official docs pattern

### Tertiary (LOW confidence)

- FTS5 content table rebuild requirement — known from SQLite FTS5 documentation [ASSUMED applies to D1]; D1-specific behavior not explicitly documented

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages verified in venv or npm registry this session
- Architecture: HIGH — based on direct codebase reading; no assumed structure
- Pitfalls: HIGH (pitfalls 1-5) / MEDIUM (pitfalls 6-7) — pitfall 6 and 7 involve UUID and path assumptions not yet verified against MP's actual URL structure
- Cloudflare platform patterns: HIGH — verified from official CF docs and Hono docs

**Research date:** 2026-05-08
**Valid until:** 2026-08-08 (stable CF/Hono APIs; Python packages in venv are pinned)
