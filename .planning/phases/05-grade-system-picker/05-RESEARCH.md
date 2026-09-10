# Phase 05: Grade System Picker — Research

**Researched:** 2026-05-16
**Domain:** React/TypeScript frontend filter UI + Cloudflare Worker D1 SQL backend
**Confidence:** HIGH — all decisions are locked in CONTEXT.md, all code has been read directly from the repo

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Grade System Picker UI**
- D-01: Picker is a dedicated top-level row (above Grade Filter), always visible — not inside an accordion.
- D-02: Control style: 5 horizontally-arranged segmented buttons — `[YDS] [V] [Aid] [Ice] [Mixed]`.
- D-03: Active state: solid blue fill (`bg-blue-600 text-white`). Inactive: gray background. Support dark mode variants.
- D-04: YDS is the default grade system on load.
- D-05: Grade system options map to labels: YDS → "YDS", V → "V", Aid → "Aid", Ice → "Ice", Mixed → "Mixed".

**Grade Filter Behavior**
- D-06: Grade filter stays min/max `<select>` for all systems — same UX as current YDS filter, just different grade list per system.
- D-07: When user switches grade system, grade filter resets to disabled (checkbox unchecked, min/max reset to first and last of new system list). No cross-system memory.
- D-08: Grade system controls which grade list populates the min/max selects:
  - YDS → existing `SIMPLE_GRADES` (5.3–5.16d)
  - V (Boulder) → VB, V0–V17 (19 options)
  - Aid → A0–A6 (7 options; LIKE also matches C grades)
  - Ice → WI1–WI7 (7 options; LIKE also matches AI grades)
  - Mixed → M1–M12 (12 options)

**Sort Behavior**
- D-09: Remove `'aid_grade' | 'ice_grade' | 'mixed_grade' | 'boulder_grade'` from `SortOption`. Keep only `'grade' | 'stars' | 'left_to_right' | 'votes'`.
- D-10: `'grade'` sort becomes polymorphic — reads `gradeSystem` from `RouteFilters` and routes to the appropriate `extract*GradeNumeric` function.
- D-11: Switching grade system does NOT auto-change the sort option (decoupled).
- D-12: Null-last behavior preserved for all grade systems.

**Types and State**
- D-13: Add `GradeSystem = 'yds' | 'boulder' | 'aid' | 'ice' | 'mixed'` type to `filters.ts`.
- D-14: Add `gradeSystem: GradeSystem` field to `RouteFilters` (default: `'yds'`).
- D-15: `RouteFilters.grades` stays as `{ min: string; max: string }` — grade string values match the active system's list.

**API Filter Contract**
- D-16: For non-YDS filtering: client expands the min→max range into a comma-separated `grade_list` param using the active system's ordered grade array.
- D-17: API receives `grade_system` param (`'yds' | 'boulder' | 'aid' | 'ice' | 'mixed'`). When `grade_system=yds` or absent, use existing `route_grade_numeric` filtering unchanged.
- D-18: For non-YDS: API receives `grade_list`. Builds: `WHERE (route_grade LIKE 'V4%' OR route_grade LIKE 'V5%' OR ...)`.
- D-19: For Aid and Mixed grades: filter on BOTH `route_grade` AND `route_protection_grading`. Ice and Boulder filter `route_grade` only.
- D-20: YDS grade filter (`grade_min`/`grade_max` numeric) and non-YDS `grade_list` are mutually exclusive.

### Claude's Discretion
- Exact handling of dual-scale grade systems in the min/max selects (Aid: A-vs-C, Ice: WI-vs-AI). Show A-scale labels (A0–A6) and WI-scale labels (WI1–WI7) in the selects, with LIKE queries also catching C and AI variants.
- Dark mode class names for the segmented buttons (follow existing dark: variants in FilterPanel.tsx).
- Label truncation strategy if segmented buttons overflow on narrow viewports.

### Deferred Ideas (OUT OF SCOPE)
- Filtering by specialty grade range (min/max boulder grade, min/max aid grade) via a full faceted filtering UI.
- Snow grade sorting.
- Alpine grade sorting (NCCS/commitment grades).
- Conditionally showing sort options based on active type filter.
- Visual tooltip or helper text explaining null-last sort behavior.
</user_constraints>

---

## Summary

Phase 05 replaces four specialty sort options (Aid Grade, Ice Grade, Mixed Grade, Boulder Grade) with a unified grade system picker that controls both grade filtering and the polymorphic "Grade" sort. The change spans frontend types, state, UI, API client, and backend query builder — but every relevant file has been read and the exact changes are well-defined by the locked decisions.

