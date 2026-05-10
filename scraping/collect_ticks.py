#!/usr/bin/env python3
"""
collect_ticks.py — Standalone tick comment collector for Mountain Project routes.

Reads route_ids from local D1 (via wrangler), authenticates a single Selenium
session via login_mp(), fetches tick comments from /route/stats/ pages, and
writes individual rows to the D1 comments table via INSERT OR IGNORE.

Usage:
    python3 -m scraping.collect_ticks --area-path /yosemite-national-park/el-capitan/ [--dry-run] [--limit N]
    python3 -m scraping.collect_ticks --area-path /yosemite-national-park/ [--dry-run]

Environment:
    MP_LOGIN_EMAIL     — Mountain Project account email
    MP_LOGIN_PASSWORD  — Mountain Project account password

Decisions:
    D-01: >=15 word filter applied in parse_stats (already done upstream)
    D-02: Each tick = individual row in comments table, parent_type='tick'
    D-05: INSERT OR IGNORE with route_id as dedup key
    D-06: Single Selenium session; re-auth on session loss; cleanup_driver() in finally
    D-07: Headless Chrome (handled by init_selenium_driver)
    D-08: Credentials from env vars
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

# Selenium-bound functions from existing scraper
from scraping.scrape_mtnpj_final import (
    login_mp,
    get_driver,
    get_route_stats,
    cleanup_driver,
)

# SQL generation utilities from import pipeline
from scraping.import_to_d1 import (
    _build_comment_rows,
    chunk_inserts,
    COMMENTS_COLUMNS,
    INSERT_BATCH_BYTES,
)

# Constants
WRANGLER_CMD = ["npx", "wrangler"]
WORKER_API_DIR = Path(__file__).parent.parent / "worker-api"
TICK_DELAY_SECONDS = 1.5  # Rate-limit courtesy delay between stats page requests
DB_NAME = "climbing-search"


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def query_d1_routes(area_path_like: str, limit: int | None = None) -> list[dict]:
    """
    Query local D1 for routes matching an area path prefix.
    Returns list of {"route_id": str, "route_url": str}.

    area_path_like: SQL LIKE pattern, e.g. '%/el-capitan/%'
    """
    limit_clause = f"LIMIT {limit}" if limit else ""
    sql = (
        f"SELECT r.route_id, r.route_url "
        f"FROM routes r JOIN areas a ON r.area_id = a.area_id "
        f"WHERE a.path LIKE '{area_path_like}' {limit_clause};"
    )
    cmd = WRANGLER_CMD + [
        "d1", "execute", DB_NAME,
        "--command", sql,
        "--local", "--json",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=WORKER_API_DIR)
    if result.returncode != 0:
        logging.error(f"D1 query failed: {result.stderr}")
        return []

    try:
        output = json.loads(result.stdout)
        # wrangler --json returns: [{"results": [...], "success": true, ...}]
        if isinstance(output, list) and output:
            return output[0].get("results", [])
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse D1 JSON output: {e}")
    return []


def write_ticks_to_d1(tick_rows: list[str], dry_run: bool = False) -> int:
    """
    Write tick comment rows to local D1 via INSERT OR IGNORE.
    Returns the number of SQL statements executed (0 if dry_run or no rows).
    Uses INSERT OR IGNORE (not INSERT OR REPLACE) per D-05.
    """
    if not tick_rows:
        return 0

    # Build INSERT OR IGNORE statements.
    # chunk_inserts uses INSERT OR REPLACE by default — override prefix manually.
    col_csv = ", ".join(COMMENTS_COLUMNS)
    prefix = f"INSERT OR IGNORE INTO comments ({col_csv}) VALUES "

    # Manually chunk to stay under D1 100KB limit (reuse INSERT_BATCH_BYTES constant)
    statements = []
    batch: list[str] = []
    batch_bytes = len(prefix.encode("utf-8"))
    for row in tick_rows:
        row_bytes = len(row.encode("utf-8")) + 1  # +1 for comma separator
        if batch and batch_bytes + row_bytes > INSERT_BATCH_BYTES:
            statements.append(prefix + ",".join(batch) + ";")
            batch = []
            batch_bytes = len(prefix.encode("utf-8"))
        batch.append(row)
        batch_bytes += row_bytes
    if batch:
        statements.append(prefix + ",".join(batch) + ";")

    if dry_run:
        for stmt in statements:
            logging.info(f"[DRY RUN] Would execute: {stmt[:120]}...")
        return 0

    executed = 0
    for stmt in statements:
        cmd = WRANGLER_CMD + ["d1", "execute", DB_NAME, "--command", stmt, "--local"]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=WORKER_API_DIR)
        if result.returncode != 0:
            logging.error(f"D1 insert failed: {result.stderr[:200]}")
        else:
            executed += 1

    return executed


def remap_tick_entry(entry: dict) -> dict:
    """
    Remap parse_stats return keys to _build_comment_rows expected keys.
    parse_stats returns: {"author": ..., "date": ..., "text": ...}
    _build_comment_rows expects: {"comment_author": ..., "comment_time": ..., "comment_text": ...}
    """
    return {
        "comment_author": entry.get("author", ""),
        "comment_time": entry.get("date", ""),
        "comment_text": entry.get("text", ""),
    }


def collect_ticks(
    area_path: str,
    dry_run: bool = False,
    limit: int | None = None,
) -> dict:
    """
    Main collection loop.

    1. Query D1 for routes matching area_path
    2. Authenticate Selenium session (single session for the full run — D-06)
    3. For each route: fetch stats, remap tick entries, write to D1
    4. Return summary stats

    area_path: URL path segment to filter on, e.g. '/el-capitan/' or '/yosemite-national-park/'
    """
    email = os.environ.get("MP_LOGIN_EMAIL", "")
    password = os.environ.get("MP_LOGIN_PASSWORD", "")
    if not email or not password:
        logging.error("MP_LOGIN_EMAIL and MP_LOGIN_PASSWORD env vars must be set")
        sys.exit(1)

    # Build SQL LIKE pattern from area_path
    area_path_like = f"%{area_path}%"
    logging.info(f"Querying D1 for routes in area path: {area_path_like}")
    routes = query_d1_routes(area_path_like, limit=limit)
    logging.info(f"Found {len(routes)} routes to process")

    if not routes:
        logging.warning("No routes found — check area_path and D1 import status")
        return {"routes_processed": 0, "ticks_written": 0, "errors": 0}

    driver = get_driver()
    if not driver:
        logging.error("Failed to initialize Selenium driver")
        sys.exit(1)

    stats = {"routes_processed": 0, "ticks_written": 0, "errors": 0}

    try:
        # Single login before the loop (D-06)
        logging.info("Authenticating with Mountain Project...")
        if not login_mp(driver, email, password):
            logging.error("Initial login failed — check credentials")
            sys.exit(1)

        for i, route in enumerate(routes, 1):
            route_id = route.get("route_id", "")
            route_url = route.get("route_url", "")
            if not route_id or not route_url:
                logging.warning(f"Skipping route with missing id/url: {route}")
                stats["errors"] += 1
                continue

            logging.info(f"[{i}/{len(routes)}] Fetching ticks for route {route_id}")

            # Validate stats URL format (Pitfall 1)
            stats_url = route_url.replace("/route/", "/route/stats/", 1)
            if "/route/stats/" not in stats_url:
                logging.error(f"Stats URL format error for {route_url} — skipping")
                stats["errors"] += 1
                continue

            try:
                _, _, tick_entries = get_route_stats(route_url)

                # Check for session loss (D-06): login redirect after stats fetch
                if "login" in driver.current_url.lower():
                    logging.warning("Session lost mid-run — re-authenticating")
                    if not login_mp(driver, email, password):
                        logging.error("Re-authentication failed — stopping")
                        break
                    _, _, tick_entries = get_route_stats(route_url)

                if not tick_entries:
                    logging.debug(f"No qualifying tick entries for route {route_id}")
                    stats["routes_processed"] += 1
                    time.sleep(TICK_DELAY_SECONDS)
                    continue

                # Remap keys and build SQL rows
                remapped = [remap_tick_entry(e) for e in tick_entries]
                rows = _build_comment_rows(remapped, route_id, "tick")

                if rows:
                    write_ticks_to_d1(rows, dry_run=dry_run)
                    stats["ticks_written"] += len(rows)
                    logging.info(f"  Wrote {len(rows)} tick(s) for route {route_id}")

            except Exception as e:
                logging.error(f"Error processing route {route_id}: {e}")
                stats["errors"] += 1

            stats["routes_processed"] += 1
            time.sleep(TICK_DELAY_SECONDS)

    finally:
        # D-06: cleanup driver ONLY in finally block — driver stays alive across all routes
        cleanup_driver()

    logging.info(
        f"Done. Routes processed: {stats['routes_processed']}, "
        f"Ticks written: {stats['ticks_written']}, "
        f"Errors: {stats['errors']}"
    )
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collect tick comments from Mountain Project stats pages"
    )
    parser.add_argument(
        "--area-path",
        required=True,
        help="Area path segment to filter routes (e.g. /el-capitan/ or /yosemite-national-park/)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch ticks but do not write to D1 (prints SQL instead)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of routes processed (for testing)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()
    setup_logging(args.verbose)
    collect_ticks(
        area_path=args.area_path,
        dry_run=args.dry_run,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
