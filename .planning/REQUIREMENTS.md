# Requirements: Mountain Project Climbing Search

**Defined:** 2026-05-09
**Core Value:** Fast, comprehensive climbing route discovery across all route types, zero-cost edge stack

## v1.1 Requirements

### Data Import

- [ ] **IMPORT-01**: All 5 state pre-tagged JSON files (AZ, CA, CO, OR, UT) imported into D1 without data loss
- [ ] **IMPORT-02**: Post-import validation passes — row counts match source, no duplicate route_ids, required fields populated

### Tick Comments (Yosemite NP — Selenium)

- [ ] **TICK-01**: Selenium login session established and stable for MountainProject authenticated pages
- [ ] **TICK-02**: Tick comments scraped for Yosemite NP routes (already in D1 from CA import — no route re-import)
- [ ] **TICK-03**: Tick comments stored in D1 `comments` table and joinable to routes via route_id

### Tagging Quality

- [ ] **TAG-01**: Grok 4.3 and GPT-5.5 Instant benchmarked on a sample set — winner selected based on tag accuracy vs cost
- [ ] **TAG-02**: Tagging pipeline migrated to winning model
- [ ] **TAG-03**: LLM prompts improved to leverage tick comment data as additional context
- [ ] **TAG-04**: Tag accuracy audited on a sample before and after prompt improvements
- [ ] **TAG-05**: Updated tagging pipeline re-run on all newly imported data

## Future Requirements

### UI Improvements

- **UI-01**: Full-text search exposed in frontend UI
- **UI-02**: Grade/rating-based sorting (numeric YDS sort)
- **UI-03**: All MP-equivalent filters enabled (star rating, length, pitches, protection, commitment grade, etc.)

### Tagging Expansion

- **TAGCAT-01**: New tag categories defined and implemented (rock type, gear/rack, etc.) — evaluate after TAG-03 accuracy audit

## Out of Scope

| Feature | Reason |
|---------|--------|
| Mobile app | PWA via Cloudflare Pages covers mobile |
| Firebase / Fly.io | Replaced by Cloudflare stack |
| OAuth / user accounts | Not needed for public route discovery |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| IMPORT-01 | Phase 2 | Pending |
| IMPORT-02 | Phase 2 | Pending |
| TICK-01 | Phase 3 | Pending |
| TICK-02 | Phase 3 | Pending |
| TICK-03 | Phase 3 | Pending |
| TAG-01 | Phase 4 | Pending |
| TAG-02 | Phase 4 | Pending |
| TAG-03 | Phase 4 | Pending |
| TAG-04 | Phase 4 | Pending |
| TAG-05 | Phase 4 | Pending |

**Coverage:**
- v1.1 requirements: 10 total
- Mapped to phases: 10
- Unmapped: 0 ✓

---
*Requirements defined: 2026-05-09*
*Last updated: 2026-05-09 after initial v1.1 definition*
