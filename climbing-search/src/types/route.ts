// Re-export new API-shaped types as canonical Route/AreaHierarchy.
export type { RouteApi as Route, AreaApi } from '../api/types';
export type { RouteType } from '../api/types';
export { ROUTE_TYPES, parseRouteTypes } from '../api/types';

// Legacy hierarchy type kept for transitional compatibility.
export interface AreaHierarchy {
  level: number;
  area_hierarchy_name: string;
  area_hierarchy_url: string;
}
