---
phase: 04-specialty-grade-sort
verified: 2026-05-16T23:00:00Z
status: human_needed
score: 6/6 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Open Sort By dropdown in browser and confirm three new options are visible"
    expected: "Dropdown shows: Grade, Stars, # of Votes, Left to Right, Aid Grade (A/C), Ice Grade (WI/AI), Mixed Grade (M)"
    why_human: "Visual dropdown rendering cannot be verified programmatically"
  - test: "Search Yosemite (El Cap area), select Aid Grade (A/C) sort, Reverse unchecked"
    expected: "Aid routes appear A0/A1/A2 first, A4/A5/A6+ later; routes with no A/C grade appear at bottom"
    why_human: "Requires live data + browser interaction to observe sort order"
  - test: "Check Reverse checkbox with Aid Grade (A/C) active"
    expected: "Graded routes flip order (A5/A6 at top); ungraded routes remain at bottom — not interleaved"
    why_human: "Requires live browser interaction; Infinity sentinel behavior cannot be exercised without real route data"
  - test: "Switch back to Grade sort after using specialty sort"
    expected: "YDS sort works normally — 5.6 before 5.10d"
    why_human: "Regression check requires browser UI"
---

# Phase 4: Specialty Grade Sort Verification Report

**Phase Goal:** Add discipline-specific sort options (Aid Grade, Ice Grade, Mixed Grade) to the Sort By dropdown so aid/ice/mixed climbers can order routes by their relevant grade system instead of YDS only.
**Verified:** 2026-05-16T23:00:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Sort By dropdown shows three new options: Aid Grade (A/C), Ice Grade (WI/AI), Mixed Grade (M) | VERIFIED | FilterPanel.tsx lines 270–272: `<option value="aid_grade">Aid Grade (A/C)</option>`, `<option value="ice_grade">Ice Grade (WI/AI)</option>`, `<option value="mixed_grade">Mixed Grade (M)</option>` |
| 2 | Selecting Aid Grade (A/C) orders routes A0 < A1 < A2 < A3 < A4 < A5 < A6 | VERIFIED | `extractAidGradeNumeric` returns integer level; multiplier=+1 when `ascending=false` (default/Reverse unchecked) produces ascending numeric order. Node simulation: "5.9 A3" → 3, "A3+" → 3.5, "5.8 C2" → 2. |
| 3 | Selecting Ice Grade (WI/AI) orders routes WI1 < WI2 < WI3 < WI4 < WI5 < WI6 < WI7 | VERIFIED | `extractIceGradeNumeric` regex `/(WI\|AI)(\d+)(\+?)/` on `route_grade`. "WI4" → 4, "WI4+" → 4.5, "AI3-4" → 3. Same multiplier convention as aid. |
| 4 | Selecting Mixed Grade (M) orders routes M1 < M2 < M3 < M4 < M5 < M6+ | VERIFIED | `extractMixedGradeNumeric` regex `/M(\d+)(\+?)/`. "M6+" → 6.5, "5.9 M7" → 7. Checks both `route_grade` and `route_protection_grading`. |
| 5 | Routes without a relevant specialty grade appear at the bottom regardless of Reverse checkbox state | VERIFIED | App.tsx lines 189–191 / 197–199 / 205–207: unconditional `if (aVal === Infinity) return 1; if (bVal === Infinity) return -1;` guards fire before `multiplier * (aVal - bVal)`, making ungraded routes always last regardless of direction. |
| 6 | Reverse checkbox flips the graded routes but ungraded routes remain at bottom | VERIFIED | Multiplier formula (App.tsx lines 157–160) now includes `aid_grade`, `ice_grade`, `mixed_grade` in the grade-style branch: `ascending ? -1 : 1`. Infinity guards are unconditional (not multiplied). When Reverse is checked (`ascending=true`), multiplier becomes −1; `−1 * (aVal − bVal)` reverses graded route order. Infinity guards remain unaffected. WR-01 fix confirmed in commit 97e4ccb. |

