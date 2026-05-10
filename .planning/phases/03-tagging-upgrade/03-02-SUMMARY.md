---
plan: "03-02"
phase: "03-tagging-upgrade"
status: complete
completed: 2026-05-10
winning_model: gpt-4o-mini
---

# Plan 03-02: Model Benchmark — COMPLETE

## What Was Built

`tagging/benchmark_models.py` — a standalone OpenAI Batch API orchestrator that submits 50 Yosemite routes to three candidate models concurrently, polls until all batches complete, and writes `benchmark_results.json` for side-by-side comparison.

## Benchmark Results

| Model | Valid responses | Avg tags/route | Verdict |
|---|---|---|---|
| **gpt-4o-mini** | **50/50** | **5.1** | **WINNER** |
| gpt-5-mini | 36/50 | 4.1 | Unreliable — reasoning overhead |
| gpt-5-nano | 6/50 | 1.5 | Failed — reasoning exhausts token budget |

**Winning model: `gpt-4o-mini`**

## Key Findings / Fixes Applied

- gpt-5-nano and gpt-5-mini are reasoning models — they burn internal reasoning tokens before producing visible output. At `max_completion_tokens=500` they return empty content. Even at 1500 tokens, complex routes exhaust the budget.
- `max_tokens` → `max_completion_tokens` required for gpt-5 models
- `temperature`/`top_p` unsupported for gpt-5 models in Chat Completions API
- `reasoning` parameter only available in Responses API, not Batch API
- gpt-4o-mini: 100% reliable, most detailed tags, cheapest per successful result

## Commits

- `054a48e` feat(03-02): implement benchmark_models.py for 3-model OpenAI batch comparison
- `a22f108` fix(03-02): use max_completion_tokens for gpt-5 model compatibility
- `009d1aa` fix(03-02): omit temperature/top_p for gpt-5 models (unsupported params)
- `4c1ecc7` fix(03-02): disable reasoning mode for gpt-5 models to get visible content output
- `43b4a80` fix(03-02): increase max_completion_tokens to 1500 for gpt-5 reasoning overhead

## Artifacts

- `tagging/benchmark_models.py` — benchmark orchestrator (reusable for future model comparisons)
- `benchmark_results.json` — side-by-side tag comparison for 50 routes

## Self-Check: PASSED

- [x] benchmark_models.py created and committed
- [x] All 3 models benchmarked (with API compatibility fixes applied)
- [x] benchmark_results.json written with valid gpt-4o-mini results
- [x] User reviewed output and selected winning model: gpt-4o-mini