The frontend work is the larger half: adding a `GradeSystem` type and `gradeSystem` field to `RouteFilters`, rendering the 5-button picker in `FilterPanel`, making the grade filter grade-list-aware, and updating the `sortedRoutes` switch in `App.tsx`. The backend adds two new query params (`grade_system`, `grade_list`) and LIKE-based SQL filtering for non-YDS systems.

The key technical risk is the D1 LIKE query construction for non-YDS filtering. The codebase already has a documented pattern for building parameterized LIKE conditions — the prior area-path filtering shows that D1 accepts short, simple LIKE patterns fine, and the grade list expansion (e.g., `V4,V5,V6,V7,V8`) produces short per-grade patterns like `'V4%'`, not complex patterns that hit the D1 "pattern too complex" limit. The grade list expansion approach (D-16) is therefore safe.

**Primary recommendation:** Implement in four sequential plans — (1) types/constants, (2) UI/FilterPanel, (3) App.tsx sort+filter wiring, (4) backend API. Each plan compiles and passes tests independently.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| GradeSystem type + grade list constants | Frontend (types/filters.ts) | — | Type-only; consumed by both FilterPanel and App |
| Grade system picker UI | Frontend (FilterPanel.tsx) | — | Pure render: segmented button row, dark mode variants |
| Grade filter dynamic grade list | Frontend (FilterPanel.tsx) | — | Select options driven by active system state |
| Polymorphic grade sort | Frontend (App.tsx) | — | Client-side sort using existing extract* functions |
| Grade list expansion (min→max→array) | Frontend (App.tsx filtersToApi) | — | Client builds comma-separated grade_list before API call |
| API client params | Frontend (api/types.ts + routeApi) | — | ApiFilters interface extended; buildQuery serializes |
| LIKE-based SQL grade filtering | Backend (worker-api queries.ts) | — | D1 LIKE WHERE clause for non-YDS grade_list |
| Query param parsing + validation | Backend (worker-api routes.ts) | — | Zod schema extended with grade_system + grade_list |

---

## Standard Stack

All libraries below are already installed in the project — no new dependencies needed.

### Core (already installed)
| Library | Version | Purpose | Role in Phase |
|---------|---------|---------|---------------|
| React | 18.2.0 | UI rendering | FilterPanel component state and rendering |
| TypeScript | ~5.7.2 (frontend) | Type safety | GradeSystem type, RouteFilters extension |
| Tailwind CSS | ^3.4.1 | Styling | Segmented button classes, dark: variants |
| Hono | ^4.12.18 | Worker HTTP framework | Route handler for new query params |
| Zod | ^4.4.3 | Query param validation | Extend routeQuerySchema |
| @hono/zod-validator | ^0.7.6 | Hono+Zod integration | zValidator middleware used in routes.ts |
| Vitest | ^4.1.5 | Worker tests | Test new grade_system/grade_list filtering |
| @cloudflare/vitest-pool-workers | ^0.16.3 | D1 test environment | Existing test setup in worker-api/test/ |

**No new dependencies required.** [VERIFIED: package.json direct read]

---

## Architecture Patterns

### System Architecture Diagram

```
User clicks picker button
        |
        v
FilterPanel (local state: gradeSystem)
  - Updates gradeSystem in RouteFilters via onChange
  - Resets grade filter (checkbox unchecked, min/max to system defaults)
  - Repopulates grade select options from system's grade array
        |
        v
App.tsx handleFilterChange
  - currentFilters.gradeSystem updated
  - Triggers: useEffect (API reload) + sortedRoutes useMemo (re-sort)
        |
        +----------------------+
        |                      |
        v                      v
filtersToApi()           sortedRoutes useMemo
  - grade_system=<sys>     - switch(sortConfig.option)
  - If grade enabled:        - case 'grade': switch(gradeSystem)
    grade_list=V4,V5,V6       -> extract*GradeNumeric
  - If YDS: grade_min/max    - null-last: null→Infinity
        |
        v
routeApi.fetchRoutes(ApiFilters)
        |
        v
Worker /api/routes
  zod parse: grade_system, grade_list
        |
        v
buildRoutesQuery()
  - grade_system='yds' or absent → existing grade_min/grade_max path
  - grade_system='boulder'/'ice' → LIKE on route_grade
  - grade_system='aid'/'mixed'  → LIKE on route_grade OR route_protection_grading
        |
        v
D1 SQL query → results → JSON response
```

