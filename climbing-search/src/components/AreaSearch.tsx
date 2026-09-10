import { formatRouteName } from '../utils/formatters'
import { useState, useEffect, useRef } from 'react';
import type { RouteApi, AreaApi } from '../api/types';
import { routeApi } from '../api/routeApi';

interface AreaSearchProps {
  onAreaSelect: (areaId: string | null) => void;
  onRouteSelect?: (route: RouteApi) => void;
}

function formatAreaPath(path: string): string {
  const segments = path.split('/').filter(Boolean);
  const last3 = segments.slice(-3);
  const truncated = last3.map(segment =>
    segment.length > 15 ? `${segment.substring(0, 12)}...` : segment
  );
  return truncated.join(' / ');
}

export function AreaSearch({ onAreaSelect, onRouteSelect }: AreaSearchProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedArea, setSelectedArea] = useState<AreaApi | null>(null);
  const [areaResults, setAreaResults] = useState<AreaApi[]>([]);
  const [routeResults, setRouteResults] = useState<RouteApi[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Debounced search: areas + routes
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);

    const trimmed = searchTerm.trim();
    if (trimmed.length < 2) {
      setAreaResults([]);
      setRouteResults([]);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      setIsSearching(true);
      try {
        // Run independently so a routes FTS error doesn't clear area results.
        const [areasRes, routesRes] = await Promise.all([
          routeApi.fetchAreas({ q: trimmed, limit: 5 }).catch(() => ({ data: [] as AreaApi[], page: 1, limit: 5 })),
          routeApi.fetchRoutes({ q: trimmed, limit: 5 }).catch(() => ({ data: [] as RouteApi[], page: 1, limit: 5 })),
        ]);

        const slug = trimmed.toLowerCase().replace(/\s+/g, '-');
        const areas = areasRes.data;

        // If no exact name match but any result has /${slug}/ as an exact path segment,
        // inject a synthetic "All routes in [slug]" entry at the top.
        // Scan all results (not just first) because shorter-path results may be for
        // a different area (e.g. "mount-index" results masking "index" area).
        const hasExact = areas.some(a => a.area_name === slug);
        const syntheticEntry = (() => {
          if (hasExact || areas.length === 0) return null;
          const matchingArea = areas.find(a => a.path.includes(`/${slug}/`));
          if (!matchingArea) return null;
          const idx = matchingArea.path.indexOf(`/${slug}/`);
          const prefix = matchingArea.path.slice(0, idx + slug.length + 2);
          return {
            area_id: `path_prefix:${prefix}`,
            area_name: slug,
            area_url: '',
            parent_id: null,
            area_gps: null, area_description: null, area_getting_there: null,
            area_access_issues: null, area_page_views: null, area_shared_on: null, area_tags: null,
            path: prefix,
            synthetic: true,
          };
        })();

        setAreaResults(syntheticEntry ? [syntheticEntry, ...areas] : areas);
        setRouteResults(routesRes.data);
      } catch {
        setAreaResults([]);
        setRouteResults([]);
      } finally {
        setIsSearching(false);
      }
    }, 250);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [searchTerm]);

  const handleAreaSelect = (area: AreaApi) => {
    setSelectedArea(area);
    onAreaSelect(area.area_id);
    setSearchTerm('');
    setAreaResults([]);
    setRouteResults([]);
    setIsOpen(false);
  };

  const handleRouteSelect = (route: RouteApi) => {
    if (onRouteSelect) onRouteSelect(route);
    setSearchTerm('');
    setAreaResults([]);
    setRouteResults([]);
    setIsOpen(false);
  };

  const handleClearArea = () => {
    setSelectedArea(null);
    onAreaSelect(null);
  };

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = () => setIsOpen(false);
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, []);

  const hasResults = areaResults.length > 0 || routeResults.length > 0;

  return (
    <div className="mb-3 bg-white dark:bg-gray-800 rounded-lg shadow p-2">
      <div className="relative">
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg className="h-3.5 w-3.5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
            </svg>
          </div>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setIsOpen(true);
            }}
            onClick={(e) => {
              e.stopPropagation();
              setIsOpen(true);
            }}
            placeholder="Search for areas or routes..."
            className="w-full py-1 pl-9 pr-2 text-sm border rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600"
          />
        </div>

        {isOpen && (searchTerm.trim().length >= 2) && (
          <div className="absolute z-10 w-full mt-0.5 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded shadow-lg max-h-64 overflow-y-auto text-sm">
            {isSearching ? (
              <div className="py-2 px-3 text-gray-500 text-xs">Searching...</div>
            ) : hasResults ? (
              <>
                <div className="py-1 px-2 text-xs text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
                  Search results - click to select
                </div>

                {areaResults.length > 0 && (
                  <div className="py-0.5 px-2 text-xs text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
                    Areas:
                  </div>
                )}
                {areaResults.map(area => (
                  <div
                    key={area.area_id}
                    className={`py-1 px-2 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 ${
                      selectedArea?.area_id === area.area_id ? 'bg-blue-100 dark:bg-blue-900' : ''
                    } ${area.synthetic ? 'border-b border-gray-200 dark:border-gray-700' : ''}`}
                    onClick={() => handleAreaSelect(area)}
                    title={area.path}
                  >
                    {area.synthetic ? (
                      <span className="text-gray-900 dark:text-gray-100 text-xs flex items-center">
                        <span className="inline-block w-4 mr-1">📁</span>
                        <span className="font-medium">{area.area_name}</span>
                        <span className="ml-1 text-gray-500">(all sub-areas)</span>
                        <span className="ml-auto text-blue-500 dark:text-blue-400">+</span>
                      </span>
                    ) : (
                      <span className="text-gray-900 dark:text-gray-100 text-xs flex items-center">
                        <span className="inline-block w-4 text-gray-500 mr-1">F</span>
                        <span>{formatAreaPath(area.path || area.area_name)}</span>
                        <span className="ml-auto text-blue-500 dark:text-blue-400">
                          {selectedArea?.area_id === area.area_id ? 'V' : '+'}
                        </span>
                      </span>
                    )}
                  </div>
                ))}

                {routeResults.length > 0 && (
                  <div className="py-0.5 px-2 text-xs text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
                    Routes:
                  </div>
                )}
                {routeResults.map(route => (
                  <div
                    key={route.route_id}
                    className="py-1 px-2 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700"
                    onClick={() => handleRouteSelect(route)}
                    title={`${route.route_name} (${route.route_grade})`}
                  >
                    <span className="text-gray-900 dark:text-gray-100 text-xs flex items-center">
                      <span className="inline-block w-4 text-gray-500 mr-1">R</span>
                      <span>{formatRouteName(route.route_name)}</span>
                      <span className="ml-1 text-gray-500">
                        {route.route_grade}
                      </span>
                    </span>
                    <div className="text-xs text-gray-500 pl-5">
                      {formatAreaPath(route.area_path || route.area_name)}
                    </div>
                  </div>
                ))}
              </>
            ) : (
              <div className="py-2 px-3 text-gray-500 text-xs">
                No matching areas or routes found
              </div>
            )}
          </div>
        )}
      </div>

      {selectedArea && (
        <div className="mt-1.5">
          <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">
            Selected Area:
          </div>
          <div className="flex flex-wrap gap-1">
            <div className="flex items-center gap-0.5 py-0.5 px-1.5 bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded text-xs">
              <span>{selectedArea.area_name}{selectedArea.synthetic ? ' (all)' : ''}</span>
              <button
                onClick={handleClearArea}
                className="inline-flex items-center justify-center w-3 h-3 ml-0.5 rounded-full bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 text-gray-500 dark:text-gray-400 text-[10px] leading-none"
                aria-label="Remove"
              >
                x
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