**Score:** 6/6 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `climbing-search/src/types/filters.ts` | SortOption extended; 3 extract functions exported | VERIFIED | SortOption at line 156 includes `\| 'aid_grade' \| 'ice_grade' \| 'mixed_grade'`. Three exported functions: `extractAidGradeNumeric`, `extractIceGradeNumeric`, `extractMixedGradeNumeric` at lines 115, 132, 146. |
| `climbing-search/src/App.tsx` | Switch handles aid_grade, ice_grade, mixed_grade with Infinity sentinel | VERIFIED | Cases at lines 185, 194, 202. Import at line 8 includes all three extract functions. Infinity sentinel pattern on all 12 guard lines. |
| `climbing-search/src/components/FilterPanel.tsx` | Three new `<option>` elements in sort `<select>` | VERIFIED | Options at lines 270–272 with values `aid_grade`, `ice_grade`, `mixed_grade` and labels "Aid Grade (A/C)", "Ice Grade (WI/AI)", "Mixed Grade (M)". |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `FilterPanel.tsx` | `types/filters.ts` | `SortOption` type cast on select `onChange` | VERIFIED | Line 263: `e.target.value as SortOption` — `SortOption` is imported from `../types/filters` at line 2. New union values are included in the type. |
| `App.tsx` | `types/filters.ts` | Import of extract functions | VERIFIED | Line 8: `import { GRADE_ORDER, normalizeGrade, extractAidGradeNumeric, extractIceGradeNumeric, extractMixedGradeNumeric } from './types/filters'`. All three functions imported and called in switch cases. |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|-------------------|--------|
| `FilterPanel.tsx` sort select | `sortConfig.option` | `SortConfig` state in App.tsx, passed as prop | Yes — state bound to select value; `onChange` fires `onSortChange` to update parent state | FLOWING |
| `App.tsx` sortedRoutes | `a.route_grade`, `a.route_protection_grading` | `RouteApi` objects from D1 via Worker API fetch | Yes — these are live API fields, not hardcoded. `routeApi.fetchRoutes()` queries Worker which queries D1. | FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| TypeScript type check | `npx tsc --noEmit` | Exit 0 — no errors | PASS |
| Vite production build | `npm run build` | Exit 0 — built in 518ms | PASS |
| SortOption union includes all 7 values | `grep "SortOption" src/types/filters.ts` | Line 156 contains all 7 values | PASS |
| 3 extract functions exported | `grep -c "export function extract" src/types/filters.ts` | 3 | PASS |
| 4 grade switch cases in App.tsx | `grep -n "case '.*grade'" src/App.tsx` | grade (163), aid_grade (185), ice_grade (194), mixed_grade (202) | PASS |
| Infinity sentinel count | `grep -n "Infinity" src/App.tsx` | 12 occurrences (4 per sort case) | PASS |
| Grade extraction parse accuracy | Node simulation | "5.9 A3"→3, "A3+"→3.5, "WI4"→4, "WI4+"→4.5, "AI3-4"→3, "M6+"→6.5 | PASS |
| Sort direction default (WR-01 fix) | Multiplier formula simulation | multiplier=+1 when `ascending=false` for aid_grade → A0 before A5 | PASS |
| WR-02 fix: listener cleanup | `grep -n "return.*removeEventListener" src/utils/registerSW.ts` | Lines 38–40: cleanup function returned | PASS |
| WR-03 fix: appinstalled cleanup | `grep -n "appinstalled.*removeEventListener" src/components/InstallPrompt.tsx` | Line 41: `removeEventListener('appinstalled', ...)` in cleanup | PASS |

---

### Requirements Coverage

| Requirement ID | Source Plan | Description | Status | Evidence |
|----------------|-------------|-------------|--------|----------|
| SORT-01 | 04-01-PLAN.md | Sort By dropdown includes specialty grade options | SATISFIED | FilterPanel.tsx lines 270–272 |
| SORT-02 | 04-01-PLAN.md | Specialty grade sort with ascending/descending and null-last | SATISFIED | App.tsx sort switch + multiplier formula + Infinity guards |
| SORT-03 | 04-01-PLAN.md | Grade extraction from route_grade/route_protection_grading string fields | SATISFIED | Three extract functions in filters.ts |