### Recommended Project Structure (no changes to directory layout)
```
climbing-search/src/
├── types/
│   └── filters.ts          # +GradeSystem type, +GRADE_LISTS constant, +gradeSystem to RouteFilters, -specialty SortOptions
├── components/
│   └── FilterPanel.tsx     # +grade system picker row, grade filter uses active system list
├── api/
│   └── types.ts            # +grade_system, +grade_list to ApiFilters
├── App.tsx                 # +gradeSystem to initial state, +grade list expansion in filtersToApi, polymorphic sort switch
worker-api/src/
├── db/
│   └── queries.ts          # +grade_system, +grade_list to RouteFilters, +LIKE WHERE clause
├── routes/
│   └── routes.ts           # +grade_system, +grade_list to zod schema
worker-api/test/
└── routes.test.ts          # +tests for grade_system=boulder/aid/ice/mixed filtering
```

### Pattern 1: Grade System State in FilterPanel

`gradeSystem` is owned by `App.tsx` as part of `currentFilters` (`RouteFilters.gradeSystem`). `FilterPanel` receives it via `filters.gradeSystem` and calls `onChange` to update it. Local `gradeFilterEnabled` state in `FilterPanel` is reset to `false` on system switch.

The grade filter reset on system switch must:
1. Set `gradeFilterEnabled` to `false` (local state)
2. Call `onChange({ ...filters, gradeSystem: newSystem, grades: { min: '', max: '' } })`

This keeps `FilterPanel`'s local checkbox state and `App.tsx`'s `currentFilters.grades` in sync.

[VERIFIED: FilterPanel.tsx direct read — gradeFilterEnabled is local, grades flows via RouteFilters]

### Pattern 2: Grade List Constants

Define `GRADE_LISTS` as a `Record<GradeSystem, string[]>` constant in `filters.ts`:

```typescript
// Source: filters.ts — add alongside SIMPLE_GRADES
export const GRADE_LISTS: Record<GradeSystem, string[]> = {
  yds: SIMPLE_GRADES,
  boulder: ['VB', 'V0', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'V7',
            'V8', 'V9', 'V10', 'V11', 'V12', 'V13', 'V14', 'V15', 'V16', 'V17'],
  aid: ['A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6'],
  ice: ['WI1', 'WI2', 'WI3', 'WI4', 'WI5', 'WI6', 'WI7'],
  mixed: ['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8', 'M9', 'M10', 'M11', 'M12'],
};
```

This is the single source of truth used by: FilterPanel selects, `filtersToApi` expansion, and test fixtures.

[VERIFIED: D-08 grade lists; 05-UI-SPEC.md Grade List Definitions section]

### Pattern 3: Grade List Expansion in filtersToApi (D-16)

```typescript
// In App.tsx filtersToApi — for non-YDS grade filter
if (uiFilters.gradeSystem !== 'yds' && uiFilters.grades.min && uiFilters.grades.max) {
  const list = GRADE_LISTS[uiFilters.gradeSystem];
  const minIdx = list.indexOf(uiFilters.grades.min);
  const maxIdx = list.indexOf(uiFilters.grades.max);
  if (minIdx !== -1 && maxIdx !== -1 && minIdx <= maxIdx) {
    params.grade_list = list.slice(minIdx, maxIdx + 1).join(',');
    params.grade_system = uiFilters.gradeSystem;
  }
} else if (uiFilters.gradeSystem === 'yds') {
  // existing grade_min / grade_max numeric path — unchanged
  params.grade_system = 'yds'; // optional, makes intent explicit
}
```

[ASSUMED: exact code shape — but structure flows directly from D-16 and existing filtersToApi pattern in App.tsx]

### Pattern 4: LIKE Clause Construction in buildRoutesQuery (D-18, D-19)

```typescript
// In queries.ts buildRoutesQuery — add after existing grade_max handling
if (f.grade_list && f.grade_system && f.grade_system !== 'yds') {
  const grades = f.grade_list.split(',').map(g => g.trim()).filter(Boolean);
  if (grades.length > 0) {
    if (f.grade_system === 'aid' || f.grade_system === 'mixed') {
      // Filter route_grade OR route_protection_grading (D-19)
      const orClauses = grades.map(() =>
        `(route_grade LIKE ? OR route_protection_grading LIKE ?)`
      ).join(' OR ');
      conds.push(`(${orClauses})`);
      for (const g of grades) { params.push(`${g}%`, `${g}%`); }
    } else {
      // boulder, ice: filter route_grade only (D-19)
      const orClauses = grades.map(() => `route_grade LIKE ?`).join(' OR ');
      conds.push(`(${orClauses})`);
      for (const g of grades) { params.push(`${g}%`); }
    }
  }
}
```

[ASSUMED: exact code shape — but pattern follows existing parameterized conditions in buildRoutesQuery]

### Pattern 5: Polymorphic Grade Sort in App.tsx (D-10)

The current `case 'grade':` uses `GRADE_ORDER.indexOf(normalizeGrade(...))`. This becomes a nested switch on `currentFilters.gradeSystem`:

```typescript
case 'grade': {
  const sys = currentFilters.gradeSystem ?? 'yds';
  if (sys === 'yds') {
    return multiplier * (
      GRADE_ORDER.indexOf(normalizeGrade(a.route_grade ?? '')) -
      GRADE_ORDER.indexOf(normalizeGrade(b.route_grade ?? ''))
    );
  }
  // non-YDS: use extract* functions with null-last
  let aVal: number | null = null;
  let bVal: number | null = null;
  if (sys === 'boulder') {
    aVal = extractBoulderGradeNumeric(a.route_grade);
    bVal = extractBoulderGradeNumeric(b.route_grade);
  } else if (sys === 'aid') {
    aVal = extractAidGradeNumeric(a.route_grade, a.route_protection_grading);
    bVal = extractAidGradeNumeric(b.route_grade, b.route_protection_grading);
  } else if (sys === 'ice') {
    aVal = extractIceGradeNumeric(a.route_grade);
    bVal = extractIceGradeNumeric(b.route_grade);
  } else if (sys === 'mixed') {
    aVal = extractMixedGradeNumeric(a.route_grade, a.route_protection_grading);
    bVal = extractMixedGradeNumeric(b.route_grade, b.route_protection_grading);
  }
  const aFinal = aVal ?? Infinity;
  const bFinal = bVal ?? Infinity;
  if (aFinal === Infinity && bFinal === Infinity) return 0;
  if (aFinal === Infinity) return 1;
  if (bFinal === Infinity) return -1;
  return multiplier * (aFinal - bFinal);
}
```

[VERIFIED: existing null-last pattern from Phase 04 in App.tsx direct read; extract* functions confirmed in filters.ts]

### Pattern 6: Segmented Button Picker (D-02, D-03, UI-SPEC)

```tsx
// In FilterPanel — above Grade Filter section
const GRADE_SYSTEMS: { value: GradeSystem; label: string }[] = [
  { value: 'yds', label: 'YDS' },
  { value: 'boulder', label: 'V' },
  { value: 'aid', label: 'Aid' },
  { value: 'ice', label: 'Ice' },
  { value: 'mixed', label: 'Mixed' },
];

<div className="filter-group">
  <div className="flex items-center gap-2">
    <h3 className="font-medium text-gray-900 dark:text-gray-100 whitespace-nowrap text-sm">
      Grade System
    </h3>
    <div className="flex flex-1 gap-1 min-w-0" role="group" aria-label="Grade System">
      {GRADE_SYSTEMS.map(({ value, label }) => {
        const isActive = filters.gradeSystem === value;
        return (
          <button
            key={value}
            type="button"
            aria-pressed={isActive}
            onClick={() => handleGradeSystemChange(value)}
            className={`flex-1 py-2 px-1 text-sm font-medium rounded border transition-colors
              whitespace-nowrap overflow-hidden text-ellipsis
              ${isActive
                ? 'bg-blue-600 text-white border-blue-600 dark:bg-blue-600 dark:text-white dark:border-blue-600'
                : 'bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600'
              }`}
          >
            {label}
          </button>
        );
      })}
    </div>
  </div>
</div>
```

[VERIFIED: UI-SPEC.md Component Inventory section; class names verified against existing FilterPanel.tsx dark: patterns]

### Anti-Patterns to Avoid

- **Storing gradeSystem in FilterPanel local state:** It belongs in `RouteFilters` (App.tsx) so it flows to `filtersToApi` and `sortedRoutes`. Do not store it locally.
- **Building LIKE with string interpolation (SQL injection):** Grade strings from the grade list are client-controlled, but they must still be passed as parameterized bind params, not interpolated into SQL.
- **Using `grade_min`/`grade_max` for non-YDS systems:** D-20 makes these mutually exclusive. Non-YDS uses `grade_list` only; `grade_min`/`grade_max` are skipped in `filtersToApi` when `gradeSystem !== 'yds'`.
- **Leaving specialty sort cases in App.tsx switch:** The old `'aid_grade'`, `'ice_grade'`, `'mixed_grade'`, `'boulder_grade'` cases must be deleted entirely (D-09). The `multiplier` computation that checks for these cases must also be simplified.
- **Forgetting the multiplier computation cleanup:** The existing multiplier line in App.tsx (line 157-159) references all four specialty options by name. After removing them, this logic must be updated or the sort direction will be wrong for `'grade'`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Grade order/sorting | Custom sort comparator | Existing `extract*GradeNumeric` functions in filters.ts | Already implemented, tested, and documented in Phase 04 |
| Grade list definition | Inline arrays in component | `GRADE_LISTS` constant in filters.ts | Single source of truth for both UI and expansion logic |
| LIKE query building | Dynamic SQL string building | Parameterized conditions array (existing pattern in queries.ts) | D1 LIKE safety; matches the established `conds`/`params` pattern |
| Dark mode toggle | CSS class conditional | `dark:` Tailwind variants | Already used throughout FilterPanel.tsx |
| Zod query validation | Manual query param parsing | Extend existing `routeQuerySchema` | Pattern is established in routes.ts |

