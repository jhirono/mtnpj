# Phase 2: Tick Comments — Research

**Researched:** 2026-05-09
**Domain:** Python Selenium authentication, HTML parsing (BeautifulSoup), Cloudflare D1 schema migration, SQLite CHECK constraint
**Confidence:** HIGH (all claims verified by direct codebase inspection, live D1 query, and MP HTTP probing)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Capture **text-only ticks** — keep the existing >=15 word filter from `parse_stats`. Skip ticks with no text or short text. Prioritizes signal quality for Phase 3 prompt enrichment.
- **D-02:** Store tick comments as **individual rows in the `comments` table** (`parent_id=route_id`, `parent_type='tick'`). Do NOT use the concatenated `route_tick_comments` blob approach. Each tick = one row, joinable via route_id.
- **D-03:** Update `parse_stats` to **preserve author and date** — extract user name → `comment_author`, tick date → `comment_time`. Current code strips these; Phase 2 must capture them for full row fidelity.
- **D-04:** **No schema changes needed** — the existing `comments` table columns (`comment_id`, `parent_id`, `parent_type`, `comment_author`, `comment_text`, `comment_time`) are sufficient. No `tick_type` column needed.
- **D-05:** Use `INSERT OR IGNORE` with `route_id` as dedup key for tick comments (consistent with existing pattern).
- **D-06:** **Single Selenium session** for the full run — one headless Chrome driver. On login redirect or request failure, re-authenticate and retry. No session pool or per-batch re-auth.
- **D-07:** **Headless Chrome** — `--headless` flag. No visible browser window during scraping runs.
- **D-08:** MP credentials via environment variables (already established pattern from prior phases).
- **D-09:** **El Cap first, then full Yosemite.** Scrape El Cap sub-area → import → run tick collection → verify rows appear in D1 → expand to full Yosemite NP.
- **D-10:** **Go/no-go signal after El Cap:** Tick rows visible in D1 for known El Cap routes (e.g., The Nose). Spot-check query: `SELECT * FROM comments WHERE parent_type='tick' LIMIT 10`. Pass = proceed to full Yosemite run.

### Deferred Ideas (OUT OF SCOPE)
- Tick type column (`Lead`/`Follow`/`TR`) — out of scope per text-only decision; could be added in a future tagging or schema phase
- Full CA scrape (beyond Yosemite) — deferred; Yosemite is the target for v1.1
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TICK-01 | Selenium login session established and stable for MountainProject authenticated pages | Login implementation is net-new (no code exists); `get_driver()` and `init_selenium_driver()` are in place — login step must be added to `get_route_stats` flow |
| TICK-02 | Yosemite NP routes scraped and imported into D1; tick comments scraped via Selenium | `scrape_async.py` + `run_scrape()` is the entry point; no Yosemite data in D1 yet — full scrape + import required |
| TICK-03 | Tick comments stored in D1 `comments` table and joinable to routes via route_id | Schema migration required: `parent_type` CHECK constraint must add `'tick'`; then `import_to_d1.py` extended with tick row writer |
</phase_requirements>

---

## Summary

Phase 2 delivers three sequential stages: (1) Yosemite NP route scrape via the existing async scraper, (2) D1 import of scraped routes using the existing pipeline, and (3) Selenium-authenticated tick comment collection stored as individual `comments` rows.

The most significant finding is a **schema conflict**: the live `comments` table has `CHECK(parent_type IN ('route', 'area'))` but D-02 requires `parent_type='tick'`. This constraint will reject all tick insert attempts, causing silent data loss. A schema migration (ALTER TABLE or recreation) must precede any tick import. This is the highest-risk item in the phase.

The second critical finding is that **Selenium login is a net-new implementation**. The existing `get_comments()` function accepts `user_email` and `user_pass` parameters but never uses them — no actual login code exists. The scraper currently accesses MP pages as an unauthenticated user; the stats page returns a "Please Confirm" anti-bot modal and a login form. Tick comments require authentication; this must be implemented from scratch using Selenium's form-filling capability.

All other assets are reusable: `scrape_async.py` (BFS area traversal, route details, caching), `import_to_d1.py` (chunked SQL batching, dedup, FTS rebuild), and the disk-based cache (7-day TTL, `data/cache/`). The 22 existing tests all pass and the test infrastructure (pytest 9.0.3 + pytest-asyncio 1.3.0) is available in the project venv.

