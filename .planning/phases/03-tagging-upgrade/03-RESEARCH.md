# Phase 3: Tagging Pipeline Upgrade — Research

**Researched:** 2026-05-09
**Domain:** OpenAI Batch API model selection, LLM prompt engineering, Cloudflare D1 import/delete, Python pipeline enrichment
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Benchmark candidates: `gpt-4o-mini` (current baseline), `gpt-5-nano`, `gpt-5-mini` — all OpenAI, same Batch API client, model string swap only
- **D-02:** Sample size: 50 routes (mix of Yosemite routes with and without tick comments)
- **D-03:** Winner selection: accuracy-first — if accuracy is equal or close, pick cheaper model. Research exact pricing for gpt-5-nano and gpt-5-mini before benchmark (batch pricing expected: gpt-5-nano ~$0.78/20K routes, gpt-5-mini TBD)
- **D-04:** Grok is ruled out for this phase — Grok-4.3 costs ~$8/20K routes vs ~$0.78–$1.43 for OpenAI options; no quality justification
- **D-05:** Pre-tagging enrichment step: query D1 for all tick comments grouped by route_id, merge into route JSON as `route_tick_comments` field (already in prompt template at line 185 of `route_area_tagging.py`)
- **D-06:** Scope: all routes that have ticks in D1 (`parent_type='tick'`) — 174 routes currently; not limited to Yosemite. Future tick collection automatically extends this.
- **D-07:** Tick inputs are treated as additional context alongside route info and area info (not a replacement)
- **D-08:** Phase 3 tags only the ~2,969 new Yosemite NP routes. Existing Nevada + WA routes keep their current v1.0 tags.
- **D-09:** Regional expansion pattern: Yosemite → Washington → others (separate future phases)
- **D-10:** Audit method: user manually spot-checks a sample of tagged Yosemite routes after benchmark run. No automated diff tooling needed.
- **D-11:** Audit timing: before full 2,969-route run — benchmark on 50, user reviews, then full run
- **D-12:** Phase 3 includes pushing Yosemite tagged data to Cloudflare remote D1 (production)
- **D-13:** After push: delete Nevada/WA data from remote D1 — production becomes Yosemite-only
- **D-14:** UI verification done by user after data push (not automated in this phase)

### Claude's Discretion

None specified — all major decisions locked.

### Deferred Ideas (OUT OF SCOPE)

- Washington scrape + tagging — next regional phase after Yosemite
- Full re-tag of Nevada/WA routes with improved model — not in scope; those regions being deleted from production anyway
- Automated tag accuracy scoring — user prefers manual spot-check for now

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TAG-01 | LLM models benchmarked on sample set — winner selected based on tag accuracy vs cost | D-01/D-03: gpt-4o-mini vs gpt-5-nano vs gpt-5-mini; pricing verified below |
| TAG-02 | Tagging pipeline migrated to winning model | Line 192 of route_area_tagging.py is the only change point; hardcoded `"gpt-4o-mini"` |
| TAG-03 | LLM prompts improved to leverage tick comment data as additional context | D-05: enrichment step feeds `route_tick_comments` field already in prompt at line 185 |
| TAG-04 | Tag accuracy audited on a sample before and after prompt improvements | D-10/D-11: manual spot-check of 50-route benchmark output by user |
| TAG-05 | Updated tagging pipeline re-run on all routes in D1 | D-08: 2,969 Yosemite routes only; full run after user approval |

</phase_requirements>

---

## Summary

Phase 3 has three distinct pipeline stages: (1) model benchmark — run 50 Yosemite routes through three models in parallel batch jobs and produce side-by-side comparison output for user review; (2) prompt enrichment — write a new enrichment script that pulls tick comment text from the local D1 `comments` table, merges it into the Yosemite route JSON `route_tick_comments` field, and produces an enriched JSON file for the full tagging run; (3) production deployment — import the enriched tagged Yosemite data to remote D1, then delete the Washington region data from remote D1.

The existing tagging pipeline (`route_area_tagging.py`) is almost entirely reusable for this phase. The model is hardcoded at line 192 (`"model": "gpt-4o-mini"`) and is the only code change needed for TAG-02. The prompt template already has the `route_tick_comments` slot at line 185 (`Comments: {route.get('route_tick_comments', '')} {' '.join(...route_comments...)}`), so the enrichment step feeds a pre-existing interface rather than requiring prompt changes. The `d1_tag_sync.py` pipeline works for any region without modification.

