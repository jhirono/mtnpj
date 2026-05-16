---
phase: 04-specialty-grade-sort
reviewed: 2026-05-16T00:00:00Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - climbing-search/src/types/filters.ts
  - climbing-search/src/App.tsx
  - climbing-search/src/components/FilterPanel.tsx
  - climbing-search/src/components/InstallPrompt.tsx
  - climbing-search/src/components/OfflineIndicator.tsx
  - climbing-search/src/utils/registerSW.ts
findings:
  critical: 0
  warning: 3
  info: 3
  total: 6
status: issues_found
---

# Phase 04: Code Review Report

**Reviewed:** 2026-05-16
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

Phase 04 added three specialty sort options (Aid Grade A/C, Ice Grade WI/AI, Mixed Grade M) as client-side regex-based sorts on `route_grade` and `route_protection_grading` string fields. The extraction functions in `filters.ts` are individually correct (regex coverage, Infinity sentinel, `+` suffix handling). However, a multiplier formula inconsistency in `App.tsx` causes all three specialty sorts to default to **harder grades first**, which is the opposite of the existing `grade` sort default. Two secondary warnings concern event listener leaks introduced alongside this feature. Three info-level items cover dead code and debug artifacts.

---

## Warnings

### WR-01: Specialty sort default direction is inverted relative to grade sort

**File:** `climbing-search/src/App.tsx:157-208`

**Issue:** The `multiplier` formula at line 157 uses two different conventions:
- For `grade` and `left_to_right`: `ascending ? -1 : 1` — default (`ascending=false`) → `+1` → **easier grades first**
- For everything else (stars, votes, and the three new specialty sorts): `ascending ? 1 : -1` — default → `-1`

Stars and votes are correct with the inverted formula because they use `return -multiplier * (bVal - aVal)` (double negation). The specialty sort cases use `return multiplier * (aVal - bVal)` — no double negation — so they inherit the raw inverted multiplier.

Tracing with concrete values:
```
// aid_grade, ascending=false (default, "Reverse" unchecked)
multiplier = -1
aVal = 1  (A1 route)
bVal = 5  (A5 route)
return (-1) * (1 - 5) = (-1) * (-4) = +4  → b (A5) sorts before a (A1)
```
Ungraded routes (Infinity) correctly sort last, but among graded routes the order is **A5, A4, A3 … A0** instead of **A0, A1 … A5**.

A user opening "Aid Grade (A/C)" sort without checking "Reverse" will see the hardest aid routes at the top. The `grade` sort under identical conditions shows the easiest YDS routes at the top. This is a user-visible logic inversion on all three new sort options.

**Fix:** Add `'aid_grade' | 'ice_grade' | 'mixed_grade'` to the grade-style multiplier branch so all grade-based sorts share the same convention:

```typescript
// App.tsx line 157
const multiplier =
  sortConfig.option === 'grade' ||
  sortConfig.option === 'left_to_right' ||
  sortConfig.option === 'aid_grade' ||
  sortConfig.option === 'ice_grade' ||
  sortConfig.option === 'mixed_grade'
    ? (sortConfig.ascending ? -1 : 1)
    : (sortConfig.ascending ? 1 : -1);
```

With this fix the specialty sort cases (lines 184–208) need no other changes; `multiplier * (aVal - bVal)` with `multiplier=+1` (default) will produce ascending order (A0 → A5).

---

### WR-02: `setupOfflineDetection` leaks `online`/`offline` event listeners on unmount

**File:** `climbing-search/src/utils/registerSW.ts:26-33`

**Issue:** `setupOfflineDetection` registers two `window` event listeners but returns nothing, so the caller cannot remove them. `OfflineIndicator`'s `useEffect` (line 10-15 of `OfflineIndicator.tsx`) has no cleanup function, meaning the listeners are added once and remain for the lifetime of the `window` object. If the component ever unmounts and remounts (e.g., hot-module replacement in development, or conditional rendering added in future), duplicate listeners will accumulate, each calling `setIsOffline` on the stale component instance.

**Fix:** Return a cleanup function from `setupOfflineDetection` and call it from the effect:

```typescript
// registerSW.ts
export function setupOfflineDetection(callback: (isOnline: boolean) => void): () => void {
  callback(navigator.onLine);
  const onOnline  = () => callback(true);
  const onOffline = () => callback(false);
  window.addEventListener('online',  onOnline);
  window.addEventListener('offline', onOffline);
  return () => {
    window.removeEventListener('online',  onOnline);
    window.removeEventListener('offline', onOffline);
  };
}

// OfflineIndicator.tsx
useEffect(() => {
  return setupOfflineDetection((isOnline) => setIsOffline(!isOnline));
}, []);
```

