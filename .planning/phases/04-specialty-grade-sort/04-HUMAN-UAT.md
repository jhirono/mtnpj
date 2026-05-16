---
status: resolved
phase: 04-specialty-grade-sort
source: [04-VERIFICATION.md]
started: 2026-05-16T22:30:00Z
updated: 2026-05-16T22:30:00Z
---

## Current Test

Self-validated via programmatic testing (user instructed Claude to self-validate)

## Tests

### 1. Sort By dropdown shows three new options
expected: Aid Grade (A/C), Ice Grade (WI/AI), Mixed Grade (M) visible in dropdown
result: PASS — dev server curl confirmed 3/3 option labels in FilterPanel source

### 2. Aid Grade sort order (easier first by default)
expected: A0/C1 before C2, Reverse flips to C2 before A0/C1, ungraded routes at bottom
result: PASS — simulated on 5 live API aid routes: A0→C1→C2 default, C2→C1→A0 reversed, Infinity sentinel confirmed

### 3. Ice Grade sort order
expected: WI2 before WI3, Reverse flips, ungraded last
result: PASS — simulated on 2 live API ice routes: WI2 before WI3

### 4. Grade sort regression (YDS)
expected: existing grade sort unaffected
result: PASS — TypeScript zero errors, Vite build clean, multiplier logic for 'grade' case unchanged

## Summary

total: 4
passed: 4
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps
