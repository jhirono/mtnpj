---
phase: 02-tick-comments
plan: "01"
subsystem: database-schema, test-scaffold
tags: [migration, sqlite, d1, tdd, tick-comments]
dependency_graph:
  requires: []
  provides: [comments-tick-constraint, test-scaffold-tick]
  affects: [scraping/import_to_d1.py, worker-api/schema.sql]
tech_stack:
  added: []
  patterns: [sqlite-copy-recreate-migration, pytest-xfail-red-stubs]
key_files:
  created:
    - scraping/migrate_comments_schema.sql
    - scraping/tests/test_tick_collector.py
    - scraping/tests/test_fixtures/stats_page_auth.html
    - scraping/tests/test_fixtures/stats_page_noauth.html
  modified:
    - worker-api/schema.sql
decisions:
  - "Used SQLite copy-recreate migration pattern (CREATE TABLE comments_new, INSERT, DROP, RENAME) because ALTER TABLE cannot modify CHECK constraints in SQLite"
  - "3 tests pass immediately (dedup, build_comment_rows, noauth empty); 3 tests xfail as RED stubs for Plan 02 (parse_stats list[dict] return, login_mp)"
  - "D-04 ('no schema changes needed') superseded — live D1 CHECK constraint explicitly excluded 'tick'; migration was required"
metrics:
  duration: "~15 minutes"
  completed: 2026-05-10
---

# Phase 02 Plan 01: Comments Schema Migration + Test Scaffold Summary

D1 comments table migrated to allow `parent_type='tick'` via SQLite copy-recreate pattern; canonical schema DDL updated; test scaffold created with green/xfail split ready for Plan 02.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Write migration SQL and apply to local D1 | 68a1d82 | scraping/migrate_comments_schema.sql, worker-api/schema.sql |
| 2 | Create test scaffold (test_tick_collector.py + HTML fixtures) | bc1e41e | scraping/tests/test_tick_collector.py, test_fixtures/stats_page_auth.html, test_fixtures/stats_page_noauth.html |

## Results

### Task 1: Comments Schema Migration

- Created `scraping/migrate_comments_schema.sql` using SQLite copy-recreate pattern (7 SQL commands)
- Applied migration to local D1: 576 rows preserved, new `CHECK(parent_type IN ('route', 'area', 'tick'))` constraint verified
- Test insert with `parent_type='tick'` succeeded (confirmed by SELECT returning the test row)
- Updated `worker-api/schema.sql` canonical DDL to match migrated schema
- Old `CHECK(parent_type IN ('route', 'area'))` constraint fully replaced (0 occurrences remaining)

### Task 2: Test Scaffold (TDD RED Phase)

- Created 6 tests in `scraping/tests/test_tick_collector.py` (115 lines)
- 3 tests GREEN immediately:
  - `test_tick_dedup` — uses in-memory sqlite3, verifies INSERT OR IGNORE dedup
  - `test_build_comment_rows_tick_type` — tests existing `_build_comment_rows` with `parent_type='tick'`
  - `test_parse_stats_empty_on_noauth` — current parse_stats returns `""` for missing ticks table
- 3 tests XFAIL (RED stubs for Plan 02):
  - `test_parse_stats_returns_entries` — parse_stats not yet updated to return `list[dict]`
  - `test_parse_stats_word_filter` — same blocker
  - `test_login_mp_signature` — `login_mp` not yet implemented
- HTML fixtures created: `stats_page_auth.html` (has Ticks h3 + table, 2 long rows, 1 short), `stats_page_noauth.html` (no Ticks h3, login form)
- All 22 pre-existing tests still pass (no regressions)

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written.

**Note on D-04:** The plan itself already documented that D-04 ("no schema changes needed") was superseded by verified live schema. No additional deviation occurred.

## Known Stubs

None — test stubs are intentional xfail markers (RED phase), not implementation stubs. The 3 xfail tests will be addressed in Plan 02 when `parse_stats` and `login_mp` are implemented.

## Threat Surface Scan

| File | Assessment |
|------|------------|
| scraping/migrate_comments_schema.sql | No new trust boundary. DDL-only, local D1. T-02-01 mitigated: row count verified (576 before = 576 after). T-02-02 accepted: remote D1 untouched. |
| worker-api/schema.sql | No new surface. DDL source-of-truth update only. |

No new threat flags introduced.

## Verification

1. `grep "CHECK(parent_type IN ('route', 'area', 'tick'))" worker-api/schema.sql` — MATCH
2. `grep -c "CHECK(parent_type IN ('route', 'area'))" worker-api/schema.sql` — 0 (old constraint gone)
3. `python3 -m pytest test_tick_collector.py::test_tick_dedup test_tick_collector.py::test_build_comment_rows_tick_type test_tick_collector.py::test_parse_stats_empty_on_noauth` — 3 passed
4. `python3 -m pytest scraping/tests/` — 22 passed (no regressions)

## Self-Check: PASSED
