# Phase 1: Full-Stack Refactor — Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-08
**Phase:** 01-refactor
**Areas discussed:** Scraper coverage & approach, Cloud DB choice & ROI, Data model design, API & data sync strategy

---

## Scraper Coverage & Approach

| Option | Description | Selected |
|--------|-------------|----------|
| All types | Sport, Trad, Aid, Ice, Alpine, Mixed, TR, Boulder, Snow — capture everything | ✓ |
| All except Aid/Ice/Alpine | Focus on most-searched types | |
| User-configurable per run | --types flag at runtime | |

**User's choice:** All types — capture everything, filter in UI

---

| Option | Description | Selected |
|--------|-------------|----------|
| Keep Selenium for everything | Simpler, already working for comments | |
| Async HTTP for areas/routes, Selenium for comments | httpx/aiohttp for bulk, Selenium only where login needed | ✓ |
| Drop comments scraping entirely | Simplest, comments added later | |

**User's choice:** Hybrid — async HTTP for bulk scraping, Selenium only for login-gated comments

---

| Option | Description | Selected |
|--------|-------------|----------|
| All US states | Full coverage, ~500k+ routes | |
| Western US first, expand later | CA, CO, UT, WA, OR, NV, AZ, WY | ✓ |
| User-defined starting URLs | Config file with area URLs | |

**User's choice:** Western US first (existing JSON files as starting point), expand later

---

| Option | Description | Selected |
|--------|-------------|----------|
| Diff-based updates | Re-scrape area pages, detect new routes by route_id | ✓ |
| MountainProject sitemap/RSS | Depends on MP infrastructure | |
| Full re-scrape on schedule | Simple but wasteful | |

**User's choice:** Diff-based incremental updates

---

| Option | Description | Selected |
|--------|-------------|----------|
| Post-scrape tagging step | scrape → store raw → tag → update DB | ✓ |
| Inline during scrape | Couples LLM cost to scrape runs | |
| On-read tagging (lazy) | Tags added on first query | |

**User's choice:** Post-scrape step — tagging as a separate pipeline stage after scraping
**Notes:** User explicitly flagged that LLM-based tagging (tagging/ directory) must be preserved in the new pipeline

---

## Cloud DB Choice & ROI

| Option | Description | Selected |
|--------|-------------|----------|
| Cloudflare D1 | SQLite at edge, pairs with R2 already in use | ✓ |
| Turso (LibSQL) | Edge SQLite, DB-provider-agnostic | |
| Supabase (Postgres) | Full Postgres, REST/GraphQL auto-generated | |
| Keep Firebase (Firestore) | WIP already exists | |

**User's choice:** Cloudflare D1

---

| Option | Description | Selected |
|--------|-------------|----------|
| Migrate frontend to Cloudflare Pages + Workers | Full CF stack | ✓ |
| Keep frontend on Fly.io, add CF Worker as API | Cross-provider hop | |
| Keep frontend on Fly.io, proxy via Fly.io backend | Two servers | |

**User's choice:** Migrate to full Cloudflare stack (Pages + Workers + D1 + R2)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Server-side SQL filtering via Worker API | WHERE clauses + FTS5 | ✓ |
| External search (Algolia, Meilisearch) | Better fuzzy search | |
| Client-side filtering, D1 for pagination only | Minimal Worker complexity | |

**User's choice:** Server-side SQL filtering

---

## Data Model Design

| Option | Description | Selected |
|--------|-------------|----------|
| Fully normalized: 4 tables | areas + routes + comments + hierarchy | ✓ |
| Semi-normalized: 2 tables + JSON comments | areas + routes, comments as JSON blob | |
| Keep nested JSON in D1 | JSON columns, minimal migration | |

**User's choice:** Fully normalized — 4 tables

---

| Option | Description | Selected |
|--------|-------------|----------|
| Boolean type columns + JSONB tags | is_sport, is_trad, is_aid... + tags JSON | ✓ |
| Separate join tables for types and tags | Most normalized, complex joins | |
| Keep as strings + indexed computed columns | Minimal schema change | |

**User's choice:** Boolean columns for route types + JSON column for tags

---

| Option | Description | Selected |
|--------|-------------|----------|
| Adjacency list: parent_id + materialized path | Simple, efficient for D1/SQLite | ✓ |
| Closure table | Fastest for ancestor queries, more storage | |
| Keep flat breadcrumb JSON column | No hierarchy queries in SQL | |

**User's choice:** Adjacency list with materialized path

---

## API & Data Sync Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| REST endpoints via Hono framework | Purpose-built for Workers, TypeScript-first | ✓ |
| GraphQL via Yoga | Flexible, more setup overhead | |
| Raw Worker fetch handler | No framework, more boilerplate | |

**User's choice:** Hono framework for Worker API

---

| Option | Description | Selected |
|--------|-------------|----------|
| Weekly scrape via CF REST API | Diff-based, frequent | |
| Monthly scrape, export JSON then import to D1 | Simpler, matches existing workflow | ✓ |
| On-demand scrape via Worker trigger | Most control, needs hosted scraper | |

**User's choice:** Monthly scrape, export JSON, import to D1 via wrangler/HTTP API

---

## Claude's Discretion

- Specific Hono route structure and middleware patterns
- D1 migration tooling (wrangler d1 vs HTTP API)
- TypeScript type generation from D1 schema
- Rate limiting and retry logic in async HTTP scraper
- Error recovery and logging strategy for the scraper pipeline

## Deferred Ideas

- Full US state coverage — after Western US is validated
- External search service (Algolia, Meilisearch) — D1 FTS5 sufficient for now
- On-demand admin-triggered scraping — monthly batch is enough
- Mobile app
- User accounts, ticks, wishlists
