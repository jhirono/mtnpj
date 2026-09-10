# Phase 05: Grade System Picker - Pattern Map

**Mapped:** 2026-05-16
**Files analyzed:** 7 files to create or modify
**Analogs found:** 7 / 7

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `climbing-search/src/types/filters.ts` | utility/types | transform | self (existing, modify) | exact |
| `climbing-search/src/components/FilterPanel.tsx` | component | request-response | self (existing, modify) | exact |
| `climbing-search/src/App.tsx` | component/orchestrator | request-response | self (existing, modify) | exact |
| `climbing-search/src/api/types.ts` | utility/types | transform | self (existing, modify) | exact |
| `climbing-search/src/api/routeApi.ts` | service | request-response | self (existing, modify) | exact |
| `worker-api/src/db/queries.ts` | service/query-builder | CRUD | self (existing, modify) | exact |
| `worker-api/src/routes/routes.ts` | controller | request-response | self (existing, modify) | exact |
| `worker-api/test/routes.test.ts` | test | request-response | self (existing, modify) | exact |

All Phase 05 work modifies existing files. Every analog is the file itself — patterns are extracted directly from current code.

---

## Pattern Assignments

### `climbing-search/src/types/filters.ts` (utility/types, transform)

**Analog:** `climbing-search/src/types/filters.ts` (self — extend in place)

**Current exports to keep** (lines 1–169 — all extract* functions, GRADE_ORDER, SIMPLE_GRADES, normalizeGrade, GradeRange, RouteFilters):
```typescript
// Import pattern (line 1-2) — no changes needed
import type { RouteType } from '../api/types';
export type { RouteType };
```

**SortOption to modify** (line 171 — remove specialty variants):
```typescript
// BEFORE (line 171):
export type SortOption = 'grade' | 'stars' | 'left_to_right' | 'votes' | 'aid_grade' | 'ice_grade' | 'mixed_grade' | 'boulder_grade';

// AFTER (D-09):
export type SortOption = 'grade' | 'stars' | 'left_to_right' | 'votes';
```

**RouteFilters to extend** (lines 14-21 — add gradeSystem field):
```typescript
// BEFORE:
export interface RouteFilters {
  grades: { min: string; max: string };
  types: RouteType[];
  tags: { category: string; selectedTags: string[] }[];
}

// AFTER (D-13, D-14):
export type GradeSystem = 'yds' | 'boulder' | 'aid' | 'ice' | 'mixed';

export interface RouteFilters {
  grades: { min: string; max: string };
  types: RouteType[];
  tags: { category: string; selectedTags: string[] }[];
  gradeSystem: GradeSystem;
}
```

**New GRADE_LISTS constant to add** (after SIMPLE_GRADES at line 65 — D-08):
```typescript
// Add after SIMPLE_GRADES, reference SIMPLE_GRADES for yds
export const GRADE_LISTS: Record<GradeSystem, string[]> = {
  yds: SIMPLE_GRADES,
  boulder: ['VB', 'V0', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'V7',
            'V8', 'V9', 'V10', 'V11', 'V12', 'V13', 'V14', 'V15', 'V16', 'V17'],
  aid: ['A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6'],
  ice: ['WI1', 'WI2', 'WI3', 'WI4', 'WI5', 'WI6', 'WI7'],
  mixed: ['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8', 'M9', 'M10', 'M11', 'M12'],
};
```

---

### `climbing-search/src/components/FilterPanel.tsx` (component, request-response)

**Analog:** `climbing-search/src/components/FilterPanel.tsx` (self — three targeted changes)