D1 state is fully understood from direct inspection: remote D1 has 10,951 Washington routes only (no Nevada, no Yosemite). Local D1 has 20,324 routes across WA + NV + Yosemite and 4,209 tick comments in the `comments` table. The Yosemite route JSON file exists at `data/yosemite-national-park_routes.json` (5.9MB, 517 areas, 2,966 routes). Only 21 of those routes have `route_tick_comments` populated from the scraper; the enrichment step will populate all 174 routes that have D1 tick data.

**Primary recommendation:** Write the benchmark as a self-contained script that runs three batch jobs concurrently (different model strings, same requests) and writes comparison output JSON. Write the enrichment as a standalone script that reads local D1 via sqlite3 and writes enriched JSON. Reuse existing `route_area_tagging.py` for the full tagging run (change only the model string). Use `d1_tag_sync.py` unchanged for tag sync. Import Yosemite areas+routes SQL to remote D1, then delete Washington via area path filter.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| LLM model benchmark | Local Python script | OpenAI Batch API | Submit/poll/retrieve pattern; outputs comparison JSON for user review |
| D1 tick export + route JSON enrichment | Local Python script | Local D1 (sqlite3) | Reads comments table, merges into JSON — all local, no network |
| LLM tagging (full run) | Local Python script | OpenAI Batch API | route_area_tagging.py with model string changed; same Batch API flow |
| D1 tag sync (local) | Local Python script | Local D1 (sqlite3 direct) | d1_tag_sync.py → generates SQL; sqlite3.executescript() avoids wrangler PRAGMA bug |
| Remote D1 import (Yosemite) | Local CLI (wrangler) | — | `wrangler d1 execute --remote --file` for areas+routes SQL |
| Remote D1 tag sync | Local CLI (wrangler) | — | `wrangler d1 execute --remote --file` for tag_update SQL |
| Remote D1 cleanup (delete WA) | Local CLI (wrangler) | — | `wrangler d1 execute --remote --command` DELETE with path filter |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| openai | 1.63.2 | OpenAI Batch API client | Already in venv; existing tagging pipeline uses it |
| sqlite3 | stdlib | Direct local D1 read for tick export | Avoids wrangler batch-mode PRAGMA bug (Phase 02 finding); python stdlib |
| json | stdlib | Route JSON serialization | Existing pipeline convention |
| wrangler | 4.90.0 | Remote D1 execute (import + delete) | Official Cloudflare tool; already installed |

[VERIFIED: venv/lib/python*/site-packages/openai; `npx wrangler --version`]

### Model IDs (Batch API)

| Model | Batch API Model ID | Batch Input $/1M | Batch Output $/1M | Context Window |
|-------|-------------------|-----------------|------------------|----------------|
| gpt-4o-mini (baseline) | `gpt-4o-mini` | $0.075 | $0.300 | 128K |
| gpt-5-nano | `gpt-5-nano` | $0.025 | $0.200 | 400K |
| gpt-5-mini | `gpt-5-mini` | $0.125 | $1.000 | 400K |

[CITED: developers.openai.com/api/docs/models/gpt-5-nano — batch pricing $0.025 input, $0.200 output]
[CITED: developers.openai.com/api/docs/models/gpt-5-mini — batch pricing $0.125 input, $1.00 output]
[CITED: developers.openai.com/api/docs/models/gpt-4o-mini — batch pricing $0.075 input, $0.300 output]

**Cost estimate for full 2,969-route Yosemite run** (~1.9M input tokens, ~0.7M output tokens):

| Model | Estimated Cost |
|-------|---------------|
| gpt-4o-mini | ~$0.35 |
| gpt-5-nano | ~$0.19 |
| gpt-5-mini | ~$0.93 |

**Cost for 50-route benchmark** (trivial — each model < $0.01 per run).

**Important caveat on gpt-5-mini batch access:** A community report from 2025-08-xx describes a provisioning error where `gpt-5-mini-2025-08-07-batch` returns 403 for some projects. The fix is to use the versioned snapshot ID (`gpt-5-mini-2025-08-07`) rather than the alias, or create a new project. [CITED: community.openai.com/t/batch-api-returns-error-project-does-not-have-access-to-model-gpt-5-mini-2025-08-07-batch/1356923]

