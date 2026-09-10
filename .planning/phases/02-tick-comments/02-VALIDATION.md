# Phase 2: Tick Comments — Validation Architecture

**Source:** Derived from RESEARCH.md Validation Architecture section  
**Phase:** 02-tick-comments  
**Created:** 2026-05-09

---

## Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 + pytest-asyncio 1.3.0 |
| Config file | `pytest.ini` not found — uses pyproject.toml or inline config |
| Quick run command | `source .venv/bin/activate && python3 -m pytest scraping/tests/ -v --tb=short` |
| Full suite command | `source .venv/bin/activate && python3 -m pytest scraping/tests/ -v` |
| Baseline (pre-phase) | 22 tests pass (verified 2026-05-09) |
| Expected (post-phase) | 28 tests pass (22 prior + 6 new in test_tick_collector.py) |

---

## Requirement → Test Map

| Req ID | Behavior | Test Name | Test Type | Automated Command | Plan |
|--------|----------|-----------|-----------|-------------------|------|
| TICK-01 | `login_mp()` returns True with valid credentials | `test_login_succeeds` | integration (requires env vars) | `pytest scraping/tests/test_tick_collector.py::test_login_succeeds -x` | 02-01 (stub), 02-02 (impl) |
| TICK-01 | `login_mp()` returns False with invalid credentials | `test_login_fails_bad_creds` | unit (mock driver) | `pytest scraping/tests/test_tick_collector.py::test_login_fails_bad_creds -x` | 02-01 (stub), 02-02 (impl) |
| TICK-01 | `login_mp(driver, email, password)` function exists and accepts correct signature | `test_login_mp_signature` | unit (mock driver) | `pytest scraping/tests/test_tick_collector.py::test_login_mp_signature -x` | 02-01 (stub, xfail), 02-02 (green) |
| TICK-02 | `parse_stats` returns `list[dict]` with author/date/text | `test_parse_stats_returns_entries` | unit (fixture HTML) | `pytest scraping/tests/test_tick_collector.py::test_parse_stats_returns_entries -x` | 02-01 (stub, xfail), 02-02 (green) |
| TICK-02 | `parse_stats` applies >=15 word filter (D-01) | `test_parse_stats_word_filter` | unit (fixture HTML) | `pytest scraping/tests/test_tick_collector.py::test_parse_stats_word_filter -x` | 02-01 (stub, xfail), 02-02 (green) |
| TICK-02 | Unauthenticated stats page returns empty tick list | `test_parse_stats_empty_on_noauth` | unit (fixture HTML) | `pytest scraping/tests/test_tick_collector.py::test_parse_stats_empty_on_noauth -x` | 02-01 (green) |
| TICK-03 | `INSERT OR IGNORE` dedup — re-inserting same tick does not duplicate | `test_tick_dedup` | unit (sqlite3 in-memory) | `pytest scraping/tests/test_tick_collector.py::test_tick_dedup -x` | 02-01 (green) |
| TICK-03 | `_build_comment_rows` produces correct `parent_type='tick'` rows | `test_build_comment_rows_tick_type` | unit (import_to_d1) | `pytest scraping/tests/test_tick_collector.py::test_build_comment_rows_tick_type -x` | 02-01 (green) |
| TICK-03 | Tick rows in D1 have `parent_type='tick'` and join to routes via route_id | D1 spot-check query | integration (local D1) | `npx wrangler d1 execute climbing-search --local --command "SELECT * FROM comments WHERE parent_type='tick' LIMIT 10;"` | 02-04 (live validation) |

---

## Test Status by Wave

### Wave 1 (Plan 02-01): Schema migration + test scaffold

Tests created as part of Plan 02-01. Green tests run immediately; xfail stubs turn green after Plan 02-02.

| Test | Expected Status After Wave 1 |
|------|------------------------------|
| `test_tick_dedup` | GREEN — uses sqlite3 in-memory, no external deps |
| `test_build_comment_rows_tick_type` | GREEN — tests existing import_to_d1 code |
| `test_parse_stats_empty_on_noauth` | GREEN — current parse_stats returns "" for missing table |
| `test_parse_stats_returns_entries` | XFAIL — red stub until Plan 02-02 updates parse_stats |
| `test_parse_stats_word_filter` | XFAIL — red stub until Plan 02-02 updates parse_stats |
| `test_login_mp_signature` | XFAIL — red stub until Plan 02-02 implements login_mp |

### Wave 2 (Plan 02-02): parse_stats update + login_mp implementation

All xfail stubs from Wave 1 turn green after Plan 02-02 lands.

| Test | Expected Status After Wave 2 |
|------|------------------------------|
| `test_parse_stats_returns_entries` | GREEN |
| `test_parse_stats_word_filter` | GREEN |
| `test_login_mp_signature` | GREEN |

### Wave 4 (Plan 02-04): El Cap validation + full Yosemite run

Integration gate via wrangler query (not pytest). Pass condition defined in D-10.

| Gate | Pass Condition |
|------|----------------|
| El Cap go/no-go (D-10) | `SELECT * FROM comments WHERE parent_type='tick' LIMIT 10` returns >= 1 row with realistic data |
| Yosemite completion | `SELECT COUNT(*) FROM comments WHERE parent_type='tick'` > 0 |

---

## Sampling Rate

- **Per task commit:** `source .venv/bin/activate && python3 -m pytest scraping/tests/ -v --tb=short`
- **Per wave merge:** Same (full suite runs in ~0.15s)
- **Phase gate:** Full suite green (28 tests) + manual D1 spot-check before `/gsd-verify-work`

---

## Phase Gate Command

```bash
# Full test suite
source .venv/bin/activate && python3 -m pytest scraping/tests/ -v

# D1 tick row validation
cd worker-api && npx wrangler d1 execute climbing-search \
  --command "SELECT COUNT(*) as tick_cnt FROM comments WHERE parent_type='tick';" \
  --local

# D1 join validation
cd worker-api && npx wrangler d1 execute climbing-search \
  --command "SELECT c.comment_text FROM comments c JOIN routes r ON c.parent_id=r.route_id WHERE c.parent_type='tick' LIMIT 1;" \
  --local
```

All three must return satisfactory results before phase is considered complete.