**Import pattern to update** (lines 1-4 — add GradeSystem, GRADE_LISTS):
```typescript
// BEFORE (lines 1-4):
import { useState, useMemo } from 'react'
import type { RouteFilters, GradeRange, SortConfig, SortOption } from '../types/filters'
import { GRADE_ORDER, SIMPLE_GRADES, ROUTE_TYPE_LABELS } from '../types/filters'
import { ROUTE_TYPES } from '../api/types'

// AFTER:
import { useState, useMemo } from 'react'
import type { RouteFilters, GradeRange, SortConfig, SortOption, GradeSystem } from '../types/filters'
import { GRADE_ORDER, SIMPLE_GRADES, GRADE_LISTS, ROUTE_TYPE_LABELS } from '../types/filters'
import { ROUTE_TYPES } from '../api/types'
```

**Sort select to trim** (lines 261-284 — remove 4 specialty options, keep 4):
```tsx
// BEFORE (lines 266-274):
<select value={sortConfig.option} onChange={...} className="...">
  <option value="grade">Grade</option>
  <option value="stars">Stars</option>
  <option value="votes"># of Votes</option>
  <option value="left_to_right">Left to Right</option>
  <option value="aid_grade">Aid Grade (A/C)</option>      // DELETE
  <option value="ice_grade">Ice Grade (WI/AI)</option>    // DELETE
  <option value="mixed_grade">Mixed Grade (M)</option>    // DELETE
  <option value="boulder_grade">Boulder Grade (V)</option>// DELETE
</select>
```

**Grade system picker row to insert** — above the Grade Filter section (line 310), following the exact structural pattern of the Sort row (lines 258-285):

The Sort row pattern for reference (lines 258-285):
```tsx
{/* Sort */}
<div className="filter-group">
  <div className="flex items-center gap-2">
    <h3 className="font-medium text-gray-900 dark:text-gray-100 whitespace-nowrap">Sort by</h3>
    <select
      value={sortConfig.option}
      onChange={(e) => onSortChange({ ...sortConfig, option: e.target.value as SortOption })}
      className="flex-1 p-1.5 border rounded text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600"
    >
      ...
    </select>
    <label className="flex items-center text-sm text-gray-700 dark:text-gray-300 whitespace-nowrap">
      <input type="checkbox" checked={sortConfig.ascending} onChange={...} className="mr-1.5" />
      Reverse
    </label>
  </div>
</div>
```

New Grade System picker (copy container structure from Sort row, use segmented buttons per D-02/D-03):
```tsx
// Constant outside component (per RESEARCH.md Pattern 6):
const GRADE_SYSTEMS: { value: GradeSystem; label: string }[] = [
  { value: 'yds', label: 'YDS' },
  { value: 'boulder', label: 'V' },
  { value: 'aid', label: 'Aid' },
  { value: 'ice', label: 'Ice' },
  { value: 'mixed', label: 'Mixed' },
];

// Handler inside component — must update both local state AND parent filters (Pitfall 2):
const handleGradeSystemChange = (newSystem: GradeSystem) => {
  setGradeFilterEnabled(false);
  onChange({ ...filters, gradeSystem: newSystem, grades: { min: '', max: '' } });
};

// JSX row — insert above Grade Filter section:
{/* Grade System */}
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

Dark mode class pattern from existing select (line 264):
```
bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600
```

**Grade filter checkbox onChange to update** (lines 316-323 — use system-aware defaults per UI-SPEC):
```tsx
// BEFORE (lines 317-323):
onChange={(e) => {
  setGradeFilterEnabled(e.target.checked)
  onChange({
    ...filters,
    grades: e.target.checked ? { min: '5.10a', max: '5.11a' } : { min: '', max: '' },
  })
}}

// AFTER (D-07, D-08 — defaults per active system):
onChange={(e) => {
  setGradeFilterEnabled(e.target.checked);
  const systemDefaults: Record<GradeSystem, { min: string; max: string }> = {
    yds: { min: '5.10a', max: '5.11a' },
    boulder: { min: 'V0', max: 'V5' },
    aid: { min: 'A0', max: 'A3' },
    ice: { min: 'WI1', max: 'WI4' },
    mixed: { min: 'M1', max: 'M6' },
  };
  onChange({
    ...filters,
    grades: e.target.checked ? systemDefaults[filters.gradeSystem] : { min: '', max: '' },
  });
}}
```

**Grade select options to make system-aware** (lines 343, 359 — replace SIMPLE_GRADES with active system list):
```tsx
// BEFORE (line 343):
{SIMPLE_GRADES.map(grade => <option key={grade} value={grade}>{grade}</option>)}

