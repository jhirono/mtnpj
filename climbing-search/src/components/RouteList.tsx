import { formatRouteName } from '../utils/formatters'
import type { Route } from '../types/route';

interface RouteListProps {
  routes: (Route & { area_name: string })[];
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
          {/* ... rest of route display ... */}
        </div>
      ))}
    </div>
  );
} 