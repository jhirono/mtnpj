import { ALLOWED_TYPE_COLUMNS, AllowedType } from '../types';

export interface RouteFilters {
  q?: string;
  grade?: string;
  grade_min?: number;
  grade_max?: number;
  type?: AllowedType;
  region?: string;
  stars_min?: number;
  votes_min?: number;
  area_id?: string;
  area_path?: string; // resolved path for area_id — avoids subquery inside LIKE
  page: number;
  limit: number;
}

export function buildRoutesQuery(f: RouteFilters): { sql: string; params: unknown[] } {
  const conds: string[] = ['1=1'];
  const params: unknown[] = [];

  // FTS5 full-text search
  if (f.q) {
    conds.push(`r.rowid IN (SELECT rowid FROM routes_fts WHERE routes_fts MATCH ?)`);
    params.push(f.q);
  }
  if (f.grade) { conds.push('r.route_grade = ?'); params.push(f.grade); }
  if (f.grade_min !== undefined) { conds.push('r.route_grade_numeric >= ?'); params.push(f.grade_min); }
  if (f.grade_max !== undefined) { conds.push('r.route_grade_numeric <= ?'); params.push(f.grade_max); }
  if (f.type) {
    // type is enum-validated; column name is sourced from ALLOWED_TYPE_COLUMNS,
    // never from raw user input. Static-known column name = safe to interpolate.
    const col = ALLOWED_TYPE_COLUMNS[f.type];
    conds.push(`r.${col} = 1`);
  }
  if (f.region) { conds.push('a.path LIKE ?'); params.push(`/${f.region}/%`); }
  if (f.stars_min !== undefined) { conds.push('r.route_stars >= ?'); params.push(f.stars_min); }
  if (f.votes_min !== undefined) { conds.push('r.route_votes >= ?'); params.push(f.votes_min); }
  if (f.area_id) {
    if (f.area_path) {
      // D1 rejects LIKE/GLOB with long slug paths ("pattern too complex").
      // INSTR(path, prefix) = 1 is a reliable prefix-match that avoids backtracking.
      conds.push(`(r.area_id = ? OR INSTR(a.path, ?) = 1)`);
      params.push(f.area_id, f.area_path);
    } else {
      conds.push(`r.area_id = ?`);
      params.push(f.area_id);
    }
  }

  const offset = (f.page - 1) * f.limit;
  const sql = `
    SELECT r.*, a.path AS area_path, a.area_name AS area_name, a.area_url AS area_url
    FROM routes r
    JOIN areas a ON r.area_id = a.area_id
    WHERE ${conds.join(' AND ')}
    ORDER BY r.route_votes DESC, r.route_stars DESC
    LIMIT ? OFFSET ?
  `;
  params.push(f.limit, offset);
  return { sql, params };
}

export function buildAreasQuery(opts: {
  q?: string; region?: string; parent_id?: string; page: number; limit: number;
}): { sql: string; params: unknown[] } {
  const conds: string[] = ['1=1'];
  const params: unknown[] = [];
  if (opts.q) {
    // area_name is stored as slugs (e.g. "el-capitan"); normalise user input the same way
    const slug = opts.q.toLowerCase().replace(/\s+/g, '-');
    conds.push('(area_name LIKE ? OR path LIKE ?)');
    params.push(`%${slug}%`, `%${slug}%`);
  }
  if (opts.region) { conds.push('path LIKE ?'); params.push(`/${opts.region}/%`); }
  if (opts.parent_id) { conds.push('parent_id = ?'); params.push(opts.parent_id); }
  const offset = (opts.page - 1) * opts.limit;
  const sql = `SELECT * FROM areas WHERE ${conds.join(' AND ')} ORDER BY area_name LIMIT ? OFFSET ?`;
  params.push(opts.limit, offset);
  return { sql, params };
}
