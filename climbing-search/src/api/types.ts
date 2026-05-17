export const ROUTE_TYPES = ['sport','trad','aid','ice','alpine','mixed','tr','boulder','snow'] as const;
export type RouteType = typeof ROUTE_TYPES[number];

export interface RouteApi {
  route_id: string;
  area_id: string;
  route_name: string;
  route_url: string;
  route_lr: number | null;
  route_grade: string | null;
  route_grade_numeric: number | null;
  route_protection_grading: string | null;
  route_stars: number | null;
  route_votes: number | null;
  is_sport: number; is_trad: number; is_aid: number; is_ice: number;
  is_alpine: number; is_mixed: number; is_tr: number; is_boulder: number; is_snow: number;
  route_pitches: number | null;
  route_length_ft: number | null;
  route_length_meter: number | null;
  route_fa: string | null;
  route_description: string | null;
  route_location: string | null;
  route_protection: string | null;
  route_page_views: number | null;
  route_shared_on: string | null;
  route_tags: string | null;
  route_suggested_ratings: string | null;
  route_tick_comments: string | null;
  area_path: string;
  area_name: string;
  area_url: string | null;
}

export interface AreaApi {
  area_id: string;
  parent_id: string | null;
  area_name: string;
  area_url: string;
  area_gps: string | null;
  area_description: string | null;
  area_getting_there: string | null;
  area_access_issues: string | null;
  area_page_views: number | null;
  area_shared_on: string | null;
  area_tags: string | null;
  path: string;
  synthetic?: boolean;
}

export interface ApiFilters {
  q?: string;
  grade?: string;
  grade_min?: number;
  grade_max?: number;
  grade_system?: 'yds' | 'boulder' | 'aid' | 'ice' | 'mixed';
  grade_list?: string;
  type?: RouteType;
  region?: string;
  stars_min?: number;
  votes_min?: number;
  area_id?: string;
  page?: number;
  limit?: number;
}

export interface AreaFilters {
  q?: string;
  region?: string;
  parent_id?: string;
  page?: number;
  limit?: number;
}

export interface PageOpts { page?: number; limit?: number; }
export interface RoutePage { data: RouteApi[]; page: number; limit: number; }
export interface AreaPage { data: AreaApi[]; page: number; limit: number; }

/**
 * Map RouteApi.is_* booleans -> array of present route types.
 */
export function parseRouteTypes(row: RouteApi): RouteType[] {
  const out: RouteType[] = [];
  if (row.is_sport)   out.push('sport');
  if (row.is_trad)    out.push('trad');
  if (row.is_aid)     out.push('aid');
  if (row.is_ice)     out.push('ice');
  if (row.is_alpine)  out.push('alpine');
  if (row.is_mixed)   out.push('mixed');
  if (row.is_tr)      out.push('tr');
  if (row.is_boulder) out.push('boulder');
  if (row.is_snow)    out.push('snow');
  return out;
}
