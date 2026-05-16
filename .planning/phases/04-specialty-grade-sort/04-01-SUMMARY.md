---
phase: 04-specialty-grade-sort
plan: "01"
subsystem: ui
tags: [react, typescript, vite, climbing-search, sort, filtering]

# Dependency graph
requires:
  - phase: 03-tagging-upgrade
    provides: route data with route_grade and route_protection_grading fields in D1
provides:
  - SortOption union extended with aid_grade | ice_grade | mixed_grade
  - extractAidGradeNumeric, extractIceGradeNumeric, extractMixedGradeNumeric exported from filters.ts
  - sortedRoutes useMemo handles all three specialty sorts with Infinity sentinel for ungraded routes
  - FilterPanel dropdown shows Aid Grade (A/C), Ice Grade (WI/AI), Mixed Grade (M) options
affects:
  - any future plan modifying FilterPanel sort options or App.tsx sort logic

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Infinity sentinel pattern for null-last sorting (graded routes first, ungraded last regardless of Reverse state)
    - Regex-based grade parsing from string fields (no DB schema changes needed)

key-files:
  created:
    - climbing-search/src/components/InstallPrompt.tsx
    - climbing-search/src/components/OfflineIndicator.tsx
    - climbing-search/src/utils/registerSW.ts
  modified:
    - climbing-search/src/types/filters.ts
    - climbing-search/src/App.tsx
    - climbing-search/src/components/FilterPanel.tsx

key-decisions:
  - "Regex-based grade extraction from existing string fields avoids any DB schema or API changes"
  - "Infinity sentinel for null returns ensures ungraded routes always sort last in both ascending and descending direction"
  - "A and C aid grades share the same numeric scale; WI and AI ice grades share the same numeric scale"
  - "Plus suffix (A3+, WI4+, M6+) adds 0.5 to numeric value for fine-grained ordering"

patterns-established:
  - "Infinity sentinel pattern: extract function returns null → ?? Infinity → guard Infinity last regardless of multiplier"

requirements-completed:
  - SORT-01
  - SORT-02
  - SORT-03

# Metrics
duration: 25min
completed: 2026-05-16
---

# Phase 4 Plan 1: Specialty Grade Sort Summary

**Aid/ice/mixed sort options added to client-side sort dropdown — regex parsing from existing route_grade/route_protection_grading string fields, Infinity sentinel keeps ungraded routes last in both directions**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-05-16T21:40:00Z
- **Completed:** 2026-05-16T22:05:00Z
- **Tasks:** 2 of 3 executed (Task 3 is checkpoint:human-verify — awaiting user)
- **Files modified:** 6

## Accomplishments
- Extended SortOption union with `aid_grade | ice_grade | mixed_grade` in filters.ts
- Implemented three grade-extraction functions with regex parsing and + suffix support
- Added three switch cases to sortedRoutes useMemo with Infinity sentinel for null-last behavior
- Added three option elements to FilterPanel sort select dropdown
- Build passes with zero TypeScript errors (Vite production build succeeds)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add SortOption union values and grade-extraction functions** - `f0ac956` (feat)
2. **Task 2: Wire sort cases in App.tsx and add option elements in FilterPanel.tsx** - `695cd3b` (feat)
3. **Task 3: Verify specialty sort options work in browser** - (checkpoint:human-verify — not yet executed)

## Files Created/Modified
- `climbing-search/src/types/filters.ts` - Extended SortOption union; added extractAidGradeNumeric, extractIceGradeNumeric, extractMixedGradeNumeric
- `climbing-search/src/App.tsx` - Updated imports; added aid_grade, ice_grade, mixed_grade switch cases with Infinity sentinel
- `climbing-search/src/components/FilterPanel.tsx` - Added three option elements to sort select
- `climbing-search/src/components/InstallPrompt.tsx` - Created (Rule 3 fix — was untracked in main repo, missing from worktree)
- `climbing-search/src/components/OfflineIndicator.tsx` - Created (Rule 3 fix — was untracked in main repo, missing from worktree)
- `climbing-search/src/utils/registerSW.ts` - Created (Rule 3 fix — was untracked in main repo, missing from worktree)

## Decisions Made
- Regex-based grade extraction from existing string fields — no DB schema or API changes needed
- Infinity sentinel for null returns ensures ungraded routes always sort last in both ascending and descending direction
- A and C aid grades share the same numeric scale; WI and AI ice grades share the same numeric scale
- Plus suffix (A3+, WI4+, M6+) adds 0.5 to numeric value for fine-grained ordering within a level

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added missing PWA component files absent from worktree**
- **Found during:** Task 2 (build verification)
- **Issue:** `InstallPrompt.tsx`, `OfflineIndicator.tsx`, and `registerSW.ts` are referenced in App.tsx but are untracked files in the main repo that don't exist in the git worktree (untracked files are not part of git history, so worktrees don't receive them)
- **Fix:** Read files from main repo and wrote them to the worktree so the Vite build could succeed
- **Files modified:** climbing-search/src/components/InstallPrompt.tsx (created), climbing-search/src/components/OfflineIndicator.tsx (created), climbing-search/src/utils/registerSW.ts (created)
- **Verification:** `npm run build` exits 0 after adding the files
- **Committed in:** 695cd3b (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Required to make build pass. Files are exact copies from main repo — no logic changes.

## Issues Encountered
- The plan's verification check 5 (`grep -c "case '.*_grade'"`) expects 4 but returns 3 because the regex `'.*_grade'` matches only underscore-containing cases (aid_grade, ice_grade, mixed_grade) not the base `'grade'` case. All 4 cases exist in the code — this is a documentation inconsistency in the plan, not a code defect.

## Known Stubs
None — all three sort options are fully wired from FilterPanel dropdown through App.tsx sort logic using real route_grade / route_protection_grading field data.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Specialty sort feature complete — awaiting user browser verification (Task 3 checkpoint)
- After verification approval, SORT-01, SORT-02, SORT-03 requirements are satisfied
- No blockers for future phases

---
*Phase: 04-specialty-grade-sort*
*Completed: 2026-05-16*
