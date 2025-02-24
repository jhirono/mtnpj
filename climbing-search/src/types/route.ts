export interface AreaHierarchy {
  level: number;
  area_hierarchy_name: string;
  area_hierarchy_url: string;
}

export interface Route {
  route_name: string;
  route_url: string;
  route_lr?: number | string; // Can be number or string from JSON
  route_grade: string;
  route_protection_grading: string;
  route_stars: number;
  route_votes: number;
  route_type: string;
  route_pitches: number;
  route_length_ft: number | null;
  route_length_meter: number | null;
  route_fa: string;
  route_description: string;
  route_location: string;
  route_protection: string;
  route_page_views: string;
  route_shared_on: string;
  route_id: string;
  route_tags: Record<string, string[]>;
  route_composite_tags: any[];
  route_comments: Comment[];
  route_suggested_ratings: Record<string, number>;
  route_tick_comments: string;
  // Area context
  area_name: string;
  area_hierarchy: AreaHierarchy[];
}