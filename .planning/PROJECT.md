# Mountain Project Climbing Search

## Summary
A climbing route search and discovery app that scrapes MountainProject.com and provides a fast, filterable UI for finding routes across US regions.

## Current Stack
- **Frontend:** Vite + React + TypeScript (`climbing-search/`)
- **Scraper:** Python + Selenium + BeautifulSoup (`scraping/`)
- **Data:** Static state-level JSON files in `data/` (sport/trad only)
- **Storage:** Cloudflare R2 (configured), Firebase WIP (`firebase-climbing-search/`)
- **Hosting:** Fly.io (primary region: lax)

## Goals
- Comprehensive route data across all route types (sport, trad, aid, ice, alpine, boulder, TR)
- Fast, filterable search powered by a cloud database
- Normalized data model with proper area and route tables

## Context
- Firebase WIP in `firebase-climbing-search/` — not production-ready
- R2 configured in `r2_config.py` and `upload_all_to_r2.py`
- Currently only sport/trad routes captured due to filename convention in DataService
