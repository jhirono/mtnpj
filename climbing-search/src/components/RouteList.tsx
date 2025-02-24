interface RouteListProps {
  routes: (Route & { area_name: string })[];
  // ... other props
}

export function RouteList({ routes, ...props }: RouteListProps) {
  return (
    <div>
      {routes.map(route => (
        <div key={route.route_id}>
          <h3>{route.route_name}</h3>
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