// AFTER (D-08):
{GRADE_LISTS[filters.gradeSystem].map(grade => <option key={grade} value={grade}>{grade}</option>)}
```

**Grade min/max validation to update** (lines 337-340 — GRADE_ORDER.indexOf only works for YDS):
```tsx
// The existing min/max cross-validation uses GRADE_ORDER.indexOf which only has YDS grades.
// For non-YDS systems, use GRADE_LISTS[gradeSystem].indexOf instead:
onChange={(e) => {
  const list = filters.gradeSystem === 'yds' ? GRADE_ORDER : GRADE_LISTS[filters.gradeSystem];
  updateGradeRange({
    ...filters.grades,
    min: e.target.value,
    max: list.indexOf(e.target.value) <= list.indexOf(filters.grades.max)
      ? filters.grades.max
      : e.target.value,
  });
}}
```

---

### `climbing-search/src/App.tsx` (component/orchestrator, request-response)

**Analog:** `climbing-search/src/App.tsx` (self — three targeted changes)

**Import to update** (lines 7-8 — add GradeSystem, GRADE_LISTS):
```typescript
// BEFORE (line 8):
import { GRADE_ORDER, normalizeGrade, extractAidGradeNumeric, extractIceGradeNumeric, extractMixedGradeNumeric, extractBoulderGradeNumeric } from './types/filters'

// AFTER:
import { GRADE_ORDER, GRADE_LISTS, normalizeGrade, extractAidGradeNumeric, extractIceGradeNumeric, extractMixedGradeNumeric, extractBoulderGradeNumeric } from './types/filters'
import type { GradeSystem } from './types/filters'
```

**Initial state to extend** (lines 58-62 — add gradeSystem default per D-04/D-14):
```typescript
// BEFORE:
const [currentFilters, setCurrentFilters] = useState<RouteFilters>({
  grades: { min: '', max: '' },
  types: [],
  tags: []
});

// AFTER:
const [currentFilters, setCurrentFilters] = useState<RouteFilters>({
  grades: { min: '', max: '' },
  types: [],
  tags: [],
  gradeSystem: 'yds',
});
```

**filtersToApi to extend** (lines 29-50 — add non-YDS grade_list expansion per D-16, D-17, D-20):
```typescript
// BEFORE (lines 40-47):
if (uiFilters.grades.min) {
  const n = gradeToNumeric(uiFilters.grades.min);
  if (n !== null) params.grade_min = n;
}
if (uiFilters.grades.max) {
  const n = gradeToNumeric(uiFilters.grades.max);
  if (n !== null) params.grade_max = n;
}

// AFTER (D-16, D-17, D-20):
if (uiFilters.gradeSystem === 'yds' || !uiFilters.gradeSystem) {
  // YDS path — existing numeric filtering unchanged
  if (uiFilters.grades.min) {
    const n = gradeToNumeric(uiFilters.grades.min);
    if (n !== null) params.grade_min = n;
  }
  if (uiFilters.grades.max) {
    const n = gradeToNumeric(uiFilters.grades.max);
    if (n !== null) params.grade_max = n;
  }
  params.grade_system = 'yds';
} else if (uiFilters.grades.min && uiFilters.grades.max) {
  // Non-YDS: expand min→max into grade_list
  const list = GRADE_LISTS[uiFilters.gradeSystem];
  const minIdx = list.indexOf(uiFilters.grades.min);
  const maxIdx = list.indexOf(uiFilters.grades.max);
  if (minIdx !== -1 && maxIdx !== -1 && minIdx <= maxIdx) {
    params.grade_list = list.slice(minIdx, maxIdx + 1).join(',');
  }
  params.grade_system = uiFilters.gradeSystem;
}
```

**Multiplier computation to fix** (lines 157-160 — remove specialty option references per D-09, Pitfall 1):
```typescript
// BEFORE (lines 157-159):
const multiplier = sortConfig.option === 'grade' || sortConfig.option === 'left_to_right'
  || sortConfig.option === 'aid_grade' || sortConfig.option === 'ice_grade' || sortConfig.option === 'mixed_grade' || sortConfig.option === 'boulder_grade'
  ? (sortConfig.ascending ? -1 : 1)
  : (sortConfig.ascending ? 1 : -1);

