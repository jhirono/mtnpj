---
created: 2026-05-16T22:45:00Z
title: Grade system picker — replace specialty sort options with unified grade section
area: ui
files:
  - climbing-search/src/types/filters.ts
  - climbing-search/src/App.tsx
  - climbing-search/src/components/FilterPanel.tsx
  - climbing-search/src/api/types.ts
  - climbing-search/src/api/routeApi.ts
  - worker-api/src/db/queries.ts
  - worker-api/src/routes/routes.ts
---

## Problem

The Sort By dropdown now has 8 options (Grade, Stars, Votes, Left to Right, Aid, Ice, Mixed, Boulder) which is cluttered and not the right UX. Aid/Ice/Mixed/Boulder sort options don't belong in Sort By — they belong in a unified grade section where the user picks their grading system.

## Solution

Replace specialty sort options in Sort By with a grade system picker in the filter panel:

**Grade system options:** YDS (default) | V (Boulder) | Aid (A/C) | Ice (WI/AI) | Mixed (M)

**Behavior decisions (confirmed with user):**
- Picking a grade system changes the grade filter checkboxes to that system's grades
  - YDS → existing GRADE_ORDER list (5.4–5.15d)
  - V → VB, V0–V17
  - Aid → A0–A6, C0–C6
  - Ice → WI1–WI7, AI1–AI5
  - Mixed → M1–M12
- "Sort by Grade" in Sort By uses the active grade system (V-scale if Boulder selected, etc.)
- Switching grade system resets selected grade filters (no cross-system memory)
- Switching grade system does NOT auto-change the sort option (decoupled)
- Grade filter for non-YDS must be server-side — API needs `grade_system` param
- API SQL: use LIKE prefix matching (e.g. `route_grade LIKE 'V4%'` catches V4, V4+, V4-5)

**Files to change:**
- `filters.ts` — add `GradeSystem` type, add to `RouteFilters`, remove `aid_grade | ice_grade | mixed_grade | boulder_grade` from `SortOption`
- `App.tsx` — grade sort switch reads `gradeSystem` to pick extract function; remove specialty sort cases
- `FilterPanel.tsx` — grade system picker UI (tabs or segmented control) + dynamic grade checkbox list
- `api/types.ts` + `routeApi.ts` — pass `grade_system` to API
- `worker-api/src/routes/routes.ts` + `queries.ts` — parse `grade_system`, LIKE-based SQL filtering

**Open question before building:**
- Where does the grade system picker live — inside the existing grade accordion section, or its own top-level row?
