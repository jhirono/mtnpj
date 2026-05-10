# Mountain Project Climbing Search

## Current Milestone: v1.1 Coverage & Tagging

**Goal:** Scrape Yosemite NP with tick comment collection via Selenium, then benchmark and upgrade the tagging pipeline.

**Target features:**
- Scrape Yosemite NP routes + tick comments via Selenium authenticated session
- Improve tag accuracy (better LLM prompts + logic rules)
- Add new tag categories to the tagging pipeline

## What This Is

A climbing route search and discovery app that scrapes MountainProject.com and provides a fast, filterable UI for finding routes across US regions — covering all 9 route types (sport, trad, aid, ice, alpine, mixed, TR, boulder, snow).

## Core Value

Fast, comprehensive climbing route discovery across all route types and area hierarchies, powered by a serverless edge stack with zero hosting cost.

## Current Stack (v1.0)

- **Frontend:** Vite + React + TypeScript — Cloudflare Pages (climbing-search.pages.dev)
- **API:** Hono on Cloudflare Workers (climbing-search-api.jumpei-hirono.workers.dev)
- **Database:** Cloudflare D1 (SQLite) — normalized areas + routes + comments + FTS5
- **Scraper:** Python httpx + asyncio (async) + Selenium (login-gated content only)
- **Tagging:** LLM + logic-based pipeline → d1_tag_sync.py

## Requirements

### Validated

- ✓ All 9 route types captured (sport, trad, aid, ice, alpine, mixed, TR, boulder, snow) — v1.0
- ✓ Deep area hierarchy traversal (Yosemite NP / El Capitan level) — v1.0
- ✓ Stable route IDs from MP URL numeric segment — v1.0
- ✓ Normalized relational schema (areas, routes, comments, FTS5) — v1.0
- ✓ Cloud database with REST API — v1.0 (Cloudflare D1 + Workers)
- ✓ Frontend filtering by all 9 route types — v1.0
- ✓ Aid/clean-aid/ice/mixed grade parsing (A0-A5+, C0-C5+, WI, AI, M) — v1.0
- ✓ Tagging pipeline (LLM + logic-based tags synced to D1) — v1.0
- ✓ Selenium authenticated tick comment collection (Yosemite NP — 4,209 ticks across 174 routes) — v1.1 Phase 02

### Active

- [ ] Improve tag accuracy (LLM prompts + logic rules)
- [ ] Add new tag categories to tagging pipeline

### Out of Scope

- Firebase — replaced by Cloudflare D1
- Fly.io / R2 — replaced by Cloudflare Pages + Workers
- Mobile app — PWA via Cloudflare Pages covers mobile
- Pre-tagged JSON bulk import — data will be scraped fresh and re-tagged instead

## Context

Shipped v1.0 with ~1,100 LOC TypeScript + ~1,800 LOC Python.
17,358 routes across Nevada + Washington in production D1 (v1.0).
Phase 02 complete: +2,969 Yosemite NP routes + 4,209 tick comments in local D1.
Deployed: climbing-search.pages.dev | climbing-search-api.jumpei-hirono.workers.dev

## Key Decisions

| Decision | Outcome | Notes |
|----------|---------|-------|
| Cloudflare D1 + Pages + Workers | ✓ Good | Zero cost, zero ops, edge-native |
| 9 boolean type columns | ✓ Good | Simple filter queries, no JOIN overhead |
| httpx + asyncio for scraping | ✓ Good | ~10x faster than Selenium for HTML pages |
| Stable route_id from URL segment | ✓ Good | Prerequisite for incremental diff scraping |
| Hono for Worker API | ✓ Good | Lightweight, zod validation, great D1 ergonomics |
| Selenium kept for login-gated content | ✓ Good | Cookie-based auth (MP→onX OAuth migration handled); 4,209 ticks collected |

## Constraints

- D1 statement limit: ≤100KB per batch (handled by chunked imports)
- D1 FK enforcement ON by default — must PRAGMA foreign_keys=0 for bulk imports
- MP scraping: concurrency=3 to avoid rate limiting; --no-selenium for CI/smoke tests

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-10 after Phase 02 completion*
