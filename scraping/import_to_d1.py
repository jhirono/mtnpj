"""
import_to_d1.py — Transform tagged climbing JSON files into batched SQL INSERT
statements for Cloudflare D1.

Usage:
    python -m scraping.import_to_d1 data/washington_routes_tagged.json
    python -m scraping.import_to_d1 data/arizona_routes_tagged.json -o worker-api/import_arizona.sql

Decisions:
    D-14: Route types as boolean columns (is_sport, is_trad, etc.)
    D-15: Area hierarchy via adjacency list (parent_id) + materialized path (path)
    D-18: Monthly scrape cadence; import script transforms JSON → D1 SQL
"""
import argparse
import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Any

# D-14: route_type keyword → boolean column map.
# Order matters for ambiguity resolution; "top rope" is checked before "tr".
ROUTE_TYPE_KEYWORDS = {
    "is_sport":   ["sport"],
    "is_trad":    ["trad"],
    "is_aid":     ["aid"],
    "is_ice":     ["ice"],
    "is_alpine":  ["alpine"],
    "is_mixed":   ["mixed"],
    "is_tr":      ["top rope", "toprope", " tr,", " tr "],  # space-bounded to avoid matching 'trad'
    "is_boulder": ["boulder"],
    "is_snow":    ["snow"],
}

BOOL_COLUMNS = list(ROUTE_TYPE_KEYWORDS.keys())  # canonical 9-column ordering

D1_MAX_STMT_BYTES = 100_000  # D1 SQL statement limit (RESEARCH.md, verified)
BATCH_SAFETY_MARGIN = 5_000  # leave headroom for BEGIN/COMMIT framing
INSERT_BATCH_BYTES = D1_MAX_STMT_BYTES - BATCH_SAFETY_MARGIN

# The route-guide stub that should be excluded from materialized paths
_ROUTE_GUIDE_SLUG = "route-guide"

# Areas column list in schema order (must match worker-api/schema.sql)
AREAS_COLUMNS = [
    "area_id", "parent_id", "area_name", "area_url", "area_gps",
    "area_description", "area_getting_there", "area_access_issues",
    "area_page_views", "area_shared_on", "area_tags", "path",
]

# Routes column list in schema order (must match worker-api/schema.sql)
ROUTES_COLUMNS = [
    "route_id", "area_id", "route_name", "route_url", "route_lr",
    "route_grade", "route_grade_numeric", "route_protection_grading",
    "route_stars", "route_votes",
    "is_sport", "is_trad", "is_aid", "is_ice", "is_alpine",
    "is_mixed", "is_tr", "is_boulder", "is_snow",
    "route_pitches", "route_length_ft", "route_length_meter",
    "route_fa", "route_description", "route_location", "route_protection",
    "route_page_views", "route_shared_on",
    "route_tags", "route_suggested_ratings", "route_tick_comments",
]

# Comments column list in schema order (must match worker-api/schema.sql)
COMMENTS_COLUMNS = [
    "comment_id", "parent_id", "parent_type",
    "comment_author", "comment_text", "comment_time",
]

logger = logging.getLogger(__name__)


def parse_route_type_to_booleans(route_type: str | None) -> dict:
    """
    Convert route_type string like 'Trad, Aid, 3 pitches, 350 ft' into
    a dict of {is_sport:0, is_trad:1, is_aid:1, ...}.

    Uses keyword matching on normalized (lowercased, space-padded) string.
    Grade modifiers like 'Grade III', 'Grade IV' are not matched by any keyword.
    """
    result = {col: 0 for col in BOOL_COLUMNS}
    if not route_type:
        return result
    # Normalize: pad with spaces so " tr " keyword can match at boundaries
    lower = " " + route_type.lower() + " "
    for col, keywords in ROUTE_TYPE_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            result[col] = 1
    return result


