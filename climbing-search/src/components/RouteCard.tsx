import type { Route } from '../types/route'

interface RouteCardProps {
  route: Route
}

export function RouteCard({ route }: RouteCardProps) {
  return (
    <div className="p-3 rounded border text-sm">
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
          {route.route_type} | {route.route_grade}
          {route.route_protection_grading && ` ${route.route_protection_grading}`} | 
          <span className="text-yellow-500">★</span> {route.route_stars} ({route.route_votes})
          {route.route_length_ft && ` | ${route.route_length_ft}ft`}
          {route.route_pitches && ` | ${route.route_pitches} pitches`}
        </span>
      </div>

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
  )
}