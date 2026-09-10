---
phase: 5
slug: grade-system-picker
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-16
---

# Phase 05 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest 4.1.5 + @cloudflare/vitest-pool-workers |
| **Config file** | `worker-api/vitest.config.ts` |
| **Quick run command** | `cd worker-api && npm test` |
| **Full suite command** | `cd worker-api && npm test` |
| **Estimated runtime** | ~15 seconds |
| **Frontend type check** | `cd climbing-search && npx tsc --noEmit` |

---

## Sampling Rate

- **After every task commit:** Run `cd worker-api && npm test` (worker side); `cd climbing-search && npx tsc --noEmit` (frontend types)
- **After every plan wave:** Run full worker test suite
- **Before `/gsd-verify-work`:** All worker tests green + TypeScript compiles clean
- **Max feedback latency:** ~15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 0 | D-13, D-14 | — | N/A | unit (tsc) | `cd climbing-search && npx tsc --noEmit` | ✅ | ⬜ pending |
| 05-01-02 | 01 | 0 | D-08 | — | N/A | unit (tsc) | `cd climbing-search && npx tsc --noEmit` | ✅ | ⬜ pending |
| 05-02-01 | 02 | 0 | D-18 (boulder) | T-05-01 | SQL injection via grade_list blocked by parameterized LIKE | integration | `cd worker-api && npm test` | ❌ Wave 0 | ⬜ pending |
| 05-02-02 | 02 | 0 | D-18 (ice) | T-05-01 | SQL injection via grade_list blocked by parameterized LIKE | integration | `cd worker-api && npm test` | ❌ Wave 0 | ⬜ pending |
| 05-02-03 | 02 | 0 | D-19 (aid) | T-05-01 | SQL injection via grade_list blocked by parameterized LIKE | integration | `cd worker-api && npm test` | ❌ Wave 0 | ⬜ pending |
| 05-02-04 | 02 | 0 | D-19 (mixed) | T-05-01 | SQL injection via grade_list blocked by parameterized LIKE | integration | `cd worker-api && npm test` | ❌ Wave 0 | ⬜ pending |
| 05-02-05 | 02 | 0 | D-20 | — | N/A | integration | `cd worker-api && npm test` | ❌ Wave 0 | ⬜ pending |
| 05-03-01 | 03 | 1 | D-09 | — | N/A | unit (tsc) | `cd climbing-search && npx tsc --noEmit` | ✅ (after change) | ⬜ pending |
| 05-03-02 | 03 | 1 | D-10, D-12 | — | N/A | manual | manual UI test | manual-only | ⬜ pending |
| 05-04-01 | 04 | 1 | D-17 | T-05-02 | grade_system=yds → existing path unchanged | integration | `cd worker-api && npm test` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `worker-api/test/setup.ts` — add aid route fixture: `route_grade='A3'`, `route_protection_grading='C2'`, `is_aid=1`
- [ ] `worker-api/test/setup.ts` — add mixed route fixture: `route_grade='M6'`, `is_mixed=1`
- [ ] `worker-api/test/routes.test.ts` — test: `grade_system=boulder&grade_list=V3` returns boulder route
- [ ] `worker-api/test/routes.test.ts` — test: `grade_system=ice&grade_list=WI4` returns ice route
- [ ] `worker-api/test/routes.test.ts` — test: `grade_system=aid&grade_list=A3` returns aid route (route_grade OR route_protection_grading)
- [ ] `worker-api/test/routes.test.ts` — test: `grade_system=mixed&grade_list=M6` returns mixed route
- [ ] `worker-api/test/routes.test.ts` — test: `grade_system=yds` skips grade_list, uses grade_min/grade_max numeric path

Note: setup.ts already seeds a boulder route (V3, line 106) and ice route (WI4, line 107) — only aid and mixed fixtures need to be added.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Null-last sort preserved for all grade systems | D-12 | No client-side sort test infra | Switch to boulder system, set Sort By to "Grade", verify routes without V grades appear at bottom |
| Grade filter resets on system switch | D-07 | FilterPanel state interaction | Select V3–V8, switch to Aid, confirm grade filter unchecked + selects show A-scale |
| Dark mode picker rendering | D-03 | Visual verification | Toggle dark mode, verify active button is `bg-blue-600` and inactive buttons are gray-700 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
