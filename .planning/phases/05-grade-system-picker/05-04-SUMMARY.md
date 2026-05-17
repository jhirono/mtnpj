---
phase: 05-grade-system-picker
plan: "04"
subsystem: frontend-orchestrator
tags: [app-tsx, grade-system, sort, filters, polymorphic]
dependency_graph:
  requires:
    - 05-01 (GradeSystem type, GRADE_LISTS constant, RouteFilters.gradeSystem field, ApiFilters.grade_system/grade_list)
  provides:
    - gradeSystem initial state in App.tsx (currentFilters)
    - filtersToApi polymorphic grade filtering (YDS numeric vs non-YDS grade_list)
    - polymorphic sortedRoutes 'grade' case dispatching on gradeSystem
    - specialty sort cases removed from App.tsx switch
  affects:
    - climbing-search/src/App.tsx — all phase 05 functional requirements wired
tech_stack:
  added: []
  patterns:
    - Polymorphic sort dispatch via switch(gradeSystem) inside single 'grade' case
    - grade_list comma-joined range expansion from GRADE_LISTS constant slice
    - Null-last Infinity sentinel preserved for all 4 non-YDS grade systems
    - Mutual exclusion of grade_min/grade_max and grade_list (YDS vs non-YDS)
key_files:
  created: []
  modified:
    - climbing-search/src/App.tsx
decisions:
  - D-09: SortOption specialty variants removed — multiplier and switch both cleaned
  - D-10: sortedRoutes case 'grade' now polymorphic — reads gradeSystem from currentFilters
  - D-12: Null-last sort preserved via Infinity sentinel for all non-YDS systems
  - D-14: gradeSystem: 'yds' added to currentFilters initial state
  - D-16: Non-YDS filtersToApi sends grade_list (GRADE_LISTS range slice)
  - D-17: filtersToApi always sends grade_system param regardless of system
  - D-20: grade_min/grade_max and grade_list are mutually exclusive per request
metrics:
  duration: "~2 minutes"
  completed: "2026-05-17"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 1
---

# Phase 05 Plan 04: App.tsx Grade System Wiring Summary

gradeSystem wired into App.tsx initial state, filtersToApi polymorphic grade expansion (grade_list for non-YDS, numeric for YDS), and polymorphic sortedRoutes 'grade' case dispatching to correct extract*GradeNumeric function — all specialty sort cases removed.

## What Was Built

### Task 1: Imports, initial state, and filtersToApi

Three targeted changes to `climbing-search/src/App.tsx`:

**Import updates:**
- Added `GRADE_LISTS` to the existing value import from `./types/filters`
- Added `import type { GradeSystem } from './types/filters'` as a new type-only import

**Initial state:**
- `currentFilters` useState now includes `gradeSystem: 'yds'` (D-04, D-14)

**filtersToApi grade block replaced:**
- YDS path: sends `grade_system='yds'` + `grade_min`/`grade_max` numeric params (existing behavior preserved)
- Non-YDS path: when `grades.min` and `grades.max` are both set, slices `GRADE_LISTS[gradeSystem]` from `minIdx` to `maxIdx+1` and joins as `grade_list` comma string; also sends `grade_system`
- Mutual exclusion enforced: `grade_min`/`grade_max` never sent with `grade_list` (D-20)
- Empty grades (filter disabled): neither branch is entered — no grade params sent

### Task 2: Polymorphic grade sort, specialty case removal, useMemo fix

Four targeted changes to the `sortedRoutes` useMemo block:

**Multiplier fix:**
- Removed `|| sortConfig.option === 'aid_grade' || sortConfig.option === 'ice_grade' || sortConfig.option === 'mixed_grade' || sortConfig.option === 'boulder_grade'` — only `'grade'` and `'left_to_right'` remain in the condition (D-09)

**Polymorphic case 'grade':**
```typescript
case 'grade': {
  const sys = currentFilters.gradeSystem ?? 'yds';
  if (sys === 'yds') { /* existing GRADE_ORDER path */ }
  // boulder/aid/ice/mixed → dispatch to extract*GradeNumeric
  // Null-last: aVal ?? Infinity; explicit Infinity checks return 1/-1 (D-12)
}
```

**Specialty cases deleted:**
- `case 'aid_grade':`, `case 'ice_grade':`, `case 'mixed_grade':`, `case 'boulder_grade':` — all four removed entirely

**useMemo dependency array:**
- `[filteredRoutes, sortConfig, selectedRoute]` → `[filteredRoutes, sortConfig, selectedRoute, currentFilters]`
- Ensures gradeSystem changes trigger re-sort (Pitfall 5 fix)

## Commits

| Commit | Type | Description |
|--------|------|-------------|
| `06dccd9` | feat | Update imports, initial state, and filtersToApi in App.tsx |
| `e518ee3` | feat | Polymorphic grade sort, remove specialty cases, fix useMemo dep |

## Deviations from Plan

None — plan executed exactly as written.

The plan specified `GRADE_LISTS[uiFilters.gradeSystem]` but `uiFilters.gradeSystem` is typed as `GradeSystem` (from Plan 01) so no cast was strictly necessary — added `as GradeSystem` for explicitness given the `|| !uiFilters.gradeSystem` guard in the else-if.

## Known Stubs

None. All wiring is complete — gradeSystem state flows from initial state through filtersToApi to the API and through sortedRoutes to the rendered list.

## Threat Flags

None. All grade_list values are sliced from the static `GRADE_LISTS` constant (not user-typed text). The API validates with Zod enum + regex (Plan 02). No new network endpoints or auth paths introduced.

## Self-Check: PASSED
