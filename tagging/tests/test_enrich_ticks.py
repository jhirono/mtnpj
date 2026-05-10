"""
Tests for tagging/enrich_ticks.py — D1 tick comment enrichment.

Tests cover:
  - build_tick_map() returns dict keyed by route_id (str)
  - build_tick_map() excludes non-tick parent_type rows
  - enrich_routes_with_tick_comments() overwrites empty route_tick_comments
  - enrich_routes_with_tick_comments() preserves scraper tick comments not in D1
  - enrich_routes_with_tick_comments() overwrites when route_id IS in D1 (D1 is richer)
  - route_id int/str coercion — int route_id in JSON matches str key in tick_map
"""

import sqlite3

from tagging.enrich_ticks import build_tick_map, enrich_routes_with_tick_comments


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_in_memory_db():
    """Create an in-memory sqlite3 DB with the comments table and sample data."""
    con = sqlite3.connect(":memory:")
    con.execute("""
        CREATE TABLE comments (
            comment_id TEXT PRIMARY KEY,
            parent_id TEXT,
            parent_type TEXT,
            comment_author TEXT,
            comment_text TEXT,
            comment_time TEXT
        )
    """)
    con.executemany(
        "INSERT INTO comments VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("c1", "105733804", "tick", "user1", "Great climb", "2023-01-01"),
            ("c2", "105733804", "tick", "user2", "Bring extra gear", "2023-01-02"),
            ("c3", "999888777", "comment", "user3", "Should be excluded", "2023-01-03"),
        ],
    )
    con.commit()
    return con


# ---------------------------------------------------------------------------
# Test 1: build_tick_map returns dict keyed by route_id
# ---------------------------------------------------------------------------

def test_build_tick_map_returns_dict_keyed_by_route_id(tmp_path):
    """build_tick_map() returns a dict with route_id (str) as key and
    concatenated comment_text as value."""
    db_path = str(tmp_path / "test.sqlite")
    con = sqlite3.connect(db_path)
    con.execute("""
        CREATE TABLE comments (
            comment_id TEXT, parent_id TEXT, parent_type TEXT,
            comment_author TEXT, comment_text TEXT, comment_time TEXT
        )
    """)
    con.executemany(
        "INSERT INTO comments VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("c1", "105733804", "tick", "u1", "Great climb", "2023-01-01"),
            ("c2", "105733804", "tick", "u2", "Bring extra gear", "2023-01-02"),
        ],
    )
    con.commit()
    con.close()

    result = build_tick_map(db_path=db_path)
    assert isinstance(result, dict)
    assert "105733804" in result
    assert "Great climb" in result["105733804"]
    assert "Bring extra gear" in result["105733804"]


# ---------------------------------------------------------------------------
# Test 2: build_tick_map excludes non-tick parent_type rows
# ---------------------------------------------------------------------------

def test_build_tick_map_excludes_non_tick_types(tmp_path):
    """Rows with parent_type != 'tick' must not appear in the returned dict."""
    db_path = str(tmp_path / "test.sqlite")
    con = sqlite3.connect(db_path)
    con.execute("""
        CREATE TABLE comments (
            comment_id TEXT, parent_id TEXT, parent_type TEXT,
            comment_author TEXT, comment_text TEXT, comment_time TEXT
        )
    """)
    con.executemany(
        "INSERT INTO comments VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("c1", "105733804", "tick", "u1", "Great climb", "2023-01-01"),
            ("c3", "999888777", "comment", "u3", "Should be excluded", "2023-01-03"),
        ],
    )
    con.commit()
    con.close()

    result = build_tick_map(db_path=db_path)
    assert "999888777" not in result
    assert "105733804" in result


# ---------------------------------------------------------------------------
# Test 3: enrich overwrites empty route_tick_comments with D1 value
# ---------------------------------------------------------------------------

def test_enrich_routes_overwrites_empty_route_tick_comments():
    """Route with route_tick_comments='' and route_id in tick_map gets D1 value."""
    tick_map = {"105733804": "Great climb | Bring extra gear"}
    data = [
        {
            "routes": [
                {
                    "route_id": "105733804",
                    "route_tick_comments": "",
                }
            ]
        }
    ]
    result = enrich_routes_with_tick_comments(data, tick_map)
    assert result[0]["routes"][0]["route_tick_comments"] == "Great climb | Bring extra gear"


# ---------------------------------------------------------------------------
# Test 4: enrich preserves scraper tick comments for routes NOT in tick_map
# ---------------------------------------------------------------------------

def test_enrich_routes_preserves_scraper_tick_comments():
    """Route with existing route_tick_comments whose route_id is NOT in tick_map
    retains its original value unchanged."""
    tick_map = {}  # empty — route_id not in D1
    data = [
        {
            "routes": [
                {
                    "route_id": "105733804",
                    "route_tick_comments": "some scraper text",
                }
            ]
        }
    ]
    result = enrich_routes_with_tick_comments(data, tick_map)
    assert result[0]["routes"][0]["route_tick_comments"] == "some scraper text"


# ---------------------------------------------------------------------------
# Test 5: enrich overwrites when route_id IS in D1 (D1 is richer)
# ---------------------------------------------------------------------------

def test_enrich_routes_overwrites_when_route_id_in_d1():
    """Route with existing scraper text whose route_id IS in tick_map gets
    replaced with the richer D1 value."""
    tick_map = {"105733804": "D1 rich comment | Another comment"}
    data = [
        {
            "routes": [
                {
                    "route_id": "105733804",
                    "route_tick_comments": "old scraper text",
                }
            ]
        }
    ]
    result = enrich_routes_with_tick_comments(data, tick_map)
    assert result[0]["routes"][0]["route_tick_comments"] == "D1 rich comment | Another comment"


# ---------------------------------------------------------------------------
# Test 6: route_id int in JSON matches str key in tick_map
# ---------------------------------------------------------------------------

def test_enrich_routes_route_id_cast_to_str():
    """route_id=105733804 (int) in JSON is cast to str '105733804' before
    lookup in tick_map, which stores keys as strings (from sqlite3)."""
    tick_map = {"105733804": "Great climb"}
    data = [
        {
            "routes": [
                {
                    "route_id": 105733804,  # int, not str
                    "route_tick_comments": "",
                }
            ]
        }
    ]
    result = enrich_routes_with_tick_comments(data, tick_map)
    assert result[0]["routes"][0]["route_tick_comments"] == "Great climb"
