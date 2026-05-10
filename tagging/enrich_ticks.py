#!/usr/bin/env python3
"""
enrich_ticks.py — Merge D1 tick comments into Yosemite route JSON.

Reads tick comments from local D1 (direct sqlite3, 4,209 comments, 174 routes),
merges them into data/yosemite-national-park_routes.json as the route_tick_comments
field, and writes data/yosemite-national-park_routes_enriched.json.

D1 values are richer than scraper-populated values: when a route_id exists in D1,
the D1 GROUP_CONCAT value overwrites whatever was there (even non-empty scraper text).
Routes not in D1 retain their existing route_tick_comments value unchanged.
"""

import glob
import json
import sqlite3

# ---------------------------------------------------------------------------
# Module constants
# ---------------------------------------------------------------------------

D1_GLOB = "worker-api/.wrangler/state/v3/d1/miniflare-D1DatabaseObject/*.sqlite"
INPUT_JSON = "data/yosemite-national-park_routes.json"
OUTPUT_JSON = "data/yosemite-national-park_routes_enriched.json"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_tick_map(db_path: str = None) -> dict:
    """Return a dict mapping route_id (str) → concatenated tick comment text.

    Parameters
    ----------
    db_path : str, optional
        Path to the sqlite3 database file. If None, the D1_GLOB pattern is
        used to locate the local Wrangler D1 file (skipping metadata.sqlite).

    Returns
    -------
    dict[str, str]
        {route_id: "comment1 | comment2 | ..."} for all routes that have
        tick-type comments in the comments table.
    """
    if db_path is None:
        candidates = [
            p for p in glob.glob(D1_GLOB)
            if "metadata" not in p
        ]
        if not candidates:
            raise FileNotFoundError(
                f"No D1 sqlite file found matching: {D1_GLOB}"
            )
        db_path = candidates[0]

    con = sqlite3.connect(db_path)
    try:
        cur = con.execute(
            """
            SELECT parent_id, GROUP_CONCAT(comment_text, ' | ')
            FROM comments
            WHERE parent_type = 'tick'
            GROUP BY parent_id
            """
        )
        rows = cur.fetchall()
    finally:
        con.close()

    tick_map = {str(row[0]): row[1] for row in rows}
    print(f"Loaded tick comments for {len(tick_map)} routes from D1")
    return tick_map


def enrich_routes_with_tick_comments(data: list, tick_map: dict) -> list:
    """Merge tick_map values into the route_tick_comments field of each route.

    Parameters
    ----------
    data : list
        List of area dicts, each with a "routes" key containing route dicts.
    tick_map : dict
        Mapping of str(route_id) → concatenated tick comment text.

    Returns
    -------
    list
        The same data list with route_tick_comments updated in-place for routes
        whose route_id appears in tick_map. Routes not in tick_map are unchanged.
    """
    for area in data:
        for route in area.get("routes", []):
            route_id = str(route.get("route_id", ""))
            if route_id in tick_map:
                route["route_tick_comments"] = tick_map[route_id]
            # else: preserve existing value (empty string or scraper data)
    return data


def main():
    """Run the full enrichment pipeline using the real D1 file and Yosemite JSON."""
    # Step 1: Load tick map from D1
    tick_map = build_tick_map()  # no args → uses D1_GLOB

    # Step 2: Load input JSON
    with open(INPUT_JSON, encoding="utf-8") as f:
        data = json.load(f)

    # Step 3: Enrich routes
    data = enrich_routes_with_tick_comments(data, tick_map)

    # Step 4: Write output JSON (no indent — matches existing data file style)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    # Step 5: Report counts
    total = sum(len(area.get("routes", [])) for area in data)
    enriched = sum(
        1
        for area in data
        for route in area.get("routes", [])
        if route.get("route_tick_comments")
    )
    print(f"Enriched {enriched} of {total} routes with D1 tick comments → {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
