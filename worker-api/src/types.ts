export type Bindings = {
  DB: D1Database;
};

export const ALLOWED_TYPES = [
  'sport','trad','aid','ice','alpine','mixed','tr','boulder','snow',
] as const;
export type AllowedType = typeof ALLOWED_TYPES[number];

export const ALLOWED_TYPE_COLUMNS: Record<AllowedType, string> = {
  sport: 'is_sport', trad: 'is_trad', aid: 'is_aid', ice: 'is_ice',
  alpine: 'is_alpine', mixed: 'is_mixed', tr: 'is_tr',
  boulder: 'is_boulder', snow: 'is_snow',
};

export interface RouteRow {
  route_id: string; area_id: string; route_name: string; route_url: string;
  route_lr: number | null; route_grade: string | null;
  route_grade_numeric: number | null; route_protection_grading: string | null;
  route_stars: number | null; route_votes: number | null;
  is_sport: number; is_trad: number; is_aid: number; is_ice: number;
  is_alpine: number; is_mixed: number; is_tr: number; is_boulder: number; is_snow: number;
  route_pitches: number | null; route_length_ft: number | null; route_length_meter: number | null;
  route_fa: string | null; route_description: string | null; route_location: string | null;
  route_protection: string | null; route_page_views: number | null; route_shared_on: string | null;
  route_tags: string | null; route_suggested_ratings: string | null; route_tick_comments: string | null;
}

export interface AreaRow {
  area_id: string; parent_id: string | null; area_name: string; area_url: string;
  area_gps: string | null; area_description: string | null; area_getting_there: string | null;
  area_access_issues: string | null; area_page_views: number | null; area_shared_on: string | null;
  area_tags: string | null; path: string;
}