The benchmark script should catch `openai.PermissionDeniedError` on batch submit and surface it clearly rather than silently failing.

---

## Architecture Patterns

### System Architecture Diagram

```
data/yosemite-national-park_routes.json (2,966 routes)
           │
           ▼
[Step 1] enrich_ticks.py
  reads: local D1 comments WHERE parent_type='tick' (4,209 ticks, 174 routes)
  writes: data/yosemite-national-park_routes_enriched.json
           │
           ├──────────────────────────────────────────────────────┐
           ▼                                                       ▼
[Step 2a] benchmark_models.py                     [Step 2b - AFTER user approval]
  50-route sample                                 route_area_tagging.py
  3 batch jobs (gpt-4o-mini, gpt-5-nano,          input: enriched JSON
                gpt-5-mini)                        model: <winner from 2a>
  output: benchmark_results.json                  output: *_tagged.json
           │                                                       │
           ▼                                                       ▼
[User review] manual spot-check             [Step 3] d1_tag_sync.py (local only)
  select winner model                         generates: tag_update_yosemite.sql
           │                                                       │
           └─────────────────────────────────────────────────────►│
                                                                   ▼
                                              [Step 4] import_to_d1.py
                                                generates: import_yosemite.sql
                                                           │
                                                           ▼
                                              [Step 5] wrangler d1 execute --remote
                                                import areas, routes, tags to remote D1
                                                           │
                                                           ▼
                                              [Step 6] wrangler d1 execute --remote
                                                DELETE FROM routes WHERE area_id IN
                                                  (SELECT area_id FROM areas WHERE
                                                   path LIKE '/washington/%')
                                                DELETE FROM areas WHERE path LIKE '/washington/%'
```

### Recommended Project Structure

New files to create (all in `tagging/`):

```
tagging/
├── enrich_ticks.py          # NEW: D1 tick export + route JSON enrichment
├── benchmark_models.py      # NEW: 3-model batch API comparison on 50 routes
├── route_area_tagging.py    # MODIFY: change model string at line 192 (and area model at line 449)
├── d1_tag_sync.py           # UNCHANGED: stage 4 tag sync
├── batch_queue.py           # UNCHANGED
└── tests/
    └── test_enrich_ticks.py # NEW: unit tests for enrichment logic
```

### Pattern 1: D1 Tick Export via sqlite3

**What:** Read tick comments from local D1 SQLite file, return dict keyed by route_id.
**When to use:** Pre-tagging enrichment step; must use direct sqlite3 (not wrangler) to avoid batch-mode PRAGMA limitations.

```python
# Source: Phase 02 SUMMARY — wrangler d1 execute batch mode limitation
import sqlite3
import glob

def load_tick_comments_from_d1() -> dict[str, str]:
    """
    Returns {route_id: concatenated_tick_text} for all routes with tick comments.
    Uses direct sqlite3 on .wrangler/state local D1 file.
    """
    db_files = glob.glob(
        "worker-api/.wrangler/state/v3/d1/miniflare-D1DatabaseObject/*.sqlite"
    )
    # Exclude metadata.sqlite
    db_path = next(f for f in db_files if "metadata" not in f)
    con = sqlite3.connect(db_path)
    rows = con.execute(
        "SELECT parent_id, GROUP_CONCAT(comment_text, ' | ') "
        "FROM comments WHERE parent_type='tick' GROUP BY parent_id"
    ).fetchall()
    con.close()
    return {row[0]: row[1] for row in rows}
```

### Pattern 2: Route JSON Enrichment

**What:** Walk the Yosemite JSON, look up each route_id in the tick dict, and overwrite (or append to) `route_tick_comments`.
**When to use:** The Yosemite JSON has 21 routes with scraper-populated `route_tick_comments` and 174 routes with D1 tick data. For routes in both sets, D1 tick data is richer (Phase 2 collected individual tick records). Strategy: overwrite with D1 data where available, preserve scraper data otherwise.

```python
# Source: direct code inspection of route_area_tagging.py line 185
def enrich_routes_with_tick_comments(data: list, tick_map: dict) -> list:
    for area in data:
        for route in area.get("routes", []):
            route_id = str(route.get("route_id", ""))
            if route_id in tick_map:
                route["route_tick_comments"] = tick_map[route_id]
            # else: preserve existing route_tick_comments from scraper (or empty string)
    return data
```

### Pattern 3: Benchmark Script (3 Parallel Batch Jobs)