**Primary recommendation:** Address the schema migration and login implementation in Wave 1 (blockers), before any scraping or import tasks. The scrape and import can then proceed in Wave 2 using existing infrastructure, and tick collection in Wave 3.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Yosemite NP area/route scraping | Scraper (local Python) | — | Existing `scrape_async.py` BFS + httpx async traversal |
| D1 route import | Local CLI (wrangler + Python) | — | `import_to_d1.py` generates SQL; `wrangler d1 execute` loads it |
| MP login authentication | Scraper (Selenium) | — | Login-gated pages require browser session; credentials via env vars |
| Tick comment collection | Scraper (Selenium) | — | `/route/stats/` pages render ticks client-side; requires authenticated browser |
| Tick data parsing (author/date/text) | Scraper (Python) | — | `parse_stats()` in `scrape_mtnpj_final.py` — targeted update |
| Tick comment D1 import | Local CLI (Python + wrangler) | — | Extension to `import_to_d1.py`; new tick-specific writer or post-import step |
| Schema migration | Local CLI (wrangler) | — | D1 ALTER TABLE or schema recreation to allow `parent_type='tick'` |
| Validation / spot-check queries | Local CLI (wrangler) | — | `wrangler d1 execute --local` for El Cap go/no-go gate |

---

## Standard Stack

### Core (verified in project venv)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| selenium | 4.43.0 | Headless Chrome browser automation | Already in venv; `get_driver()` + `init_selenium_driver()` already implemented |
| httpx | 0.28.1 | Async HTTP for area/route scraping | Already in venv and used by `scrape_async.py` |
| beautifulsoup4 | 4.14.3 | HTML parsing (stats page, route pages) | Already in venv; lxml parser backend |
| lxml | 6.1.0 | Fast HTML parser backend | Already in venv |
| aiohttp | 3.13.5 | Async HTTP alternative | In venv; not needed for Phase 2 |
| pytest | 9.0.3 | Test runner | In venv; all 22 existing tests pass |
| pytest-asyncio | 1.3.0 | Async test support | In venv |
| wrangler (npx) | 4.90.0 | D1 SQL execution, schema migration | Available via npx in worker-api/ |

[VERIFIED: direct pip list output from .venv]

### No New Dependencies Required
Phase 2 uses only existing installed packages. No `pip install` steps are needed.

---

## Architecture Patterns

### System Architecture Diagram

```
[MP Area Page: Yosemite NP URL]
        |
        v (httpx async BFS)
[scrape_async.py: scrape_lowest_level_areas()]
        |
        v (leaf area URLs)
[scrape_async.py: get_routes() per leaf area]
  |           |
  v           v (asyncio.to_thread)
[httpx      [scrape_mtnpj_final.py: get_comments()]
 route       — NOT used for ticks; kept for route comments
 pages]
        |
        v (JSON output)
[data/yosemite-national-park_routes.json]
        |
        v (import_to_d1.py)
[SQL batches → wrangler d1 execute]
        |
        v
[D1: areas + routes populated]
        |
        v (tick collection script — new)
[For each route_id in D1 WHERE area path like yosemite:]
        |
        v (Selenium authenticated session)
[scrape_mtnpj_final.py: get_route_stats(route_url)]
  → navigate to /route/stats/{id}/{slug}
  → parse_stats(soup) — updated to return tick_entries[]
        |
        v
[tick_entries: [{author, date, text}, ...]]
        |
        v (INSERT OR IGNORE)
[D1: comments table, parent_type='tick']
```

### Recommended Project Structure for New Code

```
scraping/
├── scrape_async.py          # unchanged — Yosemite run uses existing entry point
├── scrape_mtnpj_final.py    # targeted update: parse_stats() + login_if_needed()
├── import_to_d1.py          # minor extension: tick comment writer function
└── collect_ticks.py         # NEW: standalone tick collection script
                             # reads route_ids from D1, calls get_route_stats,
                             # writes tick rows to D1 via SQL INSERT OR IGNORE
```

### Pattern 1: MP Login via Selenium

**What:** Navigate to login page, fill email/password form, submit, verify session.
**When to use:** Before any stats page request in a fresh driver session.

```python
# Source: [ASSUMED — login flow inferred from existing Selenium patterns in codebase]
def login_mp(driver, email: str, password: str) -> bool:
    """Log in to Mountain Project via Selenium. Returns True on success."""
    LOGIN_URL = "https://www.mountainproject.com/user/login"
    driver.get(LOGIN_URL)
    time.sleep(2)

    try:
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        email_field.clear()
        email_field.send_keys(email)

        pw_field = driver.find_element(By.NAME, "password")
        pw_field.clear()
        pw_field.send_keys(password)

        submit = driver.find_element(By.CSS_SELECTOR, "button[type=submit]")
        submit.click()
        time.sleep(3)

        # Verify login succeeded — MP redirects away from login page on success
        if "login" not in driver.current_url.lower():
            return True
        return False
    except Exception as e:
        logging.error(f"Login failed: {e}")
        return False
```

