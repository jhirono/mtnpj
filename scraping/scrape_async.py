#!/usr/bin/env python3
"""
Async Mountain Project scraper.

Uses httpx + asyncio.Semaphore for bulk area/route HTML fetches.
Keeps Selenium only for login-gated comment + stats scraping.
Produces output JSON shape backward-compatible with existing data/*.json files.
"""
import argparse
import asyncio
import datetime
import hashlib
import json
import logging
import os
import re
import sys
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

# Reuse Selenium-bound functions from existing scraper
from scraping.scrape_mtnpj_final import (
    get_comments,
    get_route_stats,
    get_driver,
    cleanup_driver,
    parse_stats,
    get_access_issues,
    get_area_page_info,
    clean_area_name_from_url,
)

BASE_URL = "https://www.mountainproject.com"
OUTPUT_DIR = "data"
CACHE_DIR = os.path.join(OUTPUT_DIR, "cache")
CACHE_EXPIRY_DAYS = 7
CONCURRENCY_LIMIT = 5  # MP rate-limit safe; tune up to 10 after Yosemite test
DELAY_BETWEEN_REQUESTS = 0.4  # seconds, after each fetch
USER_AGENT = "Mozilla/5.0 (compatible; mtnpj-scraper/1.0)"

# Login credentials (inherited from environment, matching scrape_mtnpj_final.py)
LOGIN_EMAIL = os.environ.get("MP_LOGIN_EMAIL")
LOGIN_PASSWORD = os.environ.get("MP_LOGIN_PASSWORD")
COOKIE_FILE = "cookies.json"


# ===========================================================================
# Stable ID Extraction
# ===========================================================================

def extract_mp_route_id(route_url: str) -> str:
    """
    Extract stable numeric route ID from Mountain Project URL.
    URL format: https://www.mountainproject.com/route/105733804/the-nose
    Falls back to MD5 hash slice for malformed URLs. Never returns uuid4.
    """
    m = re.search(r'/route/(\d+)/', route_url)
    if m:
        return m.group(1)
    # Also try trailing segment (no trailing slash)
    m = re.search(r'/route/(\d+)$', route_url)
    if m:
        return m.group(1)
    return hashlib.md5(route_url.encode()).hexdigest()[:12]


def extract_mp_area_id(area_url: str) -> str:
    """
    Extract stable numeric area ID from Mountain Project URL.
    Falls back to MD5 hash slice for malformed URLs. Never returns uuid4.
    """
    m = re.search(r'/area/(\d+)/', area_url)
    if m:
        return m.group(1)
    m = re.search(r'/area/(\d+)$', area_url)
    if m:
        return m.group(1)
    return hashlib.md5(area_url.encode()).hexdigest()[:12]


# ===========================================================================
# Sub-Area & Leaf-Area Detection
# ===========================================================================

def get_sub_area_links(soup: BeautifulSoup) -> list:
    """
    Multi-strategy detection for sub-area links.
    Returns list of <a> tag objects whose href contains '/area/'.
    Tries strategies in order, returns first non-empty result.

    Strategy A: primary nav div with exact class string
    Strategy B: any div whose class string contains 'max-height' (regex)
    Strategy C: element with id matching 'left-nav'
    Strategy D: all <a> tags with /area/ href, excluding breadcrumb context
    """
    def _area_links(container):
        return [a for a in container.find_all("a")
                if a.get("href") and "/area/" in a.get("href", "")]

    # Strategy A: exact class match (primary — preserves existing behavior)
    nav_div = soup.find("div", class_="max-height max-height-md-0 max-height-xs-400")
    if nav_div:
        links = _area_links(nav_div)
        if links:
            return links

    # Strategy B: any div whose class list contains 'max-height' (handles class rename)
    for div in soup.find_all("div"):
        classes = div.get("class", [])
        if any("max-height" in c for c in classes):
            links = _area_links(div)
            if links:
                return links

    # Strategy C: element with id containing 'left-nav'
    left_nav = soup.find(id=re.compile(r"left-nav", re.IGNORECASE))
    if left_nav:
        links = _area_links(left_nav)
        if links:
            return links

    # Strategy D: last resort — scan all <a> tags with /area/ href,
    # deduplicate by href, exclude breadcrumb context
    breadcrumb_hrefs = set()
    breadcrumb_el = soup.find("nav", class_=re.compile(r"breadcrumb", re.IGNORECASE))
    if not breadcrumb_el:
        breadcrumb_el = soup.find("div", class_=re.compile(r"breadcrumb", re.IGNORECASE))
    if not breadcrumb_el:
        # Try the Mountain Project breadcrumb pattern
        breadcrumb_el = soup.find("div", class_="mb-half small text-warm")
    if breadcrumb_el:
        for a in breadcrumb_el.find_all("a"):
            if a.get("href"):
                breadcrumb_hrefs.add(a["href"])

    seen_hrefs = set()
    links = []
    for a in soup.find_all("a"):
        href = a.get("href", "")
        if "/area/" in href and href not in breadcrumb_hrefs and href not in seen_hrefs:
            seen_hrefs.add(href)
            links.append(a)
    return links


