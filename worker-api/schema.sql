-- D1 Schema for mtnpj climbing search
-- Generated for Phase 01-refactor Plan 02.
-- Decisions: D-13 (4 concepts: areas, routes, comments, hierarchy via path),
--            D-14 (route types as indexed boolean columns; tags as JSON column),
--            D-15 (adjacency list parent_id + materialized path on areas)

-- =====================================================================
-- areas: adjacency list (parent_id) + materialized path (path) hierarchy
-- =====================================================================
CREATE TABLE IF NOT EXISTS areas (
  area_id TEXT PRIMARY KEY,
  parent_id TEXT REFERENCES areas(area_id),
  area_name TEXT NOT NULL,
  area_url TEXT UNIQUE NOT NULL,
  area_gps TEXT,
  area_description TEXT,
  area_getting_there TEXT,
  area_access_issues TEXT,
  area_page_views INTEGER,
  area_shared_on TEXT,
  area_tags TEXT,  -- JSON string (legacy area-level tags from existing data)
  path TEXT NOT NULL  -- e.g. '/california/yosemite-national-park/el-capitan/'
);

CREATE INDEX IF NOT EXISTS idx_areas_parent ON areas(parent_id);
CREATE INDEX IF NOT EXISTS idx_areas_path ON areas(path);
CREATE INDEX IF NOT EXISTS idx_areas_name ON areas(area_name);

-- =====================================================================
-- routes: boolean type columns + tags JSON column + indexes
-- =====================================================================
CREATE TABLE IF NOT EXISTS routes (
  route_id TEXT PRIMARY KEY,
  area_id TEXT NOT NULL REFERENCES areas(area_id),
  route_name TEXT NOT NULL,
  route_url TEXT UNIQUE NOT NULL,
  route_lr INTEGER,
  route_grade TEXT,
  route_grade_numeric REAL,           -- normalized for ORDER BY / range filters
  route_protection_grading TEXT,
  route_stars REAL,
  route_votes INTEGER,
  -- D-14: boolean type columns (0/1), each indexed
  is_sport INTEGER NOT NULL DEFAULT 0,
  is_trad INTEGER NOT NULL DEFAULT 0,
  is_aid INTEGER NOT NULL DEFAULT 0,
  is_ice INTEGER NOT NULL DEFAULT 0,
  is_alpine INTEGER NOT NULL DEFAULT 0,
  is_mixed INTEGER NOT NULL DEFAULT 0,
  is_tr INTEGER NOT NULL DEFAULT 0,
  is_boulder INTEGER NOT NULL DEFAULT 0,
  is_snow INTEGER NOT NULL DEFAULT 0,
  route_pitches INTEGER,
  route_length_ft INTEGER,
  route_length_meter INTEGER,
  route_fa TEXT,
  route_description TEXT,
  route_location TEXT,
  route_protection TEXT,
  route_page_views INTEGER,
  route_shared_on TEXT,
  route_tags TEXT,                    -- JSON string (D-14)
  route_suggested_ratings TEXT,       -- JSON string
  route_tick_comments TEXT
);

CREATE INDEX IF NOT EXISTS idx_routes_area ON routes(area_id);
CREATE INDEX IF NOT EXISTS idx_routes_grade ON routes(route_grade_numeric);
CREATE INDEX IF NOT EXISTS idx_routes_stars ON routes(route_stars);
CREATE INDEX IF NOT EXISTS idx_routes_votes ON routes(route_votes);
CREATE INDEX IF NOT EXISTS idx_routes_sport ON routes(is_sport);
CREATE INDEX IF NOT EXISTS idx_routes_trad ON routes(is_trad);
CREATE INDEX IF NOT EXISTS idx_routes_aid ON routes(is_aid);
CREATE INDEX IF NOT EXISTS idx_routes_ice ON routes(is_ice);
CREATE INDEX IF NOT EXISTS idx_routes_alpine ON routes(is_alpine);
CREATE INDEX IF NOT EXISTS idx_routes_mixed ON routes(is_mixed);
CREATE INDEX IF NOT EXISTS idx_routes_tr ON routes(is_tr);
CREATE INDEX IF NOT EXISTS idx_routes_boulder ON routes(is_boulder);
CREATE INDEX IF NOT EXISTS idx_routes_snow ON routes(is_snow);

-- =====================================================================
-- comments: polymorphic (parent is route or area, by parent_type)
-- =====================================================================
CREATE TABLE IF NOT EXISTS comments (
  comment_id TEXT PRIMARY KEY,
  parent_id TEXT NOT NULL,
  parent_type TEXT NOT NULL CHECK(parent_type IN ('route', 'area')),
  comment_author TEXT,
  comment_text TEXT,
  comment_time TEXT
);

CREATE INDEX IF NOT EXISTS idx_comments_parent ON comments(parent_id, parent_type);

-- =====================================================================
-- FTS5: full-text search index over route_name + route_description
-- (D-12: D1 FTS5 for text search). External content table — populated
-- by INSERT INTO routes_fts(routes_fts) VALUES('rebuild') after bulk import.
-- See RESEARCH.md Pitfall 3.
-- =====================================================================
CREATE VIRTUAL TABLE IF NOT EXISTS routes_fts USING fts5(
  route_name,
  route_description,
  content='routes',
  content_rowid='rowid'
);