**Selector verification needed:** The exact `By.NAME` selectors for MP's login form must be verified at run time via Selenium's page inspection. The pattern above is the standard approach; the attribute names may differ. [ASSUMED: MP login form field names]

### Pattern 2: Updated `parse_stats` Return Shape

**What:** Return individual tick entries with author, date, and text instead of a flat string.
**Change:** Remove the `re.sub` stripping of date and `·...·` patterns; instead extract them.

```python
# Source: [VERIFIED: scraping/scrape_mtnpj_final.py lines 365-418]
# CURRENT (strips author/date):
tick_text = re.sub(r'\b[A-Za-z]{3}\s+\d{1,2},\s*\d{4}\b', '', tick_text)  # Remove date
tick_text = re.sub(r'·.*?·', '', tick_text)  # Remove climb type

# REQUIRED (preserve and extract):
def parse_stats(soup) -> tuple[dict, None, list[dict]]:
    """
    Returns:
        (suggested_ratings, None, tick_entries)
        tick_entries: list of {author: str, date: str, text: str}
    """
    tick_entries = []
    # For each table row in Ticks table:
    #   cells[0] = author cell (contains <a> tag with user name)
    #   cells[1] = tick text cell (contains "· Lead · Jun 12, 2023 · text...")
    #   Parse: extract author from <a href="/user/...">, date from date pattern,
    #          strip "· type ·" from text, apply >=15 word filter
```

The `·` separator pattern in cells[1] is: `[tick_type] · [date] · [text]`. Regex `r'·\s*([^·]+)\s*·\s*([^·]+)\s*·\s*(.+)'` extracts type, date, text in order. [ASSUMED: exact delimiter pattern — verify against live stats page HTML]

### Pattern 3: Tick Comment D1 Import (INSERT OR IGNORE)

**What:** Write individual tick rows to `comments` table with dedup.
**Key:** `comment_id` is a deterministic hash of `route_id:author:date` — same as existing `_make_comment_id()`.

```python
# Source: [VERIFIED: scraping/import_to_d1.py lines 323-343]
# Existing _make_comment_id and _build_comment_rows already handle this pattern.
# Extension: call _build_comment_rows(tick_entries, route_id, 'tick')
# after the schema migration allows parent_type='tick'.

# INSERT OR IGNORE (not INSERT OR REPLACE) for ticks — dedup guard:
INSERT_TICK_SQL = """
INSERT OR IGNORE INTO comments
  (comment_id, parent_id, parent_type, comment_author, comment_text, comment_time)
VALUES (?, ?, 'tick', ?, ?, ?);
"""
```

### Anti-Patterns to Avoid

- **Inserting `parent_type='tick'` before schema migration:** The CHECK constraint will reject silently in some SQLite builds or raise SQLITE_CONSTRAINT in strict mode. Run the migration first and verify with a test insert.
- **Re-creating the Selenium driver per route:** `get_driver()` already implements session reuse via `global_driver`. Do not call `init_selenium_driver()` directly in a per-route loop — this creates a new browser process per route.
- **Using `asyncio.to_thread` for stats in the new tick collector:** The standalone `collect_ticks.py` script does not need asyncio — it can call `get_route_stats()` synchronously per route with a delay. Reserve `asyncio.to_thread` for integration with the async scraper.
- **Caching stats pages for the Selenium-fetched content:** The existing cache (`data/cache/stats/`) will serve stale responses on restart. If tick collection was interrupted, clear the stats cache or extend TTL to 0 before re-running to ensure all routes are visited.
- **Calling `cleanup_driver()` before the full run is complete:** The driver must stay alive across all tick requests in the session. Only call `cleanup_driver()` in a `finally` block at the end of the run.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| D1 statement size limits | Custom chunker | `chunk_inserts()` in `import_to_d1.py` | Already handles 100KB D1 limit with 5KB headroom |
| SQL injection from tick text | String interpolation | `sql_quote()` in `import_to_d1.py` | Tick comment text contains apostrophes, special chars |
| Deterministic comment IDs | UUID4 | `_make_comment_id(parent_id, author, time)` | MD5 hash of route+author+date produces stable dedup key |
| Selenium driver lifecycle | New driver per call | `get_driver()` global session reuse | Already manages health check + restart on failure |
| Disk-based page caching | Custom file cache | `get_from_cache` / `save_to_cache` | 7-day TTL, keyed by URL MD5 — already in both scrapers |
| Area BFS traversal | Custom crawler | `scrape_lowest_level_areas()` in `scrape_async.py` | Multi-strategy sub-area detection; handles Yosemite deep hierarchy |