def is_lowest_level_area(soup: BeautifulSoup, sub_areas: list) -> bool:
    """
    Returns True if the area has route links and no sub-areas.
    Sub-area traversal always takes precedence over route presence.
    """
    route_table = soup.find("table", {"id": "left-nav-route-table"})
    has_routes = bool(
        route_table and route_table.find_all("a", href=lambda x: x and "/route/" in x)
    )
    has_sub_areas = bool(sub_areas)
    return has_routes and not has_sub_areas


# ===========================================================================
# Route Type Parsing
# ===========================================================================

def parse_route_type_string(type_length_str: str) -> dict:
    """
    Parse the comma-separated 'Type:' table cell from a route page.

    Returns:
        {
            "types": list[str],   # e.g. ["Trad", "Aid"]
            "pitches": int,       # default 1
            "length_ft": int|None,
            "length_m": int|None,
        }

    Handles:
    - Pitch count patterns: "3 pitches", "1 pitch"
    - Length with metric: "350 ft (107 m)"
    - Length feet-only: "80 ft"
    - Grade modifiers starting with "Grade ": dropped
    - Everything else: added to types list
    """
    types = []
    pitches = None
    length_ft = None
    length_m = None

    for item in type_length_str.split(","):
        item = item.strip()
        if not item:
            continue

        # Pitch count
        pitch_match = re.search(r"(\d+)\s*pitches?", item, re.IGNORECASE)
        if pitch_match:
            pitches = int(pitch_match.group(1))
            continue

        # Length with metric: "350 ft (107 m)"
        len_both = re.search(r"(\d+)\s*ft\s*\((\d+)\s*m\)", item, re.IGNORECASE)
        if len_both:
            length_ft = int(len_both.group(1))
            length_m = int(len_both.group(2))
            continue

        # Length feet only: "80 ft"
        len_ft_only = re.search(r"(\d+)\s*ft", item, re.IGNORECASE)
        if len_ft_only:
            length_ft = int(len_ft_only.group(1))
            continue

        # Grade modifier: "Grade III", "Grade IV", etc. — drop
        if item.startswith("Grade "):
            continue

        # Otherwise: it's a route type token
        types.append(item)

    # Default single pitch if no pitch count found
    if pitches is None:
        pitches = 1

    return {
        "types": types,
        "pitches": pitches,
        "length_ft": length_ft,
        "length_m": length_m,
    }


# ===========================================================================
# Diff / Incremental Update
# ===========================================================================

def diff_routes_by_id(existing_routes: list, scraped_route_urls: list) -> dict:
    """
    Compute added/removed/unchanged sets by stable route ID.

    Args:
        existing_routes: list of route dicts with 'route_id' key
        scraped_route_urls: list of route URLs from fresh area page scrape

    Returns:
        {"added": [...], "removed": [...], "unchanged": [...]}
    """
    existing_ids = {r.get("route_id") for r in existing_routes if r.get("route_id")}
    scraped_ids = {extract_mp_route_id(u) for u in scraped_route_urls}
    return {
        "added": sorted(scraped_ids - existing_ids),
        "removed": sorted(existing_ids - scraped_ids),
        "unchanged": sorted(existing_ids & scraped_ids),
    }


# ===========================================================================
# Cache Helpers
# ===========================================================================

def get_cache_key(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


def get_cache_path(url: str, data_type: str = "html") -> str:
    cache_dir = os.path.join(CACHE_DIR, data_type)
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, f"{get_cache_key(url)}.json")


