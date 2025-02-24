export interface AreaHierarchy {
    level: number;
    area_hierarchy_name: string;
    area_hierarchy_url: string;
}

export interface Comment {
    comment_author: string;
    comment_text: string;
    comment_time: string;
}

export interface Route {
    route_name: string;
    route_url: string;
    route_lr?: number; // Left-to-right order, optional
    route_grade: string;
    route_protection_grading: string;
    route_stars: number;
    route_votes: number;
    route_type: string;
    route_pitches: number;
    route_length_ft: number;
    route_length_meter: number;
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
}

export interface Area {
    area_id: string;
    area_url: string;
    area_name: string;
    area_gps: string;
    area_description: string;
    area_getting_there: string;
    area_tags: string[] | Record<string, string[]>;
    area_hierarchy: AreaHierarchy[];
    area_access_issues: string;
    area_page_views: string;
    area_shared_on: string;
    area_comments: Comment[];
    routes: Route[];
}

export interface AreaData {
    areas: Area[];
} 