**Traceability gap (WARNING):** SORT-01, SORT-02, SORT-03 are referenced in `04-01-PLAN.md` frontmatter and in ROADMAP.md but are **not defined in `.planning/REQUIREMENTS.md`**. The requirements file contains only TICK-01/02/03, TAG-01–05, and generic UI-01/02/03 IDs. SORT-01/02/03 are not listed in the traceability table. This is a documentation gap — the feature is fully implemented and the phase 4 ROADMAP.md Success Criteria are satisfied, but REQUIREMENTS.md has not been updated to include the SORT requirements IDs or Phase 04 in the traceability table.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| No anti-patterns found in modified files | — | — | — | — |

Scanned: `types/filters.ts`, `App.tsx`, `FilterPanel.tsx` — no TODO/FIXME/placeholder/return null/hardcoded empty stubs found.

---

### Code Review Warnings (from 04-REVIEW.md) — All Resolved

All three warnings from the code review were fixed in subsequent commits before this verification:

| Finding | Severity | Status |
|---------|----------|--------|
| WR-01: Specialty sort default direction inverted (harder-first instead of easier-first) | Warning | FIXED — commit 97e4ccb adds `aid_grade \| ice_grade \| mixed_grade` to grade-style multiplier branch |
| WR-02: `setupOfflineDetection` leaks online/offline event listeners on unmount | Warning | FIXED — commit f66242f returns cleanup function from `setupOfflineDetection` |
| WR-03: `appinstalled` event listener not removed on unmount in InstallPrompt | Warning | FIXED — commit c380d63 captures and removes both handlers in cleanup |

---

### Human Verification Required

**All 6 automated must-haves are VERIFIED.** The following require a running browser session to complete.

#### 1. Dropdown visual confirmation

**Test:** Run `npm run dev`, open http://localhost:5173, click the Sort By dropdown.
**Expected:** Dropdown shows all 7 options: Grade, Stars, # of Votes, Left to Right, Aid Grade (A/C), Ice Grade (WI/AI), Mixed Grade (M).
**Why human:** Visual dropdown rendering cannot be confirmed programmatically.

#### 2. Aid Grade sort in ascending (default) direction

**Test:** Search Yosemite / El Cap area, select "Aid Grade (A/C)" with Reverse unchecked.
**Expected:** Routes with A0/A1/A2 grades appear before A4/A5/A6+. Routes with no aid grade appear at the bottom.
**Why human:** Requires live D1 data and browser interaction to observe sort order.

#### 3. Reverse checkbox behavior with specialty sort

**Test:** With Aid Grade (A/C) active, check the Reverse checkbox.
**Expected:** Graded routes flip — A5/A6+ appear at top. Ungraded routes remain at bottom (not pulled to top).
**Why human:** Infinity sentinel correctness under reversal requires real route data in browser.

#### 4. YDS sort regression check

**Test:** After using specialty sort, switch back to "Grade".
**Expected:** YDS sort works correctly (5.6 before 5.10d, routes without YDS grade at bottom or mixed in per existing behavior).
**Why human:** Regression requires browser interaction.

---

### Gaps Summary

No functional gaps found. All 6 must-have truths are VERIFIED in the codebase. All 3 code review warnings (WR-01 sort direction, WR-02 and WR-03 listener leaks) were fixed in post-review commits.

One **documentation gap** (WARNING, not a blocker): SORT-01, SORT-02, SORT-03 requirement IDs are used in the plan and roadmap but are absent from `.planning/REQUIREMENTS.md`. The feature satisfies the ROADMAP.md Phase 04 Success Criteria. The REQUIREMENTS.md traceability table should be updated to add SORT-01/02/03 and Phase 04 in a future maintenance pass.

Status is `human_needed` because 4 browser-level smoke tests remain — not because automated checks found failures.

---

_Verified: 2026-05-16T23:00:00Z_
_Verifier: Claude (gsd-verifier)_