def get_from_cache(url: str, data_type: str = "html"):
    path = get_cache_path(url, data_type)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            cache = json.load(f)
        ts = datetime.datetime.fromisoformat(cache["timestamp"])
        if (datetime.datetime.now() - ts).days > CACHE_EXPIRY_DAYS:
            return None
        return cache["content"]
    except Exception as e:
        logging.warning(f"Cache read error for {url}: {e}")
        return None


def save_to_cache(url: str, content, data_type: str = "html") -> None:
    path = get_cache_path(url, data_type)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "url": url,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "content": content,
                },
                f,
                ensure_ascii=False,
            )
    except Exception as e:
        logging.warning(f"Cache write error for {url}: {e}")


# ===========================================================================
# Async Fetch
# ===========================================================================

async def fetch_html(client: httpx.AsyncClient, sem: asyncio.Semaphore, url: str):
    """Fetch HTML for a URL, using disk cache when available."""
    cached = get_from_cache(url, "html")
    if cached:
        return cached
    async with sem:
        try:
            resp = await client.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=20.0,
                follow_redirects=True,
            )
            resp.raise_for_status()
            await asyncio.sleep(DELAY_BETWEEN_REQUESTS)
            save_to_cache(url, resp.text, "html")
            return resp.text
        except (httpx.HTTPError, httpx.TimeoutException) as e:
            logging.warning(f"Fetch failed {url}: {e}")
            return None


def parse_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


# ===========================================================================
# Route Detail Extraction (helpers)
# ===========================================================================

def _extract_route_name_from_soup(soup: BeautifulSoup) -> str:
    h1 = soup.find("h1")
    return h1.get_text(strip=True) if h1 else "Unknown Route"


def _extract_grade(soup: BeautifulSoup) -> tuple:
    """Returns (grade, protection_grading)."""
    grade_el = soup.select_one(".rateYDS, .route-type.Ice, .rateHueco")
    if grade_el:
        grade_full = grade_el.get_text(strip=True)
        grade = grade_full.split()[0].replace("YDS", "").strip() if grade_full else "Unknown"
        h2 = grade_el.find_parent("h2")
        protection_grading = ""
        if h2:
            for item in h2.contents:
                if isinstance(item, str):
                    text = item.strip()
                    if text:
                        protection_grading += text + " "
        return grade, protection_grading.strip()
    return "Unknown", ""


def _extract_stars_votes(soup: BeautifulSoup) -> tuple:
    """Returns (stars, votes)."""
    tag = soup.find("span", id=re.compile(r"starsWithAvgText"))
    if tag:
        text = tag.get_text(strip=True)
        stars_m = re.search(r"Avg:\s*([\d.]+)", text)
        votes_m = re.search(r"from\s+([\d,]+)", text)
        stars = float(stars_m.group(1)) if stars_m else "N/A"
        votes = int(votes_m.group(1).replace(",", "")) if votes_m else "N/A"
        return stars, votes
    return "N/A", "N/A"


def _extract_type_length(soup: BeautifulSoup) -> dict:
    """Parse the Type: table cell; returns parse_route_type_string result."""
    tag = soup.find(string="Type:")
    if tag:
        td = tag.find_next("td")
        if td:
            return parse_route_type_string(td.get_text(strip=True))
    return {"types": [], "pitches": 1, "length_ft": None, "length_m": None}


def _extract_fa(soup: BeautifulSoup) -> str:
    tag = soup.find(string="FA:")
    if tag:
        td = tag.find_next("td")
        if td:
            return td.get_text(strip=True)
    return "N/A"


def _extract_text_sections(soup: BeautifulSoup) -> tuple:
    """Returns (description, location, protection)."""
    description = location = protection = "N/A"
    for h2 in soup.find_all("h2"):
        text = h2.get_text()
        if "Description" in text:
            div = h2.find_next("div", {"class": "fr-view"})
            description = div.get_text(strip=True) if div else "N/A"
        elif "Location" in text:
            div = h2.find_next("div", {"class": "fr-view"})
            location = div.get_text(strip=True) if div else "N/A"
        elif "Protection" in text or "Gear" in text:
            div = h2.find_next("div", {"class": "fr-view"})
            protection = div.get_text(strip=True) if div else "N/A"
    return description, location, protection


def _extract_lr(soup: BeautifulSoup, route_url: str) -> int:
    """Extract left-to-right ordering value from route table row."""
    route_id_segment = route_url.rstrip("/").split("/")[-2] if "/route/" in route_url else ""
    if route_id_segment:
        tr = soup.find("tr", id=lambda x: x and route_id_segment in x)
        if tr:
            lr = tr.get("data-lr")
            if lr is not None:
                return int(lr)
    return 0


