"""
Test scaffold for Phase 2 tick comment collection.
Covers TICK-01 (login), TICK-02 (parse_stats), TICK-03 (D1 insert / dedup).

Tests marked @pytest.mark.xfail are RED-phase stubs: they will fail until
Plan 02 implements login_mp and updates parse_stats.
"""
import sqlite3
import pytest
from pathlib import Path
from unittest.mock import MagicMock
from bs4 import BeautifulSoup

FIXTURE_DIR = Path(__file__).parent / "test_fixtures"


def load_fixture(name: str) -> BeautifulSoup:
    html = (FIXTURE_DIR / name).read_text(encoding="utf-8")
    return BeautifulSoup(html, "lxml")


# ---------------------------------------------------------------------------
# TICK-02: parse_stats return shape (RED — will fail until Plan 02 lands)
# ---------------------------------------------------------------------------
@pytest.mark.xfail(reason="parse_stats not yet updated to return list[dict]")
def test_parse_stats_returns_entries():
    from scraping.scrape_mtnpj_final import parse_stats
    soup = load_fixture("stats_page_auth.html")
    _, _, tick_entries = parse_stats(soup)
    assert isinstance(tick_entries, list), "tick_entries must be a list"
    assert len(tick_entries) > 0, "Authenticated page must have at least one tick entry"
    entry = tick_entries[0]
    assert "author" in entry, "Each tick entry must have 'author' key"
    assert "date" in entry, "Each tick entry must have 'date' key"
    assert "text" in entry, "Each tick entry must have 'text' key"


@pytest.mark.xfail(reason="parse_stats not yet updated to return list[dict]")
def test_parse_stats_word_filter():
    """Entries with fewer than 15 words must be excluded (D-01)."""
    from scraping.scrape_mtnpj_final import parse_stats
    soup = load_fixture("stats_page_auth.html")
    _, _, tick_entries = parse_stats(soup)
    for entry in tick_entries:
        word_count = len(entry["text"].split())
        assert word_count >= 15, f"Tick entry below 15-word filter made it through: '{entry['text']}'"


def test_parse_stats_empty_on_noauth():
    """Unauthenticated page has no tick table — must return empty list."""
    from scraping.scrape_mtnpj_final import parse_stats
    soup = load_fixture("stats_page_noauth.html")
    _, _, tick_entries = parse_stats(soup)
    # Current parse_stats returns a string; after Plan 02 it returns list.
    # Either way, empty content for noauth page is acceptable.
    # This test passes in both old and new form.
    assert tick_entries == "" or tick_entries == [], (
        f"Unauthenticated page should have no ticks, got: {tick_entries!r}"
    )


# ---------------------------------------------------------------------------
# TICK-01: login_mp function signature (RED — will fail until Plan 02 lands)
# ---------------------------------------------------------------------------
@pytest.mark.xfail(reason="login_mp not yet implemented in scrape_mtnpj_final")
def test_login_mp_signature():
    """login_mp(driver, email, password) must exist and return bool."""
    from scraping.scrape_mtnpj_final import login_mp
    mock_driver = MagicMock()
    # Simulate a failed login (mock driver returns login URL after submit)
    mock_driver.current_url = "https://www.mountainproject.com/user/login"
    result = login_mp(mock_driver, "bad@example.com", "wrongpass")
    assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# TICK-03: INSERT OR IGNORE dedup (passes immediately — uses sqlite3 in-memory)
# ---------------------------------------------------------------------------
def test_tick_dedup():
    """Re-inserting the same comment_id with INSERT OR IGNORE must not duplicate."""
    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE comments (
            comment_id TEXT PRIMARY KEY,
            parent_id TEXT NOT NULL,
            parent_type TEXT NOT NULL,
            comment_author TEXT,
            comment_text TEXT,
            comment_time TEXT
        )
    """)
    insert_sql = """
        INSERT OR IGNORE INTO comments
        (comment_id, parent_id, parent_type, comment_author, comment_text, comment_time)
        VALUES ('abc123', 'route-id', 'tick', 'Alice', 'Great route, found it super sustained and fun.', '2024-01-01')
    """
    conn.execute(insert_sql)
    conn.execute(insert_sql)  # second insert — must be ignored
    count = conn.execute("SELECT COUNT(*) FROM comments WHERE comment_id='abc123'").fetchone()[0]
    assert count == 1, f"Expected 1 row after dedup insert, got {count}"
    conn.close()


# ---------------------------------------------------------------------------
# TICK-03: _build_comment_rows produces correct parent_type='tick' rows
# ---------------------------------------------------------------------------
def test_build_comment_rows_tick_type():
    from scraping.import_to_d1 import _build_comment_rows
    tick_entries = [
        {"comment_author": "Alice", "comment_text": "Long enough tick comment text here to pass filter.", "comment_time": "2024-01-01"},
    ]
    rows = _build_comment_rows(tick_entries, "test-route-id", "tick")
    assert len(rows) == 1, "Expected 1 row"
    assert "'tick'" in rows[0], f"Expected parent_type='tick' in row, got: {rows[0]}"
    assert "'test-route-id'" in rows[0], "Expected parent_id in row"
