---
phase: 05-grade-system-picker
plan: "02"
subsystem: worker-api
tags: [backend, api, zod, sql, filtering, tdd-green]
dependency_graph:
  requires:
    - GradeSystem type (filters.ts) — from Plan 01
    - grade_system + grade_list in ApiFilters (api/types.ts) — from Plan 01
    - grade_system integration tests RED (routes.test.ts) — from Plan 01
  provides:
    - Zod validation for grade_system (enum) and grade_list (max 200 + regex) in routes.ts
    - LIKE-based non-YDS grade filtering in buildRoutesQuery (queries.ts)
    - All 4 RED grade_system tests now GREEN
  affects:
    - climbing-search/src/api/routeApi.ts (serializes grade_system, grade_list — Plan 03)
    - climbing-search/src/App.tsx (calls API with grade_system — Plan 03)
tech_stack:
  added: []
  patterns:
    - Zod z.enum for grade_system validation (rejects unknowns with 400)
    - z.string().max(200).regex for grade_list length + character safety
    - LIKE prefix matching with parameterized ? placeholders (never interpolated)
    - Aid/mixed dual-column OR: route_grade OR route_protection_grading
    - Boulder/ice single-column: route_grade only
key_files:
  created: []
  modified:
    - worker-api/src/routes/routes.ts
    - worker-api/src/db/queries.ts
decisions:
  - D-17: grade_system=yds uses existing route_grade_numeric path unchanged; non-YDS uses grade_list LIKE
  - D-18: grade_list comma-separated strings expand to LIKE ? OR LIKE ? clauses with parameterized bindings
  - D-19: Aid/mixed filter both route_grade AND route_protection_grading; boulder/ice filter route_grade only
  - D-20: grade_min/grade_max and grade_list are mutually exclusive per grade_system value
  - T-05-01: All grade values bound as params — never interpolated into SQL strings
  - T-05-02: z.enum(['yds','boulder','aid','ice','mixed']) rejects any non-listed value with 400
  - T-05-03: z.string().max(200) caps grade_list at 200 chars
metrics:
  duration: "~8 minutes"
  completed: "2026-05-16"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 2
---

# Phase 05 Plan 02: Backend Non-YDS Grade Filtering Summary

Parameterized LIKE prefix filtering for boulder, ice, aid, and mixed grade systems in the Hono worker API — turns all 4 RED grade_system integration tests GREEN with zero existing test regressions.

## What Was Built

### Task 1: Extend Zod schema in routes.ts (`bab87f8`)

Added two fields to `routeQuerySchema`:

- `grade_system: z.enum(['yds', 'boulder', 'aid', 'ice', 'mixed']).optional()` — enum validation rejects unknown values with HTTP 400 (T-05-02)
- `grade_list: z.string().max(200).regex(/^[A-Z0-9,+\-]+$/i).optional()` — caps length at 200 chars, restricts to grade-safe characters (T-05-03)

The route handler body was unchanged — the `buildRoutesQuery({ ...f, area_id: resolvedAreaId, area_path: resolvedAreaPath })` spread already passes all validated fields through to the query builder.

### Task 2: Add LIKE-based grade filtering in queries.ts (`6a7fa79`)

Extended `RouteFilters` interface with `grade_system` and `grade_list` optional fields.

Added LIKE clause block in `buildRoutesQuery` immediately after the `grade_max` condition:

- **boulder / ice systems:** `WHERE (r.route_grade LIKE ? OR r.route_grade LIKE ? ...)` — single column, one `?` param per grade
- **aid / mixed systems:** `WHERE ((r.route_grade LIKE ? OR r.route_protection_grading LIKE ?) OR ...)` — dual column, two `?` params per grade (D-19)
- **yds system:** block is skipped entirely — existing `grade_min`/`grade_max` numeric path is untouched (D-20)

Security: all grade values go through `params.push(`${g}%`)` — the SQL template only ever contains `?` placeholders (T-05-01). No user-supplied string is ever interpolated into the SQL template.

## Test Results

Before Plan 02: 4 failing, 23 passing (27 total)
After Plan 02: **27 passing, 0 failing**

Tests that went GREEN:
- `grade_system=boulder + grade_list filters by V-grade LIKE` — returns only routes with V3% grades
- `grade_system=ice + grade_list filters by WI-grade LIKE` — returns only routes with WI4% grades
- `rejects invalid grade_system value with 400` — "french" returns 400
- `rejects grade_list exceeding max length with 400` — 300-char grade_list returns 400

Tests that were already passing and remain passing:
- `grade_system=aid + grade_list filters route_grade OR route_protection_grading` — A3 matches route_grade='A3' OR route_protection_grading='C2'
- `grade_system=mixed + grade_list filters by M-grade LIKE` — M6 matches route_grade='M6'
- `grade_system=yds uses grade_min/grade_max numeric path` — unchanged behavior
- All 20 original worker-api tests still pass

## Commits

| Commit | Type | Description |
|--------|------|-------------|
| `bab87f8` | feat | Extend Zod schema with grade_system enum and grade_list validation |
| `6a7fa79` | feat | Add LIKE-based non-YDS grade filtering in buildRoutesQuery — GREEN |

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. All filtering logic is fully implemented and tested.

## Threat Flags

None. Security-relevant surfaces (grade_system enum validation, grade_list length cap, parameterized SQL) were all explicitly covered by the plan's threat model (T-05-01, T-05-02, T-05-03) and are now implemented.

## TDD Gate Compliance

RED gate: `test(05-01)` commit `dcc9c58` exists (from Plan 01) — grade_system tests were failing.
GREEN gate: `feat(05-02)` commits `bab87f8` and `6a7fa79` exist — all 27 tests pass.

## Self-Check

Files verified:
- `worker-api/src/routes/routes.ts` — grade_system z.enum, grade_list z.string().max(200) present
- `worker-api/src/db/queries.ts` — RouteFilters extended, LIKE block present, no SQL interpolation

Commits verified:
- `bab87f8` — exists (git log confirms)
- `6a7fa79` — exists (git log confirms)

Test suite: 27/27 passing (`npm test` exit 0)

## Self-Check: PASSED