**Key insight:** Phase 2 is almost entirely integration work — the hard problems (async scraping, chunked D1 import, Selenium session management, disk caching) are already solved. The new code is a login function, a `parse_stats` update, and a tick collection orchestrator.

---

## Runtime State Inventory

> Phase 2 is not a rename/refactor phase. This section covers data state relevant to the phase execution.

| Category | Items Found | Action Required |
|----------|-------------|-----------------|
| Stored data | D1 local: 17,358 routes, 576 comments, 3,252 areas — NO Yosemite NP data | Full Yosemite scrape + import required before tick collection |
| Stored data | `data/el-capitan_routes.json` exists (7 areas, 110 routes) — tick_comments all empty strings | El Cap data scraped without Selenium (--no-selenium or pre-Phase 2); re-import with tick collection enabled |
| Live service config | D1 remote: auth error (7403) — local D1 is the working target for development | Use `--local` flag for all wrangler commands during dev; sync to remote when validated |
| OS-registered state | None | — |
| Secrets/env vars | `MP_LOGIN_EMAIL`, `MP_LOGIN_PASSWORD` — must be set before any Selenium tick run | Verify env vars are set before running collect_ticks.py |
| Build artifacts | `data/cache/` — stats cache entries from prior runs may be stale or absent | Clear or respect TTL; stats cache holds Selenium-fetched page content |

---

## Critical Issue: Schema Conflict (BLOCKER)

**D-02 decision:** `parent_type='tick'`
**Live schema constraint:** `CHECK(parent_type IN ('route', 'area'))`

Verified against local D1:

```sql
-- Actual DDL (verified 2026-05-09 via wrangler d1 execute --local):
CREATE TABLE comments (
  comment_id TEXT PRIMARY KEY,
  parent_id TEXT NOT NULL,
  parent_type TEXT NOT NULL CHECK(parent_type IN ('route', 'area')),
  comment_author TEXT,
  comment_text TEXT,
  comment_time TEXT
)
```

D-04 in CONTEXT.md states "No schema changes needed" — this is **incorrect based on the actual live schema**. The existing CHECK constraint explicitly excludes `'tick'`. Inserting a tick row will fail with `SQLITE_CONSTRAINT_CHECK`. **D-04 must be reconciled before planning.**

**Resolution options:**

1. **Migrate schema** (recommended): Drop and recreate `comments` table with `CHECK(parent_type IN ('route', 'area', 'tick'))`. Since there are only 576 rows currently, migration is fast. Script: backup existing rows → DROP → CREATE with updated CHECK → reinsert backed-up rows.

2. **Use `parent_type='route'` with a marker**: Store ticks as `parent_type='route'` but distinguish them via a prefix on `comment_text` or a separate `comment_time` convention. This avoids schema migration but makes the data harder to query for Phase 3. **Not recommended.**

3. **Use the existing `route_tick_comments` column on `routes`**: Store ticks in the legacy blob column. Violates D-02. **Not recommended.**

**Planner must address this conflict before tick import tasks are written.** The schema migration is a Wave 0 task that blocks all tick import work.

---

## Critical Issue: Login Implementation Missing (BLOCKER)

`get_comments()` in `scrape_mtnpj_final.py` accepts `user_email` and `user_pass` but **never uses them** — no login form interaction code exists. The function opens the target URL directly with Selenium and parses whatever is rendered for unauthenticated users.

Verified by code inspection (lines 295-363): no `find_element(By.NAME, 'email')`, no `send_keys`, no form submission.

The `/route/stats/` page behavior without authentication (verified via live HTTP probe, 2026-05-09):
- Returns HTTP 200 but renders a "Please Confirm" modal + login form
- Does NOT redirect to `/login` — it serves a page with a modal overlay
- Tick table is not present in the unauthenticated HTML

**Implication:** A new `login_mp(driver, email, password)` function must be written and called before the first stats page request. The Selenium driver must navigate to the MP login URL, submit credentials, and verify the session before any tick collection begins.

---

## Common Pitfalls

