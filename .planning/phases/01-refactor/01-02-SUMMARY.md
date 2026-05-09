---
phase: 01-refactor
plan: "02"
subsystem: data-pipeline
tags: [d1-schema, import-script, sqlite, fts5, tdd, cloudflare]
dependency_graph:
  requires: []
  provides: [worker-api/schema.sql, scraping/import_to_d1.py]
  affects: [01-03, 01-04, 01-05]
tech_stack:
  added: []
  patterns: [sqlite-fts5, tdd-red-green, batched-sql-inserts, materialized-path]
key_files:
  created:
    - worker-api/schema.sql
    - scraping/import_to_d1.py
    - scraping/tests/test_import.py
    - scraping/tests/test_fixtures/sample_area.json
    - scraping/__init__.py
    - scraping/tests/__init__.py
  modified:
    - .gitignore
decisions:
  - D1 schema locked with 3 tables (areas, routes, comments) + FTS5 virtual table + 16 indexes
  - Route types as 9 indexed boolean columns (is_sport, is_trad, is_aid, is_ice, is_alpine, is_mixed, is_tr, is_boulder, is_snow)
  - Area hierarchy via adjacency list (parent_id) + materialized path (path) built from URL slugs
  - FTS5 rebuild appended as final statement in every generated SQL file (manual trigger required)
  - Generated SQL files excluded from git via worker-api/import_*.sql pattern
metrics:
  duration: "5m"
  completed: "2026-05-08"
  tasks: 4
  files: 7
---

# Phase 01 Plan 02: D1 Schema + Import Pipeline Summary

**One-liner:** D1 SQLite schema with 3 tables + FTS5 locked; Python import script transforms tagged JSON into batched SQL INSERTs under the 100KB D1 limit, validated against 10,951 Washington state routes.

## What Was Built

### Task 1: worker-api/schema.sql
Full D1 schema definition:
- `areas` table: adjacency list (`parent_id`) + materialized path (`path`), 3 indexes
- `routes` table: 9 boolean type columns (D-14), 13 indexes (all is_* columns + grade/stars/votes/area)
- `comments` table: polymorphic via `parent_type` check constraint, 1 index
- `routes_fts` FTS5 virtual table: external content table on routes (requires manual rebuild)
- Validated with `sqlite3 :memory:` — 106 lines, all CREATE IF NOT EXISTS

### Task 2: TDD RED — test scaffold
13 unit tests in `scraping/tests/test_import.py`:
1. `test_parse_route_type_to_booleans_basic` — "Sport, 80 ft" → is_sport=1 only
2. `test_parse_route_type_to_booleans_compound` — "Trad, Aid, 3 pitches, 350 ft" → is_trad=1 + is_aid=1
3. `test_parse_route_type_to_booleans_top_rope` — "TR, 100 ft" and "Top Rope, 100 ft" → is_tr=1
4. `test_parse_route_type_to_booleans_grade_modifier_dropped` — "Grade III" not parsed as type
5. `test_parse_route_type_to_booleans_empty` — empty/None → all zeros, no crash
6. `test_build_materialized_path_basic` — URL slug extraction, route-guide excluded
7. `test_build_materialized_path_handles_trailing_slash` — trailing slash invariance
8. `test_grade_to_numeric_basic` — 5.9→9.0, 5.10a→10.1, V3→None, Unknown→None
9. `test_extract_mp_id_from_url` — numeric ID from /area/ and /route/ URLs
10. `test_batch_inserts_under_size_limit` — 1000 rows chunked, each ≤100KB, no rows dropped
11. `test_sql_escape_single_quotes` — "O'Brien's Route" → "'O''Brien''s Route'"
12. `test_import_idempotent` — same input → identical output
13. `test_fts_rebuild_appended` — SQL ends with FTS rebuild statement

Sample fixture: 1 area (6-level Meatwad hierarchy), 3 routes (Boulder V3-, Trad+Aid 31-pitch, Sport with apostrophe)