def build_materialized_path(area_hierarchy: list[dict] | None) -> str:
    """
    Build materialized path string from area_hierarchy URL slugs.

    Example:
        hierarchy = [
            {"area_hierarchy_url": "https://...mountainproject.com/route-guide"},
            {"area_hierarchy_url": "https://...mountainproject.com/area/105708962/arizona"},
            {"area_hierarchy_url": "https://...mountainproject.com/area/107447521/southern-arizona"},
        ]
        → "/arizona/southern-arizona/"

    Uses URL slugs (not area names) to avoid delimiter collision (RESEARCH A1, Pitfall 7).
    Excludes: the 'route-guide' stub, purely numeric path segments, empty segments.
    """
    segments = []
    for h in area_hierarchy or []:
        url = (h.get("area_hierarchy_url") or "").rstrip("/")
        if not url:
            continue
        last = url.split("/")[-1]
        # Skip the All-Locations stub
        if last in (_ROUTE_GUIDE_SLUG, ""):
            continue
        # If last segment is purely numeric (e.g., "/area/NNN" with no slug), skip
        if last.isdigit():
            continue
        segments.append(last)
    return "/" + "/".join(segments) + "/" if segments else "/"


def grade_to_numeric(grade: str | None) -> float | None:
    """
    Convert Yosemite Decimal System grade string to a sortable float.

    5.9  → 9.0
    5.10a → 10.1
    5.10b → 10.2
    5.10c → 10.3
    5.10d → 10.4
    5.11d → 11.4
    V3 (boulder) → None (not supported)
    Unknown → None

    Returns None for grades that don't match the 5.X[a-d] pattern.
    """
    if not grade or grade == "Unknown":
        return None
    m = re.match(r"^5\.(\d+)([a-d]?)([+\-]?)$", grade.strip())
    if not m:
        return None  # boulder grades (V0…V16) and other formats unsupported here
    minor = int(m.group(1))
    letter = m.group(2)
    # 5.9 = 9.0; 5.10a = 10.1; 5.10b = 10.2; 5.10c = 10.3; 5.10d = 10.4
    letter_offset = {"": 0.0, "a": 0.1, "b": 0.2, "c": 0.3, "d": 0.4}.get(letter, 0.0)
    return float(minor) + letter_offset


def extract_mp_id_from_url(url: str | None) -> str:
    """
    Extract the stable Mountain Project numeric ID from a URL.

    https://www.mountainproject.com/area/105708962/arizona → "105708962"
    https://www.mountainproject.com/route/105733804/the-nose → "105733804"

    Falls back to a deterministic MD5-based ID for malformed URLs (RESEARCH A2).
    """
    m = re.search(r"/(?:area|route)/(\d+)/", (url or "") + "/")
    if m:
        return m.group(1)
    # Deterministic fallback for malformed URLs (Pitfall 6)
    return hashlib.md5((url or "").encode()).hexdigest()[:12]


def sql_quote(value: Any) -> str:
    """
    Render a Python value as a SQL literal string.

    - None → NULL
    - bool → 1 or 0
    - int/float → numeric string
    - str → 'escaped' with single-quote doubling (SQL standard)

    Prevents SQL injection from content values (Threat T-02-01, T-02-02).
    """
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value)
    # Escape single quotes by doubling them (SQL standard, T-02-01)
    s = str(value).replace("'", "''")
    return f"'{s}'"


def chunk_inserts(
    rows: list[str],
    table: str,
    columns: list[str],
    max_bytes: int = INSERT_BATCH_BYTES,
) -> list[str]:
    """
    Pack row value tuples into INSERT OR REPLACE statements ≤ max_bytes each.

    Args:
        rows: List of parenthesized value tuple strings, e.g. ["('1','foo',1)", ...]
        table: Target table name
        columns: Column name list for INSERT header
        max_bytes: Maximum byte length per SQL statement

    Returns:
        List of SQL INSERT statements, each ≤ max_bytes bytes.
    """
    if not rows:
        return []

    col_csv = ", ".join(columns)
    prefix = f"INSERT OR REPLACE INTO {table} ({col_csv}) VALUES "
    statements = []
    batch: list[str] = []
    batch_bytes = len(prefix.encode("utf-8"))

    for row in rows:
        row_bytes = len(row.encode("utf-8")) + 1  # +1 for comma separator
        if batch and batch_bytes + row_bytes > max_bytes:
            # Flush current batch
            statements.append(prefix + ",".join(batch) + ";")
            batch = []
            batch_bytes = len(prefix.encode("utf-8"))
        batch.append(row)
        batch_bytes += row_bytes

    if batch:
        statements.append(prefix + ",".join(batch) + ";")

    return statements


