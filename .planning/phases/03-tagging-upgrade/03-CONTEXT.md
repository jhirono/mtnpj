# Phase 3: Tagging Upgrade - Context

**Gathered:** 2026-05-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Benchmark LLM models for route tagging, improve prompts with tick comment context, tag all new Yosemite NP routes, push to Cloudflare remote D1, and clean up Nevada/WA data from production.

**In scope:**
- LLM benchmark: gpt-4o-mini (baseline) vs gpt-5-nano vs gpt-5-mini on 50 sample routes
- Pre-tagging D1 enrichment step: export tick comments per route_id and merge into route JSON
- Prompt improvement: incorporate tick comment text as tagging context
- Tag new Yosemite NP routes (~2,969) with upgraded model + enriched prompt
- Manual spot-check audit by user before full run
- Push tagged Yosemite data to Cloudflare remote D1
- Delete Nevada/WA data from remote D1 (Yosemite-only dataset going forward)

**Out of scope:**
- Re-tagging existing Nevada/WA routes (kept as-is)
- Washington scrape + tagging (future phase)
- Automated tag accuracy scoring (manual spot-check only)
- UI changes

</domain>

<decisions>
## Implementation Decisions

### Model Benchmark
- **D-01:** Benchmark candidates: `gpt-4o-mini` (current baseline), `gpt-5-nano`, `gpt-5-mini` — all OpenAI, same Batch API client, model string swap only
- **D-02:** Sample size: 50 routes (mix of Yosemite routes with and without tick comments)
- **D-03:** Winner selection: accuracy-first — if accuracy is equal or close, pick cheaper model. Research exact pricing for gpt-5-nano and gpt-5-mini before benchmark (batch pricing expected: gpt-5-nano ~$0.78/20K routes, gpt-5-mini TBD)
- **D-04:** Grok is ruled out for this phase — Grok-4.3 costs ~$8/20K routes vs ~$0.78–$1.43 for OpenAI options; no quality justification

### Tick Comment Integration
- **D-05:** Pre-tagging enrichment step: query D1 for all tick comments grouped by route_id, merge into route JSON as `route_tick_comments` field (already in prompt template at line 185 of `route_area_tagging.py`)
- **D-06:** Scope: all routes that have ticks in D1 (`parent_type='tick'`) — 174 routes currently; not limited to Yosemite. Future tick collection automatically extends this.
- **D-07:** Tick inputs are treated as additional context alongside route info and area info (not a replacement)

### Re-Tagging Scope
- **D-08:** Phase 3 tags only the ~2,969 new Yosemite NP routes. Existing Nevada + WA routes keep their current v1.0 tags.
- **D-09:** Regional expansion pattern: Yosemite → Washington → others (separate future phases)

### Accuracy Audit
- **D-10:** Audit method: user manually spot-checks a sample of tagged Yosemite routes after benchmark run. No automated diff tooling needed.
- **D-11:** Audit timing: before full 2,969-route run — benchmark on 50, user reviews, then full run

### Deployment
- **D-12:** Phase 3 includes pushing Yosemite tagged data to Cloudflare remote D1 (production)
- **D-13:** After push: delete Nevada/WA route data from remote D1 — production becomes Yosemite-only
- **D-14:** UI verification done by user after data push (not automated in this phase)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Tagging Pipeline
- `tagging/route_area_tagging.py` — Main tagging pipeline; `create_batch_requests()` at line 175 shows current prompt template and tick comment slot; `gpt-4o-mini` hardcoded at line 192
- `tagging/d1_tag_sync.py` — Syncs tagged JSON → D1 via SQL UPDATE; handles route_tags and area_tags columns; stage 4 of the pipeline
- `tagging/batch_queue.py` — Batch queue management
- `tagging/tests/` — Existing test suite

### Data & Schema
- `.planning/phases/02-tick-comments/02-04-SUMMARY.md` — Current D1 state: 2,969 Yosemite routes, 4,209 tick comments across 174 routes; tick schema: `comments` table, `parent_type='tick'`, `parent_id=route_id`
- `data/yosemite-national-park_routes.json` — Yosemite route JSON to be tagged (5.9MB, 517 areas, 2,966 routes)

### Phase Requirements
- `.planning/REQUIREMENTS.md` — TAG-01 through TAG-05 requirements
- `.planning/ROADMAP.md` — Phase 03 success criteria

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `route_area_tagging.py:create_batch_requests()` — Prompt template already has `route_tick_comments` slot at line 185; enrichment step populates it
- `route_area_tagging.py:submit_batch()` + `wait_for_batch_completion()` — OpenAI Batch API mechanics reused as-is; only `model=` string changes
- `d1_tag_sync.py` — Stage 4 sync pipeline works for any region; reuse directly
- `manual_tagging()` — Logic-based tags (rope, pitch, runout, etc.) — region-independent, no changes needed

### Established Patterns
- OpenAI Batch API: JSONL upload → 24h completion window → poll → retrieve. Same client, just change `model="gpt-4o-mini"` to `model="gpt-5-nano"` or `model="gpt-5-mini"`
- Tagging pipeline is JSON-in/JSON-out: stage 3 produces `*_tagged.json`, stage 4 syncs to D1
- D1 imports use chunked batches (≤100KB per statement) — same pattern for tag sync

### Integration Points
- New step between JSON prep and tagging: **D1 tick export + route JSON enrichment** — query `comments WHERE parent_type='tick'`, group by `parent_id`, merge into route JSON `route_tick_comments` field
- Remote D1 push: `wrangler d1 execute climbing-search --remote --file tag_update_yosemite.sql`
- Nevada/WA deletion: `wrangler d1 execute climbing-search --remote --command "DELETE FROM routes WHERE ..."` — researcher should verify exact area path patterns

</code_context>

<specifics>
## Specific Ideas

- User will manually review the 50-route benchmark output before approving full run — plan should include a checkpoint for this
- The `route_tick_comments` field in the prompt template (line 185) needs to be populated from D1, not from the scraped JSON (which has empty strings for Yosemite)
- Model names to test: `gpt-5-nano` and `gpt-5-mini` — researcher should confirm exact API model IDs and current batch pricing before planning benchmark

</specifics>

<deferred>
## Deferred Ideas

- Washington scrape + tagging — next regional phase after Yosemite
- Full re-tag of Nevada/WA routes with improved model — not in scope; those regions being deleted from production anyway
- Automated tag accuracy scoring — user prefers manual spot-check for now

</deferred>

---

*Phase: 3-Tagging Upgrade*
*Context gathered: 2026-05-10*