**What:** Submit three OpenAI batch jobs (one per model) against the same 50-route sample, then poll all three, then write a comparison JSON.
**When to use:** TAG-01 requirement; submits then blocks until all complete (batch completion window is up to 24h but gpt-5-nano/gpt-5-mini are fast in practice).

```python
# Source: route_area_tagging.py:submit_batch() and wait_for_batch_completion()
# Pattern: each model gets its own JSONL batch; poll independently
BENCHMARK_MODELS = ["gpt-4o-mini", "gpt-5-nano", "gpt-5-mini"]

def run_benchmark(sample_routes, route_prompt):
    batch_ids = {}
    for model in BENCHMARK_MODELS:
        requests = create_batch_requests_for_model(sample_routes, route_prompt, model)
        batch_ids[model] = submit_batch(requests)

    results = {}
    for model, batch_id in batch_ids.items():
        results[model] = wait_for_batch_completion(batch_id)

    # Write side-by-side comparison
    write_benchmark_comparison(sample_routes, results, "benchmark_results.json")
```

The `create_batch_requests_for_model` function is identical to `create_batch_requests()` in `route_area_tagging.py` except it takes `model` as a parameter instead of hardcoding `"gpt-4o-mini"`.

### Pattern 4: Remote D1 Push for Import SQL

**What:** Use `wrangler d1 execute --remote --file` to execute large SQL files. Large files (>1MB) should be chunked into multiple statements, which `import_to_d1.py` already handles (100KB per INSERT batch).

```bash
# Source: CONTEXT.md canonical_refs; wrangler --help verified
npx wrangler d1 execute climbing-search --remote --file worker-api/import_yosemite.sql
npx wrangler d1 execute climbing-search --remote --file worker-api/tag_update_yosemite-national-park_routes_tagged.sql
```

The Nevada SQL file (`import_nevada_routes_tagged.sql`) is 8.3MB / 90 statements and was successfully imported via this pattern in Phase 01. The Yosemite file will be similar scale (2,966 routes vs 6,407 NV routes → estimate ~3.5MB).

### Pattern 5: Remote D1 Cleanup — Delete Washington

**What:** Delete Washington routes and areas from remote D1. Route delete must come before area delete (FK constraint on `routes.area_id`).

```sql
-- Source: VERIFIED against schema.sql (area_id FK) + remote D1 path format
-- Run via: npx wrangler d1 execute climbing-search --remote --command "..."
DELETE FROM routes WHERE area_id IN (
    SELECT area_id FROM areas WHERE path LIKE '/washington/%'
);
DELETE FROM areas WHERE path LIKE '/washington/%';
```

[VERIFIED: remote D1 path format confirmed — paths start with `/washington/` for all WA areas]
[VERIFIED: 10,951 routes and 2,033 WA areas in remote D1 — all WA, all deleted]

### Anti-Patterns to Avoid

- **Hardcoded model in benchmark:** The benchmark must parameterize the model string. Copying `create_batch_requests()` verbatim will bake in `"gpt-4o-mini"` for all three batches.
- **Using wrangler for local D1 write during enrichment:** Phase 02 established that wrangler `d1 execute --file` runs each statement in its own connection, breaking PRAGMA persistence. Use direct `sqlite3.connect().execute()` for local reads and `executescript()` for local writes.
- **Running the full 2,969-route tagging before user review:** Plans must include a checkpoint between benchmark (50 routes) and full run. The plan should require explicit user confirmation.
- **Deleting WA before Yosemite is confirmed in remote D1:** The delete step must be the last step, after Yosemite routes are visible and verified in production.
- **Forgetting Nevada in local D1 context:** Nevada exists only in local D1 (never pushed to remote). The remote D1 cleanup only needs to delete Washington (the only region currently in remote D1). [VERIFIED: remote D1 NV count = 0]
- **gpt-5-mini batch 403 error:** The Batch API provisioning bug means `gpt-5-mini` may fail for the project. The benchmark script must catch this and report the error clearly rather than silently producing empty results.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Batch API polling loop | Custom retry/sleep loop | `wait_for_batch_completion()` in route_area_tagging.py | Already handles multiple batch IDs, 3 retries, status states |
| SQL injection prevention in tag values | Custom escaping | `sql_quote()` in scraping/import_to_d1.py | Already handles apostrophe doubling; tested |
| D1 statement chunking | Custom byte counter | `chunk_updates()` in d1_tag_sync.py | Enforces 100KB limit with safety margin; 11 tests passing |
| Route/area ID resolution | Custom URL parsing | `resolve_route_d1_id()` / `resolve_area_d1_id()` in d1_tag_sync.py | Handles numeric passthrough, URL extraction, MD5 fallback |

