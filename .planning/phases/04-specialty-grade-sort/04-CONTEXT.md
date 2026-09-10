# Phase 04: Specialty Grade Sort — Context

**Gathered:** 2026-05-16
**Status:** Ready for planning
**Source:** User conversation

<domain>
## Phase Boundary

Add sort options for aid (A/C), ice (WI/AI), and mixed (M) grades to the Sort By dropdown in FilterPanel. Entirely client-side — no API, no DB, no scraper changes. The grade data is already in `route_grade` and `route_protection_grading` columns; we just need to parse and sort by it.

</domain>

<decisions>
## Implementation Decisions

### New SortOption values (filters.ts)
- Add `'aid_grade'` to the `SortOption` union type
- Add `'ice_grade'` to the `SortOption` union type
- Add `'mixed_grade'` to the `SortOption` union type

### Grade parsing functions (filters.ts)
- `extractAidGradeNumeric(routeGrade, protectionGrading)` — regex `/([AC])(\d+)(\+?)/` applied to `route_grade` then `route_protection_grading`. Returns level + 0.5 for `+` suffix. A and C on same numeric scale.
- `extractIceGradeNumeric(routeGrade)` — regex `/(WI|AI)(\d+)(\+?)/` on `route_grade`. WI and AI on same numeric scale.
- `extractMixedGradeNumeric(routeGrade, protectionGrading)` — regex `/M(\d+)(\+?)/` applied to `route_grade` then `route_protection_grading`.
- Routes returning `null` sort LAST (not treated as 0) so unrated routes don't pollute the front/back.

### Sort logic (App.tsx)
- Add cases in the `sortedRoutes` useMemo switch for `'aid_grade'`, `'ice_grade'`, `'mixed_grade'`
- Null-last sentinel: `null → Infinity` for both ascending and descending directions (always appends unrated routes at the bottom regardless of direction)

### UI (FilterPanel.tsx)
- Add three new `<option>` elements to the sort `<select>`: "Aid Grade (A/C)", "Ice Grade (WI/AI)", "Mixed Grade (M)"
- Always visible — don't hide based on type filter (simpler, no state coupling; the sort still works correctly on non-aid routes, they just all go to the bottom)

### Ascending/Descending semantics
- Ascending = easier first (A0, A1, A2…)
- Descending = harder first (A6+, A5+, A4+…) — the default useful direction for aid climbers looking for big-wall objectives

### Claude's Discretion
- Exact label wording in dropdown
- Whether to add helper text/tooltip explaining null-last behavior

</decisions>

<canonical_refs>
## Canonical References

- `climbing-search/src/types/filters.ts` — SortOption type, GRADE_ORDER, normalizeGrade
- `climbing-search/src/App.tsx` — sortedRoutes useMemo, sort switch cases, gradeToNumeric
- `climbing-search/src/components/FilterPanel.tsx` — sort <select> UI, sort option labels
- `climbing-search/src/api/types.ts` — RouteApi shape (route_grade, route_protection_grading fields)

</canonical_refs>

<specifics>
## Specific Ideas from User

- Aid climbers care about C0/C1/C2/C3 order — clean aid (C) and traditional aid (A) both wanted
- Ice climbers want WI sorting — "other grading" for AI (alpine ice) also in DB
- Mixed routes have M-grades (M4, M5, M6+)
- User said: aid climber is "more focused on this vs less concerned with 5.x" — so these should be first-class sort options, not hidden behind a filter

</specifics>

<deferred>
## Deferred Ideas

- Snow grade sorting (no standard numeric scale in DB)
- Alpine grade sorting (NCCS/Commitment grades like D, TD, ED — not parsed yet)
- Conditionally showing sort options based on active type filter (adds complexity, low value since null-last handles mixed datasets cleanly)
- Filtering by specialty grade range (min/max aid grade) — separate feature from sorting

</deferred>

---

*Phase: 04-specialty-grade-sort*
*Context gathered: 2026-05-16*
