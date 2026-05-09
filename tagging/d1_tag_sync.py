"""
d1_tag_sync.py — Read tagged JSON output from tagging/route_area_tagging.py and
generate batched, idempotent UPDATE SQL for D1's route_tags and area_tags columns.

Pipeline position (D-07, D-08):
  Stage 1: scrape          → data/<state>_routes.json
  Stage 2: import_to_d1   → D1 rows with route_tags = NULL
  Stage 3: route_area_tagging.py → data/<state>_routes_tagged.json
  Stage 4: d1_tag_sync.py → worker-api/tag_update_<state>.sql
           → wrangler d1 execute --file=tag_update_<state>.sql --remote

Tags come from BOTH LLM-based and rule/logic-based tagging in stage 3. This
module reads the full route_tags and area_tags payload from the tagged JSON
regardless of which pipeline produced them.

Usage:
    python -m tagging.d1_tag_sync data/arizona_routes_tagged.json
    python -m tagging.d1_tag_sync data/arizona_routes_tagged.json -o worker-api/tag_update_az.sql

Decisions:
    D-07: Tagging is a post-scrape step — this is stage 4 of the pipeline
    D-08: route_tags JSON column in D1 updated here, not at import time
    T-05-01: All tag values pass through sql_quote() (SQL injection prevention)
    T-05-03: chunk_updates() enforces 100KB per statement (DoS prevention)
"""
import argparse
import json
import logging
from pathlib import Path
from typing import Any

from scraping.import_to_d1 import (
    extract_mp_id_from_url,
    sql_quote,
)

D1_MAX_STMT_BYTES = 100_000  # D1 SQL statement limit (RESEARCH.md, verified)
SAFETY_MARGIN = 5_000
UPDATE_BATCH_BYTES = D1_MAX_STMT_BYTES - SAFETY_MARGIN

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# ID resolution
# ---------------------------------------------------------------------------

def resolve_route_d1_id(route: dict) -> str:
    """
    Map a tagged-JSON route to its D1 route_id.

    Modern scraper data has numeric MP IDs in route_id.
    Legacy data has uuid4 strings — fall back to URL-derived ID.

    Strategy (matches Plan 02 import convention via extract_mp_id_from_url):
      1. If route_id is purely numeric → return as-is
      2. Otherwise → extract numeric MP ID from route_url
      3. Fallback → deterministic 12-char MD5 slice of route_url

    Args:
        route: Route dict from tagged JSON; must have 'route_id' and/or 'route_url'.

    Returns:
        String route_id suitable for use as D1 primary key.
    """
    rid = (route.get("route_id") or "").strip()
    if rid.isdigit():
        return rid
    # Legacy uuid or unknown — derive from URL (matches Plan 02 import convention)
    return extract_mp_id_from_url(route.get("route_url") or "")


def resolve_area_d1_id(area: dict) -> str:
    """
    Map a tagged-JSON area to its D1 area_id.

    Applies the same resolution strategy as resolve_route_d1_id but for areas.

    Args:
        area: Area dict from tagged JSON; must have 'area_id' and/or 'area_url'.

    Returns:
        String area_id suitable for use as D1 primary key.
    """
    aid = (area.get("area_id") or "").strip()
    if aid.isdigit():
        return aid
    return extract_mp_id_from_url(area.get("area_url") or "")


# ---------------------------------------------------------------------------
# Tag extraction
# ---------------------------------------------------------------------------

def build_route_tag_updates(data: list[dict]) -> list[tuple[str, str]]:
    """
    Walk all areas and their routes; emit (route_d1_id, route_tags_json_string)
    for routes that have non-empty route_tags.

    Reads the full route_tags payload produced by tagging/route_area_tagging.py,
    which combines BOTH LLM-based tags and rule/logic-based tags into route_tags.
    This function does not distinguish between tag sources — it syncs whatever
    is present in the route_tags dict.

    Skips routes with empty or missing route_tags (we don't clobber existing
    D1 values with an empty JSON object).

    Returns a stable, deduplicated list sorted by route_d1_id for deterministic
    SQL generation across re-runs (satisfies idempotency requirement).

    Args:
        data: Top-level list of area dicts from tagged JSON.

    Returns:
        Sorted list of (route_d1_id, json_string) tuples.
    """
    out: list[tuple[str, str]] = []
    for area in data or []:
        for route in area.get("routes", []) or []:
            tags = route.get("route_tags")
            if not tags:  # None, empty dict, or falsy
                continue
            if isinstance(tags, dict) and len(tags) == 0:
                continue
            rid = resolve_route_d1_id(route)
            if not rid:
                continue
            tags_json = json.dumps(tags, sort_keys=True, ensure_ascii=False)
            out.append((rid, tags_json))

    # Deduplicate (same route_id appearing in multiple areas) — keep last occurrence
    dedup: dict[str, str] = {}
    for rid, tj in out:
        dedup[rid] = tj
    return sorted(dedup.items())


def build_area_tag_updates(data: list[dict]) -> list[tuple[str, str]]:
    """
    Walk all areas; emit (area_d1_id, area_tags_json_string) for areas that
    have non-empty area_tags.

    Area tags may come from LLM tagging or from rule-based logic in
    route_area_tagging.py — both are captured in the area_tags dict.

    Args:
        data: Top-level list of area dicts from tagged JSON.

    Returns:
        Sorted list of (area_d1_id, json_string) tuples.
    """
    out: list[tuple[str, str]] = []
    for area in data or []:
        tags = area.get("area_tags")
        if not tags:
            continue
        if isinstance(tags, dict) and len(tags) == 0:
            continue
        aid = resolve_area_d1_id(area)
        if not aid:
            continue
        tags_json = json.dumps(tags, sort_keys=True, ensure_ascii=False)
        out.append((aid, tags_json))

    dedup: dict[str, str] = {}
    for aid, tj in out:
        dedup[aid] = tj
    return sorted(dedup.items())


