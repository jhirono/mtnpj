---
phase: 02-tick-comments
plan: "03"
subsystem: scraping
tags: [selenium, python, tick-comments, d1, orchestrator, collect_ticks]

dependency_graph:
  requires:
    - phase: 02-01
      provides: comments table with tick parent_type support
    - phase: 02-02
      provides: login_mp() + parse_stats() returning list[dict]
  provides:
    - collect_ticks() orchestrator function in scraping/collect_ticks.py
    - query_d1_routes() — wrangler-based D1 route query
    - write_ticks_to_d1() — INSERT OR IGNORE batch writer
    - remap_tick_entry() — key remapper for parse_stats → _build_comment_rows
  affects:
    - 02-04 (El Cap validation run uses collect_ticks as the entry point)

tech-stack:
  added: []
  patterns:
    - Standalone CLI orchestrator: argparse --area-path --dry-run --limit flags
    - Sequential Selenium loop: no asyncio.gather (avoids Selenium thread-safety risk)
    - INSERT OR IGNORE with manual chunking (INSERT_BATCH_BYTES constant from import_to_d1)
    - Single Selenium session with re-auth on session loss (D-06)
    - Key remapping: parse_stats keys (author/date/text) → _build_comment_rows keys

key-files:
  created:
    - scraping/collect_ticks.py
  modified: []

key-decisions:
  - "INSERT OR IGNORE (not INSERT OR REPLACE) for tick dedup per D-05; chunk_inserts() uses REPLACE by default so prefix is overridden manually"
  - "cleanup_driver() called only in finally block — driver stays alive across all route iterations (D-06)"
  - "login_mp() called once before the route loop; session-loss check after each get_route_stats() call via driver.current_url"
  - "INSERT_BATCH_BYTES imported directly from import_to_d1 (public constant at line 40) for consistent D1 100KB chunking"
  - "remap_tick_entry() isolated as a named function — makes key mapping testable and explicit"

metrics:
  duration: "~2 minutes"
  completed: 2026-05-10
---

# Phase 02 Plan 03: collect_ticks.py Orchestrator Summary

Standalone tick collection orchestrator built: queries local D1 for routes by area path, authenticates single Selenium session via login_mp(), fetches tick entries per route, writes INSERT OR IGNORE rows to D1 comments table with session-loss re-auth.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Build collect_ticks.py — standalone tick collection orchestrator | a750234 | scraping/collect_ticks.py |

## Results

### Task 1: collect_ticks.py Orchestrator

- Created `scraping/collect_ticks.py` (301 lines) — runnable as `python3 -m scraping.collect_ticks`
- `collect_ticks()` function: queries D1 via wrangler, single Selenium session, sequential per-route tick fetch, INSERT OR IGNORE to D1
- `query_d1_routes()`: executes SQL via wrangler d1 execute --local --json; parses wrangler JSON output format
- `write_ticks_to_d1()`: manually chunks rows against INSERT_BATCH_BYTES limit with INSERT OR IGNORE prefix (overrides chunk_inserts default INSERT OR REPLACE)
- `remap_tick_entry()`: maps `author`/`date`/`text` → `comment_author`/`comment_time`/`comment_text` for _build_comment_rows compatibility
- Session-loss detection: checks `driver.current_url` for 'login' after each stats fetch; re-authenticates with login_mp() on detection
- `cleanup_driver()` called only in `finally` block (D-06 compliance)
- `--dry-run` flag: prints SQL to log without executing wrangler inserts
- `--limit N` flag: caps route count for testing
- All 28 tests pass (no regressions)

## Verification

1. `grep -c "def collect_ticks" scraping/collect_ticks.py` → 1 ✓
2. `grep -c "INSERT OR IGNORE" scraping/collect_ticks.py` → 6 (docstring + comments + prefix) ✓
3. `grep -c "finally" scraping/collect_ticks.py` → 3 ✓
4. `python3 -m scraping.collect_ticks --help` exits 0 and shows `--area-path` ✓
5. `python3 -m pytest scraping/tests/ -v --tb=short` → 28 passed ✓
6. `python3 -c "from scraping.collect_ticks import collect_ticks, ..."` → imports OK ✓

## Deviations from Plan

None — plan executed exactly as written. The INSERT OR REPLACE occurrences in grep output are comment lines explaining why REPLACE is NOT used; the actual SQL prefix at line 112 uses INSERT OR IGNORE exclusively.

## Known Stubs

None — all functions are fully implemented. The `--dry-run` flag is an intentional operational mode, not a stub.

## Threat Surface Scan

| Flag | File | Description |
|------|------|-------------|
| T-02-06 mitigated | scraping/collect_ticks.py | login_mp() never logs email/password; only success/failure status |
| T-02-07 mitigated | scraping/collect_ticks.py | Tick text passes through _build_comment_rows which uses sql_quote() |
| T-02-08 mitigated | scraping/collect_ticks.py | TICK_DELAY_SECONDS=1.5 between requests; sequential loop only |
| T-02-09 accepted | scraping/collect_ticks.py | wrangler --local only; no remote D1 credentials present |

No new threat surface beyond the plan's threat model.

## Self-Check: PASSED

- scraping/collect_ticks.py — FOUND (301 lines)
- Commit a750234 — FOUND
- `def collect_ticks` count: 1 — CORRECT
- `INSERT OR IGNORE` in SQL prefix (line 112): CONFIRMED
- `cleanup_driver()` in finally block: CONFIRMED
- `login_mp` call count ≥ 2: CONFIRMED (initial + re-auth)
- 28 tests pass: CONFIRMED

---
*Phase: 02-tick-comments*
*Completed: 2026-05-10*
