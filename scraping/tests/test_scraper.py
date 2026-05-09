"""
Unit tests for scrape_async.py
RED phase: these tests import from scrape_async which does not yet exist.
They MUST fail at import time until Task 2 creates the module.
"""
from pathlib import Path
from bs4 import BeautifulSoup

FIXTURE_DIR = Path(__file__).parent / "test_fixtures"


def load_fixture(name: str) -> BeautifulSoup:
    html = (FIXTURE_DIR / name).read_text(encoding="utf-8")
    return BeautifulSoup(html, "lxml")


from scraping.scrape_async import get_sub_area_links, is_lowest_level_area, extract_mp_route_id, parse_route_type_string, diff_routes_by_id


# ---------------------------------------------------------------------------
# Test 1: sub-area links for deep hierarchy area (Yosemite)
# ---------------------------------------------------------------------------
def test_get_sub_area_links_yosemite():
    soup = load_fixture("yosemite_area.html")
    links = get_sub_area_links(soup)
    assert len(links) >= 5, f"Expected >= 5 sub-area links, got {len(links)}"


# ---------------------------------------------------------------------------
# Test 2: sub-area detection falls back gracefully when primary div class missing
# ---------------------------------------------------------------------------
def test_get_sub_area_links_handles_missing_class():
    """When max-height div class is renamed/missing, falls back to href-based detection."""
    html = """<html><body>
    <div id="left-nav">
      <a href="/area/111111111/sub-area-one">Sub Area One</a>
      <a href="/area/222222222/sub-area-two">Sub Area Two</a>
      <a href="/route/333333333/some-route">Some Route</a>
    </div>
    </body></html>"""
    soup = BeautifulSoup(html, "lxml")
    links = get_sub_area_links(soup)
    hrefs = [a.get("href", "") for a in links]
    assert any("/area/" in h for h in hrefs), (
        f"Expected /area/ links from fallback strategy, got: {hrefs}"
    )


# ---------------------------------------------------------------------------
# Test 3: is_lowest_level_area returns True for leaf fixture
# ---------------------------------------------------------------------------
def test_is_lowest_level_area_true():
    soup = load_fixture("leaf_area.html")
    sub_areas = get_sub_area_links(soup)
    result = is_lowest_level_area(soup, sub_areas)
    assert result is True, "Leaf area with routes and no sub-areas should return True"


# ---------------------------------------------------------------------------
# Test 4: is_lowest_level_area returns False when sub-areas exist
# ---------------------------------------------------------------------------
def test_is_lowest_level_area_false_when_subareas_exist():
    """Area with both sub-areas and routes → False (sub-area traversal takes precedence)."""
    html = """<html><body>
    <div class="max-height max-height-md-0 max-height-xs-400">
      <a href="/area/111111111/sub-area-one">Sub Area One</a>
      <a href="/area/222222222/sub-area-two">Sub Area Two</a>
    </div>
    <table id="left-nav-route-table">
      <tr><td><a href="/route/333333333/some-route">Some Route</a></td></tr>
    </table>
    </body></html>"""
    soup = BeautifulSoup(html, "lxml")
    sub_areas = get_sub_area_links(soup)
    result = is_lowest_level_area(soup, sub_areas)
    assert result is False, "Area with sub-areas should return False even if routes exist"


# ---------------------------------------------------------------------------
# Test 5: extract_mp_route_id is stable and returns numeric string
# ---------------------------------------------------------------------------
def test_extract_mp_route_id_stable():
    url = "https://www.mountainproject.com/route/105733804/the-nose"
    result1 = extract_mp_route_id(url)
    result2 = extract_mp_route_id(url)
    assert result1 == "105733804", f"Expected '105733804', got '{result1}'"
    assert result1 == result2, "Same URL must return same ID (stable)"
    # Must NOT be UUID4
    import re
    assert not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-4', result1), (
        "route_id must not be a UUID4"
    )


# ---------------------------------------------------------------------------
# Test 6: extract_mp_route_id falls back to deterministic hash (not uuid4)
# ---------------------------------------------------------------------------
def test_extract_mp_route_id_fallback():
    """Malformed URL with no numeric segment → deterministic hash, NOT uuid4."""
    url = "https://www.mountainproject.com/route/the-nose"
    result1 = extract_mp_route_id(url)
    result2 = extract_mp_route_id(url)
    # Must be deterministic
    assert result1 == result2, "Fallback hash must be deterministic"
    # Must NOT look like uuid4
    import re
    assert not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-4', result1), (
        "Fallback must not be a UUID4"
    )
    # Must not be empty
    assert len(result1) > 0, "Fallback ID must not be empty"


# ---------------------------------------------------------------------------
# Test 7: parse_route_type_string handles all 9 type variants
# ---------------------------------------------------------------------------
def test_parse_route_type_string_all_types():
    # Multi-type with pitches and feet
    result = parse_route_type_string("Trad, Aid, 3 pitches, 350 ft")
    assert result["types"] == ["Trad", "Aid"], f"Expected ['Trad', 'Aid'], got {result['types']}"
    assert result["pitches"] == 3, f"Expected 3 pitches, got {result['pitches']}"
    assert result["length_ft"] == 350, f"Expected 350 ft, got {result['length_ft']}"
    assert result["length_m"] is None, f"Expected None length_m, got {result['length_m']}"

    # Sport with feet only
    result2 = parse_route_type_string("Sport, 80 ft")
    assert result2["types"] == ["Sport"], f"Expected ['Sport'], got {result2['types']}"
    assert result2["pitches"] == 1, f"Expected 1 pitch, got {result2['pitches']}"
    assert result2["length_ft"] == 80, f"Expected 80 ft, got {result2['length_ft']}"
    assert result2["length_m"] is None

    # Boulder with no length
    result3 = parse_route_type_string("Boulder")
    assert result3["types"] == ["Boulder"], f"Expected ['Boulder'], got {result3['types']}"
    assert result3["pitches"] == 1
    assert result3["length_ft"] is None
    assert result3["length_m"] is None


# ---------------------------------------------------------------------------
# Test 8: parse_route_type_string drops grade modifiers
# ---------------------------------------------------------------------------
def test_parse_route_type_with_grade_modifier():
    result = parse_route_type_string("Trad, Alpine, Grade III, 8 pitches, 800 ft")
    assert "Alpine" in result["types"], f"'Alpine' should be in types: {result['types']}"
    assert "Trad" in result["types"], f"'Trad' should be in types: {result['types']}"
    assert "Grade III" not in result["types"], (
        f"'Grade III' should be dropped from types: {result['types']}"
    )
    assert result["pitches"] == 8
    assert result["length_ft"] == 800


# ---------------------------------------------------------------------------
# Test 9: diff_routes_by_id computes added/removed/unchanged correctly
# ---------------------------------------------------------------------------
def test_diff_routes_by_stable_id():
    existing_routes = [
        {"route_id": "105733804", "route_name": "The Nose"},
        {"route_id": "105733805", "route_name": "Salathe"},
    ]
    scraped_route_urls = [
        "https://www.mountainproject.com/route/105733804/the-nose",
        "https://www.mountainproject.com/route/105733806/zodiac",
    ]
    result = diff_routes_by_id(existing_routes, scraped_route_urls)
    assert result["added"] == ["105733806"], f"Expected added=['105733806'], got {result['added']}"
    assert result["removed"] == ["105733805"], f"Expected removed=['105733805'], got {result['removed']}"
    assert result["unchanged"] == ["105733804"], f"Expected unchanged=['105733804'], got {result['unchanged']}"