# ===========================================================================
# Async Route & Area Scrapers
# ===========================================================================

async def get_route_details(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    route_url: str,
    *,
    selenium_enabled: bool = True,
) -> dict:
    """
    Fetch and parse full route details.
    Selenium calls (comments, stats) are wrapped in asyncio.to_thread so they
    don't block the event loop.
    """
    # Check route-details cache first
    cached = get_from_cache(route_url, "route_details")
    if cached:
        return cached

    html = await fetch_html(client, sem, route_url)
    if not html:
        return {}

    soup = parse_html(html)

    grade, protection_grading = _extract_grade(soup)
    stars, votes = _extract_stars_votes(soup)
    type_info = _extract_type_length(soup)
    fa = _extract_fa(soup)
    description, location, protection = _extract_text_sections(soup)
    page_views, shared_on = get_area_page_info(soup)

    route_details = {
        "route_name": _extract_route_name_from_soup(soup),
        "route_url": route_url,
        "route_lr": _extract_lr(soup, route_url),
        "route_grade": grade,
        "route_protection_grading": protection_grading,
        "route_stars": stars,
        "route_votes": votes,
        "route_type": ", ".join(type_info["types"]),
        "route_pitches": type_info["pitches"],
        "route_length_ft": type_info["length_ft"],
        "route_length_meter": type_info["length_m"],
        "route_fa": fa,
        "route_description": description,
        "route_location": location,
        "route_protection": protection,
        "route_page_views": page_views,
        "route_shared_on": shared_on,
        "route_id": extract_mp_route_id(route_url),
        "route_tags": [],
        "route_composite_tags": [],
        "route_comments": [],
        "route_suggested_ratings": {},
        "route_tick_comments": "",
    }

    if selenium_enabled:
        try:
            comments = await asyncio.to_thread(
                get_comments,
                route_url,
                LOGIN_EMAIL,
                LOGIN_PASSWORD,
                COOKIE_FILE,
            )
            route_details["route_comments"] = comments or []
        except Exception as e:
            logging.warning(f"Comments fetch failed for {route_url}: {e}")

        try:
            suggested_ratings, _, tick_comments = await asyncio.to_thread(
                get_route_stats, route_url
            )
            route_details["route_suggested_ratings"] = suggested_ratings or {}
            route_details["route_tick_comments"] = tick_comments or ""
        except Exception as e:
            logging.warning(f"Stats fetch failed for {route_url}: {e}")

    save_to_cache(route_url, route_details, "route_details")
    return route_details


def _extract_route_urls_from_soup(soup: BeautifulSoup) -> list:
    """Extract route URLs from the left-nav-route-table."""
    route_table = soup.find("table", {"id": "left-nav-route-table"})
    if not route_table:
        return []
    urls = []
    for tr in route_table.find_all("tr"):
        link = tr.find("a")
        if link and link.get("href") and "/route/" in link.get("href", ""):
            href = link["href"]
            if not href.startswith("http"):
                href = BASE_URL + href
            urls.append(href)
    return urls


def _extract_area_hierarchy(soup: BeautifulSoup, area_url: str) -> list:
    """Build area_hierarchy list from breadcrumb navigation."""
    hierarchy = []
    breadcrumb = soup.find("div", class_="mb-half small text-warm")
    if breadcrumb:
        links = breadcrumb.find_all("a")
        for idx, link in enumerate(links):
            raw_name = link.get_text(strip=True)
            href = link.get("href", "")
            cleaned = (
                clean_area_name_from_url(href)
                if (not raw_name or raw_name.endswith("…") or len(raw_name) < 5)
                else raw_name
            )
            hierarchy.append(
                {
                    "level": idx + 1,
                    "area_hierarchy_name": cleaned,
                    "area_hierarchy_url": href,
                }
            )
        # Add current area
        current_name = clean_area_name_from_url(area_url)
        hierarchy.append(
            {
                "level": len(hierarchy) + 1,
                "area_hierarchy_name": current_name,
                "area_hierarchy_url": area_url,
            }
        )
    return hierarchy


