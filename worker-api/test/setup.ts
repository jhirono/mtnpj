import { env } from 'cloudflare:test';

// Schema SQL inlined to avoid node:fs in the Workers runtime environment
const SCHEMA_SQL = `
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
  area_tags TEXT,
  path TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_areas_parent ON areas(parent_id);
CREATE INDEX IF NOT EXISTS idx_areas_path ON areas(path);
CREATE INDEX IF NOT EXISTS idx_areas_name ON areas(area_name);

CREATE TABLE IF NOT EXISTS routes (
  route_id TEXT PRIMARY KEY,
  area_id TEXT NOT NULL REFERENCES areas(area_id),
  route_name TEXT NOT NULL,
  route_url TEXT UNIQUE NOT NULL,
  route_lr INTEGER,
  route_grade TEXT,
  route_grade_numeric REAL,
  route_protection_grading TEXT,
  route_stars REAL,
  route_votes INTEGER,
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
  route_tags TEXT,
  route_suggested_ratings TEXT,
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

CREATE TABLE IF NOT EXISTS comments (
  comment_id TEXT PRIMARY KEY,
  parent_id TEXT NOT NULL,
  parent_type TEXT NOT NULL CHECK(parent_type IN ('route', 'area')),
  comment_author TEXT,
  comment_text TEXT,
  comment_time TEXT
);

CREATE INDEX IF NOT EXISTS idx_comments_parent ON comments(parent_id, parent_type);

CREATE VIRTUAL TABLE IF NOT EXISTS routes_fts USING fts5(
  route_name,
  route_description,
  content='routes',
  content_rowid='rowid'
)
`;

export async function seedDB(db: D1Database): Promise<void> {
  // Apply schema from inlined SQL (node:fs not available in Workers runtime)
  const stmts = SCHEMA_SQL.split(/;\s*\n/).map(s => s.trim()).filter(Boolean);
  for (const stmt of stmts) {
    await db.prepare(stmt).run();
  }
  // Seed fixture data
  await db.batch([
    db.prepare("INSERT INTO areas (area_id, parent_id, area_name, area_url, path) VALUES ('100', NULL, 'Arizona', 'https://example.com/area/100/arizona', '/arizona/')"),
    db.prepare("INSERT INTO areas (area_id, parent_id, area_name, area_url, path) VALUES ('200', '100', 'Southern Arizona', 'https://example.com/area/200/southern-arizona', '/arizona/southern-arizona/')"),
    db.prepare("INSERT INTO areas (area_id, parent_id, area_name, area_url, path) VALUES ('300', '200', 'Panther Peak', 'https://example.com/area/300/panther-peak', '/arizona/southern-arizona/panther-peak/')"),
    // 5 routes: one per type (sport, trad, aid, boulder, ice)
    db.prepare("INSERT INTO routes (route_id, area_id, route_name, route_url, route_grade, route_grade_numeric, route_stars, route_votes, is_sport, route_description) VALUES ('1001', '300', 'Sport Climb', 'https://example.com/route/1001/sport-climb', '5.10b', 10.2, 3.5, 50, 1, 'A nice sport route up the wall')"),
    db.prepare("INSERT INTO routes (route_id, area_id, route_name, route_url, route_grade, route_grade_numeric, route_stars, route_votes, is_trad, route_description) VALUES ('1002', '300', 'Crack Master', 'https://example.com/route/1002/crack-master', '5.9', 9.0, 4.0, 100, 1, 'Classic finger crack with tricky moves')"),
    db.prepare("INSERT INTO routes (route_id, area_id, route_name, route_url, route_grade, route_grade_numeric, route_stars, route_votes, is_trad, is_aid, route_description) VALUES ('12345', '300', 'The Nose', 'https://example.com/route/12345/the-nose', '5.14a', 14.1, 4.0, 500, 1, 1, 'Iconic big wall with crack systems')"),
    db.prepare("INSERT INTO routes (route_id, area_id, route_name, route_url, route_grade, route_grade_numeric, route_stars, route_votes, is_boulder) VALUES ('1004', '300', 'Boulder Problem', 'https://example.com/route/1004/boulder-problem', 'V3', NULL, 3.0, 25, 1)"),
    db.prepare("INSERT INTO routes (route_id, area_id, route_name, route_url, route_grade, route_grade_numeric, route_stars, route_votes, is_ice) VALUES ('1005', '300', 'Frozen Pillar', 'https://example.com/route/1005/frozen-pillar', 'WI4', NULL, 3.5, 40, 1)"),
    // FTS rebuild after inserting routes
    db.prepare("INSERT INTO routes_fts(routes_fts) VALUES('rebuild')"),
  ]);
}

export { env };