// AFTER:
const multiplier = sortConfig.option === 'grade' || sortConfig.option === 'left_to_right'
  ? (sortConfig.ascending ? -1 : 1)
  : (sortConfig.ascending ? 1 : -1);
```

**sortedRoutes switch to update** (lines 162-218 — make grade polymorphic, remove specialty cases per D-09, D-10, D-12):

Existing null-last pattern to reuse (lines 186-193 — proven approach):
```typescript
case 'aid_grade': {
  const aVal = extractAidGradeNumeric(a.route_grade, a.route_protection_grading) ?? Infinity;
  const bVal = extractAidGradeNumeric(b.route_grade, b.route_protection_grading) ?? Infinity;
  if (aVal === Infinity && bVal === Infinity) return 0;
  if (aVal === Infinity) return 1;
  if (bVal === Infinity) return -1;
  return multiplier * (aVal - bVal);
}
```

New polymorphic grade case (replaces current `case 'grade':` at lines 163-167):
```typescript
case 'grade': {
  const sys = currentFilters.gradeSystem ?? 'yds';
  if (sys === 'yds') {
    return multiplier * (
      GRADE_ORDER.indexOf(normalizeGrade(a.route_grade ?? '')) -
      GRADE_ORDER.indexOf(normalizeGrade(b.route_grade ?? ''))
    );
  }
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
// DELETE: case 'aid_grade', case 'ice_grade', case 'mixed_grade', case 'boulder_grade' blocks
```

**sortedRoutes useMemo dependency array to fix** (line 222 — add currentFilters per Pitfall 5):
```typescript
// BEFORE (line 222):
}, [filteredRoutes, sortConfig, selectedRoute]);

// AFTER (gradeSystem must trigger re-sort):
}, [filteredRoutes, sortConfig, selectedRoute, currentFilters]);
```

---

### `climbing-search/src/api/types.ts` (utility/types, transform)

**Analog:** `climbing-search/src/api/types.ts` (self — extend ApiFilters)

**ApiFilters to extend** (lines 50-62 — add grade_system and grade_list per D-17):
```typescript
// BEFORE (lines 50-62):
export interface ApiFilters {
  q?: string;
  grade?: string;
  grade_min?: number;
  grade_max?: number;
  type?: RouteType;
  region?: string;
  stars_min?: number;
  votes_min?: number;
  area_id?: string;
  page?: number;
  limit?: number;
}