---

### WR-03: `appinstalled` event listener is not removed on unmount in `InstallPrompt`

**File:** `climbing-search/src/components/InstallPrompt.tsx:33-41`

**Issue:** The `useEffect` cleanup at line 38-40 removes the `beforeinstallprompt` listener but not the `appinstalled` listener added at line 33. The `appinstalled` listener captures `setIsInstalled` and `setInstallPrompt` from its closure; if the component unmounts and the event fires later, React will call `setState` on an unmounted component (triggers a React warning and may cause unexpected state behaviour in future React versions).

**Fix:** Capture the handler reference so it can be removed:

```typescript
useEffect(() => {
  if (window.matchMedia('(display-mode: standalone)').matches) {
    setIsInstalled(true);
    return;
  }

  const handleBeforeInstallPrompt = (e: Event) => {
    e.preventDefault();
    setInstallPrompt(e as BeforeInstallPromptEvent);
  };
  const handleAppInstalled = () => {
    setIsInstalled(true);
    setInstallPrompt(null);
  };

  window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
  window.addEventListener('appinstalled', handleAppInstalled);

  return () => {
    window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.removeEventListener('appinstalled', handleAppInstalled);
  };
}, []);
```

---

## Info

### IN-01: `extractAidGradeNumeric` and `extractMixedGradeNumeric` loop over `route_protection_grading` but it never contains aid/mixed grades

**File:** `climbing-search/src/types/filters.ts:117-122` and `148-153`

**Issue:** Both functions iterate `[routeGrade, protectionGrading]` to find aid/mixed grades. However, the scraper (`scrape_async.py` line 355-400) stores only `PG-13`, `PG`, `R`, or `X` in `route_protection_grading`. Aid, ice, and mixed grades are embedded in `route_grade` (e.g., `"5.8 A3"`, `"WI4+ 5.9"`). The second loop iteration — checking `protectionGrading` against `AID_RE` / `MIXED_RE` — will never produce a match and is dead code.

The code works correctly (returns the right value from the `routeGrade` arm), but the `protectionGrading` parameter and loop iteration are misleading. The JSDoc comments for both functions claim to check both fields, which is inaccurate.

**Fix:** Drop the `protectionGrading` parameter and loop; check only `routeGrade`. Update the JSDoc accordingly. This also makes the function signatures consistent with `extractIceGradeNumeric`, which already takes only `routeGrade`.

```typescript
export function extractAidGradeNumeric(routeGrade: string | null): number | null {
  const AID_RE = /([AC])(\d+)(\+?)/;
  if (!routeGrade) return null;
  const m = routeGrade.match(AID_RE);
  return m ? parseInt(m[2]) + (m[3] === '+' ? 0.5 : 0) : null;
}
```

Update call sites in `App.tsx` lines 185 and 202 to drop the second argument.

---

### IN-02: Debug `console.log` statements left in production paths

**File:** `climbing-search/src/utils/registerSW.ts:13` and `climbing-search/src/components/InstallPrompt.tsx:53, 55`

**Issue:** Three `console.log` calls remain in code that runs in production:
- `registerSW.ts:13` — logs service worker scope on every page load.
- `InstallPrompt.tsx:53` — logs "User accepted the install prompt".
- `InstallPrompt.tsx:55` — logs "User dismissed the install prompt".

These emit to the browser console in production builds. The SW registration error on line 16 (`console.error`) is appropriate to keep.

**Fix:** Remove the three `console.log` calls. If install outcome tracking is wanted, use an analytics call instead of a console statement.

---

### IN-03: `MIXED_RE` silently truncates range grades (`M4-5`) to the lower bound

**File:** `climbing-search/src/types/filters.ts:147`

**Issue:** The scraper accepts mixed grades like `M4-5` (range notation, `_MIXED_GRADE_RE = r"^M\d+[-+]?\d*$"`). The frontend regex `MIXED_RE = /M(\d+)(\+?)/` captures only the first digit group, so `M4-5` sorts as `M4`. A route graded `M4-5` might feel closer to `M5` in practice, but will sort with `M4` routes.

This is not wrong, but the JSDoc comment at line 143 says the regex "matches M1-M12+" without mentioning range grades. There is no data loss; sort position is simply at the lower bound of the range.

**Fix:** Add a note to the JSDoc that range grades (`M4-5`) are sorted by their lower value, or extend the regex to capture and average/round the range. A doc-only fix is sufficient:

```typescript
/**
 * ...
 * Range grades (e.g. M4-5) are sorted by their lower bound (M4).
 * Returns null if no mixed grade found in either field.
 */
```

---

_Reviewed: 2026-05-16_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
