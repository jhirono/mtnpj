"""
Tests for scraping/import_to_d1.py

Tests are written against the expected function signatures and behavior.
Module import will fail (RED) until import_to_d1.py is created in Task 3.
"""
import json
from pathlib import Path
from scraping.import_to_d1 import (
    parse_route_type_to_booleans,
    build_materialized_path,
    grade_to_numeric,
    extract_mp_id_from_url,
    chunk_inserts,
    sql_quote,
    generate_sql,
)

FIXTURE = Path(__file__).parent / "test_fixtures" / "sample_area.json"


# ---------------------------------------------------------------------------
# Test 1: Basic sport type parsing
# ---------------------------------------------------------------------------
def test_parse_route_type_to_booleans_basic():
    result = parse_route_type_to_booleans("Sport, 80 ft")
    assert result == {
        "is_sport": 1,
        "is_trad": 0,
        "is_aid": 0,
        "is_ice": 0,
        "is_alpine": 0,
        "is_mixed": 0,
        "is_tr": 0,
        "is_boulder": 0,
        "is_snow": 0,
    }, f"Expected only is_sport=1, got {result}"


# ---------------------------------------------------------------------------
# Test 2: Compound type parsing (trad + aid)
# ---------------------------------------------------------------------------
def test_parse_route_type_to_booleans_compound():
    result = parse_route_type_to_booleans("Trad, Aid, 3 pitches, 350 ft")
    assert result["is_trad"] == 1, "Expected is_trad=1"
    assert result["is_aid"] == 1, "Expected is_aid=1"
    # All other booleans must be 0
    for col in ["is_sport", "is_ice", "is_alpine", "is_mixed", "is_tr", "is_boulder", "is_snow"]:
        assert result[col] == 0, f"Expected {col}=0, got {result[col]}"


# ---------------------------------------------------------------------------
# Test 3: Top rope type with alias
# ---------------------------------------------------------------------------
def test_parse_route_type_to_booleans_top_rope():
    result_tr = parse_route_type_to_booleans("TR, 100 ft")
    assert result_tr["is_tr"] == 1, "Expected is_tr=1 for 'TR, 100 ft'"

    result_top_rope = parse_route_type_to_booleans("Top Rope, 100 ft")
    assert result_top_rope["is_tr"] == 1, "Expected is_tr=1 for 'Top Rope, 100 ft'"


# ---------------------------------------------------------------------------
# Test 4: Grade modifier tokens are dropped (not parsed as type)
# ---------------------------------------------------------------------------
def test_parse_route_type_to_booleans_grade_modifier_dropped():
    result = parse_route_type_to_booleans("Trad, Alpine, Grade III, 8 pitches")
    assert result["is_trad"] == 1, "Expected is_trad=1"
    assert result["is_alpine"] == 1, "Expected is_alpine=1"
    # Grade III should NOT produce any boolean set to 1
    assert "is_grade" not in result, "No is_grade column should exist"
    # Ensure no unexpected booleans are set
    for col in ["is_sport", "is_aid", "is_ice", "is_mixed", "is_tr", "is_boulder", "is_snow"]:
        assert result[col] == 0, f"Expected {col}=0, got {result[col]}"


# ---------------------------------------------------------------------------
# Test 5: Empty and None inputs produce all zeros without crashing
# ---------------------------------------------------------------------------
def test_parse_route_type_to_booleans_empty():
    expected_all_zero = {
        "is_sport": 0,
        "is_trad": 0,
        "is_aid": 0,
        "is_ice": 0,
        "is_alpine": 0,
        "is_mixed": 0,
        "is_tr": 0,
        "is_boulder": 0,
        "is_snow": 0,
    }
    assert parse_route_type_to_booleans("") == expected_all_zero
    assert parse_route_type_to_booleans(None) == expected_all_zero


# ---------------------------------------------------------------------------
# Test 6: Materialized path built from URL slugs
# ---------------------------------------------------------------------------
def test_build_materialized_path_basic():
    hierarchy = [
        {"area_hierarchy_url": "https://www.mountainproject.com/route-guide"},
        {"area_hierarchy_url": "https://www.mountainproject.com/area/105708962/arizona"},
        {"area_hierarchy_url": "https://www.mountainproject.com/area/107447521/southern-arizona"},
    ]
    result = build_materialized_path(hierarchy)
    assert result == "/arizona/southern-arizona/", (
        f"Expected '/arizona/southern-arizona/', got '{result}'"
    )


