"""
Tests for tagging/d1_tag_sync.py — tag sync transformer RED phase.

Tests cover:
  - route_id resolution (URL-derived MP ID, modern numeric passthrough, fallback MD5)
  - area_id resolution (same logic for areas)
  - build_route_tag_updates / build_area_tag_updates extraction
  - skip routes/areas with empty/missing tags
  - chunk_updates batching under 100KB limit
  - CASE-WHEN SQL generation
  - full pipeline via generate_sync_sql (SQLite in-memory integration test)
  - idempotent re-runs produce byte-identical SQL
  - SQL escaping of apostrophes in tag values (T-05-01)
"""

import hashlib
import json
import sqlite3
from pathlib import Path

from tagging.d1_tag_sync import (
    build_area_tag_updates,
    build_route_tag_updates,
    chunk_updates,
    generate_sync_sql,
    resolve_area_d1_id,
    resolve_route_d1_id,
)

FIXTURE = Path(__file__).parent / "test_fixtures" / "tagged_sample.json"


# ---------------------------------------------------------------------------
# Test 1: URL-derived MP ID overrides legacy UUID
# ---------------------------------------------------------------------------

def test_resolve_route_d1_id_from_url():
    route = {
        "route_url": "https://www.mountainproject.com/route/105733804/the-nose",
        "route_id": "legacy-uuid-1234",
    }
    assert resolve_route_d1_id(route) == "105733804"


# ---------------------------------------------------------------------------
# Test 2: Modern numeric IDs pass through unchanged
# ---------------------------------------------------------------------------

def test_resolve_route_d1_id_from_modern_id():
    route = {
        "route_url": "https://www.mountainproject.com/route/105733804/the-nose",
        "route_id": "105733804",
    }
    assert resolve_route_d1_id(route) == "105733804"


# ---------------------------------------------------------------------------
# Test 3: Garbage URL + uuid-style id → deterministic 12-char MD5 slice
# ---------------------------------------------------------------------------

def test_resolve_route_d1_id_falls_back_for_garbage_url():
    url = "https://www.mountainproject.com/totally-not-a-route"
    route = {
        "route_url": url,
        "route_id": "legacy-uuid-bad-1234",
    }
    result = resolve_route_d1_id(route)
    expected = hashlib.md5(url.encode()).hexdigest()[:12]
    assert result == expected, f"Expected MD5 fallback {expected!r}, got {result!r}"
    assert len(result) == 12


# ---------------------------------------------------------------------------
# Test 4: build_route_tag_updates returns (route_d1_id, tags_json) tuples
# ---------------------------------------------------------------------------

def test_build_route_tag_updates_basic():
    data = [
        {
            "area_id": "test-area",
            "area_url": "https://www.mountainproject.com/area/999999/test",
            "routes": [
                {
                    "route_url": "https://www.mountainproject.com/route/105733804/the-nose",
                    "route_id": "legacy-uuid",
                    "route_tags": {"Rope Length": ["rope_60m"]},
                }
            ],
        }
    ]
    updates = build_route_tag_updates(data)
    assert len(updates) == 1
    rid, tags_json = updates[0]
    assert rid == "105733804"
    parsed = json.loads(tags_json)
    assert parsed == {"Rope Length": ["rope_60m"]}


# ---------------------------------------------------------------------------
# Test 5: build_area_tag_updates returns (area_d1_id, tags_json) tuples
# ---------------------------------------------------------------------------

def test_build_area_tag_updates_basic():
    data = [
        {
            "area_url": "https://www.mountainproject.com/area/106584089/meatwad",
            "area_id": "legacy-uuid-area",
            "area_tags": {"Approach & Accessibility": ["approach_short"]},
            "routes": [],
        }
    ]
    updates = build_area_tag_updates(data)
    assert len(updates) == 1
    aid, tags_json = updates[0]
    assert aid == "106584089"
    parsed = json.loads(tags_json)
    assert parsed == {"Approach & Accessibility": ["approach_short"]}


# ---------------------------------------------------------------------------
# Test 6: Routes with empty/missing route_tags are skipped
# ---------------------------------------------------------------------------

def test_skip_routes_without_tags():
    data = json.loads(FIXTURE.read_text())
    updates = build_route_tag_updates(data)
    # Route C (100000002) has route_tags={} — must not appear
    route_ids = [rid for rid, _ in updates]
    assert "100000002" not in route_ids
    # Route A and B (with tags) must appear
    assert "106608542" in route_ids
    assert "100000001" in route_ids


# ---------------------------------------------------------------------------
# Test 7: chunk_updates keeps each statement under max_bytes
# ---------------------------------------------------------------------------

def test_chunk_updates_under_size_limit():
    # Generate 1000 synthetic update tuples
    updates = [(str(i), json.dumps({"Rope Length": ["rope_60m"]})) for i in range(1000)]
    max_bytes = 100_000
    chunks = chunk_updates("routes", "route_tags", "route_id", updates, max_bytes=max_bytes)
    assert len(chunks) >= 1
    for chunk in chunks:
        assert len(chunk.encode("utf-8")) <= max_bytes, (
            f"Chunk exceeds {max_bytes} bytes: {len(chunk.encode('utf-8'))}"
        )
    # Total UPDATE statements across all chunks must cover all 1000 rows
    total_when_clauses = sum(chunk.count("WHEN") for chunk in chunks)
    assert total_when_clauses == 1000, (
        f"Expected 1000 WHEN clauses, found {total_when_clauses}"
    )


