# Phase 05: Grade System Picker — Context

**Gathered:** 2026-05-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace the 4 specialty sort options (Aid Grade, Ice Grade, Mixed Grade, Boulder Grade) in the Sort By dropdown with a unified grade system picker that lives as its own top-level row in FilterPanel. The picker controls which grading system is active (YDS | V | Aid | Ice | Mixed). Picking a system changes the grade filter min/max options to that system's grade list and makes "Sort by Grade" sort by that system's scale. The grade filter resets to disabled on system switch. All specialty sort cases are removed from `SortOption` — the single `'grade'` option becomes polymorphic.

Backend changes required: non-YDS grade filtering must be server-side via LIKE prefix matching, since `route_grade_numeric` is YDS-only.

</domain>

<decisions>
## Implementation Decisions

### Grade System Picker UI
- **D-01:** Picker is a dedicated top-level row (above Grade Filter), always visible — not inside an accordion.
- **D-02:** Control style: 5 horizontally-arranged segmented buttons — `[YDS] [V] [Aid] [Ice] [Mixed]`.
- **D-03:** Active state: solid blue fill (`bg-blue-600 text-white`). Inactive: gray background. Support dark mode variants.
- **D-04:** YDS is the default grade system on load.
- **D-05:** Grade system options map to labels: YDS → "YDS", V → "V", Aid → "Aid", Ice → "Ice", Mixed → "Mixed".

### Grade Filter Behavior
- **D-06:** Grade filter stays min/max `<select>` for all systems — same UX as current YDS filter, just different grade list per system.
- **D-07:** When user switches grade system, grade filter resets to **disabled** (checkbox unchecked, min/max reset to first and last of new system list). No cross-system memory.
- **D-08:** Grade system controls which grade list populates the min/max selects:
  - YDS → existing `SIMPLE_GRADES` (5.3–5.16d)
  - V (Boulder) → VB, V0–V17 (19 options)
  - Aid → A0–A6 (7 options for select labels; LIKE will also match C grades at same numeric level)
  - Ice → WI1–WI7 (7 options for select labels; LIKE will also match AI grades at same numeric level)
  - Mixed → M1–M12 (12 options)

### Sort Behavior
- **D-09:** Remove `'aid_grade' | 'ice_grade' | 'mixed_grade' | 'boulder_grade'` from `SortOption`. Keep only `'grade' | 'stars' | 'left_to_right' | 'votes'`.
- **D-10:** `'grade'` sort becomes polymorphic — reads `gradeSystem` from `RouteFilters` and routes to the appropriate `extract*GradeNumeric` function. YDS uses existing `gradeToNumeric` path.
- **D-11:** Switching grade system does NOT auto-change the sort option (decoupled).
- **D-12:** Null-last behavior is preserved for all grade systems — routes without a grade in the active system sort to the bottom (same as Phase 04 logic).

### Types and State
- **D-13:** Add `GradeSystem = 'yds' | 'boulder' | 'aid' | 'ice' | 'mixed'` type to `filters.ts`.
- **D-14:** Add `gradeSystem: GradeSystem` field to `RouteFilters` (default: `'yds'`).
- **D-15:** `RouteFilters.grades` stays as `{ min: string; max: string }` — grade string values that match the active system's grade list (e.g., "V4" and "V8" for boulder, "A2" and "A5" for aid).

### API Filter Contract
- **D-16:** For non-YDS filtering: client expands the min→max range into a comma-separated `grade_list` param (e.g., `grade_list=V4,V5,V6,V7,V8`) using the active system's ordered grade array. Client slices from minIdx to maxIdx+1.
- **D-17:** API receives `grade_system` param (`'yds' | 'boulder' | 'aid' | 'ice' | 'mixed'`). When `grade_system=yds` or absent, use existing `route_grade_numeric` filtering unchanged.
- **D-18:** For non-YDS: API receives `grade_list` (comma-separated strings). Builds: `WHERE (route_grade LIKE 'V4%' OR route_grade LIKE 'V5%' OR ...)`.
- **D-19:** For Aid and Mixed grades: filter on BOTH `route_grade` AND `route_protection_grading` columns: `WHERE ((route_grade LIKE 'A3%' OR route_protection_grading LIKE 'A3%') OR ...)`. Ice and Boulder filter `route_grade` only.
- **D-20:** YDS grade filter (`grade_min`/`grade_max` numeric) and non-YDS `grade_list` are mutually exclusive — only one applies per request based on `grade_system`.

### Claude's Discretion
- Exact handling of dual-scale grade systems in the min/max selects (Aid: A-vs-C, Ice: WI-vs-AI). Showing A-scale labels (A0–A6) and WI-scale labels (WI1–WI7) in the selects, with LIKE queries also catching C and AI variants, is the intended approach — exact label format is up to Claude.
- Dark mode class names for the segmented buttons (follow existing dark: variants in FilterPanel.tsx).
- Label truncation strategy if segmented buttons overflow on narrow viewports.