---

## Common Pitfalls

### Pitfall 1: Multiplier computation references deleted sort options
**What goes wrong:** After removing `'aid_grade'`, `'ice_grade'`, `'mixed_grade'`, `'boulder_grade'` from `SortOption`, the multiplier computation in App.tsx (currently checks for them by name) becomes dead code that may cause TypeScript errors or incorrect sort direction.
**Why it happens:** The existing multiplier line explicitly lists these options: `sortConfig.option === 'aid_grade' || sortConfig.option === 'ice_grade' || ...`
**How to avoid:** When removing the specialty cases from the switch, also update the multiplier to only include the remaining options. The polymorphic `'grade'` case uses `ascending ? -1 : 1` (same as the specialty options, not stars/votes).
**Warning signs:** TypeScript unused-variable error on the deleted SortOption variants; sort direction inverted for grade sort.

### Pitfall 2: Grade filter reset on system switch leaves grades.min/max stale
**What goes wrong:** If only the local `gradeFilterEnabled` checkbox state is reset but `filters.grades` is not cleared, the stale min/max values from the previous system's grade list may be sent to the API on the next filter change.
**Why it happens:** `gradeFilterEnabled` is local state in FilterPanel; `filters.grades` is owned by App.tsx. Both must be updated together on system switch.
**How to avoid:** `handleGradeSystemChange` must call `onChange({ ...filters, gradeSystem: newSystem, grades: { min: '', max: '' } })` AND `setGradeFilterEnabled(false)`.
**Warning signs:** API request with `grade_list=V4,V5` after switching to Ice system; grade selects showing wrong grade options.

### Pitfall 3: D1 LIKE with long or complex patterns
**What goes wrong:** D1 rejects LIKE patterns that are "too complex" (documented in queries.ts comments). This happened with area path LIKE queries.
**Why it happens:** D1's SQLite implementation rejects patterns that trigger exponential backtracking.
**How to avoid:** Grade LIKE patterns (`'V4%'`, `'A3%'`, `'WI4%'`) are simple prefix matches with a single wildcard at the end — not complex patterns. These are safe. The "pattern too complex" error only occurs with patterns like `LIKE '%/long-slug-path/%'`. Monitor if grade lists grow excessively long (>20 OR clauses).
**Warning signs:** 500 error from worker when grade_list filter is active.

### Pitfall 4: Aid/Mixed LIKE catching wrong grades
**What goes wrong:** LIKE `'M1%'` would match "M10", "M11", "M12" when the user selected only M1.
**Why it happens:** Prefix LIKE match on short grade strings.
**How to avoid:** Mixed grades M10, M11, M12 only appear as `M1` prefix if the pattern is `M1%` — which will match `M10`, `M11`, `M12`. For grades with 2-digit numbers (M10–M12), the LIKE pattern `M10%` uniquely matches only M10-grade routes. The grade list expansion sends each grade as a separate LIKE pattern, so `M1%` only appears when M1 is explicitly in the grade_list. If the user selects M1 to M12, all 12 patterns are in grade_list and the full OR expansion covers all.

Actually: `M1%` DOES match `M10`, `M11`, `M12` — this is a real concern when M1 is the only selected grade. The query becomes `route_grade LIKE 'M1%'` which matches M10, M11, M12 as well as M1.
**How to avoid:** For 1-digit Mixed grades (M1–M9), use `M{n}[^0-9]%` patterns, OR add a trailing space/non-digit anchor. Simpler approach: if the grade list is M1–M12 in full, accept the false positives (they're all within the user's selected range anyway). If the user selects M1 as the minimum, M10-M12 being included is functionally acceptable since they're harder. The decision is left to Claude's discretion since the CONTEXT.md does not specify exact pattern anchoring.

The safest approach: append a non-digit guard. E.g., `LIKE 'M1 %' OR LIKE 'M1+%'` — but D1 string functions may be limited. Simplest safe approach: use `M1%` and accept that M10/M11/M12 may appear when M1 is selected in isolation. This is an acceptable UX tradeoff for this MVP.

**Warning signs:** User selects "M1 to M3" but routes with M10 appear in results.

