# Phase 3: Tagging Upgrade - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-10
**Phase:** 3-Tagging Upgrade
**Areas discussed:** Model benchmark setup, Tick comment integration, Re-tagging scope, Accuracy audit process

---

## Model Benchmark Setup

### Model name clarification

| Option | Description | Selected |
|--------|-------------|----------|
| These are placeholders — let's pick real ones | Roadmap had speculative model names | ✓ |
| Fixed — those are the ones | API access already set up | |
| One is fixed, one is open | Partial flexibility | |

**User's choice:** Placeholders — pick real ones

---

### Initial model options

| Option | Description | Selected |
|--------|-------------|----------|
| Claude Sonnet vs gpt-4o-mini | Cross-provider, strong structured output | |
| GPT-4o vs gpt-4o-mini | Same provider upgrade | |
| Grok vs GPT-4o | Cross-provider, requires xAI client | |
| You decide | Claude picks best ROI | |

**User's choice (free text):** "research the best ROI model with decent performance among grok, openai. I believe Claude models are too expensive"

---

### After ROI research (pricing table presented)

| Option | Batch cost / 20K routes | Selected |
|--------|------------------------|----------|
| gpt-4o-mini vs gpt-5-nano | $1.43 vs $0.78 | |
| gpt-4o-mini vs gpt-5.4-nano | $1.43 vs $2.58 | |
| Skip benchmark — prompt only | — | |

**User's choice (free text):** "check gpt 5 mini as well"

---

### Final model selection

**User's choice:** Benchmark gpt-4o-mini (baseline) vs gpt-5-nano vs gpt-5-mini
**Notes:** gpt-5-nano at ~$0.78 batch is cheaper than current gpt-4o-mini ($1.43). Grok-4.3 ruled out at ~$8/run. Researcher to confirm exact gpt-5-mini batch pricing before planning.

---

### Winner criteria

| Option | Description | Selected |
|--------|-------------|----------|
| Accuracy first, cost tiebreaker | Switch if better; cost breaks ties | ✓ |
| Cost first — must be cheaper | Only switch if also cheaper | |
| You decide from sample results | User calls it after seeing output | |

**User's choice:** Accuracy first, cost tiebreaker

---

## Tick Comment Integration

### Data flow

| Option | Description | Selected |
|--------|-------------|----------|
| Export from D1 + enrich JSON (pre-tagging step) | Clean pipeline stages | ✓ |
| Query D1 inside tagging script | Simpler but slower | |
| Re-scrape with Selenium | Hours of Selenium work | |

**User's choice:** Export from D1 and enrich route JSON before tagging
**Notes:** User clarified: "the inputs of tagging are ticks as well as route info and sometimes area info" — ticks are a core input, not optional enrichment

---

### Enrichment scope

| Option | Description | Selected |
|--------|-------------|----------|
| All routes with ticks in D1 | 174 routes currently, auto-extends | ✓ |
| Yosemite only | Region-limited | |
| You decide | Researcher figures out scope | |

**User's choice (implicit from clarification):** All routes with ticks — ticks are a standard input regardless of region

---

## Re-Tagging Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Only new Yosemite routes (~2,969) | Existing tags unchanged | ✓ |
| All routes (~20K) | Full re-tag, consistent quality | |
| Ticked routes first, then rest | Two-pass approach | |

**User's choice:** Only new Yosemite routes (~2,969)
**Notes:** "after yosemite np, i will run the same process for washington" — regional expansion pattern. Phase 3 is Yosemite only.

---

## Accuracy Audit Process

| Option | Description | Selected |
|--------|-------------|----------|
| Manual spot-check by user | Simple, no automation | ✓ |
| Automated before/after diff | Two runs, systematic | |
| Skip — trust benchmark | Benchmark validates quality | |

**User's choice:** Manual spot-check of tagged sample routes

---

## Deployment (emerged during audit discussion)

**User's note:** "after yosemite np tagging, i will load the data to cloudflare, then delete washington/nevada data. then i check all UI works or not"

| Option | Description | Selected |
|--------|-------------|----------|
| Phase 3 includes push to remote + cleanup | Full delivery | ✓ |
| Manual push after Phase 3 | Phase 3 stops at local D1 | |

**User's choice:** Phase 3 includes Cloudflare push + Nevada/WA data deletion

---

## Claude's Discretion

None — all areas had explicit user decisions.

## Deferred Ideas

- Washington scrape + tagging — next regional phase
- Full re-tag of existing Nevada/WA routes — deferred (those regions being deleted from production)
- Automated tag accuracy scoring — user prefers manual spot-check for now
