---
phase: 05-grade-system-picker
plan: "01"
subsystem: frontend-types, worker-tests
tags: [types, constants, test-fixtures, tdd-red]
dependency_graph:
  requires: []
  provides:
    - GradeSystem type (filters.ts)
    - GRADE_LISTS constant (filters.ts)
    - gradeSystem field in RouteFilters (filters.ts)
    - grade_system and grade_list in ApiFilters (api/types.ts)
    - aid/mixed test fixtures (setup.ts)
    - grade_system integration tests RED (routes.test.ts)
  affects:
    - climbing-search/src/components/FilterPanel.tsx (imports GradeSystem, GRADE_LISTS — Plan 03)
    - climbing-search/src/App.tsx (uses gradeSystem in RouteFilters — Plan 03)
    - climbing-search/src/api/routeApi.ts (serializes grade_system, grade_list — Plan 03)
    - worker-api/src/db/queries.ts (LIKE filtering — Plan 02)
    - worker-api/src/routes/routes.ts (Zod validation — Plan 02)
tech_stack:
  added: []
  patterns:
    - GradeSystem union type as single source of truth for picker, filter, sort
    - GRADE_LISTS Record<GradeSystem, string[]> for grade list constants
    - TDD RED: write integration tests before backend implementation
key_files:
  created: []
  modified:
    - climbing-search/src/types/filters.ts
    - climbing-search/src/api/types.ts
    - worker-api/test/setup.ts
    - worker-api/test/routes.test.ts
decisions:
  - D-08: GRADE_LISTS constant defined with boulder(19), aid(7), ice(7), mixed(12), yds=SIMPLE_GRADES
  - D-09: SortOption trimmed to exactly 4 members — specialty variants removed
  - D-13/D-14: GradeSystem type and gradeSystem field added to RouteFilters
  - D-17/D-18/D-19: grade_system and grade_list added to ApiFilters for backend routing
metrics:
  duration: "~5 minutes"
  completed: "2026-05-16"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 4
---

# Phase 05 Plan 01: Type Contracts and Test Scaffold Summary

GradeSystem type, GRADE_LISTS constant, updated RouteFilters/ApiFilters, and RED integration tests for all 4 non-YDS grade_system filtering modes.

## What Was Built

### Task 1: Type contracts in filters.ts and api/types.ts

Added the foundational type contracts that all Phase 05 plans depend on:

- `GradeSystem = 'yds' | 'boulder' | 'aid' | 'ice' | 'mixed'` exported from `filters.ts`
- `GRADE_LISTS: Record<GradeSystem, string[]>` — 5 grade lists (boulder=19, ice=7, aid=7, mixed=12, yds=SIMPLE_GRADES)
- `RouteFilters.gradeSystem: GradeSystem` — required field (default `'yds'` set in Plan 03 App.tsx init)
- `SortOption` reduced to `'grade' | 'stars' | 'left_to_right' | 'votes'` — removed `'aid_grade' | 'ice_grade' | 'mixed_grade' | 'boulder_grade'`
- `ApiFilters.grade_system?: 'yds' | 'boulder' | 'aid' | 'ice' | 'mixed'` — new optional field
- `ApiFilters.grade_list?: string` — new optional field for comma-separated grade values

TypeScript compile exits 0 with no errors in this plan's files.

### Task 2: Test fixtures and RED integration tests

Extended the worker-api test suite:

- Added route 1006 (`A3`, `route_protection_grading='C2'`, `is_aid=1`) — tests aid LIKE on both columns (D-19)
- Added route 1007 (`M6`, `is_mixed=1`) — tests mixed grade LIKE filtering
- Total fixtures: 7 routes (was 5)
- Updated `toBe(5)` → `toBe(7)` in paginated list test and SQL injection probe test
- Added 7 new integration tests in `grade_system filtering` describe block

**RED tests (expected — backend not implemented until Plan 02):**
- `grade_system=boulder + grade_list=V3` — FAIL (no LIKE filtering in backend)
- `grade_system=ice + grade_list=WI4` — FAIL (no LIKE filtering in backend)
- `rejects invalid grade_system value with 400` — FAIL (Zod schema not extended yet)
- `rejects grade_list exceeding max length with 400` — FAIL (Zod validation not added yet)

**Passing grade_system tests (weak assertions, work with unfiltered result set):**
- `grade_system=aid + grade_list=A3` — PASS (checks `some` on full result set)
- `grade_system=mixed + grade_list=M6` — PASS (checks `some` on full result set)
- `grade_system=yds` with numeric range — PASS (existing YDS path works)

Existing 23 tests: all PASS.

## Commits

| Commit | Type | Description |
|--------|------|-------------|
| `4f9be45` | feat | GradeSystem type, GRADE_LISTS, RouteFilters + ApiFilters updates |
| `dcc9c58` | test | Aid/mixed fixtures, 7 integration tests (RED), paginated count updated to 7 |

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written.

### Notes

The SQL injection test also asserts `probeJson.data.length === 5` (verifying table not dropped). This was updated to 7 along with the paginated list test, as both reflect total fixture count. This was an expected side effect of adding 2 fixtures not explicitly called out in the plan, but required for correctness (Rule 1 — bug fix).

## Threat Flags

None. Files modified are pure type definitions and test infrastructure — no network endpoints, auth paths, or schema changes introduced.

## TDD Gate Compliance

RED gate: `test(05-01)` commit `dcc9c58` exists with failing grade_system tests.
GREEN gate: Deferred to Plan 02 (backend LIKE filtering implementation).

## Self-Check

Files verified:
- `climbing-search/src/types/filters.ts` — GradeSystem, GRADE_LISTS, updated RouteFilters, SortOption
- `climbing-search/src/api/types.ts` — grade_system, grade_list in ApiFilters
- `worker-api/test/setup.ts` — 7 route fixtures including A3 and M6
- `worker-api/test/routes.test.ts` — 7 grade_system tests, paginated count updated

## Self-Check: PASSED
