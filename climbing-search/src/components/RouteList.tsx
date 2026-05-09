import { formatRouteName } from '../utils/formatters'
import type { RouteApi } from '../api/types';

interface RouteListProps {
  routes: RouteApi[];
}

export function RouteList({ routes }: RouteListProps) {
  return (
    <div>
      {routes.map(route => (
        <div key={route.route_id}>
          <h3>{formatRouteName(route.route_name)}</h3>
          <p>Area: {route.area_name}</p>
          <p>Grade: {route.route_grade}</p>
          {route.route_lr !== undefined && (
            <p>Left-to-right order: {route.route_lr}</p>
          )}
        </div>
      ))}
    </div>
  );
}
