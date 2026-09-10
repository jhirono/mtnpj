# Phase 3: Tagging Upgrade - Context

**Gathered:** 2026-05-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Benchmark LLM models for route tagging, improve prompts with tick comment context, tag all new Yosemite NP routes, push to Cloudflare remote D1, and clean up Washington data from production.

**In scope:**
- LLM benchmark: gpt-4o-mini (baseline) vs gpt-5-nano vs gpt-5-mini on 50 sample routes
- Pre-tagging D1 enrichment step: export tick comments per route_id and merge into route JSON
- Prompt improvement: incorporate tick comment text as tagging context
- Tag new Yosemite NP routes (~2,969) with upgraded model + enriched prompt
- Redesigned tag category structure (6 categories, see decisions below)
- Manual spot-check audit by user before full run
- Push tagged Yosemite data to Cloudflare remote D1
- Delete Washington data from remote D1 (Yosemite-only dataset going forward)

**Out of scope:**
- Re-tagging existing Nevada/WA routes (kept as-is / being deleted)
- Washington scrape + tagging (future phase)
- Automated tag accuracy scoring (manual spot-check only)
- UI changes
- Area tagging pipeline (removed — see D-15)

</domain>

<decisions>
## Implementation Decisions

### Model Benchmark
- **D-01:** Benchmark candidates: `gpt-4o-mini` (current baseline), `gpt-5-nano`, `gpt-5-mini` — all OpenAI, same Batch API client, model string swap only
- **D-02:** Sample size: 50 routes (mix of Yosemite routes with and without tick comments)
- **D-03:** Winner selection: accuracy-first — if accuracy is equal or close, pick cheaper model
- **D-04:** Grok is ruled out for this phase — costs ~$8/20K routes vs ~$0.19–$0.93 for OpenAI options

### Tick Comment Integration
- **D-05:** Pre-tagging enrichment step: query D1 for all tick comments grouped by route_id, merge into route JSON as `route_tick_comments` field (already in prompt template at line 185 of `route_area_tagging.py`)
- **D-06:** Scope: all routes that have ticks in D1 (`parent_type='tick'`) — 174 routes currently
- **D-07:** Tick inputs are treated as additional context alongside route info (not a replacement)

### Re-Tagging Scope
- **D-08:** Phase 3 tags only the ~2,969 new Yosemite NP routes. Existing Nevada + WA routes keep their current v1.0 tags.
- **D-09:** Regional expansion pattern: Yosemite → Washington → others (separate future phases)

### Accuracy Audit
- **D-10:** Audit method: user manually spot-checks a sample of tagged Yosemite routes after benchmark run. No automated diff tooling needed.
- **D-11:** Audit timing: before full 2,969-route run — benchmark on 50, user reviews, then full run

### Deployment
- **D-12:** Phase 3 includes pushing Yosemite tagged data to Cloudflare remote D1 (production)
- **D-13:** Delete Washington route data from remote D1 — production becomes Yosemite-only (Nevada was never in remote D1)
- **D-14:** UI verification done by user after data push (not automated in this phase)

### Tag System Redesign
- **D-15:** Area tagging pipeline removed entirely — `area_prompt.txt`, `create_area_batch_requests()`, `inherit_approach_tags()` all dropped. Area text rarely has enough structured info for reliable tagging.
- **D-16:** Multi-pitch logic rule: replace `short_multipitch` / `long_multipitch` with two independent boolean tags — `single_pitch` (`route_pitches == 1`) and `multi_pitch` (`route_pitches > 1`). `route_pitches` remains as a numeric field for range filtering (e.g. "2–5 pitches") — separate from tags.
- **D-17:** `new_routes` tag removed. `route_shared_on` date field kept as-is for query-time filtering.
- **D-18:** `low_crowds` and `polished_rock` removed from tag set.
- **D-19:** Tag categories reorganized from 7 to 6. Route Style & Angle and Crack Climbing remain separate (not merged).

### Tag Category Structure (canonical — replaces all prior versions)

**Route Style** (LLM, route only)
`slab` | `vertical` | `gentle_overhang` | `steep_roof` | `tower_climbing` | `sporty_trad`

**Crack Climbing** (LLM, route only — trad/sport only)
`finger` | `thin_hand` | `wide_hand` | `offwidth` | `chimney` | `layback`

**Movement** (LLM, route only — trad/sport only)
`reachy` | `dynamic_moves` | `pumpy_sustained` | `technical_moves` | `powerful_bouldery` | `pockets_holes` | `small_edges` | `slopey_holds`