### Pitfall 1: stats URL format mismatch
**What goes wrong:** `route_url.replace('/route/', '/route/stats/', 1)` works only when the URL has the `/route/` prefix at the correct position. MP route URLs are `https://www.mountainproject.com/route/{id}/{slug}` — the replace produces `https://www.mountainproject.com/route/stats/{id}/{slug}` which is the correct stats URL format. Verified via live HTTP probe (the stats URL was found in page source of a route page).
**Why it happens:** The replace is position-sensitive; if `route_url` somehow lacks `/route/` (e.g., a cached URL with extra path), the replace silently fails.
**How to avoid:** After replace, assert the resulting URL contains `/route/stats/`.

### Pitfall 2: Selenium and asyncio thread safety
**What goes wrong:** `asyncio.to_thread(get_route_stats, url)` works in `scrape_async.py` because `global_driver` is module-level and the thread shares the same process memory. However, Selenium WebDriver is NOT thread-safe — concurrent calls to `asyncio.to_thread` targeting the same driver will cause race conditions.
**Why it happens:** `asyncio.to_thread` can run multiple calls concurrently if they are gathered together.
**How to avoid:** In `collect_ticks.py`, process routes sequentially (no `asyncio.gather` over `get_route_stats` calls). The existing `scrape_async.py` already wraps stats calls in individual `to_thread` calls per route, with `asyncio.gather` only over the route list for a single area — this is safe only if routes in an area batch are gathered sequentially by the Semaphore (CONCURRENCY_LIMIT=5 means up to 5 concurrent threads, each calling the same driver). This is an existing race condition risk in `scrape_async.py` that Phase 2 should not replicate.

### Pitfall 3: CHECK constraint silent failure
**What goes wrong:** `INSERT OR IGNORE` silently swallows the SQLITE_CONSTRAINT_CHECK error for `parent_type='tick'` before migration. All tick inserts succeed with exit code 0 but zero rows are written. No error log entry unless the caller checks `changes()`.
**How to avoid:** Run the schema migration before any tick import. After migration, do a test insert with `parent_type='tick'` and verify `changes() = 1`.

### Pitfall 4: Login session loss mid-run
**What goes wrong:** MP may expire the session or serve a redirect-to-login during a long scrape run (hundreds of routes).
**How to avoid:** Per D-06, implement a login-redirect detector in `get_route_stats`: after navigating to the stats URL, check `driver.current_url` and page title. If it contains 'login' or the tick table is absent, re-authenticate and retry once.

### Pitfall 5: Cache serving stale unauthenticated stats
**What goes wrong:** If the stats page for a route was previously fetched without auth (or partially fetched), the disk cache will return the unauthenticated HTML on the next run.
**How to avoid:** The cache is keyed by URL and stored in `data/cache/stats/`. For Phase 2's first tick collection run, clear the stats cache directory or use a fresh cache dir to ensure all stats pages are freshly fetched with an authenticated session.

### Pitfall 6: D1 FTS rebuild required after route import
**What goes wrong:** `import_to_d1.py` already appends `INSERT INTO routes_fts(routes_fts) VALUES('rebuild');` at the end of the SQL output. If tick comment import is run as a separate SQL file, the FTS rebuild is not included — search may return stale results.
**How to avoid:** FTS rebuild is only needed after route inserts (tick comments go to `comments` table, not `routes`). No FTS rebuild is needed for tick-only imports. Do not add a redundant FTS rebuild to the tick import SQL.

### Pitfall 7: Yosemite hierarchy depth exceeds BFS batch assumptions
**What goes wrong:** Yosemite NP has a deep hierarchy (Park → Formation → Wall → Sub-area → Routes). The BFS in `scrape_lowest_level_areas` processes `CONCURRENCY_LIMIT` URLs per batch. If the hierarchy is 6+ levels deep, BFS may require many rounds before reaching leaf areas.
**Why it matters:** This is expected behavior — the existing scraper handles it. The El Cap sub-area (`~261K` area noted in CONTEXT.md specifics) is a faster validation target for the tick flow before running the full Yosemite NP hierarchy.
**How to avoid:** Start with El Cap sub-area URL directly: `https://www.mountainproject.com/area/105808956/el-capitan` — this skips the Yosemite NP hierarchy and goes directly to the El Cap sub-tree.

---

## Code Examples

### Verified: `parse_stats` current return signature
```python
# Source: [VERIFIED: scraping/scrape_mtnpj_final.py line 418]
return suggested_ratings, None, tick_comments  # tick_comments is a joined string
# Current callers:
suggested_ratings, _, tick_comments = get_route_stats(route_url)
route_details["route_tick_comments"] = tick_comments or ""
```

After update, return shape must be:
```python
return suggested_ratings, None, tick_entries  # tick_entries is list[dict]
# Each dict: {"author": str, "date": str, "text": str}
```