def _extract_area_gps(soup: BeautifulSoup) -> str:
    for tr in soup.find_all("tr"):
        if "GPS:" in tr.get_text():
            gps_tag = tr.find("a", {"target": "_blank", "href": True})
            if gps_tag and "maps.google.com" in gps_tag["href"]:
                return gps_tag["href"]
    return "N/A"


def _extract_area_description(soup: BeautifulSoup) -> str:
    div = soup.find("div", {"class": "fr-view"})
    return div.get_text(strip=True) if div else "N/A"


def _extract_getting_there(soup: BeautifulSoup) -> str:
    for h2 in soup.find_all("h2"):
        if "Getting There" in h2.get_text():
            div = h2.find_next("div", {"class": "fr-view"})
            return div.get_text(strip=True) if div else "N/A"
    return "N/A"


async def get_routes(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    area_url: str,
    *,
    selenium_enabled: bool = True,
    existing_routes: list = None,
) -> dict:
    """
    Fetch all routes for a leaf-level area.
    Supports incremental diff: if existing_routes is provided, only fetches
    full details for new routes (added IDs); copies unchanged routes from existing.
    """
    cached = get_from_cache(area_url, "area")
    if cached:
        return cached

    html = await fetch_html(client, sem, area_url)
    if not html:
        return {}

    soup = parse_html(html)

    area_name = area_url.rstrip("/").split("/")[-1]
    area_description = _extract_area_description(soup)
    area_getting_there = _extract_getting_there(soup)
    area_gps = _extract_area_gps(soup)
    area_access_issues = get_access_issues(soup)
    area_page_views, area_shared_on = get_area_page_info(soup)
    area_hierarchy = _extract_area_hierarchy(soup, area_url)

    route_urls = _extract_route_urls_from_soup(soup)

    # Incremental diff: determine which routes need full fetching
    if existing_routes is not None:
        diff = diff_routes_by_id(existing_routes, route_urls)
        added_ids = set(diff["added"])
        existing_by_id = {r["route_id"]: r for r in existing_routes}

        routes_to_fetch = [u for u in route_urls if extract_mp_route_id(u) in added_ids]
        new_route_details = await asyncio.gather(
            *[get_route_details(client, sem, u, selenium_enabled=selenium_enabled)
              for u in routes_to_fetch]
        )

        routes = []
        for url in route_urls:
            rid = extract_mp_route_id(url)
            if rid in added_ids:
                # Find the newly fetched details
                for rd in new_route_details:
                    if rd.get("route_id") == rid:
                        routes.append(rd)
                        break
            else:
                # Unchanged — copy from existing
                if rid in existing_by_id:
                    routes.append(existing_by_id[rid])
    else:
        # Full fetch
        routes = list(
            await asyncio.gather(
                *[get_route_details(client, sem, u, selenium_enabled=selenium_enabled)
                  for u in route_urls]
            )
        )
        routes = [r for r in routes if r]

    area_comments = []
    if selenium_enabled:
        try:
            area_comments = await asyncio.to_thread(
                get_comments,
                area_url,
                LOGIN_EMAIL,
                LOGIN_PASSWORD,
                COOKIE_FILE,
            )
        except Exception as e:
            logging.warning(f"Area comments fetch failed for {area_url}: {e}")

    area_data = {
        "area_id": extract_mp_area_id(area_url),
        "area_url": area_url,
        "area_name": area_name,
        "area_gps": area_gps,
        "area_description": area_description,
        "area_getting_there": area_getting_there,
        "area_tags": [],
        "area_hierarchy": area_hierarchy,
        "area_access_issues": area_access_issues,
        "area_page_views": area_page_views,
        "area_shared_on": area_shared_on,
        "area_comments": area_comments,
        "routes": routes,
    }

    save_to_cache(area_url, area_data, "area")
    return area_data