### Task 3: TDD GREEN — import_to_d1.py
465-line implementation, all 13 tests pass:
- `parse_route_type_to_booleans`: space-padded keyword matching; `" tr,"` + `" tr "` handles comma-separated "TR, 100 ft" correctly
- `build_materialized_path`: URL slug extraction, skips route-guide stub and numeric-only segments
- `grade_to_numeric`: regex `^5\.(\d+)([a-d]?)` with letter offset map
- `extract_mp_id_from_url`: `/(?:area|route)/(\d+)/` pattern, MD5 fallback
- `sql_quote`: single-quote doubling (SQL standard, T-02-01 SQLi mitigation)
- `chunk_inserts`: greedy packing with `INSERT OR REPLACE INTO ... VALUES ...;`
- `generate_sql`: deterministic sort by MP ID, separates areas/routes/comments, FTS rebuild at end

End-to-end smoke on fixture: 1 area, 3 routes, 1 comment, FTS MATCH 'nose' → 1 result.

### Task 4: Washington state validation + .gitignore

**Washington state import results:**
| Metric | Value |
|--------|-------|
| Areas | 2,033 |
| Routes | 10,951 |
| Comments | 384 |
| FTS 'crack' results | 2,521 |
| Total SQL bytes | 12,406,009 (12 MB) |
| Max statement bytes | 94,905 (under 100KB D1 limit) |

**Yosemite import path** (after Plan 01-01 T03 produces output):
```bash
python -m scraping.import_to_d1 "/tmp/yosemite-smoke/yosemite-national-park_routes.json" \
  -o "worker-api/import_yosemite-national-park_routes.sql"
```
Same command, no code changes required.

**Other states (AZ, CO, NV, OR, UT) — deferred, command identical:**
```bash
python -m scraping.import_to_d1 "data/{state}_routes_tagged.json" \
  -o "worker-api/import_{state}_routes_tagged.sql"
```

## Data Quality Observations

- Most routes have `route_type` as simple strings like "Boulder", "Trad", "Sport" without length/pitch suffix — parsing handles both formats
- Some routes have `route_type` = "" (empty) → all boolean columns default to 0
- Grade distribution: boulder grades (V0-V16) return `grade_numeric = NULL` as intended (not YDS)
- Route IDs in existing data are UUID v4 strings; `extract_mp_id_from_url` correctly derives stable numeric MP IDs from URLs instead
- `area_page_views` stored as string in source JSON (e.g., "3664") — `sql_quote` handles via string wrapping

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] TR keyword boundary matching**
- **Found during:** Task 3 (TDD GREEN — test 3 failed)
- **Issue:** `" tr "` keyword (space after) did not match `"TR, 100 ft"` because after lowercasing + padding the string is `" tr, 100 ft "` — the `tr` is followed by `,` not space
- **Fix:** Added `" tr,"` as an additional keyword alongside `" tr "` in `ROUTE_TYPE_KEYWORDS`
- **Files modified:** `scraping/import_to_d1.py`
- **Commit:** 6e9abf7

## Known Stubs

None. All columns are wired from JSON input data. `route_tags` and `route_suggested_ratings` are serialized as JSON strings from the source data (may be empty dict `{}` for untagged routes — this is correct and expected; tagging happens in Plan 05).

## Threat Flags

None. The trust boundary analysis in the plan's `<threat_model>` was fully addressed:
- T-02-01 (SQLi via apostrophe): mitigated by `sql_quote()` double-quote escaping, tested in test 11
- T-02-02 (SQLi via SQL fragments): mitigated by same `sql_quote()` wrapping
- T-02-03 (DoS via statement-too-long): mitigated by `chunk_inserts` with 95KB safety limit, verified against Washington state (max observed: 94,905 bytes)
- T-02-04 (Path collision via slash in name): mitigated by URL slug extraction, not area names

## Self-Check: PASSED

All claimed files exist and all commits verified:
- worker-api/schema.sql: FOUND
- scraping/import_to_d1.py: FOUND
- scraping/tests/test_import.py: FOUND
- scraping/tests/test_fixtures/sample_area.json: FOUND
- Commit 3fe4ceb (schema.sql): FOUND
- Commit dca0d7f (TDD RED tests): FOUND
- Commit 6e9abf7 (TDD GREEN import_to_d1.py): FOUND
- Commit df9906d (.gitignore update): FOUND
