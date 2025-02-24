import { Route, AreaHierarchy } from '../types/route'

interface RouteCardProps {
  route: Route & {
    area_name: string;
    area_hierarchy: AreaHierarchy[];
  }
}

function getShortLocation(hierarchy: AreaHierarchy[]): string {
  // Skip "All Locations" and get last two levels
  const relevantHierarchy = hierarchy
    .filter(h => h.area_hierarchy_name !== "All Locations")
    .map(h => h.area_hierarchy_name);

  // Return last two levels
  return relevantHierarchy.slice(-2).join(' / ');
}

export function RouteCard({ route }: RouteCardProps) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div>
        {/* Route name and info */}
        <div className="flex items-baseline gap-2">
          <a 
            href={route.route_url}
            className="text-blue-600 hover:text-blue-800 font-medium"
            target="_blank"
            rel="noopener noreferrer"
          >
            {route.route_name}
          </a>
          <span className="text-gray-600 text-sm">
            {route.route_type} | {route.route_grade} |
            <span className="text-yellow-500">★</span> {route.route_stars} ({route.route_votes}) | 
            {getShortLocation(route.area_hierarchy)} |
            {route.route_length_ft && ` ${route.route_length_ft}ft |`}
            {route.route_pitches} {route.route_pitches === 1 ? 'pitch' : 'pitches'}
          </span>
        </div>

        {/* Tags below */}
        <div className="mt-1.5 flex flex-wrap gap-1.5">
          {Object.entries(route.route_tags).map(([category, tags]) =>
            tags.map(tag => (
              <span 
                key={`${category}-${tag}`}
                className="inline-flex px-2 py-0.5 text-xs bg-blue-50 text-blue-600 rounded"
              >
                {tag}
              </span>
            ))
          )}
        </div>
      </div>
    </div>
  );
}