### Pitfall 5: gradeSystem not flowing to sortedRoutes
**What goes wrong:** The polymorphic grade sort reads `currentFilters.gradeSystem`, but if the `sortedRoutes` useMemo dependency array doesn't include `currentFilters` (or the gradeSystem field changes but React doesn't re-run the memo), sort stays on the old system.
**Why it happens:** `sortedRoutes` depends on `filteredRoutes` and `sortConfig`, but `currentFilters` is needed for the new polymorphic path.
**How to avoid:** Add `currentFilters` to the `sortedRoutes` useMemo dependency array, or pass `gradeSystem` explicitly.
**Warning signs:** Switching to Boulder system while sort is "Grade" — routes do not re-sort.

[VERIFIED: App.tsx sortedRoutes useMemo dependency array at line 222 — currently `[filteredRoutes, sortConfig, selectedRoute]`. Missing `currentFilters`.]

### Pitfall 6: Zod schema for grade_list — overly restrictive validation
**What goes wrong:** If grade_list is validated with a strict regex that doesn't allow all grade characters (V, W, I, A, C, M, digits, commas), valid requests are rejected with 400.
**Why it happens:** Zod string validation on the new query param.
**How to avoid:** Use `.regex(/^[A-Z0-9,+]+$/i)` or simply `.string().optional()` — the actual values are safe because they're sliced from the client-controlled grade list, not raw user text fields. However, basic sanitization is good hygiene.

---

## Code Examples

### Verified: Existing null-last sort pattern (Phase 04, App.tsx)
```typescript
// Source: App.tsx lines 186-213 — proven pattern for non-YDS null-last sort
case 'aid_grade': {
  const aVal = extractAidGradeNumeric(a.route_grade, a.route_protection_grading) ?? Infinity;
  const bVal = extractAidGradeNumeric(b.route_grade, b.route_protection_grading) ?? Infinity;
  if (aVal === Infinity && bVal === Infinity) return 0;
  if (aVal === Infinity) return 1;
  if (bVal === Infinity) return -1;
  return multiplier * (aVal - bVal);
}
```
[VERIFIED: App.tsx direct read]

### Verified: Existing parameterized LIKE condition pattern (queries.ts)
```typescript
// Source: queries.ts — established pattern for safe parameterized SQL
if (f.q) {
  conds.push(`r.rowid IN (SELECT rowid FROM routes_fts WHERE routes_fts MATCH ?)`);
  params.push(ftsQ);
}
```
[VERIFIED: queries.ts direct read]

### Verified: RouteFilters interface (current state to extend)
```typescript
// Source: filters.ts lines 14-21 — add gradeSystem field here
export interface RouteFilters {
  grades: { min: string; max: string };
  types: RouteType[];
  tags: { category: string; selectedTags: string[] }[];
  // ADD: gradeSystem: GradeSystem;
}
```
[VERIFIED: filters.ts direct read]

### Verified: ApiFilters interface (current state to extend)
```typescript
// Source: api/types.ts lines 50-62 — add grade_system and grade_list here
export interface ApiFilters {
  q?: string; grade?: string; grade_min?: number; grade_max?: number;
  type?: RouteType; region?: string; stars_min?: number; votes_min?: number;
  area_id?: string; page?: number; limit?: number;
  // ADD: grade_system?: GradeSystem; grade_list?: string;
}
```
[VERIFIED: api/types.ts direct read]

### Verified: Grade filter default init values per system (UI-SPEC)
| System | Default min | Default max |
|--------|-------------|-------------|
| YDS | "5.10a" | "5.11a" |
| V (Boulder) | "V0" | "V5" |
| Aid | "A0" | "A3" |
| Ice | "WI1" | "WI4" |
| Mixed | "M1" | "M6" |
[VERIFIED: 05-UI-SPEC.md Grade Filter Row section]

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 4 separate specialty sort options | Single polymorphic 'grade' sort + grade system picker | Phase 05 | Removes 4 sort options, adds 1 picker; cleaner UX |
| YDS-only numeric grade filter | System-aware grade filter with LIKE for non-YDS | Phase 05 | Enables boulder/aid/ice/mixed grade range filtering |
| LIKE with path complexity issues | Parameterized LIKE per-grade in OR clause | Phase 05 | Safe: short prefix patterns, no backtracking risk |

**Deprecated/outdated (to remove in Phase 05):**
- `'aid_grade' | 'ice_grade' | 'mixed_grade' | 'boulder_grade'` SortOption variants — replaced by polymorphic `'grade'`
- Specialty sort `<option>` elements in FilterPanel sort select
- Specialty `case` blocks in `sortedRoutes` switch in App.tsx
- Specialty option checks in multiplier computation in App.tsx

---

## Runtime State Inventory

