# Phase 2: Tick Comments - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-09
**Phase:** 02-tick-comments
**Areas discussed:** Tick comment scope, Selenium session strategy, Schema fit for tick data, Validation scope

---

## Tick Comment Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Text-only ticks (current behavior) | Keep ≥15 word filter, skip short/empty ticks. Aligns with current parse_stats logic. | ✓ |
| All ticks with metadata | Capture every tick: user, date, tick type, full text. More data, more noise. | |
| Text-only + tick type preserved | Keep ≥15 word filter but also save tick type (Lead/Follow/TR). | |

**User's choice:** Text-only ticks (current behavior)
**Notes:** Signal quality over volume — consistent with how the data feeds Phase 3 tagging.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Individual rows in `comments` table (ROADMAP intent) | Each tick = one row, parent_type='tick', joinable via route_id. | ✓ |
| Concatenated blob in route_tick_comments | Keep existing column approach. Simpler, no schema change. | |
| Both — individual rows + update the blob | Backward compat while enabling row-level queries. | |

**User's choice:** Individual rows in `comments` table
**Notes:** ROADMAP intent confirmed. Enables Phase 3 to JOIN ticks to routes cleanly.

---

## Selenium Session Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Single session, re-auth on failure | One driver for full run. Re-authenticate on redirect. Matches existing get_driver() pattern. | ✓ |
| Session pool with cookie file | Login once, save cookies, reuse across runs. More complex. | |
| Re-authenticate per batch of N routes | Re-login every N routes. Extra overhead. | |

**User's choice:** Single session, re-auth on failure
**Notes:** Simplest approach, consistent with existing Selenium architecture.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Headless | Chrome --headless. Lower resource use, standard for batch scraping. | ✓ |
| Headed (visible browser) | Useful for debugging, leaves browser open during run. | |

**User's choice:** Headless Chrome
**Notes:** Production/batch mode. Headed can be used manually for debugging auth issues.

---

## Schema Fit for Tick Data

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — parse author + date from tick table | Update parse_stats to extract user name + tick date. Store in comment_author + comment_time. | ✓ |
| No — store text only, leave author/date null | Minimal change. Loses provenance. | |

**User's choice:** Yes — parse author + date
**Notes:** Keeps rows consistent with regular comments. Phase 3 can filter/sort by date if needed.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Existing schema is sufficient | No ALTER TABLE needed. comment_id, parent_id, parent_type, comment_author, comment_text, comment_time covers tick data. | ✓ |
| Add a tick_type column | Would capture Lead/Follow/TR. Requires schema migration. | |

**User's choice:** Existing schema is sufficient
**Notes:** No migration needed. tick_type out of scope given text-only filter decision.

---

## Validation Scope — El Cap First vs Full Yosemite

| Option | Description | Selected |
|--------|-------------|----------|
| El Cap first, then full Yosemite | Validate on sub-area before full run. Safer for auth/scale issues. | ✓ |
| Full Yosemite directly | Skip El Cap validation. Faster, higher risk. | |

**User's choice:** El Cap first, then full Yosemite
**Notes:** Standard validation approach.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Tick rows visible in D1 for known El Cap routes | Spot-check: query comments table for known routes like The Nose. | ✓ |
| N tick comments imported with no errors | Quantitative count threshold. | |
| You decide | Let planner define the gate. | |

**User's choice:** Tick rows visible in D1 (spot-check)
**Additional context:** User noted that without tagging (Phase 3), the service offers no differentiation from MountainProject itself. Phase 2 tick data directly enables Phase 3 prompt enrichment — completeness of tick collection affects tag quality downstream.

---

## Claude's Discretion

None — all areas had clear user selections.

## Deferred Ideas

- Tick type column (`Lead`/`Follow`/`TR`) — not captured in Phase 2 per text-only decision; could be added in a future schema or analysis phase
- Full CA scrape beyond Yosemite — deferred to a later milestone
