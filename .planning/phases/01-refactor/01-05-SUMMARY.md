---
phase: 01-refactor
plan: "05"
subsystem: tagging-pipeline
tags: [python, d1, sql, tagging, batch-update]
dependency_graph:
  requires: ["01-02"]
  provides: ["tagging/d1_tag_sync.py", "batched UPDATE SQL for route_tags and area_tags"]
  affects: ["worker-api/tag_update_*.sql", "D1 routes.route_tags", "D1 areas.area_tags"]
tech_stack:
  added: []
  patterns: ["CASE-WHEN bulk UPDATE", "URL-derived stable ID resolution", "TDD RED/GREEN cycle"]
key_files:
  created:
    - tagging/d1_tag_sync.py
    - tagging/__init__.py
    - tagging/tests/__init__.py
    - tagging/tests/test_d1_tag_sync.py
    - tagging/tests/test_fixtures/tagged_sample.json
  modified:
    - tagging/README.md
decisions:
  - "CASE-WHEN UPDATE chosen over per-row UPDATE for batch efficiency — one statement updates hundreds of routes"
  - "Sorted output by route_d1_id for deterministic byte-identical re-runs (idempotency)"
  - "Deduplication uses last-wins strategy for routes appearing in multiple areas"
metrics:
  duration: "4 minutes"
  completed: "2026-05-09T02:17:31Z"
  tasks_completed: 3
  files_created: 5
  files_modified: 1
---

# Phase 01 Plan 05: D1 Tag Sync Summary

**One-liner:** Thin transformer reads tagged JSON (LLM + rule-based tags), generates CASE-WHEN batched UPDATE SQL for D1 route_tags and area_tags columns under the 100KB D1 statement limit.

## What Was Built

`tagging/d1_tag_sync.py` — a new sibling module to `tagging/route_area_tagging.py` that:
1. Resolves D1 route/area IDs (legacy uuid4 → URL-derived MP numeric ID; modern numeric IDs pass through)
2. Reads the full `route_tags` and `area_tags` payload from tagged JSON (both LLM-generated and rule-based tags)
3. Skips routes/areas with empty tags (no clobbering)
4. Emits batched `UPDATE routes SET route_tags = CASE route_id WHEN ... END WHERE route_id IN (...)` statements
5. Enforces 95KB max per statement (D1 100KB limit minus safety margin)
6. Produces byte-identical SQL on re-runs (deterministic sort + dedup)

## Tag Sync Statistics (All 6 States)

| State | Route Updates | Area Updates | SQL File Size |
|-------|--------------|-------------|---------------|
| Arizona | 12,521 | 1,935 | 3.2 MB |
| Colorado | 35,409 | 5,987 | 7.4 MB |
| Nevada | 6,407 | 1,176 | 1.7 MB |
| Oregon | 5,220 | 741 | 1.4 MB |
| Utah | 18,959 | 2,975 | 5.0 MB |
| Washington | 10,951 | 1,884 | 2.8 MB |
| **Total** | **89,467** | **14,698** | **21.5 MB** |

**Max single statement size across all states:** 93,627 bytes (Utah) — well under 95KB UPDATE_BATCH_BYTES.

## Test Coverage

11 tests in `tagging/tests/test_d1_tag_sync.py`, all passing:

| Test | Behavior Verified |
|------|-------------------|
| test_resolve_route_d1_id_from_url | Legacy UUID → URL-derived MP numeric ID |
| test_resolve_route_d1_id_from_modern_id | Modern numeric IDs pass through unchanged |
| test_resolve_route_d1_id_falls_back_for_garbage_url | Garbage URL → 12-char MD5 fallback |
| test_build_route_tag_updates_basic | Tags extracted as (id, json_string) tuples |
| test_build_area_tag_updates_basic | Area tags extracted correctly |
| test_skip_routes_without_tags | Empty route_tags dict → route not in output |
| test_chunk_updates_under_size_limit | 1000 updates packed within 100KB/statement |
| test_chunk_updates_uses_case_when | CASE WHEN pattern in generated SQL |
| test_generate_sync_sql_full_pipeline | SQLite in-memory integration: routes + areas updated |
| test_idempotent_repeat_run | Two runs produce byte-identical SQL |
| test_sql_escapes_special_chars_in_tag_values | O'Brien → O''Brien in SQL literal |

TDD gate compliance:
- RED commit: `c538f32` (test scaffold, confirmed ImportError)
- GREEN commit: `85bd11f` (implementation, all 11 tests pass)

## Commits

| Hash | Description |
|------|-------------|
| c538f32 | test(01-05): add failing tests for d1_tag_sync (RED phase) |
| 85bd11f | feat(01-05): implement tagging/d1_tag_sync.py — batched UPDATE SQL generator |
| 83d8c97 | docs(01-05): document 4-stage pipeline in tagging/README.md |

## Deviations from Plan

None — plan executed exactly as written. The user's context note (that `d1_tag_sync.py` must handle both LLM-based and logic-based tags) was already satisfied by the plan's design: `build_route_tag_updates` reads the full `route_tags` dict regardless of tag source, and the docstrings explicitly document this behavior.

## Known Stubs

None. The module fully wires the tagged JSON output to D1-ready SQL.

## Threat Surface Scan

No new network endpoints, auth paths, or file access patterns introduced. The module reads local JSON files and writes local SQL files. All tag values pass through `sql_quote()` (T-05-01, T-05-02 mitigated). Statement size is enforced by `chunk_updates()` (T-05-03 mitigated). No new threat surface beyond what was modeled in the plan's threat register.

## Self-Check: PASSED

Files verified:
- tagging/d1_tag_sync.py — FOUND (351 lines)
- tagging/tests/test_d1_tag_sync.py — FOUND (11 tests)
- tagging/tests/test_fixtures/tagged_sample.json — FOUND (valid JSON, O'Brien route present)
- tagging/__init__.py — FOUND
- tagging/tests/__init__.py — FOUND
- tagging/README.md — FOUND (311 lines, Stage 4 section present)

Commits verified:
- c538f32 — FOUND (RED phase)
- 85bd11f — FOUND (GREEN phase)
- 83d8c97 — FOUND (docs)

All 11 tests pass. Nevada smoke test: 6407 tagged routes. Max statement size: 93,627 bytes (< 95,000 limit).

tagging/route_area_tagging.py — NOT MODIFIED (last commit pre-dates this plan: 29a82e7).