**Logistics** (mixed: logic + LLM)
- Logic: `single_pitch`, `multi_pitch`, `rope_60m`, `rope_70m`, `rope_80m` (single-pitch by length)
- LLM: `bolted_anchor`, `walk_off`, `tricky_rappel`, `rope_60m`, `rope_70m`, `rope_80m` (multi-pitch, text-based)
- Note: `bolted_anchor`, `walk_off`, `tricky_rappel` kept for now — evaluate accuracy after Yosemite run

**Safety** (mixed: logic + LLM)
- Logic: `runout_dangerous` (from protection grading PG13/R/X)
- LLM: `stick_clip` (sport only), `loose_rock`, `rope_drag_warning`, `seasonal_closure`

**Quality** (mixed: logic + LLM)
- Logic: `classic_route` (≥3 stars AND ≥5 votes)
- LLM: `classic_route` (text-based confirmation)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Tagging Pipeline
- `tagging/route_area_tagging.py` — Main tagging pipeline; `create_batch_requests()` at line 175 shows current prompt template and tick comment slot; `gpt-4o-mini` hardcoded at line 192 AND line 449 (both must change for TAG-02); `ALLOWED_TAGS` dict at line 25 must be updated to reflect new tag structure
- `tagging/d1_tag_sync.py` — Syncs tagged JSON → D1 via SQL UPDATE; handles route_tags and area_tags columns; stage 4 of the pipeline
- `tagging/batch_queue.py` — Batch queue management
- `tagging/tests/` — Existing test suite
- `prompt/route_prompt.txt` — Route LLM prompt; must be updated to reflect new tag categories and removed tags
- `prompt/area_prompt.txt` — Area LLM prompt; REMOVED in Phase 3 (D-15)

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
- `manual_tagging()` — Logic-based tags; needs updates for D-16 and D-17

### Code Changes Required by Tag Redesign
- `ALLOWED_TAGS` dict (line 25): restructure to 6 categories, remove `low_crowds`, `polished_rock`, `new_routes`, replace `short_multipitch`/`long_multipitch` with `multi_pitch`
- `manual_tagging()`: Rule 2 → emit `single_pitch`/`multi_pitch` only; Rule 5 → remove `new_routes` (Rule 6 deleted); Rule 4 (classic_route) and Rule 3 (runout_dangerous) unchanged
- `create_area_batch_requests()`: delete function (D-15)
- `inherit_approach_tags()`: delete function (D-15)
- `process_stick_clip_tag()`: keep — still needed for sport-only enforcement
- `prompt/route_prompt.txt`: update tag reference section to new 6-category structure
- `process_areas_and_routes()`: remove area batch creation and area tag processing branches

### Integration Points
- New step between JSON prep and tagging: **D1 tick export + route JSON enrichment** — query `comments WHERE parent_type='tick'`, group by `parent_id`, merge into route JSON `route_tick_comments` field
- Remote D1 push: `wrangler d1 execute climbing-search --remote --file tag_update_yosemite.sql`
- Washington deletion: `wrangler d1 execute climbing-search --remote --command "DELETE FROM routes WHERE path LIKE '/washington/%'"` — Nevada was never in remote D1

</code_context>

<specifics>
## Specific Ideas

- User will manually review the 50-route benchmark output before approving full run — plan should include a checkpoint for this
- The `route_tick_comments` field in the prompt template (line 185) needs to be populated from D1, not from the scraped JSON
- Model names to test: `gpt-5-nano` and `gpt-5-mini` — confirm exact API model IDs and batch pricing before benchmark
- `ALLOWED_TAGS` dict in code is the enforcement layer — must be updated to match new category structure before any tagging run
- `bolted_anchor`, `walk_off`, `tricky_rappel` accuracy to be evaluated after Yosemite run; may be removed in a future phase

</specifics>

<deferred>
## Deferred Ideas

- Washington scrape + tagging — next regional phase after Yosemite
- Full re-tag of Nevada/WA routes — not in scope; those regions being deleted from production
- Automated tag accuracy scoring — user prefers manual spot-check for now
- Remove `bolted_anchor`, `walk_off`, `tricky_rappel` if accuracy is poor — deferred until post-Yosemite audit

</deferred>

---

*Phase: 3-Tagging Upgrade*
*Context gathered: 2026-05-10 (tag system redesign added)*