---

## Common Pitfalls

### Pitfall 1: gpt-5-mini Batch API 403 (Project Provisioning)

**What goes wrong:** `client.batches.create(...)` raises `openai.PermissionDeniedError: Project does not have access to model gpt-5-mini-2025-08-07-batch`.
**Why it happens:** Provisioning issue affects some projects; not all projects have batch access to gpt-5 models on first use.
**How to avoid:** Wrap the batch submit in a try/except for `openai.PermissionDeniedError`. If it fires, print guidance: "Try snapshot ID `gpt-5-mini-2025-08-07` or create a new API project." The benchmark script should degrade gracefully — report partial results from the models that succeeded rather than crashing.
**Warning signs:** 403 on `client.batches.create()` rather than on the batch result retrieval.

[CITED: community.openai.com/t/batch-api-returns-error-project-does-not-have-access-to-model-gpt-5-mini-2025-08-07-batch/1356923]

### Pitfall 2: Route Tick Comments Already Partially Populated in JSON

**What goes wrong:** Enrichment script overwrites the 21 Yosemite routes that already have `route_tick_comments` from the scraper with an empty string (because those routes have no D1 tick data separately).
**Why it happens:** The scraper populated `route_tick_comments` inline for routes where it parsed tick text during scraping. The D1 `comments` table was filled by `collect_ticks.py` for 174 *different* routes (the ones visited via Selenium).
**How to avoid:** In the enrichment function, only overwrite `route_tick_comments` if `route_id in tick_map`. Otherwise preserve existing value. The 21 scraper-populated routes and 174 D1-tick routes are different sets (verified — the 21 routes have non-empty `route_tick_comments` in JSON but their IDs do not appear in the D1 tick `parent_id` column).
**Warning signs:** After enrichment, routes that previously had non-empty `route_tick_comments` now have empty string.

[VERIFIED: python3 inspection of yosemite-national-park_routes.json — 21 routes with non-empty `route_tick_comments`; D1 tick data covers 174 routes]

### Pitfall 3: Model String at Line 192 Is Not the Only Hardcode

**What goes wrong:** Developer changes model at line 192 (`create_batch_requests()`) but misses line 449 in `create_area_batch_requests()` — area tagging still uses `gpt-4o-mini`.
**Why it happens:** The model string is independently hardcoded in both `create_batch_requests()` (line 192) and `create_area_batch_requests()` (line 449).
**How to avoid:** When migrating to winner model, change both locations. Better: extract model as a module-level constant or CLI argument.
**Warning signs:** Area tags use `gpt-4o-mini` even after route model is changed.

[VERIFIED: direct code inspection of route_area_tagging.py — `"model": "gpt-4o-mini"` appears at line 192 AND line 449]

### Pitfall 4: Local vs. Remote D1 State Confusion

**What goes wrong:** Plans written as if local D1 and remote D1 are identical. In reality:
- Local D1: WA + NV + Yosemite routes, 4,209 tick comments
- Remote D1: WA only, no tick comments, no Yosemite

**Why it happens:** Phase 02 imported everything to local D1 only (direct sqlite3 write). Remote D1 was not touched in Phase 02.
**How to avoid:** All enrichment and tagging steps run against local D1 and local JSON. Remote D1 push is the final step only (import Yosemite areas + routes → sync tags → delete WA).
**Warning signs:** Any plan step that queries remote D1 for tick comments or Yosemite routes is wrong.

[VERIFIED: remote D1 query — 2,033 areas all WA, 10,951 routes all WA, 0 tick comments]

### Pitfall 5: FK Order for Remote D1 Delete

**What goes wrong:** `DELETE FROM areas WHERE path LIKE '/washington/%'` before deleting routes causes FK constraint failure.
**Why it happens:** `routes.area_id` references `areas.area_id` with FK enforcement. Deleting parent before child violates constraint.
**How to avoid:** Always delete routes first, then areas.

[VERIFIED: schema.sql — `routes.area_id TEXT NOT NULL REFERENCES areas(area_id)`]

