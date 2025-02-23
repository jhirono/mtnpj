export interface Route {
  route_name: string;
  route_url: string;
  route_grade: string;
  route_type: 'Trad' | 'Sport';
  route_stars: number;
  route_votes: number;
  route_protection_grading?: 'G' | 'PG13' | 'R' | 'X';
  route_tags: {
    [category: string]: string[];
  };
  route_length_ft?: number;
  route_pitches?: number;
  route_description?: string;
  route_lr?: number;  // Left to right ordering
}