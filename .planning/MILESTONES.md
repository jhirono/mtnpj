# Milestones

## v1.0 — Full-Stack Refactor

**Shipped:** 2026-05-09
**Phases:** 1 (5 plans)

### Delivered

Complete rebuild: async scraper → Cloudflare D1 → Hono Worker API → React/Vite frontend on Cloudflare Pages. All 9 route types captured end-to-end including aid, ice, alpine, and mixed with correct grade extraction.

### Key Accomplishments

1. **Async scraper** — httpx + asyncio.Semaphore with multi-strategy BFS sub-area detection; handles deep hierarchies (El Capitan, Yosemite); stable numeric route IDs; all 9 route types
2. **D1 schema + import pipeline** — 3 tables + FTS5; batched INSERTs under 100KB D1 limit; FK-safe bulk import via topological sort; 13 tests
3. **Hono Worker API** — 4 REST endpoints (routes, areas, route detail, area routes); zod SQL-injection whitelist; FTS5 text search; 20 vitest tests; deployed to workers.dev
4. **Frontend migration** — routeApi.ts client replacing static JSON; 9 type checkboxes; debounced area search; deployed to Cloudflare Pages
5. **Tagging pipeline** — d1_tag_sync.py syncing LLM + logic-based tags to D1 via CASE-WHEN batched SQL; 89,467 route updates across 6 states; 11 tests
6. **Grade extraction fixes** — full support for A/C (aid/clean-aid), WI/AI (ice), M (mixed) grades extracted from MP h2 structure; combined grades like "5.10b A2" and "5.6 WI3 M4-5"

### Stats

- Plans: 5 | Tests: 44 (22 Python + 20 vitest + 2 integration)
- Routes in production D1: 17,358 (Nevada + Washington)
- Deployed: climbing-search.pages.dev + climbing-search-api.jumpei-hirono.workers.dev
- Timeline: 2026-05-08 → 2026-05-09 (~2 days)
