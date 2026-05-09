# Phase 2: Tick Comments - Context

**Gathered:** 2026-05-09
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase delivers:
1. **Yosemite NP route scrape** — run the existing async scraper (`scrape_async.py`) on the full Yosemite NP area URL; no pre-imported CA data exists.
2. **D1 import** — import scraped routes using the existing chunked pipeline (PRAGMA foreign_keys=0, INSERT OR IGNORE dedup by route_id).
3. **Tick comment collection via Selenium** — for each Yosemite route, scrape the login-gated `/route/stats/` page to extract tick comments, store as individual rows in the D1 `comments` table.

Validation follows a two-step approach: El Cap sub-area first, then full Yosemite NP once tick flow is confirmed.

</domain>

<decisions>
## Implementation Decisions

### Tick Comment Scope
- **D-01:** Capture **text-only ticks** — keep the existing ≥15 word filter from `parse_stats`. Skip ticks with no text or short text. Prioritizes signal quality for Phase 3 prompt enrichment.
- **D-02:** Store tick comments as **individual rows in the `comments` table** (`parent_id=route_id`, `parent_type='tick'`). Do NOT use the concatenated `route_tick_comments` blob approach. Each tick = one row, joinable via route_id.

### Tick Data Parsing
- **D-03:** Update `parse_stats` to **preserve author and date** — extract user name → `comment_author`, tick date → `comment_time`. Current code strips these; Phase 2 must capture them for full row fidelity.
- **D-04:** **No schema changes needed** — the existing `comments` table columns (`comment_id`, `parent_id`, `parent_type`, `comment_author`, `comment_text`, `comment_time`) are sufficient. No `tick_type` column needed (tick type is out of scope per text-only decision).
- **D-05:** Use `INSERT OR IGNORE` with `route_id` as dedup key for tick comments (consistent with existing pattern).

### Selenium Session Management
- **D-06:** **Single Selenium session** for the full run — one headless Chrome driver. On login redirect or request failure, re-authenticate and retry. No session pool or per-batch re-auth.
- **D-07:** **Headless Chrome** — `--headless` flag. No visible browser window during scraping runs.
- **D-08:** MP credentials via environment variables (already established pattern from prior phases).

### Validation Approach
- **D-09:** **El Cap first, then full Yosemite.** Scrape El Cap sub-area → import → run tick collection → verify rows appear in D1 → expand to full Yosemite NP.
- **D-10:** **Go/no-go signal after El Cap:** Tick rows visible in D1 for known El Cap routes (e.g., The Nose). Spot-check query: `SELECT * FROM comments WHERE parent_type='tick' LIMIT 10`. Pass = proceed to full Yosemite run.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Scraper
- `scraping/scrape_async.py` — Main async scraper; entry point for Yosemite NP scrape. `scrape_area()` is the key function. `--no-selenium` flag skips stats/tick collection.
- `scraping/scrape_mtnpj_final.py` — Selenium-bound functions: `get_comments`, `get_route_stats`, `parse_stats`, `get_driver`, `cleanup_driver`. `parse_stats` must be updated to preserve author + date (D-03).
- `scraping/import_to_d1.py` — Existing D1 import pipeline; handles chunked batches and FK-safe imports.

### Database Schema
- `.planning/phases/01-refactor/01-CONTEXT.md` — D-13 defines the full normalized schema: `areas`, `routes`, `comments` table structure. `comments` table: `comment_id, parent_id, parent_type, comment_author, comment_text, comment_time`.

### Requirements
- `.planning/REQUIREMENTS.md` — TICK-01, TICK-02, TICK-03 define the acceptance criteria for this phase.
- `.planning/ROADMAP.md` — Phase 02 build notes (El Cap validation approach, dedup guard, credential handling).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scraping/scrape_async.py` → `scrape_area(url, ...)` — already handles deep hierarchy traversal, async HTTP bulk scraping, and Selenium-wrapped stats calls via `asyncio.to_thread`
- `scraping/import_to_d1.py` — chunked D1 import with PRAGMA foreign_keys=0; reuse as-is for Yosemite routes
- `scraping/scrape_mtnpj_final.py` → `parse_stats` — needs targeted update: stop stripping author/date, return them alongside tick text

### Established Patterns
- Disk-based cache (`data/cache/`, 7-day TTL) — `get_from_cache`/`save_to_cache` in `scrape_mtnpj_final.py` already caches stats pages; reuse to avoid re-fetching on restart
- `INSERT OR IGNORE` dedup by route_id — established in prior import pipeline; apply same pattern for tick comment rows
- Concurrency=3 for async scraper — existing rate limit guard; keep for Yosemite run

### Integration Points
- `parse_stats` → must return `(suggested_ratings, tick_entries[])` where each `tick_entry` is `{author, date, text}` instead of a flat concatenated string
- Import pipeline → must write tick entries as individual `comments` rows with `parent_type='tick'`
- D1 `comments` table — already exists with correct schema; no migration needed

### Known Issues
- `parse_stats` currently strips author, date, and tick type with regex (`re.sub(r'· ... ·', '', tick_text)`) — this must be changed to extract and preserve those fields
- Selenium `get_driver()` creates a new driver on each call if the shared driver is None; session persistence across `asyncio.to_thread` calls needs verification

</code_context>

<specifics>
## Specific Ideas

- Start URL for Yosemite NP: `https://www.mountainproject.com/area/105833381/yosemite-national-park`
- El Cap sub-area is the validation target — known routes like The Nose make good spot-check anchors
- Phase 2 tick comment data feeds Phase 3 directly: tick text becomes additional LLM prompt context for tagging. Phase 2 completeness directly affects Phase 3 tag quality.

</specifics>

<deferred>
## Deferred Ideas

- Tick type column (`Lead`/`Follow`/`TR`) — out of scope per text-only decision; could be added in a future tagging or schema phase if analysis shows it's valuable
- Full CA scrape (beyond Yosemite) — deferred; Yosemite is the target for v1.1

</deferred>

---

*Phase: 02-tick-comments*
*Context gathered: 2026-05-09*
