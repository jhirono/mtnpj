---
phase: 01-refactor
plan: "01"
subsystem: scraper
tags: [async, httpx, scraping, tdd, stable-ids, route-types]
dependency_graph:
  requires: []
  provides: [scraping/scrape_async.py, scraping/tests/test_scraper.py]
  affects: [data/*.json]
tech_stack:
  added: [httpx>=0.28.1, pytest>=8.0, pytest-asyncio>=0.24]
  patterns: [async/await + asyncio.Semaphore, TDD RED/GREEN cycle, BFS area traversal, disk-based HTML caching]
key_files:
  created:
    - scraping/scrape_async.py
    - scraping/tests/test_scraper.py
    - scraping/tests/test_fixtures/yosemite_area.html
    - scraping/tests/test_fixtures/leaf_area.html
    - scraping/requirements.txt
    - scraping/__init__.py
    - scraping/tests/__init__.py
  modified: []
decisions:
  - "Multi-strategy sub-area detection: primary div class → class-contains fallback → left-nav id → href scan — handles MP CSS class changes"
  - "Stable route_id from /route/(\\d+)/ regex; MD5-hash fallback for malformed URLs; uuid4 never called"
  - "asyncio.to_thread wraps Selenium calls (get_comments, get_route_stats) so they don't block event loop"
  - "CONCURRENCY_LIMIT=5 with 0.4s delay per request for polite MP scraping (T-01-02 mitigation)"
  - "BFS leaf-area discovery processes CONCURRENCY_LIMIT URLs per round via asyncio.gather"
metrics:
  completed_date: "2026-05-09"
  tasks_completed: 2
  tasks_total: 3
  files_created: 7
  files_modified: 0
  scrape_async_lines: 856
  test_count: 9
---

# Phase 01 Plan 01: Full Scraper Coverage Summary

One-liner: Async scraper (httpx + asyncio.Semaphore) with multi-strategy sub-area detection, stable MP route IDs from URL numeric segment, all 9 route types preserved, and 9 unit tests passing TDD RED/GREEN cycle.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| T01 | Test scaffold and fixtures (RED phase) | 4e4f964 | scraping/tests/test_scraper.py, test_fixtures/, requirements.txt, __init__.py files |
| T02 | Implement scrape_async.py (GREEN phase) | 84d39da | scraping/scrape_async.py |
| T03 | Yosemite NP smoke test | CHECKPOINT | Awaiting human verification |

## What Was Built

### scrape_async.py (856 lines)

**Core functions:**

- `extract_mp_route_id(url)` — regex `/route/(\d+)/` → numeric string; MD5 fallback; zero uuid4 calls
- `extract_mp_area_id(url)` — same pattern for area IDs
- `get_sub_area_links(soup)` — 4-strategy detection:
  1. Primary: `div.max-height.max-height-md-0.max-height-xs-400`
  2. Fallback: any div with class containing "max-height"
  3. Fallback: element with id matching "left-nav"
  4. Last resort: all `/area/` hrefs excluding breadcrumb context
- `is_lowest_level_area(soup, sub_areas)` — route table presence AND zero sub-areas
- `parse_route_type_string(s)` — comma-split parser: drops grade modifiers ("Grade III"), extracts pitches/ft/m
- `diff_routes_by_id(existing, scraped_urls)` — set operations on stable IDs → {added, removed, unchanged}
- `async fetch_html(client, sem, url)` — httpx fetch with semaphore throttle + disk cache
- `async get_route_details(client, sem, url)` — full route scrape; Selenium calls in asyncio.to_thread
- `async get_routes(client, sem, area_url)` — area-level scrape with incremental diff support
- `async scrape_lowest_level_areas(client, sem, start_url)` — BFS with concurrent batch fetching
- `async run_scrape(start_url)` — orchestrator: BFS → per-area route fetch → JSON output

**Backward compatibility:** Output JSON uses same keys as existing `data/*.json` (area_id, area_url, area_name, area_gps, area_description, area_getting_there, area_tags, area_hierarchy, area_access_issues, area_page_views, area_shared_on, area_comments, routes, route_id, route_type, etc.)

### Test Suite (9 tests)

| Test | What it verifies |
|------|-----------------|
| test_get_sub_area_links_yosemite | Live Yosemite fixture → >= 5 sub-area links |
| test_get_sub_area_links_handles_missing_class | left-nav fallback returns /area/ links |
| test_is_lowest_level_area_true | Leaf fixture (routes, no sub-areas) → True |
| test_is_lowest_level_area_false_when_subareas_exist | Sub-areas present → False |
| test_extract_mp_route_id_stable | Numeric ID extracted, same twice, no UUID4 |
| test_extract_mp_route_id_fallback | Malformed URL → deterministic MD5 hash |
| test_parse_route_type_string_all_types | Trad/Aid/Sport/Boulder all parsed correctly |
| test_parse_route_type_with_grade_modifier | Grade III dropped; Alpine/Trad kept |
| test_diff_routes_by_stable_id | added/removed/unchanged sets correct |

## TDD Gate Compliance

- RED gate commit: `4e4f964` — `test(01-01): add failing test scaffold for async scraper (RED phase)`
- GREEN gate commit: `84d39da` — `feat(01-01): implement scrape_async.py async scraper (GREEN phase)`
- Both gates present in correct order.

## Deviations from Plan

### Auto-added: scraping/__init__.py

**Rule 2 — Missing critical functionality**
- **Found during:** Task 1
- **Issue:** `from scraping.scrape_async import` requires `scraping/` to be a Python package (needs `__init__.py`). Without it, pytest would not be able to import the module.
- **Fix:** Created `scraping/__init__.py` (empty) to make `scraping/` a proper Python package.
- **Files modified:** scraping/__init__.py
- **Commit:** 4e4f964

### Note on T03 checkpoint

Task 3 is a `checkpoint:human-verify` — the Yosemite NP smoke test requires a live 5–20 minute scrape run. This cannot be automated by the executor agent. The checkpoint is documented below.

## Known Stubs

None. The implementation is complete. `route_tags` and `route_composite_tags` are empty lists by design (tagging is handled in a separate downstream plan per the project architecture).

## Threat Surface Scan

No new network endpoints, auth paths, or schema changes introduced beyond what the plan's threat model covers. `T-01-02` (DoS against MP) is mitigated by `asyncio.Semaphore(5)` + 0.4s delay. `T-01-04` (adversarial route type parsing) is mitigated by regex-only parsing in `parse_route_type_string` (no `eval`).

## Yosemite Smoke Test (T03 — Pending Human Verification)

The smoke test requires running:
```bash
cd /Users/jhirono/Dev/mtnpj
source venv/bin/activate
mkdir -p /tmp/yosemite-smoke
PYTHONPATH=/Users/jhirono/Dev/mtnpj/.claude/worktrees/agent-a8891279bf0c9527b \
OUTPUT_DIR=/tmp/yosemite-smoke python -m scraping.scrape_async \
  "https://www.mountainproject.com/area/105833381/yosemite-national-park" \
  --no-selenium --concurrency 3 -v 2>&1 | tee /tmp/yosemite-smoke.log
```

Acceptance thresholds: Areas >= 50, Total routes >= 1000, Aid routes >= 50, UUID4 IDs == 0.

## Self-Check

- [x] scraping/scrape_async.py exists (856 lines)
- [x] scraping/tests/test_scraper.py exists (9 tests)
- [x] scraping/tests/test_fixtures/yosemite_area.html exists (non-empty)
- [x] scraping/tests/test_fixtures/leaf_area.html exists
- [x] scraping/__init__.py exists
- [x] scraping/tests/__init__.py exists
- [x] scraping/requirements.txt exists
- [x] Commit 4e4f964 exists (RED phase)
- [x] Commit 84d39da exists (GREEN phase)
- [x] All 9 tests pass: `pytest scraping/tests/test_scraper.py -x -q` → 9 passed

## Self-Check: PASSED