# ---------------------------------------------------------------------------
# Test 8: chunk_updates uses CASE WHEN pattern
# ---------------------------------------------------------------------------

def test_chunk_updates_uses_case_when():
    updates = [("105733804", '{"Rope Length": ["rope_60m"]}')]
    chunks = chunk_updates("routes", "route_tags", "route_id", updates)
    assert len(chunks) == 1
    sql = chunks[0]
    assert "CASE route_id WHEN" in sql, f"Expected CASE WHEN in SQL, got:\n{sql}"
    assert "END WHERE route_id IN" in sql


# ---------------------------------------------------------------------------
# Test 9: generate_sync_sql full pipeline (SQLite in-memory integration)
# ---------------------------------------------------------------------------

def test_generate_sync_sql_full_pipeline(tmp_path):
    # Set up minimal schema matching worker-api/schema.sql essentials
    db_path = tmp_path / "test.db"
    con = sqlite3.connect(str(db_path))
    con.executescript("""
        CREATE TABLE areas (
            area_id TEXT PRIMARY KEY,
            area_tags TEXT,
            path TEXT NOT NULL DEFAULT '/',
            area_name TEXT NOT NULL DEFAULT '',
            area_url TEXT UNIQUE NOT NULL
        );
        CREATE TABLE routes (
            route_id TEXT PRIMARY KEY,
            area_id TEXT NOT NULL,
            route_name TEXT NOT NULL,
            route_url TEXT UNIQUE NOT NULL,
            route_tags TEXT
        );
        INSERT INTO areas (area_id, area_url)
            VALUES ('106584089', 'https://www.mountainproject.com/area/106584089/meatwad');
        INSERT INTO routes (route_id, area_id, route_name, route_url)
            VALUES ('106608542', '106584089', 'Cyborg', 'https://www.mountainproject.com/route/106608542/cyborg-sucker-punch');
        INSERT INTO routes (route_id, area_id, route_name, route_url)
            VALUES ('100000001', '106584089', 'O''Brien''s Route', 'https://www.mountainproject.com/route/100000001/o-briens-route');
        INSERT INTO routes (route_id, area_id, route_name, route_url)
            VALUES ('100000002', '106584089', 'No Tags', 'https://www.mountainproject.com/route/100000002/no-tags');
    """)
    con.commit()

    out_sql = tmp_path / "tag_update.sql"
    generate_sync_sql(FIXTURE, out_sql)
    con.executescript(out_sql.read_text())

    # Cyborg should have rope_60m tag
    cur = con.execute("SELECT route_tags FROM routes WHERE route_id = '106608542'")
    tags = json.loads(cur.fetchone()[0])
    assert "Rope Length" in tags and "rope_60m" in tags["Rope Length"]

    # O'Brien's apostrophe tag survived
    cur = con.execute("SELECT route_tags FROM routes WHERE route_id = '100000001'")
    tags = json.loads(cur.fetchone()[0])
    assert "Difficulty & Safety" in tags and "O'Brien" in tags["Difficulty & Safety"]

    # No-Tags route was NOT updated (route_tags stays NULL)
    cur = con.execute("SELECT route_tags FROM routes WHERE route_id = '100000002'")
    assert cur.fetchone()[0] is None

    # Area was updated
    cur = con.execute("SELECT area_tags FROM areas WHERE area_id = '106584089'")
    area_tags = json.loads(cur.fetchone()[0])
    assert "Approach & Accessibility" in area_tags

    con.close()


# ---------------------------------------------------------------------------
# Test 10: Idempotent re-runs produce byte-identical SQL
# ---------------------------------------------------------------------------

def test_idempotent_repeat_run(tmp_path):
    out1 = tmp_path / "run1.sql"
    out2 = tmp_path / "run2.sql"
    generate_sync_sql(FIXTURE, out1)
    generate_sync_sql(FIXTURE, out2)
    assert out1.read_text() == out2.read_text(), "Two runs produced different SQL output"


# ---------------------------------------------------------------------------
# Test 11: SQL escapes apostrophes in tag values (T-05-01)
# ---------------------------------------------------------------------------

def test_sql_escapes_special_chars_in_tag_values(tmp_path):
    out_sql = tmp_path / "tags.sql"
    generate_sync_sql(FIXTURE, out_sql)
    sql_text = out_sql.read_text()
    # The tag value "O'Brien" should appear as O''Brien in the SQL literal
    # (json.dumps wraps it in a JSON string; sql_quote then doubles the outer quotes)
    # The JSON-encoded version of "O'Brien" is "O'Brien" (apostrophe not escaped in JSON)
    # When sql_quote wraps the JSON string containing a single quote, it must double it.
    assert "O''Brien" in sql_text, (
        "Expected O''Brien (SQL-escaped apostrophe) in generated SQL"
    )
