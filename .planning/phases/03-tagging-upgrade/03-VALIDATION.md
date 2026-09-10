---
phase: 3
slug: tagging-upgrade
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-09
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 |
| **Config file** | None — pytest discovers tests from project root |
| **Quick run command** | `python3 -m pytest tagging/tests/ -q` |
| **Full suite command** | `python3 -m pytest tagging/tests/ scraping/tests/ -q` |
| **Estimated runtime** | ~5 seconds (39 existing tests pass in 4.21s) |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m pytest tagging/tests/ -q`
- **After every plan wave:** Run `python3 -m pytest tagging/tests/ scraping/tests/ -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | TAG-03 | T-03-09 | Tick text with SQL metacharacters safely escaped via sql_quote() | unit | `pytest tagging/tests/test_enrich_ticks.py::test_enrich_routes -q` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 1 | TAG-03 | T-03-09 | Route IDs cast to str() to prevent type mismatch | unit | `pytest tagging/tests/test_enrich_ticks.py::test_enrich_routes_route_id_cast_to_str -q` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 1 | TAG-01, TAG-04 | T-03-06 | PermissionDeniedError caught gracefully (no crash) | integration | `python3 tagging/benchmark_models.py --dry-run` | ❌ W0 | ⬜ pending |
| 03-03-01 | 03 | 2 | TAG-02, TAG-03 | T-03-01 | TAGGING_MODEL constant used in both create_batch_requests functions | unit | `pytest tagging/tests/ -q` (existing tests must still pass after model swap) | ✅ existing | ⬜ pending |
| 03-04-01 | 04 | 3 | TAG-04, TAG-05 | T-03-09 | All route tags validated before D1 sync | integration | `python3 -m pytest tagging/tests/ -q` | ✅ existing | ⬜ pending |
| 03-05-01 | 05 | 4 | TAG-05 | T-03-10 | Remote D1 shows 0 Washington routes after delete | manual | `wrangler d1 execute climbing-search --remote --command "SELECT COUNT(*) FROM routes WHERE path LIKE '/washington/%'" --json` — expect 0 | N/A — manual | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tagging/tests/test_enrich_ticks.py` — unit tests for `build_tick_map()` and `enrich_routes_with_tick_comments()` (created in Plan 03-01)
- [ ] `tagging/enrich_ticks.py` — main enrichment script (created in Plan 03-01)
- [ ] `tagging/benchmark_models.py` — benchmark orchestrator (created in Plan 03-02)

*Plans 03-01 and 03-02 run in Wave 1 and create all Wave 0 artifacts.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Benchmark output quality — user selects winning model | TAG-01, TAG-04 | Tag quality requires human judgment; accuracy vs cost tradeoff is subjective | User reviews `benchmark_results.json` in 03-02 checkpoint and selects model |
| Yosemite tag spot-check — sample of 20 tagged routes | TAG-04 | Tag accuracy on climbing-specific terminology requires domain expertise | User reviews 20 random routes from `data/yosemite-national-park_routes_tagged.json` in 03-04 checkpoint |
| UI verification after remote D1 push | TAG-05 (D-14) | End-to-end UI behavior requires browser testing | User opens production Cloudflare Pages URL and verifies Yosemite routes appear with tags |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