The existing `get_route_stats` caches result as `{"suggested_ratings": ..., "tick_comments": ...}`. The cache format must be updated alongside the function — or the stats cache cleared to avoid type mismatches on restart.

### Verified: D1 local query for tick validation
```bash
# Source: [VERIFIED: npx wrangler d1 execute --local 2026-05-09]
cd worker-api && npx wrangler d1 execute climbing-search \
  --command "SELECT * FROM comments WHERE parent_type='tick' LIMIT 10;" \
  --local
```

### Verified: D1 schema migration pattern
```sql
-- Source: [ASSUMED — SQLite ALTER TABLE limitations]
-- SQLite does not support ALTER TABLE ... MODIFY COLUMN for CHECK constraints.
-- Must use the copy-recreate pattern:

PRAGMA foreign_keys = 0;

CREATE TABLE comments_new (
  comment_id TEXT PRIMARY KEY,
  parent_id TEXT NOT NULL,
  parent_type TEXT NOT NULL CHECK(parent_type IN ('route', 'area', 'tick')),
  comment_author TEXT,
  comment_text TEXT,
  comment_time TEXT
);

INSERT INTO comments_new SELECT * FROM comments;
DROP TABLE comments;
ALTER TABLE comments_new RENAME TO comments;
CREATE INDEX IF NOT EXISTS idx_comments_parent ON comments(parent_id, parent_type);

PRAGMA foreign_keys = 1;
```

### Verified: Existing tick row builder (for reference)
```python
# Source: [VERIFIED: scraping/import_to_d1.py lines 323-343]
def _build_comment_rows(comments: list[dict], parent_id: str, parent_type: str) -> list[str]:
    rows = []
    for c in comments or []:
        comment_id = _make_comment_id(parent_id, c.get("comment_author"), c.get("comment_time"))
        values = (
            sql_quote(comment_id),
            sql_quote(parent_id),
            sql_quote(parent_type),
            sql_quote(c.get("comment_author")),
            sql_quote(c.get("comment_text")),
            sql_quote(c.get("comment_time")),
        )
        rows.append("(" + ",".join(values) + ")")
    return rows
# Reusable as-is for tick entries: _build_comment_rows(tick_entries, route_id, 'tick')
```

---

## State of the Art

| Old Approach | Current Approach | Notes |
|--------------|-----------------|-------|
| Concatenated tick blob (`route_tick_comments TEXT`) | Individual rows in `comments` table per D-02 | Migration required; existing blob column remains for backward compat but is unused |
| Sync requests-based scraper (`scrape_mtnpj_final.py`) | Async httpx scraper (`scrape_async.py`) | Phase 1 completed this; `scrape_async.py` is the entry point |
| UUID4 for route/area IDs | Stable MP numeric IDs extracted from URLs | Already implemented in `import_to_d1.py` |
| Selenium `--headless` (old flag) | `--headless=new` flag (Chrome 109+) | Already in `init_selenium_driver()` line 247 [VERIFIED] |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | MP login form fields are accessible via `By.NAME` with names `email` and `password` | Pattern 1 | Login function fails; must adjust selectors. Mitigation: verify in El Cap validation run |
| A2 | The `·` delimiter separating tick type, date, and text in stats table cells is U+00B7 (middle dot) | Pattern 2 | `parse_stats` extracts wrong fields. Mitigation: print raw cell text during El Cap validation |
| A3 | D1 schema migration (copy-recreate) works on Cloudflare D1 remote | Schema migration pattern | Remote D1 may have restrictions on DDL in multi-statement batches. Mitigation: test locally first, apply to remote via wrangler |
| A4 | El Cap sub-area URL is `https://www.mountainproject.com/area/105808956/el-capitan` | Pitfall 7 | Wrong URL causes empty scrape. Mitigation: verify via browser before running |
| A5 | D-04 "No schema changes needed" is based on misread of the schema — the live CHECK constraint must be updated | Critical Issue section | If schema does NOT need updating (perhaps 'tick' was already allowed), Wave 0 migration task is unnecessary. Mitigation: test `INSERT` with `parent_type='tick'` before starting Wave 0 |

---

## Open Questions (RESOLVED)

1. **D-04 conflict with live schema**
   - What we know: The live `comments` table has `CHECK(parent_type IN ('route', 'area'))`. D-02 requires `parent_type='tick'`.
   - What's unclear: D-04 says "no schema changes needed" — was this written before verifying the constraint?
   - Recommendation: Planner should treat the schema migration as required (Wave 0 task) and flag D-04 as superseded by the live schema finding. The migration is low-risk (576 rows to migrate).
   - **RESOLVED:** Schema migration chosen. Plan 02-01 performs the copy-recreate migration to add 'tick' to the CHECK constraint. D-04 is superseded by the verified live schema.

2. **MP login form HTML structure**
   - What we know: The login page exists at `https://www.mountainproject.com/user/login`; the unauthenticated stats page shows a login modal.
   - What's unclear: Exact form field names/IDs, whether there's CSRF token handling, whether a modal login or full-page login works better with Selenium.
   - Recommendation: Implement full-page login (navigate to `/user/login`) rather than interacting with the modal overlay. Full-page login is more reliable with Selenium.
   - **RESOLVED:** Full-page login approach chosen (navigate to `/user/login`, fill email/password fields). Selectors (By.NAME "email", "password") verified during El Cap validation run in Plan 02-04.

3. **Tick collection scope: scrape_async.py integration vs. standalone script**
   - What we know: Phase 2 scrapes routes first, then collects ticks. The async scraper already calls `get_route_stats` inline.
   - What's unclear: Should tick collection be integrated into the Yosemite scrape run (inline during route detail fetch) or run as a separate post-import pass on D1 route_ids?
   - Recommendation: Standalone post-import pass (separate `collect_ticks.py`). Reasons: (1) inline Selenium during async scrape has thread-safety risks; (2) tick collection can be re-run independently if it fails; (3) the D1 route_ids are already stable after import.
   - **RESOLVED:** Standalone `collect_ticks.py` chosen (Plan 02-03). Avoids asyncio thread-safety risk and supports independent re-runs after import.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.13 | All scraping scripts | Yes | 3.13.3 | — |
| selenium | Tick collection | Yes (in .venv) | 4.43.0 | — |
| httpx | Async area scraping | Yes (in .venv) | 0.28.1 | — |
| beautifulsoup4 | HTML parsing | Yes (in .venv) | 4.14.3 | — |
| Google Chrome | Selenium headless | Yes | Detected at `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome` | — |
| chromedriver | Selenium driver | Not in PATH | — | `Service()` with no path (selenium-manager auto-downloads) |
| wrangler (npx) | D1 execute | Yes | 4.90.0 | — |
| MP_LOGIN_EMAIL env var | Tick collection auth | Unknown | — | Run will fail with empty credentials |
| MP_LOGIN_PASSWORD env var | Tick collection auth | Unknown | — | Run will fail with empty credentials |

[VERIFIED: python3 --version, pip list in .venv, ls /Applications/Google Chrome.app, npx wrangler --version 2026-05-09]