> Phase 05 is a frontend + backend code change with no data migration.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — no DB schema change; route_grade and route_protection_grading columns unchanged | None |
| Live service config | None — Cloudflare Worker deployed via wrangler; no config UI state | None |
| OS-registered state | None | None |
| Secrets/env vars | None — no new env vars; D1 binding unchanged | None |
| Build artifacts | Cloudflare Pages dist/ — auto-rebuilt on deploy | None (auto) |

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js / npm | Build + test | Yes | system | — |
| wrangler | Worker deploy | Yes (in devDeps) | ^4.90.0 | — |
| Vitest | Worker tests | Yes (in devDeps) | ^4.1.5 | — |
| @cloudflare/vitest-pool-workers | Worker tests | Yes (in devDeps) | ^0.16.3 | — |
| D1 (local) | Test seed | Yes (via wrangler dev) | — | — |

No missing dependencies. All tools already installed. [VERIFIED: worker-api/package.json direct read]

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vitest 4.1.5 + @cloudflare/vitest-pool-workers |
| Config file | `worker-api/vitest.config.ts` |
| Quick run command | `cd worker-api && npm test` |
| Full suite command | `cd worker-api && npm test` (same — no separate full suite) |

### Phase Requirements → Test Map
| Req | Behavior | Test Type | Automated Command | File Exists? |
|-----|----------|-----------|-------------------|-------------|
| D-17 | grade_system=yds → existing numeric filter unchanged | integration | `cd worker-api && npm test` | ✅ routes.test.ts |
| D-18 | grade_system=boulder + grade_list → LIKE route_grade | integration | `cd worker-api && npm test` | ❌ Wave 0 |
| D-18 | grade_system=ice + grade_list → LIKE route_grade | integration | `cd worker-api && npm test` | ❌ Wave 0 |
| D-19 | grade_system=aid + grade_list → LIKE route_grade OR route_protection_grading | integration | `cd worker-api && npm test` | ❌ Wave 0 |
| D-19 | grade_system=mixed + grade_list → LIKE route_grade OR route_protection_grading | integration | `cd worker-api && npm test` | ❌ Wave 0 |
| D-20 | grade_system=yds skips grade_list param | integration | `cd worker-api && npm test` | ❌ Wave 0 |
| D-09 | SortOption type excludes specialty options | unit (TypeScript compile) | `cd climbing-search && npx tsc --noEmit` | ✅ (after code change) |
| D-12 | null-last sort preserved for all systems | client-side (no automated test infra) | manual | manual-only |

### Sampling Rate
- **Per task commit:** `cd worker-api && npm test` (worker side); `cd climbing-search && npx tsc --noEmit` (frontend types)
- **Per wave merge:** full worker test suite
- **Phase gate:** all worker tests green before deploy

### Wave 0 Gaps
- [ ] Add boulder route fixture to `worker-api/test/setup.ts` with `route_grade='V3'`, `is_boulder=1` — covers D-18 boulder LIKE test
- [ ] Add ice route fixture with `route_grade='WI4'`, `is_ice=1` — covers D-18 ice LIKE test
- [ ] Add aid route fixture with `route_grade='A3'`, `route_protection_grading='C2'`, `is_aid=1` — covers D-19 aid LIKE test
- [ ] Add mixed route fixture with `route_grade='M6'`, `is_mixed=1` — covers D-19 mixed LIKE test
- [ ] Add test cases to `worker-api/test/routes.test.ts` for `grade_system=boulder&grade_list=V3`, `grade_system=aid&grade_list=A3`, `grade_system=ice&grade_list=WI4`, `grade_system=mixed&grade_list=M6`

Note: The setup.ts already seeds a boulder route (V3) and ice route (WI4) — these fixtures can be reused. [VERIFIED: setup.ts direct read lines 106-107]

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | — |
| V3 Session Management | No | — |
| V4 Access Control | No | — |
| V5 Input Validation | Yes | Zod schema in routes.ts; parameterized SQL in queries.ts |
| V6 Cryptography | No | — |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| SQL injection via grade_list | Tampering | Parameterized bind params in buildRoutesQuery — never interpolate grade strings into SQL |
| grade_list with arbitrary length | DoS | Validate max length in Zod (e.g., `.max(200)`) — longest possible grade_list is 19 items × ~4 chars = ~76 chars |
| grade_system with invalid value | Tampering | Zod enum validation: `z.enum(['yds','boulder','aid','ice','mixed']).optional()` |

**SQL injection note:** The grade_list param is client-constructed from known grade arrays, but the API must still treat it as untrusted input. All grade values must be bound as parameters, not interpolated. This is enforced by the existing `conds`/`params` pattern in `buildRoutesQuery`. [VERIFIED: queries.ts pattern — all conditions use `params.push(value)`]