# ---------------------------------------------------------------------------
# SQL generation
# ---------------------------------------------------------------------------

def chunk_updates(
    table: str,
    column: str,
    key_column: str,
    updates: list[tuple[str, str]],
    max_bytes: int = UPDATE_BATCH_BYTES,
) -> list[str]:
    """
    Generate batched UPDATE statements using CASE-WHEN for bulk efficiency.

    Packs as many (key, value) tuples as fit within max_bytes into a single
    UPDATE statement of the form:

        UPDATE {table} SET {column} = CASE {key_column}
            WHEN 'key1' THEN 'value1'
            WHEN 'key2' THEN 'value2'
            ...
        END WHERE {key_column} IN ('key1', 'key2', ...);

    Values are SQL-quoted via sql_quote() (T-05-01: SQL injection prevention).
    Each statement is kept under max_bytes (T-05-03: DoS prevention).

    Args:
        table: Target table name ('routes' or 'areas').
        column: Target column name ('route_tags' or 'area_tags').
        key_column: Primary key column name ('route_id' or 'area_id').
        updates: Sorted list of (key, value) string tuples.
        max_bytes: Maximum byte length per generated SQL statement.

    Returns:
        List of SQL UPDATE statement strings, each <= max_bytes bytes.
    """
    if not updates:
        return []

    statements: list[str] = []
    buf_when: list[str] = []
    buf_keys: list[str] = []
    buf_size = 0

    HEADER = f"UPDATE {table} SET {column} = CASE {key_column} "
    FOOTER_TEMPLATE = " END WHERE {key} IN ({keys});"

    def flush() -> None:
        nonlocal buf_when, buf_keys, buf_size
        if not buf_when:
            return
        footer = FOOTER_TEMPLATE.format(
            key=key_column,
            keys=",".join(buf_keys),
        )
        sql = HEADER + " ".join(buf_when) + footer
        statements.append(sql)
        buf_when, buf_keys, buf_size = [], [], 0

    for key, value in updates:
        key_sql = sql_quote(key)
        value_sql = sql_quote(value)
        when_clause = f"WHEN {key_sql} THEN {value_sql}"
        # Estimate incremental byte cost: when_clause + space + key_sql for IN list + comma + space
        inc = len(when_clause.encode("utf-8")) + len(key_sql.encode("utf-8")) + 6
        # Estimate overhead for the full statement framing
        header_footer_est = (
            len(HEADER.encode("utf-8"))
            + len(FOOTER_TEMPLATE.format(key=key_column, keys="").encode("utf-8"))
        )
        if buf_size and (buf_size + inc + header_footer_est) > max_bytes:
            flush()
        buf_when.append(when_clause)
        buf_keys.append(key_sql)
        buf_size += inc

    flush()
    return statements


def generate_sync_sql(
    input_path: "Path | str",
    output_path: "Path | str",
) -> str:
    """
    Full pipeline: read tagged JSON → build updates → write batched SQL file.

    Reads the tagged JSON produced by tagging/route_area_tagging.py (which
    contains both LLM-derived and rule-based tags in route_tags and area_tags),
    then generates idempotent UPDATE statements for D1.

    The output SQL file is safe to run multiple times (idempotent) because:
    - UPDATE sets the value unconditionally from the same source data.
    - Routes with empty tags are excluded, so we never overwrite with empty.
    - Deterministic ordering (sorted by ID) ensures byte-identical re-runs.

    Args:
        input_path: Path to tagged JSON file (e.g., data/arizona_routes_tagged.json).
        output_path: Path for generated SQL file (e.g., worker-api/tag_update_arizona.sql).

    Returns:
        The full SQL string that was written to output_path.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    route_updates = build_route_tag_updates(data)
    area_updates = build_area_tag_updates(data)

    logger.info(
        "Generating tag sync SQL: %d route updates, %d area updates from %s",
        len(route_updates),
        len(area_updates),
        input_path.name,
    )

    lines: list[str] = [
        f"-- Generated tag sync for {input_path.name}",
        f"-- Routes: {len(route_updates)} | Areas: {len(area_updates)}",
        "",
    ]

    for stmt in chunk_updates("routes", "route_tags", "route_id", route_updates):
        lines.append(stmt)

    for stmt in chunk_updates("areas", "area_tags", "area_id", area_updates):
        lines.append(stmt)

    sql = "\n".join(lines) + "\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(sql, encoding="utf-8")
    return sql


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Command-line interface for d1_tag_sync."""
    parser = argparse.ArgumentParser(
        description="Generate D1 UPDATE SQL from tagged JSON (stage 4 of 4-stage pipeline)"
    )
    parser.add_argument(
        "input",
        help="Tagged JSON path, e.g., data/arizona_routes_tagged.json",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output SQL path (default: worker-api/tag_update_<basename>.sql)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    in_path = Path(args.input)
    if args.output:
        out_path = Path(args.output)
    else:
        out_path = Path("worker-api") / f"tag_update_{in_path.stem}.sql"

    sql = generate_sync_sql(in_path, out_path)
    logger.info("Wrote %d bytes to %s", len(sql), out_path)


if __name__ == "__main__":
    main()