### Folded Todos
- **Grade system picker redesign** (`.planning/todos/pending/2026-05-16-grade-system-picker-redesign.md`) — folded in full. This phase IS the todo.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Frontend — filters and sort
- `climbing-search/src/types/filters.ts` — SortOption union (remove specialty options), GRADE_ORDER, SIMPLE_GRADES, extract*GradeNumeric functions (reuse for polymorphic sort), GradeSystem type (add here), RouteFilters (add gradeSystem field)
- `climbing-search/src/App.tsx` — sortedRoutes useMemo (polymorphic grade sort switch), gradeToNumeric, currentFilters state init
- `climbing-search/src/components/FilterPanel.tsx` — FilterPanel component: add grade system picker row, update grade filter to use active system's grade list, remove specialty sort options from select

### API types and client
- `climbing-search/src/api/types.ts` — ApiFilters interface (add grade_system, grade_list params), RouteApi (existing — no changes needed)
- `climbing-search/src/api/routeApi.ts` — where filter params are assembled and sent to worker API

### Backend worker
- `worker-api/src/db/queries.ts` — buildRoutesQuery: add grade_system/grade_list handling; LIKE-based SQL filtering for non-YDS systems
- `worker-api/src/routes/routes.ts` — route handler: parse grade_system + grade_list from query params, pass to buildRoutesQuery

### Prior phase context
- `.planning/phases/04-specialty-grade-sort/04-CONTEXT.md` — decisions from Phase 04 being superseded (null-last behavior to preserve, extract* functions to reuse)
- `.planning/todos/pending/2026-05-16-grade-system-picker-redesign.md` — original todo with problem statement and confirmed decisions

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `extractAidGradeNumeric`, `extractIceGradeNumeric`, `extractMixedGradeNumeric`, `extractBoulderGradeNumeric` in `filters.ts` — already implemented and tested in Phase 04. Reuse directly in the polymorphic `grade` sort switch.
- `normalizeGrade` + `gradeToNumeric` in `App.tsx` — existing YDS sort path, keep for `gradeSystem === 'yds'`.
- Accordion + checkbox pattern in `FilterPanel.tsx` — existing section expand/collapse; grade filter row can follow the same inline-row pattern it uses today.

### Established Patterns
- Sort By row: inline flex with label + `<select>` + Reverse checkbox — keep this structure, just reduce to 4 options.
- Grade filter: toggle checkbox → conditional min/max selects — same pattern, extend with system-aware grade list.
- Dark mode: every UI element uses `dark:` Tailwind variants — new picker must follow same pattern.
- State in `App.tsx`: `currentFilters` is a `RouteFilters` object managed via `useState` + `handleFilterChange` — `gradeSystem` field added to this object.

### Integration Points
- `RouteFilters` flows App.tsx → FilterPanel (via `filters` prop) → onChange callback → back to App.tsx → `buildApiFilters()` → routeApi → worker
- `SortConfig` flows App.tsx → FilterPanel (via `sortConfig` prop) → `onSortChange` callback → `sortedRoutes` useMemo
- `buildRoutesQuery` in `queries.ts` receives `RouteFilters` (worker-side shape) — add `grade_system` and `grade_list` fields there

</code_context>

<specifics>
## Specific Ideas

- "Picking a grade system changes the grade filter checkboxes to that system's grades" — todo language; final decision is min/max selects (not checkboxes), but the grade list changes dynamically.
- Aid: A and C grades share the same numeric scale (C2 ≈ A2, gear style differs). LIKE queries should match both A and C variants when Aid system is active.
- Ice: WI and AI share the same numeric scale. LIKE queries should match both when Ice system is active.
- Null-last behavior from Phase 04 must be preserved — routes without a grade for the active system sort to the bottom in both ascending and descending directions.

</specifics>

<deferred>
## Deferred Ideas

- Filtering by specialty grade range (min/max boulder grade, min/max aid grade) was partially in the todo — this phase implements it via grade_list. Full faceted filtering UI is out of scope.
- Snow grade sorting (no standard numeric scale in DB) — deferred from Phase 04, still deferred.
- Alpine grade sorting (NCCS/commitment grades) — deferred from Phase 04, still deferred.
- Conditionally showing sort options based on active type filter — deferred from Phase 04. The grade system picker handles this concern differently (system selection changes the sort behavior, not the dropdown options).
- Visual tooltip or helper text explaining null-last sort behavior — deferred per Phase 04 decision.

</deferred>

---

*Phase: 05-grade-system-picker*
*Context gathered: 2026-05-16*