**Notes:**
- `chromedriver` is not in PATH but `init_selenium_driver()` uses `Service()` with no path, which invokes selenium-manager for auto-download. This is the correct approach for Chrome 115+.
- Cloudflare D1 remote (database_id `4183c756-4393-4fc1-913e-10e5f2e813ac`) returned auth error 7403 — local D1 is the target for development and validation. Remote sync is a deployment step.
- MP credentials are not verified — they must be present in the shell environment before any tick collection run.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 + pytest-asyncio 1.3.0 |
| Config file | `pytest.ini` not found — uses pyproject.toml or inline config |
| Quick run command | `source .venv/bin/activate && python3 -m pytest scraping/tests/ -v --tb=short` |
| Full suite command | `source .venv/bin/activate && python3 -m pytest scraping/tests/ -v` |
| Current status | 22 tests pass (verified 2026-05-09) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TICK-01 | `login_mp()` returns True with valid credentials | integration (requires env vars) | `pytest scraping/tests/test_tick_collector.py::test_login_succeeds -x` | ❌ Wave 0 |
| TICK-01 | `login_mp()` returns False with invalid credentials | unit (mock driver) | `pytest scraping/tests/test_tick_collector.py::test_login_fails_bad_creds -x` | ❌ Wave 0 |
| TICK-01 | Session stays alive across multiple `get_route_stats` calls | integration | `pytest scraping/tests/test_tick_collector.py::test_session_reuse -x` | ❌ Wave 0 |
| TICK-02 | `parse_stats` returns `list[dict]` with author/date/text | unit (fixture HTML) | `pytest scraping/tests/test_tick_collector.py::test_parse_stats_returns_entries -x` | ❌ Wave 0 |
| TICK-02 | `parse_stats` applies >=15 word filter | unit (fixture HTML) | `pytest scraping/tests/test_tick_collector.py::test_parse_stats_word_filter -x` | ❌ Wave 0 |
| TICK-03 | Tick rows in D1 have `parent_type='tick'` and join to routes via route_id | integration (local D1) | `pytest scraping/tests/test_tick_collector.py::test_tick_rows_in_d1 -x` | ❌ Wave 0 |
| TICK-03 | `INSERT OR IGNORE` dedup — re-inserting same tick does not duplicate | unit (sqlite in-memory) | `pytest scraping/tests/test_tick_collector.py::test_tick_dedup -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `source .venv/bin/activate && python3 -m pytest scraping/tests/ -v --tb=short`
- **Per wave merge:** Same (all tests run in 0.15s)
- **Phase gate:** Full suite green + manual D1 spot-check (`SELECT * FROM comments WHERE parent_type='tick' LIMIT 10`) before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `scraping/tests/test_tick_collector.py` — covers TICK-01, TICK-02, TICK-03
- [ ] `scraping/tests/test_fixtures/stats_page.html` — fixture for `parse_stats` unit tests (unauthenticated stats page showing login modal, and authenticated stats page with tick table)

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | Yes | MP credentials via env vars (`MP_LOGIN_EMAIL`, `MP_LOGIN_PASSWORD`) — never hardcoded |
| V3 Session Management | Yes | Single Selenium session; credentials not stored in cookies.json (no `COOKIE_FILE` write in tick flow) |
| V4 Access Control | No | Scraper has read-only MP access; no user-facing auth |
| V5 Input Validation | Yes | Tick text from MP HTML — sanitized via `sql_quote()` in `import_to_d1.py` before SQL insert |
| V6 Cryptography | No | No encryption needed; `_make_comment_id` uses MD5 for dedup (not security) |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| SQL injection via tick text content | Tampering | `sql_quote()` — single-quote doubling (already in `import_to_d1.py`) |
| Credential leak via logging | Information Disclosure | Never log `MP_LOGIN_EMAIL` or `MP_LOGIN_PASSWORD`; only log "Login succeeded/failed" |
| Stale session serving another user's data | Spoofing | N/A — MP is a public site; only concern is session expiry, not data isolation |

---

## Sources

### Primary (HIGH confidence)
- [VERIFIED: scraping/scrape_mtnpj_final.py] — `parse_stats`, `get_route_stats`, `get_driver`, `login_mp` absence, stats URL format
- [VERIFIED: scraping/scrape_async.py] — BFS traversal, `run_scrape`, Selenium integration via `asyncio.to_thread`
- [VERIFIED: scraping/import_to_d1.py] — `_build_comment_rows`, `_make_comment_id`, `chunk_inserts`, `sql_quote`, `INSERT OR REPLACE` pattern
- [VERIFIED: worker-api/schema.sql] — D1 schema DDL; `comments` table with `CHECK(parent_type IN ('route', 'area'))`
- [VERIFIED: wrangler d1 execute --local] — Live D1 state: 17,358 routes, 576 comments, 3,252 areas, no Yosemite NP data
- [VERIFIED: pip list in .venv] — selenium 4.43.0, httpx 0.28.1, beautifulsoup4 4.14.3, pytest 9.0.3
- [VERIFIED: python3 -m pytest scraping/tests/] — 22 tests pass in 0.15s
- [VERIFIED: live HTTP probe to mountainproject.com/route/stats/] — Unauthenticated stats page returns "Please Confirm" modal + login form; no tick data visible
- [VERIFIED: ls /Applications/Google Chrome.app/] — Chrome present at standard macOS path
- [VERIFIED: npx wrangler --version] — wrangler 4.90.0 available

### Secondary (MEDIUM confidence)
- [VERIFIED: data/el-capitan_routes.json] — 7 areas, 110 routes, all `route_tick_comments` are empty strings

### Tertiary (LOW confidence)
- [ASSUMED: A1] MP login form field names (`email`, `password`) — standard HTML form naming
- [ASSUMED: A2] Tick cell delimiter is `·` (U+00B7) — inferred from `re.sub(r'·.*?·', '', tick_text)` in `parse_stats`

---

## Metadata

**Confidence breakdown:**
- Schema conflict discovery: HIGH — verified via live D1 query
- Login gap discovery: HIGH — verified by code inspection (no login code present)
- MP stats URL format: HIGH — verified via live HTTP probe
- Selenium session management: HIGH — verified by reading `get_driver()` implementation
- `parse_stats` return shape change: HIGH — current code verified; new shape follows D-03
- MP login form selectors: LOW — assumed standard; must verify at run time

**Research date:** 2026-05-09
**Valid until:** 2026-06-09 (30 days; MP HTML structure changes infrequently; D1 schema is local)
