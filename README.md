# Mountain Project Climbing Search

This repository combines two related pieces of work:

1. A climbing route search web app in [`climbing-search`](/Users/jhirono/Dev/mtnpj/climbing-search).
2. Python data pipelines that scrape Mountain Project data, enrich it with OpenAI-generated tags, and prepare JSON files for the app.

It also contains an older Firebase/Firestore version of the app in [`firebase-climbing-search`](/Users/jhirono/Dev/mtnpj/firebase-climbing-search), which looks like an earlier backend approach that was kept around for reference.

## Repo Overview

### Current web app

The main app is [`climbing-search`](/Users/jhirono/Dev/mtnpj/climbing-search), a React + TypeScript + Vite frontend that loads static JSON datasets from `public/data`.

Based on the current code, it supports:

- searching areas and individual routes
- filtering by grade, route type, and AI/manual tags
- sorting by votes, stars, grade, and left-to-right order
- infinite scrolling for large result sets
- offline/PWA-related support
- optional Cloudflare R2-backed data hosting via [`climbing-search/src/config.ts`](/Users/jhirono/Dev/mtnpj/climbing-search/src/config.ts)

The shipped datasets currently live under [`climbing-search/public/data`](/Users/jhirono/Dev/mtnpj/climbing-search/public/data) and are organized by region, for example `california_sport_trad.json`.

### Scraping pipeline

The Mountain Project scraping scripts live in [`scraping`](/Users/jhirono/Dev/mtnpj/scraping).

Key files:

- [`scraping/scrape_mtnpj_final.py`](/Users/jhirono/Dev/mtnpj/scraping/scrape_mtnpj_final.py): main scraper with caching, requests/BeautifulSoup parsing, and Selenium for login/browser-assisted flows
- [`scraping/fast_scrape.py`](/Users/jhirono/Dev/mtnpj/scraping/fast_scrape.py): parallelized scraping helper for batches of URLs
- [`scraping/multi_scrape.sh`](/Users/jhirono/Dev/mtnpj/scraping/multi_scrape.sh): convenience wrapper for scraping multiple URLs

The scraper writes area/route JSON into the top-level [`data`](/Users/jhirono/Dev/mtnpj/data) directory and uses [`data/cache`](/Users/jhirono/Dev/mtnpj/data/cache) for HTML/data caching.

The scraper expects Mountain Project credentials from environment variables:

- `MP_LOGIN_EMAIL`
- `MP_LOGIN_PASSWORD`

### Tagging pipeline

The OpenAI tagging system lives in [`tagging`](/Users/jhirono/Dev/mtnpj/tagging).

Key files:

- [`tagging/route_area_tagging.py`](/Users/jhirono/Dev/mtnpj/tagging/route_area_tagging.py): main tagging script
- [`tagging/batch_queue.py`](/Users/jhirono/Dev/mtnpj/tagging/batch_queue.py): queue/continuation logic for sequential batch processing
- [`prompt/route_prompt.txt`](/Users/jhirono/Dev/mtnpj/prompt/route_prompt.txt): route tagging prompt
- [`prompt/area_prompt.txt`](/Users/jhirono/Dev/mtnpj/prompt/area_prompt.txt): area tagging prompt

What the tagging code does today:

- uses the OpenAI Batch API
- tags both areas and routes
- validates model output against a fixed allowed-tag vocabulary
- adds deterministic manual tags for things like rope length, multipitch, classic routes, and safety flags
- inherits some area-level tags down to routes
- supports multi-batch continuation when a dataset is too large for one batch

The tagging script currently initializes the OpenAI client from `OPENAI_API_KEY` and sends requests with model `gpt-4o-mini`.

### Data preparation and publishing

There are a few top-level helper scripts that turn tagged raw data into app-ready files:

- [`filter_sport_trad.py`](/Users/jhirono/Dev/mtnpj/filter_sport_trad.py): filters datasets down to sport/trad routes and writes `*_sport_trad.json` files for the web app
- [`upload_to_r2.py`](/Users/jhirono/Dev/mtnpj/upload_to_r2.py) and [`upload_all_to_r2.py`](/Users/jhirono/Dev/mtnpj/upload_all_to_r2.py): upload JSON files from the app data directory to Cloudflare R2
- [`r2_config.py`](/Users/jhirono/Dev/mtnpj/r2_config.py): shared R2 upload/config logic
- [`r2_setup.md`](/Users/jhirono/Dev/mtnpj/r2_setup.md): notes about the R2 deployment setup

## High-Level Workflow

The intended repo flow appears to be:

1. Scrape Mountain Project areas/routes into [`data`](/Users/jhirono/Dev/mtnpj/data).
2. Run OpenAI batch tagging over those JSON files from [`tagging`](/Users/jhirono/Dev/mtnpj/tagging).
3. Produce tagged output such as `*_routes_tagged.json`.
4. Filter the tagged output to sport/trad-only app datasets with [`filter_sport_trad.py`](/Users/jhirono/Dev/mtnpj/filter_sport_trad.py).
5. Copy or publish the resulting JSON into [`climbing-search/public/data`](/Users/jhirono/Dev/mtnpj/climbing-search/public/data).
6. Serve those files locally or upload them to Cloudflare R2 for production use.

## Directory Guide

- [`climbing-search`](/Users/jhirono/Dev/mtnpj/climbing-search): current static-data search app
- [`firebase-climbing-search`](/Users/jhirono/Dev/mtnpj/firebase-climbing-search): older Firestore-backed app and migration scripts
- [`scraping`](/Users/jhirono/Dev/mtnpj/scraping): Mountain Project scraping code
- [`tagging`](/Users/jhirono/Dev/mtnpj/tagging): OpenAI-based tag generation and batch queueing
- [`prompt`](/Users/jhirono/Dev/mtnpj/prompt): prompt templates used by the tagging scripts
- [`data`](/Users/jhirono/Dev/mtnpj/data): scraped/tagged intermediate data
- [`spec`](/Users/jhirono/Dev/mtnpj/spec): product/spec notes
- [`.old`](/Users/jhirono/Dev/mtnpj/.old): older archived files and experiments

## Running Things

### Web app

```bash
cd climbing-search
npm install
npm run dev
```

Build for production:

```bash
cd climbing-search
npm run build
```

### Scraping

Example pattern:

```bash
python3 scraping/scrape_mtnpj_final.py <mountain-project-area-url>
```

Or for multiple URLs:

```bash
./scraping/multi_scrape.sh <url1> <url2>
```

### Tagging

Submit a batch:

```bash
python3 tagging/route_area_tagging.py <input_json_file>
```

Retrieve a completed batch:

```bash
python3 tagging/route_area_tagging.py <input_json_file> <batch_id>
```

Run the queue processor:

```bash
python3 tagging/batch_queue.py run
```

## Notes on Project State

- [`climbing-search/README.md`](/Users/jhirono/Dev/mtnpj/climbing-search/README.md) is still the default Vite template, so the root README is now the more useful starting point.
- [`firebase-climbing-search`](/Users/jhirono/Dev/mtnpj/firebase-climbing-search) still contains a fuller README and Firestore migration scripts, but it does not appear to be the primary app anymore.
- The repo already includes generated/tagged regional datasets under [`data`](/Users/jhirono/Dev/mtnpj/data) and app-facing regional datasets under [`climbing-search/public/data`](/Users/jhirono/Dev/mtnpj/climbing-search/public/data).

## Environment Variables

At minimum, the repo appears to rely on:

- `OPENAI_API_KEY` for tagging
- `MP_LOGIN_EMAIL` and `MP_LOGIN_PASSWORD` for Mountain Project scraping
- `VITE_R2_ACCOUNT_ID` and `VITE_R2_BUCKET_NAME` if the web app is switched to R2-backed data loading

## Recommended Next Cleanup

If you revisit this repo later, the highest-value cleanup would probably be:

- refresh [`climbing-search/README.md`](/Users/jhirono/Dev/mtnpj/climbing-search/README.md) so it matches the actual app
- document the exact JSON schema expected between scraping, tagging, and frontend stages
- centralize the data publication flow so moving from `data/` to `climbing-search/public/data/` is explicit
