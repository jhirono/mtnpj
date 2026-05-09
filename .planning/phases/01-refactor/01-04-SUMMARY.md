---
phase: 01-refactor
plan: 04
subsystem: ui
tags: [react, typescript, vite, cloudflare-pages, pwa, worker-api]

# Dependency graph
requires:
  - phase: 01-03
    provides: Worker API with D1-backed routes/areas endpoints at /api/routes and /api/areas
provides:
  - routeApi.ts: Single API client class for Worker API (fetchRoutes/fetchRoute/fetchAreas/fetchAreaRoutes)
  - api/types.ts: TypeScript types matching Worker schema (RouteApi, AreaApi, ApiFilters, parseRouteTypes)
  - FilterPanel with 9 route type checkboxes (sport/trad/aid/ice/alpine/mixed/tr/boulder/snow)
  - AreaSearch using live API search (debounced fetchAreas)
  - RouteCard using boolean is_* columns and JSON route_tags
  - wrangler.pages.toml for Cloudflare Pages deployment
  - Deleted: DataService.ts, loadData.ts, public/data/*.json, firebase-climbing-search/
affects:
  - 01-05
  - Any future frontend plans

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Worker API client with in-flight promise deduplication
    - Debounced API search (250ms) replacing in-memory area search
    - filtersToApi() helper mapping UI filter state to API query params
    - NetworkFirst service worker caching for /api/* responses
    - parseRouteTypes() helper converting is_* booleans to RouteType[]

key-files:
  created:
    - climbing-search/src/api/types.ts
    - climbing-search/src/api/routeApi.ts
    - climbing-search/wrangler.pages.toml
    - climbing-search/.env.example
  modified:
    - climbing-search/src/App.tsx
    - climbing-search/src/config.ts
    - climbing-search/src/types/route.ts
    - climbing-search/src/types/area.ts
    - climbing-search/src/types/filters.ts
    - climbing-search/src/components/FilterPanel.tsx
    - climbing-search/src/components/AreaSearch.tsx
    - climbing-search/src/components/RouteCard.tsx
    - climbing-search/src/components/RouteList.tsx
    - climbing-search/src/hooks/useSearch.ts
    - climbing-search/vite.config.ts
    - climbing-search/package.json

key-decisions:
  - "Multi-type filter (2+ types) handled client-side via parseRouteTypes; single type goes to ?type= API param"
  - "Area search replaced with debounced API calls — no longer requires pre-loaded areas[] prop"
  - "route_tags JSON string parsed per-route in RouteCard via useMemo to avoid re-parsing"
  - "FilterPanel areas prop removed — tag categories show hardcoded structure (tags from API TBD)"

patterns-established:
  - "routeApi singleton pattern: single RouteApiClient instance exported, in-flight dedup via Map"
  - "filtersToApi(): canonical bridge between UI RouteFilters state and ApiFilters query params"
  - "All data fetching through routeApi; zero static JSON loading remains"

requirements-completed:
  - D-01
  - D-03
  - D-10
  - D-11
  - D-12
  - D-17

# Metrics
duration: ~45min
completed: 2026-05-09
---

# Phase 01 Plan 04: Frontend API Migration Summary

**React/Vite frontend migrated from static JSON loading to Worker API client with 9-type filter checkboxes; Firebase WIP and all _sport_trad legacy files deleted**

## Performance

- **Duration:** ~45 min
- **Started:** 2026-05-09T19:15:00Z
- **Completed:** 2026-05-09T19:58:00Z
- **Tasks:** 3 completed (T01, T02, T03); T04 is checkpoint:human-verify (pending)
- **Files modified:** 16 (includes 60 deletions)

## Accomplishments
- Created `src/api/types.ts` + `src/api/routeApi.ts`: full Worker API client with in-flight dedup, parseRouteTypes helper, 9-element ROUTE_TYPES tuple
- Updated all components (App.tsx, FilterPanel, AreaSearch, RouteCard) to use Worker API; 9 type checkboxes now visible in FilterPanel including Aid, Ice, Alpine, Mixed, Boulder, Snow
- Deleted DataService.ts, loadData.ts, 9 public/data/*.json files (all _sport_trad), and entire firebase-climbing-search/ WIP directory; TypeScript compiles clean, production build succeeds

## Task Commits

Each task was committed atomically:

1. **Task 1: Create routeApi.ts + api/types.ts + TS type updates** - `fa0aa08` (feat)
2. **Task 2: Update App/FilterPanel/AreaSearch/RouteCard to use routeApi** - `7114c71` (feat)
3. **Task 3: Delete legacy code + vite.config + wrangler.pages.toml** - `fb6dd11` (feat)

_Task 4 (checkpoint:human-verify) is pending user verification_

## Files Created/Modified

Created:
- `climbing-search/src/api/types.ts` - RouteApi, AreaApi, ApiFilters, ROUTE_TYPES, parseRouteTypes
- `climbing-search/src/api/routeApi.ts` - RouteApiClient singleton with 4 methods
- `climbing-search/wrangler.pages.toml` - Cloudflare Pages deploy config
- `climbing-search/.env.example` - VITE_API_BASE_URL placeholder

Modified:
- `climbing-search/src/App.tsx` - Worker API data loading; removed EXCLUDED_TYPES; filtersToApi helper
- `climbing-search/src/config.ts` - API_BASE_URL replacing R2/static config
- `climbing-search/src/types/route.ts` - Re-exports RouteApi as Route from api/types
- `climbing-search/src/types/area.ts` - Re-exports AreaApi as Area from api/types
- `climbing-search/src/types/filters.ts` - Added RouteType, ROUTE_TYPE_LABELS; types: RouteType[]
- `climbing-search/src/components/FilterPanel.tsx` - 9-type checkbox loop; removed areas prop
- `climbing-search/src/components/AreaSearch.tsx` - Debounced API search; removed areas prop
- `climbing-search/src/components/RouteCard.tsx` - parseRouteTypes; JSON.parse route_tags; area_path
- `climbing-search/vite.config.ts` - NetworkFirst API caching; removed /data/*.json workbox entries

Deleted:
- `climbing-search/src/utils/DataService.ts` - Legacy static JSON fetcher
- `climbing-search/src/utils/loadData.ts` - Legacy entry point
- `climbing-search/public/data/*.json` - 9 static _sport_trad JSON files
- `firebase-climbing-search/` - Entire WIP Firebase directory (D-11)

## Decisions Made
- Multi-type filter (2+ types selected) is handled client-side via `parseRouteTypes`; when exactly 1 type is selected, it's sent as `?type=` API param for server-side filtering
- AreaSearch now calls `routeApi.fetchAreas({ q, limit: 5 })` with 250ms debounce; the old `areas: Area[]` prop is removed entirely
- `FilterPanel` tag categories (Crack, Style, Weather, etc.) show hardcoded structure but will be empty until API-driven tag discovery is implemented in a future plan
- `vite.config.ts` comment mentions `/data/` deletion but the actual workbox config only caches `/api/*` (no static data caching)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed buildQuery TypeScript type error**
- **Found during:** Task 1 (routeApi.ts creation)
- **Issue:** `buildQuery(params: Record<string, unknown>)` rejected `ApiFilters`/`AreaFilters` interface args (missing index signature)
- **Fix:** Changed parameter type to `object` with internal cast `Object.entries(params as Record<string, unknown>)`
- **Files modified:** `climbing-search/src/api/routeApi.ts`
- **Verification:** `tsc --noEmit` on api files passed
- **Committed in:** fa0aa08

**2. [Rule 1 - Bug] Removed unused toggleType function from FilterPanel**
- **Found during:** Task 2 (FilterPanel update)
- **Issue:** Old `toggleType` function became unused after replacing it with inline onChange in the ROUTE_TYPES.map loop; TypeScript noUnusedLocals flagged it
- **Fix:** Removed the function; replaced with inline handler in JSX
- **Files modified:** `climbing-search/src/components/FilterPanel.tsx`
- **Verification:** `tsc --noEmit -p tsconfig.app.json` passed with zero errors
- **Committed in:** 7114c71

**3. [Rule 2 - Missing Critical] Stubbed DataService.ts/loadData.ts for T02 compile**
- **Found during:** Task 2 (TypeScript check)
- **Issue:** DataService.ts and loadData.ts (scheduled for T03 deletion) had old Area type with `.routes`/`.area_hierarchy` fields that no longer exist after types/area.ts was rewritten; this blocked `tsc --noEmit`
- **Fix:** Replaced both files with deprecation stubs before Task 2 commit; properly deleted them in Task 3 commit
- **Files modified:** Both files, then deleted in T03
- **Verification:** `tsc --noEmit -p tsconfig.app.json` produced 0 errors before T03
- **Committed in:** 7114c71 (stub), fb6dd11 (deletion)

---

**Total deviations:** 3 auto-fixed (2 Rule 1 bugs, 1 Rule 2 missing critical)
**Impact on plan:** All auto-fixes necessary for correctness. No scope creep.

## Known Stubs

- **FilterPanel tag categories**: The "Crowds & Popularity", "Difficulty & Safety", "Multi-Pitch", "Crack Climbing", etc. sections show hardcoded tag structures but no actual tags will appear until the API delivers populated route_tags data. The `availableTags` state is now always empty `{}` since areas prop was removed. Tags display correctly from route cards (route_tags JSON parsed per-route). This is intentional — tags require data to be present in D1, which depends on the scraper outputting populated route_tags (future work).

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: info-disclosure | climbing-search/src/api/routeApi.ts | API_BASE_URL baked into bundle — accepted per plan T-04-02 (public URL by design) |

## Issues Encountered
- The `tsc --noEmit --skipLibCheck src/api/types.ts src/api/routeApi.ts` command in the plan verification produced `import.meta.env` errors because standalone tsc doesn't include vite-env.d.ts types. Verified using `tsc -p tsconfig.app.json` instead, which correctly picks up Vite client types. The API files themselves have zero errors in the full project compilation.

## User Setup Required

Before deploying:
1. Copy `.env.example` to `.env.local` for dev: set `VITE_API_BASE_URL=https://climbing-search-api.jumpei-hirono.workers.dev`
2. For production build: create `.env.production` with the same `VITE_API_BASE_URL` set to the deployed Worker URL
3. Deploy with: `cd climbing-search && npm run build && npm run pages:deploy`
4. First deploy will prompt to create the Cloudflare Pages project

## Next Phase Readiness
- Frontend is fully wired to Worker API; zero static JSON loading remains
- All 9 route types are filterable; aid/boulder/ice/alpine/mixed/snow checkboxes appear in FilterPanel
- Production build is clean (172KB JS bundle + CSS, PWA service worker caches API responses)
- Cloudflare Pages deployment ready: `wrangler pages deploy dist --project-name climbing-search`
- Pending: T04 human verification (local dev test + Pages deployment + smoke test)

---
*Phase: 01-refactor*
*Completed: 2026-05-09*
