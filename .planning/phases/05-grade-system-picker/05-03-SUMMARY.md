---
phase: 05-grade-system-picker
plan: "03"
subsystem: frontend-ui
tags: [filter-panel, grade-system-picker, segmented-buttons, ui]
dependency_graph:
  requires:
    - 05-01  # GradeSystem type, GRADE_LISTS, RouteFilters.gradeSystem
  provides:
    - Grade system picker row (FilterPanel.tsx)
    - System-aware grade filter (FilterPanel.tsx)
    - Trimmed sort select (FilterPanel.tsx)
  affects:
    - climbing-search/src/App.tsx (Plan 04 — must provide gradeSystem in currentFilters init)
tech_stack:
  added: []
  patterns:
    - Segmented button group (flex-1 buttons, aria-pressed, role=group)
    - System-aware grade list via GRADE_LISTS[filters.gradeSystem]
    - Handler resets both local state (gradeFilterEnabled) and parent state (grades) together
key_files:
  created: []
  modified:
    - climbing-search/src/components/FilterPanel.tsx
decisions:
  - D-01/D-02: Picker is a dedicated top-level row (above Grade Filter), 5 segmented buttons
  - D-03: Active button bg-blue-600 text-white; inactive bg-gray-100 text-gray-700 with dark variants
  - D-06: Grade filter retains min/max select UX; only grade list changes per system
  - D-07: Grade filter resets on system switch (both checkbox and grades.min/max cleared)
  - D-08: GRADE_LISTS[filters.gradeSystem] drives select options for all systems
  - D-09: 4 specialty sort options (aid_grade, ice_grade, mixed_grade, boulder_grade) removed
metrics:
  duration: "~10 minutes"
  completed: "2026-05-16"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 1
---

# Phase 05 Plan 03: FilterPanel Grade System Picker Summary

Grade system picker row (5 segmented buttons: YDS, V, Aid, Ice, Mixed) added above Grade Filter; grade filter made system-aware; 4 specialty sort options removed — all in FilterPanel.tsx.

## What Was Built

### Task 1: Grade system picker row and imports/sort select

Added to `climbing-search/src/components/FilterPanel.tsx`:

- Updated imports: added `GradeSystem` type and `GRADE_LISTS` from `../types/filters`
- Added `GRADE_SYSTEMS` constant (array of 5 `{ value, label }` objects) outside the component
- Added `handleGradeSystemChange` handler inside component: calls `setGradeFilterEnabled(false)` AND `onChange({ ...filters, gradeSystem: newSystem, grades: { min: '', max: '' } })` together
- Inserted grade system picker row JSX above Grade Filter:
  - `<div className="filter-group">` container
  - "Grade System" h3 label
  - `<div role="group" aria-label="Grade System">` button container
  - 5 buttons with `aria-pressed`, `flex-1`, `bg-blue-600 text-white border-blue-600` active / `bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200` inactive styling
  - Full dark mode variants on all buttons
- Removed 4 specialty sort options: `aid_grade`, `ice_grade`, `mixed_grade`, `boulder_grade`
- Sort By select now has exactly 4 options: Grade, Stars, # of Votes, Left to Right

### Task 2: System-aware grade filter

Three targeted changes to the grade filter section:

1. **Grade filter checkbox onChange**: replaced hardcoded `{ min: '5.10a', max: '5.11a' }` with `systemDefaults` object covering all 5 systems (yds/boulder/aid/ice/mixed). On uncheck, resets to `{ min: '', max: '' }`.

2. **Min/max grade select options**: replaced `{SIMPLE_GRADES.map(...)}` with `{GRADE_LISTS[filters.gradeSystem].map(...)}` on both selects — options update dynamically when grade system changes.

3. **Min/max cross-validation**: updated both select `onChange` handlers to use `filters.gradeSystem === 'yds' ? GRADE_ORDER : GRADE_LISTS[filters.gradeSystem]` for index-based min ≤ max enforcement. GRADE_ORDER only contains YDS grades so it cannot be used for non-YDS systems.

## Commits

| Commit | Type | Description |
|--------|------|-------------|
| `0e1c14c` | feat | Add grade system picker row and trim sort select |
| `a21bdc5` | feat | Make grade filter system-aware |

## Deviations from Plan

None — plan executed exactly as written.

## Threat Flags

None. Changes are pure UI rendering driven by TypeScript-constrained `GradeSystem` union type — no new network endpoints, auth paths, or schema changes.

T-05-04 (accepted): `gradeSystem` is constrained to the GradeSystem union by TypeScript. Only `'yds'|'boulder'|'aid'|'ice'|'mixed'` can be passed from button clicks.

T-05-05 (accepted): Select options rendered from `GRADE_LISTS` — only known grade strings can be selected; no arbitrary input reaches the API.

## Self-Check: PASSED

Files verified:
- `climbing-search/src/components/FilterPanel.tsx` — FOUND
- `.planning/phases/05-grade-system-picker/05-03-SUMMARY.md` — FOUND

Commits verified:
- `0e1c14c` — feat(05-03): add grade system picker row and trim sort select
- `a21bdc5` — feat(05-03): make grade filter system-aware