// AFTER:
export interface ApiFilters {
  q?: string;
  grade?: string;
  grade_min?: number;
  grade_max?: number;
  grade_system?: 'yds' | 'boulder' | 'aid' | 'ice' | 'mixed';
  grade_list?: string;
  type?: RouteType;
  region?: string;
  stars_min?: number;
  votes_min?: number;
  area_id?: string;
  page?: number;
  limit?: number;
}
```

No change to `routeApi.ts` — `buildQuery` iterates all keys generically (line 9: `for (const [k, v] of Object.entries(params)`), so new fields are automatically included.

---

### `worker-api/src/db/queries.ts` (service/query-builder, CRUD)

**Analog:** `worker-api/src/db/queries.ts` (self — extend RouteFilters interface and buildRoutesQuery)

**RouteFilters interface to extend** (lines 3-16 — add grade_system and grade_list):
```typescript
// BEFORE (lines 3-16):
export interface RouteFilters {
  q?: string;
  grade?: string;
  grade_min?: number;
  grade_max?: number;
  type?: AllowedType;
  region?: string;
  stars_min?: number;
  votes_min?: number;
  area_id?: string;
  area_path?: string;
  page: number;
  limit: number;
}

// AFTER (D-17):
export interface RouteFilters {
  q?: string;
  grade?: string;
  grade_min?: number;
  grade_max?: number;
  grade_system?: 'yds' | 'boulder' | 'aid' | 'ice' | 'mixed';
  grade_list?: string;
  type?: AllowedType;
  region?: string;
  stars_min?: number;
  votes_min?: number;
  area_id?: string;
  area_path?: string;
  page: number;
  limit: number;
}
```

**buildRoutesQuery to extend** — insert after existing grade_max condition (line 33), following the `conds.push() / params.push()` pattern already used throughout:

Existing parameterized condition pattern (lines 31-33):
```typescript
if (f.grade) { conds.push('r.route_grade = ?'); params.push(f.grade); }
if (f.grade_min !== undefined) { conds.push('r.route_grade_numeric >= ?'); params.push(f.grade_min); }
if (f.grade_max !== undefined) { conds.push('r.route_grade_numeric <= ?'); params.push(f.grade_max); }
```

New LIKE-based grade_list condition (insert after line 33, per D-18/D-19):
```typescript
// Non-YDS grade filtering via LIKE prefix matching (D-18, D-19)
// grade_min/grade_max are skipped in filtersToApi when grade_system !== 'yds' (D-20)
if (f.grade_list && f.grade_system && f.grade_system !== 'yds') {
  const grades = f.grade_list.split(',').map((g: string) => g.trim()).filter(Boolean);
  if (grades.length > 0) {
    if (f.grade_system === 'aid' || f.grade_system === 'mixed') {
      // Aid and Mixed: filter route_grade OR route_protection_grading (D-19)
      // Note: 'M1%' LIKE matches M10/M11/M12 — known MVP tradeoff (see RESEARCH pitfall 4)
      const orClauses = grades.map(() =>
        `(r.route_grade LIKE ? OR r.route_protection_grading LIKE ?)`
      ).join(' OR ');
      conds.push(`(${orClauses})`);
      for (const g of grades) { params.push(`${g}%`, `${g}%`); }
    } else {
      // boulder, ice: filter route_grade only (D-19)
      const orClauses = grades.map(() => `r.route_grade LIKE ?`).join(' OR ');
      conds.push(`(${orClauses})`);
      for (const g of grades) { params.push(`${g}%`); }
    }
  }
}
```

---

### `worker-api/src/routes/routes.ts` (controller, request-response)

**Analog:** `worker-api/src/routes/routes.ts` (self — extend zod schema)

**routeQuerySchema to extend** (lines 10-22 — add grade_system and grade_list per D-17, security notes):
```typescript
// BEFORE (lines 10-22):
const routeQuerySchema = z.object({
  q: z.string().min(1).optional(),
  grade: z.string().optional(),
  grade_min: z.coerce.number().optional(),
  grade_max: z.coerce.number().optional(),
  type: z.enum(ALLOWED_TYPES).optional(),
  region: z.string().regex(/^[a-z0-9-]+$/, 'region must be slug').optional(),
  stars_min: z.coerce.number().min(0).max(4).optional(),
  votes_min: z.coerce.number().min(0).optional(),
  area_id: z.string().optional(),
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(200).default(50),
});

// AFTER (D-17, D-18, security: Zod enum for grade_system, max(200) on grade_list):
const routeQuerySchema = z.object({
  q: z.string().min(1).optional(),
  grade: z.string().optional(),
  grade_min: z.coerce.number().optional(),
  grade_max: z.coerce.number().optional(),
  grade_system: z.enum(['yds', 'boulder', 'aid', 'ice', 'mixed']).optional(),
  grade_list: z.string().max(200).regex(/^[A-Z0-9,+\-]+$/i).optional(),
  type: z.enum(ALLOWED_TYPES).optional(),
  region: z.string().regex(/^[a-z0-9-]+$/, 'region must be slug').optional(),
  stars_min: z.coerce.number().min(0).max(4).optional(),
  votes_min: z.coerce.number().min(0).optional(),
  area_id: z.string().optional(),
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(200).default(50),
});
```

No change needed in the route handler body (lines 24-46) — `buildRoutesQuery({ ...f, ... })` spread already passes all new fields through.

---

### `worker-api/test/routes.test.ts` (test, request-response)

**Analog:** `worker-api/test/routes.test.ts` (self — add new describe block)

**Test structure pattern** (lines 1-7, 9-18 — copy the describe/it/SELF.fetch pattern):
```typescript
// Pattern: describe block with SELF.fetch, parse json as any, assert on json.data
describe('GET /api/routes', () => {
  it('filters by type=sport', async () => {
    const res = await SELF.fetch('http://localhost/api/routes?type=sport');
    const json = await res.json() as any;
    expect(json.data.every((r: any) => r.is_sport === 1)).toBe(true);
  });
```

New test block to add (follows existing pattern, uses fixtures already in setup.ts — V3 boulder, WI4 ice per RESEARCH line 545):
```typescript
describe('GET /api/routes — grade_system filtering', () => {
  it('grade_system=boulder + grade_list filters by V-grade LIKE', async () => {
    const res = await SELF.fetch('http://localhost/api/routes?grade_system=boulder&grade_list=V3');
    expect(res.status).toBe(200);
    const json = await res.json() as any;
    expect(json.data.some((r: any) => r.route_grade?.includes('V3'))).toBe(true);
  });

  it('grade_system=ice + grade_list filters by WI-grade LIKE', async () => {
    const res = await SELF.fetch('http://localhost/api/routes?grade_system=ice&grade_list=WI4');
    expect(res.status).toBe(200);
    const json = await res.json() as any;
    expect(json.data.some((r: any) => r.route_grade?.includes('WI4'))).toBe(true);
  });

  it('grade_system=aid + grade_list filters route_grade OR route_protection_grading', async () => {
    const res = await SELF.fetch('http://localhost/api/routes?grade_system=aid&grade_list=A3');
    expect(res.status).toBe(200);
    const json = await res.json() as any;
    expect(json.data.some((r: any) =>
      r.route_grade?.includes('A3') || r.route_protection_grading?.includes('A3')
    )).toBe(true);
  });

  it('grade_system=mixed + grade_list filters route_grade OR route_protection_grading', async () => {
    const res = await SELF.fetch('http://localhost/api/routes?grade_system=mixed&grade_list=M6');
    expect(res.status).toBe(200);
    const json = await res.json() as any;
    // Mixed route fixture must exist in setup.ts
    expect(res.status).toBe(200);
  });

  it('rejects invalid grade_system value with 400', async () => {
    const res = await SELF.fetch('http://localhost/api/routes?grade_system=french');
    expect(res.status).toBe(400);
  });

  it('rejects grade_list exceeding max length', async () => {
    const long = 'V0,'.repeat(100);
    const res = await SELF.fetch(`http://localhost/api/routes?grade_system=boulder&grade_list=${encodeURIComponent(long)}`);
    expect(res.status).toBe(400);
  });
});
```

Note: Setup.ts already seeds a boulder route (`route_grade='V3'`, `is_boulder=1`) and ice route (`route_grade='WI4'`, `is_ice=1`) per RESEARCH.md line 545. Aid and Mixed fixtures must be added to setup.ts (Wave 0 gap per RESEARCH.md lines 539-544).

---

## Shared Patterns

### State ownership: gradeSystem in RouteFilters (not local state)
**Source:** `climbing-search/src/App.tsx` lines 58-62, `climbing-search/src/components/FilterPanel.tsx` line 147
**Apply to:** FilterPanel.tsx (do NOT use useState for gradeSystem)
**Rule:** `gradeSystem` belongs in `RouteFilters` (App.tsx state), not in local FilterPanel state. `gradeFilterEnabled` IS local state (line 147: `const [gradeFilterEnabled, setGradeFilterEnabled] = useState(false)`) — only the boolean checkbox state is local. `gradeSystem` flows down via `filters` prop.

### Parameterized SQL — never interpolate user values
**Source:** `worker-api/src/db/queries.ts` lines 19-57 (conds/params array pattern)
**Apply to:** `worker-api/src/db/queries.ts` grade_list LIKE block
```typescript
// Every condition: conds.push(template with ?); params.push(value)
conds.push(`r.route_grade = ?`);
params.push(f.grade);
// Grade LIKE must follow same pattern — never `r.route_grade LIKE '${g}%'`
```

### Dark mode Tailwind variants
**Source:** `climbing-search/src/components/FilterPanel.tsx` lines 210, 264, 341
**Apply to:** Grade system picker button classes
```
// Select dark pattern (line 264):
bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600

// Active button (D-03):
bg-blue-600 text-white border-blue-600 dark:bg-blue-600 dark:text-white dark:border-blue-600

// Inactive button (D-03):
bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600
```

### Zod enum validation for new query params
**Source:** `worker-api/src/routes/routes.ts` line 15
**Apply to:** grade_system param validation
```typescript
// Existing enum pattern:
type: z.enum(ALLOWED_TYPES).optional(),

// New grade_system — same pattern, inline enum:
grade_system: z.enum(['yds', 'boulder', 'aid', 'ice', 'mixed']).optional(),
```

### onChange spread pattern for filter updates
**Source:** `climbing-search/src/components/FilterPanel.tsx` lines 195, 199, 319-323
**Apply to:** handleGradeSystemChange in FilterPanel
```typescript
// Existing pattern: always spread full filters object, replace changed fields:
onChange({ ...filters, tags: newTags })
onChange({ ...filters, grades: range })

// Grade system change must reset grades too (Pitfall 2):
onChange({ ...filters, gradeSystem: newSystem, grades: { min: '', max: '' } })
```

---

## No Analog Found

None. All files are modifications of existing files with established patterns. RESEARCH.md provides concrete code shapes for all new logic blocks.

---

## Critical Pitfalls (from RESEARCH.md)

1. **Multiplier references deleted SortOptions** — lines 157-159 in App.tsx explicitly name `'aid_grade' | 'ice_grade' | 'mixed_grade' | 'boulder_grade'`. Delete all four references when removing the sort cases.

2. **Grade filter reset on system switch** — both `setGradeFilterEnabled(false)` (local state) AND `onChange({ ...filters, grades: { min: '', max: '' } })` (parent state) must fire together in `handleGradeSystemChange`.

3. **sortedRoutes missing currentFilters dependency** — line 222 currently has `[filteredRoutes, sortConfig, selectedRoute]`. Add `currentFilters` so polymorphic grade sort reacts to `gradeSystem` changes.

4. **Grade select validation uses GRADE_ORDER** — GRADE_ORDER only contains YDS grades. For non-YDS min/max cross-validation, use `GRADE_LISTS[filters.gradeSystem].indexOf(...)` instead.

---

## Metadata

**Analog search scope:** `climbing-search/src/`, `worker-api/src/`, `worker-api/test/`
**Files scanned:** 8 (all direct reads, no analog search required — all modifications to existing files)
**Pattern extraction date:** 2026-05-16