async def scrape_lowest_level_areas(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    start_url: str,
) -> list:
    """
    BFS traversal to find all lowest-level areas (leaf areas with routes, no sub-areas).
    Processes up to CONCURRENCY_LIMIT URLs per round via asyncio.gather.
    Returns list of leaf area URLs.
    """
    visited = set()
    to_visit = [start_url]
    lowest_level_urls = []

    while to_visit:
        # Process current batch
        batch = []
        for url in to_visit:
            if url not in visited:
                batch.append(url)
                visited.add(url)
            if len(batch) >= CONCURRENCY_LIMIT:
                break

        remaining = [u for u in to_visit if u not in visited or u in [b for b in batch]]
        to_visit = [u for u in to_visit if u not in batch]

        if not batch:
            break

        logging.info(f"BFS batch: {len(batch)} URLs, {len(lowest_level_urls)} leaves found so far")

        # Fetch all in batch concurrently
        html_results = await asyncio.gather(
            *[fetch_html(client, sem, url) for url in batch]
        )

        next_to_visit = []
        for url, html in zip(batch, html_results):
            if not html:
                logging.warning(f"No HTML for {url}, skipping")
                continue

            soup = parse_html(html)
            sub_areas = get_sub_area_links(soup)

            if is_lowest_level_area(soup, sub_areas):
                lowest_level_urls.append(url)
                logging.info(f"  Leaf area: {url}")
            else:
                for link in sub_areas:
                    href = link.get("href", "")
                    if not href:
                        continue
                    if not href.startswith("http"):
                        href = BASE_URL + href
                    if href not in visited:
                        next_to_visit.append(href)

        # Deduplicate before extending
        seen = set()
        for u in next_to_visit:
            if u not in visited and u not in seen:
                seen.add(u)
                to_visit.append(u)

    return lowest_level_urls


# ===========================================================================
# Top-level Orchestrator
# ===========================================================================

async def run_scrape(
    start_url: str,
    *,
    output_dir: str = "data",
    selenium_enabled: bool = True,
    existing_json_path: str = None,
) -> None:
    """
    Main scrape orchestrator.
    1. BFS to find all leaf-level areas
    2. For each leaf area: optionally diff against existing JSON for incremental mode
    3. Save output to {output_dir}/{slug}_routes.json
    """
    global OUTPUT_DIR, CACHE_DIR
    OUTPUT_DIR = output_dir
    CACHE_DIR = os.path.join(output_dir, "cache")

    os.makedirs(output_dir, exist_ok=True)

    # Load existing JSON for diff/incremental mode
    existing_areas_by_url: dict = {}
    if existing_json_path and os.path.exists(existing_json_path):
        try:
            with open(existing_json_path, encoding="utf-8") as f:
                existing_data = json.load(f)
            for area in existing_data:
                url = area.get("area_url", "")
                if url:
                    existing_areas_by_url[url] = area.get("routes", [])
            logging.info(f"Loaded {len(existing_areas_by_url)} existing areas from {existing_json_path}")
        except Exception as e:
            logging.warning(f"Could not load existing JSON {existing_json_path}: {e}")

    sem = asyncio.Semaphore(CONCURRENCY_LIMIT)

    async with httpx.AsyncClient() as client:
        logging.info(f"Finding all leaf-level areas under {start_url}...")
        leaf_urls = await scrape_lowest_level_areas(client, sem, start_url)
        logging.info(f"Found {len(leaf_urls)} leaf areas")

        all_areas = []
        for i, area_url in enumerate(leaf_urls, 1):
            logging.info(f"Processing area {i}/{len(leaf_urls)}: {area_url}")
            try:
                existing_routes = existing_areas_by_url.get(area_url, None)
                area_data = await get_routes(
                    client,
                    sem,
                    area_url,
                    selenium_enabled=selenium_enabled,
                    existing_routes=existing_routes,
                )
                if area_data:
                    all_areas.append(area_data)
            except Exception as e:
                logging.error(f"Error processing {area_url}: {e}")

    # Derive output filename from start URL slug
    slug = start_url.rstrip("/").split("/")[-1]
    output_file = os.path.join(output_dir, f"{slug}_routes.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_areas, f, indent=2, ensure_ascii=False)
    logging.info(f"Saved {len(all_areas)} areas to {output_file}")


# ===========================================================================
# CLI Entry Point
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(description="Async Mountain Project scraper")
    parser.add_argument("url", help="Base area URL")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--no-selenium", action="store_true", help="Skip comments/stats (Selenium)")
    parser.add_argument(
        "--existing-json",
        help="Path to existing JSON for diff-mode incremental scrape",
    )
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--output-dir", default="data", help="Output directory for JSON files")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    global CONCURRENCY_LIMIT
    CONCURRENCY_LIMIT = args.concurrency

    try:
        asyncio.run(
            run_scrape(
                args.url,
                output_dir=args.output_dir,
                selenium_enabled=not args.no_selenium,
                existing_json_path=args.existing_json,
            )
        )
    finally:
        cleanup_driver()


if __name__ == "__main__":
    main()