### Pitfall 6: Batch Completion Window — gpt-5 Models Are Fast

**What goes wrong:** Plans assume 24h wait for batch results.
**Why it happens:** The batch API has a 24h completion *window* but processes much faster in practice (minutes for 50 routes, ~1-2h for 3,000 routes with current tier).
**How to avoid:** The existing `wait_for_batch_completion()` polls every 10 seconds. This is appropriate. Plans should mention the max window is 24h but execution typically completes in minutes to hours.

---

## Code Examples

### Enrich Route JSON with D1 Tick Comments

```python
# Source: direct inspection of local D1 schema + route_area_tagging.py line 185
import sqlite3, json, glob

def build_tick_map() -> dict[str, str]:
    """Read all tick comments from local D1, return dict[route_id -> concat text]."""
    db_files = glob.glob(
        "worker-api/.wrangler/state/v3/d1/miniflare-D1DatabaseObject/*.sqlite"
    )
    db_path = next(f for f in db_files if "metadata" not in f)
    con = sqlite3.connect(db_path)
    rows = con.execute(
        "SELECT parent_id, GROUP_CONCAT(comment_text, ' | ') "
        "FROM comments WHERE parent_type='tick' GROUP BY parent_id"
    ).fetchall()
    con.close()
    return {row[0]: row[1] for row in rows}

def enrich_json(input_path: str, output_path: str, tick_map: dict) -> dict:
    with open(input_path) as f:
        data = json.load(f)
    for area in data:
        for route in area.get("routes", []):
            rid = str(route.get("route_id", ""))
            if rid in tick_map:
                route["route_tick_comments"] = tick_map[rid]
    with open(output_path, "w") as f:
        json.dump(data, f)
    return data
```

### Parameterized Batch Request Creator (for Benchmark)

```python
# Source: route_area_tagging.py create_batch_requests() — extracted with model param
def create_batch_requests_for_model(routes, prompt_template, model: str):
    batch_requests = []
    for route in routes:
        input_text = f"""
Route Description: {route.get('route_description', '')}
Route Location: {route.get('route_location', '')}
Route Type: {route.get('route_type', '')}
Route Protection: {route.get('route_protection', '')}
Comments: {route.get('route_tick_comments', '')} {' '.join([c.get('comment_text', '') for c in route.get('route_comments', [])])}
"""
        request = {
            "custom_id": str(route.get("route_id")),
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": model,  # parameterized
                "messages": [
                    {"role": "system", "content": prompt_template},
                    {"role": "user", "content": input_text},
                ],
                "temperature": 0.3,
                "max_tokens": 500,
                "top_p": 0.95,
                "n": 1,
            },
        }
        batch_requests.append(request)
    return batch_requests
```

### Remote D1 Washington Delete

```bash
# Source: verified against remote D1 path format and schema.sql FK constraint
# Routes MUST be deleted before areas (FK order)
npx wrangler d1 execute climbing-search --remote \
  --command "DELETE FROM routes WHERE area_id IN (SELECT area_id FROM areas WHERE path LIKE '/washington/%');"

npx wrangler d1 execute climbing-search --remote \
  --command "DELETE FROM areas WHERE path LIKE '/washington/%';"
```

### Model Migration in route_area_tagging.py

Change two lines (both hardcoded `"model": "gpt-4o-mini"`):

```python
# Line 192 in create_batch_requests():
"model": "gpt-5-nano",   # was "gpt-4o-mini"

# Line 449 in create_area_batch_requests():
"model": "gpt-5-nano",   # was "gpt-4o-mini" — THIS IS OFTEN MISSED
```

Or extract to a module constant:

```python
TAGGING_MODEL = "gpt-5-nano"  # set at top of file; used in both functions
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| gpt-4o-mini only | gpt-5-nano or gpt-5-mini (to be selected) | Phase 3 (this phase) | Lower cost (nano) or higher accuracy (mini) |
| Empty tick comments field | D1-enriched tick comments | Phase 3 enrichment step | 174/2,966 Yosemite routes gain real user tick text as tagging context |
| Nevada + WA in remote D1 | Yosemite-only production | Phase 3 deployment | Production dataset becomes geographically coherent |

---

## Runtime State Inventory

This is not a rename/refactor phase — no runtime state changes involving renamed strings.

**Storage artifacts relevant to this phase:**

| Category | Items Found | Action Required |
|----------|-------------|-----------------|
| Stored data (local D1) | 4,209 tick comments in `comments` table; 2,966 Yosemite routes in `routes` table | Read by enrich_ticks.py; no migration |
| Stored data (remote D1) | 10,951 WA routes + 2,033 WA areas; no Yosemite, no tick comments | Yosemite import + WA delete in Phase 3 deployment |
| Live service config | None — no external service config for this phase | None |
| OS-registered state | None | None |
| Secrets/env vars | `OPENAI_API_KEY` in `.env` — used by route_area_tagging.py and benchmark script | Confirm set before running benchmark |
| Build artifacts | `data/yosemite-national-park_routes.json` (gitignored, 5.9MB) | Input to enrichment step; verify file exists before running |

---

## Open Questions

1. **Does the current OpenAI project have batch access to gpt-5-nano and gpt-5-mini?**
   - What we know: The batch provisioning error exists for some projects. No way to verify without attempting the API call.
   - What's unclear: Whether the user's specific project key has access.
   - Recommendation: The benchmark script should be the discovery point. If gpt-5-mini fails, the script should report clearly and fall back to just comparing gpt-4o-mini vs gpt-5-nano.

2. **How large will the Yosemite import SQL file be?**
   - What we know: Nevada had 6,407 routes → 8.3MB SQL. Yosemite has 2,966 routes → estimate ~3.5MB.
   - What's unclear: Whether chunking at 100KB per statement produces a file wrangler can execute in one shot.
   - Recommendation: `import_to_d1.py` already handles chunking; the resulting file will be ~90 statements similar to Nevada. The existing pattern works.

3. **Will local D1 tick data correctly match Yosemite route IDs?**
   - What we know: 174 routes have tick comments in local D1; route IDs are numeric MP IDs. Yosemite route JSON also uses numeric MP IDs in `route_id`.
   - What's unclear: Whether any route_id mismatch exists (e.g., routes where the JSON has a different ID format than what `collect_ticks.py` stored).
   - Recommendation: The enrichment script should log how many of the 174 D1 tick routes successfully matched to JSON routes. Expected: ~174 matches if IDs are consistent.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.13 | All tagging scripts | Yes | 3.13.3 | — |
| openai Python SDK | Benchmark + tagging | Yes | 1.63.2 | — |
| OPENAI_API_KEY | Benchmark + tagging | Assumed (in .env) | — | Must set before running |
| wrangler | Remote D1 push + delete | Yes | 4.90.0 | — |
| sqlite3 | Tick enrichment | Yes (stdlib) | — | — |
| data/yosemite-national-park_routes.json | Enrichment + tagging | Yes | 5.9MB, 2966 routes | Re-run Phase 02 scraper |
| local D1 with 4,209 tick comments | Enrichment | Yes (verified) | — | Re-run collect_ticks.py |

[VERIFIED: `python3 --version`, `python3 -c "import openai; print(openai.__version__)"`, `npx wrangler --version`, `ls data/yosemite-national-park_routes.json`, local D1 sqlite3 query]

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | None — pytest discovers tests from project root |
| Quick run command | `python3 -m pytest tagging/tests/ -q` |
| Full suite command | `python3 -m pytest tagging/tests/ scraping/tests/ -q` |

Current state: 39 tests pass in 4.21s.

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TAG-01 | Benchmark runs 3 models on 50-route sample | integration | `python3 tagging/benchmark_models.py --dry-run` (or a unit test of the output structure) | ❌ Wave 0 |
| TAG-02 | Model string changed in both create_batch_requests functions | unit | `pytest tagging/tests/test_enrich_ticks.py::test_model_param` | ❌ Wave 0 |
| TAG-03 | Tick comments from D1 merged into route_tick_comments field | unit | `pytest tagging/tests/test_enrich_ticks.py::test_enrich_routes` | ❌ Wave 0 |
| TAG-04 | Manual audit | manual-only | N/A | N/A — user reviews benchmark output |
| TAG-05 | All Yosemite routes have route_tags in D1 after full run | integration | `wrangler d1 execute climbing-search --command "SELECT COUNT(*) FROM routes WHERE route_tags IS NULL" --json` — expect 0 | ❌ Wave 0 (post-execution verification) |

### Wave 0 Gaps

- [ ] `tagging/tests/test_enrich_ticks.py` — unit tests for `build_tick_map()` and `enrich_routes_with_tick_comments()` using a mock sqlite3 fixture
- [ ] `tagging/enrich_ticks.py` — main enrichment script (Wave 0 creation)
- [ ] `tagging/benchmark_models.py` — benchmark orchestrator (Wave 0 creation)

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | OPENAI_API_KEY from env var (existing pattern) |
| V3 Session Management | No | No user sessions |
| V4 Access Control | No | Single-user local CLI tool |
| V5 Input Validation | Yes | `sql_quote()` in scraping/import_to_d1.py — already applied to all D1 UPDATE values via d1_tag_sync.py |
| V6 Cryptography | No | No crypto operations |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Tick comment text containing SQL metacharacters (apostrophes, quotes) | Tampering | `sql_quote()` in `chunk_updates()` — already doubles apostrophes; tested in `test_sql_escapes_special_chars_in_tag_values` |
| LLM output containing invalid JSON | Tampering | `validate_tags()` in route_area_tagging.py strips invalid tags; `json.JSONDecodeError` caught in `process_batch_results()` |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | gpt-5-nano and gpt-5-mini support `completion_window="24h"` without parameter changes vs gpt-4o-mini | Standard Stack | Benchmark submit fails; fix: remove or adjust completion_window parameter |
| A2 | The 174 routes with D1 tick data have the same numeric `route_id` format as the Yosemite JSON | Code Examples | Enrichment matches 0 routes; fix: add ID normalization (str() cast) |
| A3 | The Yosemite routes not yet in remote D1 can be imported using the same `import_to_d1.py` pipeline used for Nevada | Architecture Patterns | Import SQL fails due to schema drift; fix: re-run schema.sql migration on remote D1 first |

---

## Sources

### Primary (HIGH confidence)

- `tagging/route_area_tagging.py` — Direct code inspection: model hardcoded at line 192 (route) and line 449 (area); `route_tick_comments` slot at line 185; batch API client pattern verified
- `tagging/d1_tag_sync.py` — Direct code inspection: `chunk_updates()`, `sql_quote()`, generate pipeline confirmed
- `worker-api/schema.sql` — Direct inspection: `comments.parent_type` CHECK constraint includes `'tick'`; `routes.area_id` FK constraint; `routes.route_tick_comments` column exists
- Local D1 sqlite3 query — 4,209 tick comments; 174 distinct routes; 20,324 total routes (WA+NV+Yosemite)
- Remote D1 wrangler query — 10,951 WA routes; 2,033 WA areas; 0 NV or Yosemite; path format `/washington/...`
- [CITED: developers.openai.com/api/docs/models/gpt-5-nano] — Model ID `gpt-5-nano`, batch pricing $0.025/$0.200 per 1M tokens
- [CITED: developers.openai.com/api/docs/models/gpt-5-mini] — Model ID `gpt-5-mini`, batch pricing $0.125/$1.00 per 1M tokens
- [CITED: developers.openai.com/api/docs/models/gpt-4o-mini] — Model ID `gpt-4o-mini`, batch pricing $0.075/$0.300 per 1M tokens

### Secondary (MEDIUM confidence)

- [CITED: community.openai.com/t/batch-api-returns-error-project-does-not-have-access-to-model-gpt-5-mini-2025-08-07-batch/1356923] — gpt-5-mini batch provisioning error; snapshot ID workaround; OpenAI acknowledged as known issue
- [CITED: helicone.ai/llm-cost/provider/openai/model/gpt-5-nano-batch] — Cross-verification of gpt-5-nano batch pricing ($0.025/$0.200)
- [CITED: helicone.ai/llm-cost/provider/openai/model/gpt-5-mini-batch] — Cross-verification of gpt-5-mini batch pricing ($0.125/$1.00)

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — model IDs and pricing verified via official OpenAI docs + Helicone cross-check
- Architecture: HIGH — all patterns verified by direct code inspection of existing pipeline
- Pitfalls: HIGH — most discovered by direct code inspection (dual model hardcode, D1 state); one MEDIUM (gpt-5-mini provisioning, community-sourced)
- D1 state: HIGH — all counts verified by direct sqlite3 queries (local) and wrangler queries (remote)

**Research date:** 2026-05-09
**Valid until:** Model pricing stable for 30 days; gpt-5-mini batch provisioning fix status may change within days

---

*Phase: 3-Tagging Upgrade*
*Research completed: 2026-05-09*
