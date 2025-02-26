import { Route, AreaHierarchy } from '../types/route'

interface RouteCardProps {
  route: Route & {
    area_name: string;
    area_hierarchy: AreaHierarchy[];
  }
}

function getShortLocation(hierarchy: AreaHierarchy[]): AreaHierarchy[] {
  // Skip "All Locations" and get last two levels
  const relevantHierarchy = hierarchy
    .filter(h => h.area_hierarchy_name !== "All Locations");
  
  // Return last two levels with full hierarchy info
  return relevantHierarchy.slice(-2);
}

export function RouteCard({ route }: RouteCardProps) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
      <div>
        {/* Route name and info */}
        <div className="flex items-baseline gap-2">
          <a 
            href={route.route_url}
            className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 font-medium"
            target="_blank"
            rel="noopener noreferrer"
          >
            {route.route_name}
          </a>
          <span className="text-gray-600 dark:text-gray-300 text-sm">
            {route.route_type} | {route.route_grade} {route.route_protection_grading} |
            <span className="text-yellow-500"> ★</span> {route.route_stars} ({route.route_votes}) |
            {route.route_length_ft && ` ${route.route_length_ft}ft`} |
            {` ${route.route_pitches} ${route.route_pitches === 1 ? 'pitch' : 'pitches'}`} |
            {/* Last two levels of area hierarchy with links */}
            {` `}{getShortLocation(route.area_hierarchy).map((h, i, arr) => (
              <span key={h.area_hierarchy_url}>
                <a 
                  href={h.area_hierarchy_url}
                  className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {h.area_hierarchy_name}
                </a>
                {i < arr.length - 1 ? " / " : ""}
              </span>
            ))}
          </span>
        </div>

        {/* Tags below - excluding certain categories */}
        <div className="mt-1.5 flex flex-wrap gap-1.5">
          {Object.entries(route.route_tags)
            .filter(([category]) => 
              category !== "Weather & Conditions" && 
              category !== "Approach & Accessibility"
            )
            .map(([category, tags]) =>
              tags.map(tag => (
                <span 
                  key={`${category}-${tag}`}
                  className="inline-flex px-2 py-0.5 text-xs bg-blue-50 dark:bg-blue-900 text-blue-600 dark:text-blue-300 rounded"
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