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
    id?: string; // Firestore document ID
    route_id: string;
    route_name: string;
    route_url: string;
    route_lr?: number; // Left-to-right order, optional
    route_grade: string;
    normalized_grade: string; // Normalized grade for consistent comparison
    grade_numeric: number; // Numeric value for grade sorting
    route_protection_grading: string;
    route_stars: number;
    route_votes: number;
    quality_score: number; // Combined score of stars and votes
    route_type: string[]; // Array of route types
    route_pitches: number;
    route_length_ft: number;
    route_length_meter: number;
    route_fa: string;
    route_description: string;
    route_location: string;
    route_protection: string;
    route_page_views: string;
    route_shared_on: string;
    route_tags: Record<string, string[]>;
    route_composite_tags: any[];
    route_comments: Comment[];
    route_suggested_ratings: Record<string, number>;
    route_tick_comments: string;
    
    // Firebase-specific fields
    area_id: string; // Reference to parent area
    area_name: string; // Denormalized for easier querying
    area_hierarchy: AreaHierarchy[]; // Denormalized for easier querying
    area_hierarchy_path: string; // Path string for hierarchical queries
    
    // Boolean flags for efficient filtering
    is_multipitch: boolean;
    is_trad: boolean;
    is_sport: boolean;
    
    // Search optimization
    tags: string[]; // Flattened tags for easier querying
    searchable_text: string; // Combined text fields for search
    
    // Timestamps
    created_at: any; // Firebase Timestamp
    updated_at: any; // Firebase Timestamp
}

export interface Area {
    id?: string; // Firestore document ID
    area_id: string;
    area_url: string;
    area_name: string;
    area_gps: string;
    area_description: string;
    area_getting_there: string;
    area_tags: string[]; // Flattened tags array
    area_hierarchy: AreaHierarchy[];
    area_hierarchy_path: string; // Path string for hierarchical queries
    area_hierarchy_levels: number[]; // Array of hierarchy levels
    area_access_issues: string;
    area_page_views: string;
    area_shared_on: string;
    area_comments: Comment[];
    
    // Search optimization
    searchable_text: string; // Combined text fields for search
    
    // Timestamps
    created_at: any; // Firebase Timestamp
    updated_at: any; // Firebase Timestamp
    
    // Optional in Firestore since routes are stored separately
    routes?: Route[];
    
    // Tree structure for area hierarchy (not stored in Firestore)
    children?: Area[];
}

export interface AreaData {
    areas: Area[];
}

export interface RouteFilters {
    minGrade?: string;
    maxGrade?: string;
    types?: string[];
    tags?: string[];
    excludedTypes?: string[];
    isMultipitch?: boolean;
    isTrad?: boolean;
    isSport?: boolean;
    areaIds?: string[];
    areaPath?: string;
}

export interface SortConfig {
    key: 'grade' | 'stars' | 'votes' | 'lr' | 'quality';
    direction: 'asc' | 'desc';
}

// Firebase pagination
export interface PaginationState {
    lastVisible: any; // Last document for pagination
    hasMore: boolean;
    loading: boolean;
} 