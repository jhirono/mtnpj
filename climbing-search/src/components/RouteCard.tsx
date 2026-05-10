import { formatRouteName } from '../utils/formatters'
import { useMemo } from 'react'
import type { RouteApi } from '../api/types'
import { parseRouteTypes, ROUTE_TYPES } from '../api/types'
import { ROUTE_TYPE_LABELS } from '../types/filters'

interface RouteCardProps {
  route: RouteApi;
}

function getShortAreaPath(areaPath: string): string {
  // area_path is slash-delimited slugs (e.g. /CA/Yosemite/El-Cap/)
  const segments = areaPath.split('/').filter(Boolean);
  return segments.slice(-3).join(' / ');
}

export function RouteCard({ route }: RouteCardProps) {
  const routeTypes = useMemo(() => parseRouteTypes(route), [route]);

  const parsedTags = useMemo(() => {
    try {
      return JSON.parse(route.route_tags || '{}') as Record<string, string[]>;
    } catch {
      return {} as Record<string, string[]>;
    }
  }, [route.route_tags]);

  const typeLabel = routeTypes
    .map(t => ROUTE_TYPE_LABELS[t])
    .join(', ') || 'Unknown';

  // Determine known route types for highlighting
  const isKnownType = ROUTE_TYPES.some(t => routeTypes.includes(t));

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
            {formatRouteName(route.route_name)}
          </a>
          <span className="text-gray-600 dark:text-gray-300 text-sm">
            {isKnownType ? typeLabel : 'Unknown'} | {route.route_grade} {route.route_protection_grading} |
            <span className="text-yellow-500"> *</span> {route.route_stars} ({route.route_votes}) |
            {route.route_length_ft && ` ${route.route_length_ft}ft`} |
            {` ${route.route_pitches} ${route.route_pitches === 1 ? 'pitch' : 'pitches'}`} |
            {` `}
            {route.area_url ? (
              <a
                href={route.area_url}
                className="text-blue-500 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                target="_blank"
                rel="noopener noreferrer"
              >
                {route.area_name}
              </a>
            ) : (
              route.area_name
            )}
            {route.area_path && (
              <span className="text-gray-400 dark:text-gray-500 ml-1 text-xs">
                ({getShortAreaPath(route.area_path)})
              </span>
            )}
          </span>
        </div>

        {/* Tags below */}
        <div className="mt-1.5 flex flex-wrap gap-1.5">
          {Object.entries(parsedTags)
            .map(([category, tags]) =>
              (Array.isArray(tags) ? tags : []).map(tag => (
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