def _build_area_row(area: dict) -> str:
    """Build a SQL value tuple for an area record."""
    area_url = area.get("area_url") or ""
    area_id = extract_mp_id_from_url(area_url)
    hierarchy = area.get("area_hierarchy") or []

    # Parent ID: the MP ID of the second-to-last hierarchy entry,
    # excluding the route-guide stub.
    parent_id = None
    for h in reversed(hierarchy):
        url = (h.get("area_hierarchy_url") or "").rstrip("/")
        last_seg = url.split("/")[-1]
        if last_seg in (_ROUTE_GUIDE_SLUG, "") or last_seg.isdigit():
            continue
        if extract_mp_id_from_url(h.get("area_hierarchy_url")) != area_id:
            parent_id = extract_mp_id_from_url(h.get("area_hierarchy_url"))
            break

    path = build_materialized_path(hierarchy)
    area_tags_json = json.dumps(area.get("area_tags") or {})

    values = (
        sql_quote(area_id),
        sql_quote(parent_id),
        sql_quote(area.get("area_name")),
        sql_quote(area_url),
        sql_quote(area.get("area_gps")),
        sql_quote(area.get("area_description")),
        sql_quote(area.get("area_getting_there")),
        sql_quote(area.get("area_access_issues")),
        sql_quote(area.get("area_page_views")),
        sql_quote(area.get("area_shared_on")),
        sql_quote(area_tags_json),
        sql_quote(path),
    )
    return "(" + ",".join(values) + ")"


def _build_route_row(route: dict, area_id: str) -> str:
    """Build a SQL value tuple for a route record."""
    route_url = route.get("route_url") or ""
    route_id = extract_mp_id_from_url(route_url)
    route_type = route.get("route_type") or ""
    booleans = parse_route_type_to_booleans(route_type)
    grade_numeric = grade_to_numeric(route.get("route_grade"))

    route_tags_json = json.dumps(route.get("route_tags") or {})
    suggested_ratings_json = json.dumps(route.get("route_suggested_ratings") or {})

    values = (
        sql_quote(route_id),
        sql_quote(area_id),
        sql_quote(route.get("route_name")),
        sql_quote(route_url),
        sql_quote(route.get("route_lr")),
        sql_quote(route.get("route_grade")),
        sql_quote(grade_numeric),
        sql_quote(route.get("route_protection_grading")),
        sql_quote(route.get("route_stars")),
        sql_quote(route.get("route_votes")),
        # Boolean type columns (D-14)
        str(booleans["is_sport"]),
        str(booleans["is_trad"]),
        str(booleans["is_aid"]),
        str(booleans["is_ice"]),
        str(booleans["is_alpine"]),
        str(booleans["is_mixed"]),
        str(booleans["is_tr"]),
        str(booleans["is_boulder"]),
        str(booleans["is_snow"]),
        sql_quote(route.get("route_pitches")),
        sql_quote(route.get("route_length_ft")),
        sql_quote(route.get("route_length_meter")),
        sql_quote(route.get("route_fa")),
        sql_quote(route.get("route_description")),
        sql_quote(route.get("route_location")),
        sql_quote(route.get("route_protection")),
        sql_quote(route.get("route_page_views")),
        sql_quote(route.get("route_shared_on")),
        sql_quote(route_tags_json),
        sql_quote(suggested_ratings_json),
        sql_quote(route.get("route_tick_comments")),
    )
    return "(" + ",".join(values) + ")"