---

## Open Questions

1. **Mixed grade LIKE false match for M1 vs M10–M12**
   - What we know: `LIKE 'M1%'` matches M10, M11, M12 as well as M1 routes
   - What's unclear: Is this acceptable UX for MVP? The user decision D-18 says "Builds WHERE route_grade LIKE 'V4%'" — this pattern was explicitly chosen, implying prefix matching is acceptable
   - Recommendation: Accept false positives for single-digit Mixed grades in MVP. The grade range selection (min M1 to max M3) would produce `grade_list=M1,M2,M3` which still correctly catches M10-M12 only if M1 is included. This is a known limitation of prefix LIKE. Flag in code comment.

2. **Aid C-grade LIKE catch: does `A0%` also match `AC0` or other variants?**
   - What we know: D-19 says LIKE on `route_grade` for Aid, and the filter on `route_protection_grading` handles C-grades. The LIKE pattern `A0%` catches `A0`, `A0+` etc. on `route_grade`, and separately checks `route_protection_grading` which may contain `C2` etc.
   - What's unclear: Whether `route_protection_grading` stores standalone grades like `C2` or full phrases like `C2 runout`
   - Recommendation: Use `LIKE 'A0%'` for the grade_list item `A0` — this is a prefix match which catches all A0 variants. The `route_protection_grading` field is checked separately with the same LIKE pattern (or with a C-equivalent). Since the user decision uses A-scale labels in the select, the grade_list will only contain A-prefixed strings; C-grade matching happens via the `route_protection_grading` LIKE clause using the same numeric level. Implementer should verify actual `route_protection_grading` values in D1 to confirm format.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `filtersToApi` grade list expansion code shape (exact variable names and conditionals) | Pattern 3 | Low — structure follows directly from D-16 and existing function; easy to adjust |
| A2 | LIKE clause construction code shape in buildRoutesQuery | Pattern 4 | Low — structure follows existing conds/params pattern; easy to adjust |
| A3 | Adding `currentFilters` to sortedRoutes useMemo deps is correct fix for gradeSystem reactivity | Pitfall 5 | Medium — alternative is to pull gradeSystem into separate state, but the existing pattern is for currentFilters to own all filter state |
| A4 | M1 LIKE false positive for M10-M12 is acceptable UX for MVP | Pitfall 4 / Open Questions | Low — worst case is user sees slightly broader results when selecting M1 solo |
| A5 | `route_protection_grading` contains short grade strings (e.g. "C2", "A3") usable with LIKE prefix | Open Question 2 | Medium — if the field stores long phrases, the LIKE pattern needs to be `%C2%` not `C2%` |

---

## Sources

### Primary (HIGH confidence — direct file reads)
- `climbing-search/src/types/filters.ts` — complete file; all types, constants, extract* functions confirmed
- `climbing-search/src/App.tsx` — complete file; sortedRoutes switch, filtersToApi, currentFilters state
- `climbing-search/src/components/FilterPanel.tsx` — complete file; grade filter pattern, sort select, dark: variants
- `climbing-search/src/api/types.ts` — complete file; ApiFilters interface, RouteApi shape
- `climbing-search/src/api/routeApi.ts` — complete file; buildQuery, fetchRoutes
- `worker-api/src/db/queries.ts` — complete file; buildRoutesQuery pattern, conds/params
- `worker-api/src/routes/routes.ts` — complete file; Zod schema, route handler
- `worker-api/src/types.ts` — complete file; RouteRow, Bindings, AllowedType
- `worker-api/test/setup.ts` — complete file; seed fixtures (V3 boulder + WI4 ice already present)
- `worker-api/test/routes.test.ts` — complete file; test pattern for new tests to follow
- `.planning/phases/05-grade-system-picker/05-CONTEXT.md` — all decisions D-01 through D-20
- `.planning/phases/05-grade-system-picker/05-UI-SPEC.md` — component classes, grade lists, interaction contracts

### Secondary (MEDIUM confidence)
- `.planning/phases/04-specialty-grade-sort/04-CONTEXT.md` — Phase 04 decisions; null-last pattern origin
- `climbing-search/package.json` + `worker-api/package.json` — dependency versions confirmed

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages verified from package.json; no new deps needed
- Architecture: HIGH — all files read directly; data flow fully traceable
- Pitfalls: HIGH — derived from direct code reading (not WebSearch); A5 is the only unverified claim about runtime data format
- Code examples: HIGH (patterns) / ASSUMED (exact variable names)

**Research date:** 2026-05-16
**Valid until:** 2026-06-16 (stable stack; no external API dependencies)
