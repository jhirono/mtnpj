# Roadmap — Mountain Project Climbing Search Refactor

## Phase 1 — Full Scraper Coverage
**Goal:** Fix scraper to capture all route types (aid, ice, alpine, mixed, TR, boulder) across all area hierarchy levels including large parks like Yosemite NP.
**Status:** planning

## Phase 2 — Data Model Normalization
**Goal:** Replace nested JSON (area contains routes[]) with normalized relational tables (areas table, routes table, comments table, hierarchy table).
**Status:** planning

## Phase 3 — Cloud Database Migration
**Goal:** Migrate from static JSON file loading to a cloud database. Evaluate and implement best-ROI solution (Cloudflare D1, Firebase, Supabase, Turso, etc.).
**Status:** planning