def _make_comment_id(parent_id: str, author: str | None, time_val: str | None) -> str:
    """Generate a deterministic comment ID from parent_id + author + time."""
    raw = f"{parent_id}:{author or ''}:{time_val or ''}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def _build_comment_rows(comments: list[dict], parent_id: str, parent_type: str) -> list[str]:
    """Build SQL value tuples for comment records."""
    rows = []
    for c in comments or []:
        comment_id = _make_comment_id(parent_id, c.get("comment_author"), c.get("comment_time"))
        values = (
            sql_quote(comment_id),
            sql_quote(parent_id),
            sql_quote(parent_type),
            sql_quote(c.get("comment_author")),
            sql_quote(c.get("comment_text")),
            sql_quote(c.get("comment_time")),
        )
        rows.append("(" + ",".join(values) + ")")
    return rows


def generate_sql(
    input_path: Path | str,
    output_path: Path | str | None = None,
) -> str:
    """
    Transform a tagged climbing JSON file into batched D1-compatible SQL INSERTs.

    The generated SQL:
    - Uses INSERT OR REPLACE for idempotent re-imports (D-18)
    - Batches INSERTs under D1's 100KB statement limit (Pitfall 4)
    - Derives route_id and area_id from MP URL numeric segments (Pitfall 6)
    - Builds materialized path from URL slugs (Pitfall 7, A1)
    - Appends FTS5 rebuild at end (Pitfall 3)
    - Is deterministic: sorting by extracted MP ID (Test 12)

    Args:
        input_path: Path to the tagged JSON file
        output_path: Optional path to write the SQL output

    Returns:
        The generated SQL string.
    """
    input_path = Path(input_path)
    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    # Sort areas deterministically by extracted MP ID for idempotent output
    data_sorted = sorted(
        data,
        key=lambda a: extract_mp_id_from_url(a.get("area_url") or ""),
    )

    area_rows: list[str] = []
    route_rows: list[str] = []
    comment_rows: list[str] = []

    for area in data_sorted:
        area_url = area.get("area_url") or ""
        area_id = extract_mp_id_from_url(area_url)

        area_rows.append(_build_area_row(area))

        # Sort routes by route_id for determinism
        routes_sorted = sorted(
            area.get("routes") or [],
            key=lambda r: extract_mp_id_from_url(r.get("route_url") or ""),
        )
        for route in routes_sorted:
            route_url = route.get("route_url") or ""
            route_id = extract_mp_id_from_url(route_url)
            route_rows.append(_build_route_row(route, area_id))
            comment_rows.extend(
                _build_comment_rows(route.get("route_comments") or [], route_id, "route")
            )

        # Area comments
        comment_rows.extend(
            _build_comment_rows(area.get("area_comments") or [], area_id, "area")
        )

    # Build SQL statements — batched to stay under D1 100KB limit (T-02-03)
    sql_parts: list[str] = []

    if area_rows:
        for stmt in chunk_inserts(area_rows, "areas", AREAS_COLUMNS):
            sql_parts.append(stmt)

    if route_rows:
        for stmt in chunk_inserts(route_rows, "routes", ROUTES_COLUMNS):
            sql_parts.append(stmt)

    if comment_rows:
        for stmt in chunk_inserts(comment_rows, "comments", COMMENTS_COLUMNS):
            sql_parts.append(stmt)

    # FTS5 rebuild MUST be the last statement (Pitfall 3)
    sql_parts.append("INSERT INTO routes_fts(routes_fts) VALUES('rebuild');")

    sql = "\n".join(sql_parts)

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(sql, encoding="utf-8")
        logger.info("Wrote %d bytes to %s", len(sql), out)

    return sql


def main() -> None:
    """CLI entry point: transform tagged climbing JSON to D1 SQL."""
    parser = argparse.ArgumentParser(
        description="Transform tagged climbing JSON to D1 SQL"
    )
    parser.add_argument(
        "input",
        help="Input JSON file (e.g., data/arizona_routes_tagged.json)",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output SQL file (default: worker-api/import_<basename>.sql)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
    )
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    in_path = Path(args.input)
    out_path = (
        Path(args.output)
        if args.output
        else Path("worker-api") / f"import_{in_path.stem}.sql"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sql = generate_sql(in_path, out_path)
    logging.info("Wrote %d bytes of SQL to %s", len(sql), out_path)


if __name__ == "__main__":
    main()