# ---------------------------------------------------------------------------
# Test 7: URLs with trailing slashes parsed identically to those without
# ---------------------------------------------------------------------------
def test_build_materialized_path_handles_trailing_slash():
    hierarchy_with_slash = [
        {"area_hierarchy_url": "https://www.mountainproject.com/route-guide/"},
        {"area_hierarchy_url": "https://www.mountainproject.com/area/105708962/arizona/"},
        {"area_hierarchy_url": "https://www.mountainproject.com/area/107447521/southern-arizona/"},
    ]
    hierarchy_without_slash = [
        {"area_hierarchy_url": "https://www.mountainproject.com/route-guide"},
        {"area_hierarchy_url": "https://www.mountainproject.com/area/105708962/arizona"},
        {"area_hierarchy_url": "https://www.mountainproject.com/area/107447521/southern-arizona"},
    ]
    assert build_materialized_path(hierarchy_with_slash) == build_materialized_path(
        hierarchy_without_slash
    ), "Trailing slash should not affect result"


# ---------------------------------------------------------------------------
# Test 8: Grade to numeric conversion
# ---------------------------------------------------------------------------
def test_grade_to_numeric_basic():
    assert grade_to_numeric("5.10a") == 10.1, "5.10a should be 10.1"
    assert grade_to_numeric("5.9") == 9.0, "5.9 should be 9.0"
    assert grade_to_numeric("5.11d") == 11.4, "5.11d should be 11.4"
    assert grade_to_numeric("V3") is None, "Boulder grades should return None"
    assert grade_to_numeric("Unknown") is None, "Unknown should return None"


# ---------------------------------------------------------------------------
# Test 9: Extract MP numeric ID from URL
# ---------------------------------------------------------------------------
def test_extract_mp_id_from_url():
    area_url = "https://www.mountainproject.com/area/105708962/arizona"
    assert extract_mp_id_from_url(area_url) == "105708962"

    route_url = "https://www.mountainproject.com/route/105733804/the-nose"
    assert extract_mp_id_from_url(route_url) == "105733804"


# ---------------------------------------------------------------------------
# Test 10: Batch inserts respect size limit and no rows are dropped
# ---------------------------------------------------------------------------
def test_batch_inserts_under_size_limit():
    # Generate 1000 fake route value tuples
    rows = [f"('{i}','Route {i}',1,0,0,0,0,0,0,0,0)" for i in range(1000)]
    table = "routes"
    columns = ["route_id", "route_name", "is_sport", "is_trad", "is_aid",
               "is_ice", "is_alpine", "is_mixed", "is_tr", "is_boulder", "is_snow"]

    statements = chunk_inserts(rows, table, columns, max_bytes=100_000)

    # No single statement exceeds 100KB
    for stmt in statements:
        assert len(stmt.encode("utf-8")) <= 100_000, (
            f"Statement exceeds 100KB: {len(stmt.encode('utf-8'))} bytes"
        )

    # Count total rows inserted across all statements
    total_rows = 0
    for stmt in statements:
        # Count the number of '(' that start value tuples after VALUES
        values_part = stmt.split("VALUES", 1)[-1]
        total_rows += values_part.count("(")

    assert total_rows == 1000, f"Expected 1000 rows, got {total_rows}"


# ---------------------------------------------------------------------------
# Test 11: SQL quote escapes single quotes
# ---------------------------------------------------------------------------
def test_sql_escape_single_quotes():
    result = sql_quote("O'Brien's Route")
    assert result == "'O''Brien''s Route'", (
        f"Expected \"'O''Brien''s Route'\", got {result!r}"
    )


# ---------------------------------------------------------------------------
# Test 12: generate_sql is deterministic (same input → same output)
# ---------------------------------------------------------------------------
def test_import_idempotent():
    sql_first = generate_sql(FIXTURE)
    sql_second = generate_sql(FIXTURE)
    assert sql_first == sql_second, "generate_sql must be deterministic for same input"


# ---------------------------------------------------------------------------
# Test 13: FTS rebuild statement is appended at end of generated SQL
# ---------------------------------------------------------------------------
def test_fts_rebuild_appended():
    sql = generate_sql(FIXTURE)
    fts_rebuild = "INSERT INTO routes_fts(routes_fts) VALUES('rebuild');"
    # FTS rebuild precedes the final PRAGMA foreign_keys = 1 re-enable statement
    assert fts_rebuild in sql, (
        f"Expected FTS rebuild statement in SQL. Last 200 chars: {sql[-200:]!r}"
    )
    fts_pos = sql.rindex(fts_rebuild)
    pragma_pos = sql.rindex("PRAGMA foreign_keys = 1;")
    assert fts_pos < pragma_pos, "FTS rebuild must appear before PRAGMA foreign_keys = 1"
