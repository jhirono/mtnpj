import { useEffect, useState, useMemo, useRef, useCallback } from 'react'
import { FilterPanel } from './components/FilterPanel'
import { AreaSearch } from './components/AreaSearch'
import { RouteCard } from './components/RouteCard'
import OfflineIndicator from './components/OfflineIndicator'
import InstallPrompt from './components/InstallPrompt'
import type { RouteFilters, SortConfig } from './types/filters'
import { GRADE_ORDER, normalizeGrade } from './types/filters'
import { routeApi } from './api/routeApi'
import type { RouteApi, ApiFilters, RouteType } from './api/types'
import { parseRouteTypes } from './api/types'

function gradeToNumeric(grade: string): number | null {
  const normalized = normalizeGrade(grade);
  const match = normalized.match(/^5\.(\d+)([abcd]?)$/);
  if (!match) return null;
  const num = parseInt(match[1]);
  const letter = match[2] || '';
  const letterMap: Record<string, number> = { '': 0, a: 1, b: 2, c: 3, d: 4 };
  return num >= 10 ? num + (letterMap[letter] ?? 0) * 0.1 : num;
}

const ROUTES_PER_PAGE = 100;

/**
 * Map UI filter state -> API query params.
 * If exactly one type is selected, send ?type=; otherwise omit and filter client-side.
 */
function filtersToApi(
  uiFilters: RouteFilters,
  _sort: SortConfig,
  page: number
): ApiFilters {
  const params: ApiFilters = { page, limit: ROUTES_PER_PAGE };

  if (uiFilters.types.length === 1) {
    params.type = uiFilters.types[0];
  }

  if (uiFilters.grades.min) {
    const n = gradeToNumeric(uiFilters.grades.min);
    if (n !== null) params.grade_min = n;
  }
  if (uiFilters.grades.max) {
    const n = gradeToNumeric(uiFilters.grades.max);
    if (n !== null) params.grade_max = n;
  }

  return params;
}

function App() {
  const [routes, setRoutes] = useState<RouteApi[]>([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [selectedAreaId, setSelectedAreaId] = useState<string | null>(null);
  const [selectedRoute, setSelectedRoute] = useState<RouteApi | null>(null);
  const [currentFilters, setCurrentFilters] = useState<RouteFilters>({
    grades: { min: '', max: '' },
    types: [],
    tags: []
  });
  const [sortConfig, setSortConfig] = useState<SortConfig>({
    option: 'votes',
    ascending: false
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [visibleRoutes, setVisibleRoutes] = useState<number>(ROUTES_PER_PAGE);

  // Reset page to 1 whenever filters/sort/area changes
  useEffect(() => {
    setPage(1);
    setRoutes([]);
  }, [currentFilters, sortConfig, selectedAreaId]);

  // Load routes from the Worker API
  useEffect(() => {
    if (selectedRoute) return; // Single-route view: skip API call

    let cancelled = false;
    setLoading(true);

    const apiFilters: ApiFilters = filtersToApi(currentFilters, sortConfig, page);
    if (selectedAreaId) {
      apiFilters.area_id = selectedAreaId;
    }

    routeApi.fetchRoutes(apiFilters)
      .then(res => {
        if (cancelled) return;
        setRoutes(prev => page === 1 ? res.data : [...prev, ...res.data]);
        setHasMore(res.data.length === res.limit);
        setLoading(false);
      })
      .catch(err => {
        if (cancelled) return;
        setError(String(err));
        setLoading(false);
      });

    return () => { cancelled = true; };
  }, [currentFilters, sortConfig, page, selectedAreaId, selectedRoute]);

  // Client-side filtering: multi-type filter + tag filter (tags are JSON strings from D1)
  const filteredRoutes = useMemo(() => {
    if (selectedRoute) return [selectedRoute];

    return routes.filter(route => {
      // Multi-type filter: if 2+ types selected, filter client-side by is_* booleans
      if (currentFilters.types.length >= 2) {
        const routeTypes = parseRouteTypes(route);
        const matchesType = currentFilters.types.some((t: RouteType) => routeTypes.includes(t));
        if (!matchesType) return false;
      }

      // Tag filter
      if (currentFilters.tags.length > 0) {
        const parsedTags = (() => {
          try { return JSON.parse(route.route_tags || '{}') as Record<string, string[]>; }
          catch { return {} as Record<string, string[]>; }
        })();

        // Tags in the Safety category that, when selected, EXCLUDE routes having them.
        // These match the `exclude: true` options defined in FilterPanel.tsx.
        const SAFETY_EXCLUDE_TAGS = new Set(['runout_dangerous', 'sandbag']);

        return currentFilters.tags.every(({ category, selectedTags }) => {
          const routeTagsForCategory: string[] = parsedTags[category] || [];

          if (category === 'Safety') {
            // Exclusion tags: return false if route has any of the excluded tags.
            for (const tag of selectedTags) {
              if (SAFETY_EXCLUDE_TAGS.has(tag) && routeTagsForCategory.includes(tag)) return false;
            }
          }

          // Inclusion tags: route must have at least one of the non-exclusion selected tags.
          const inclusionTags = category === 'Safety'
            ? selectedTags.filter(tag => !SAFETY_EXCLUDE_TAGS.has(tag))
            : selectedTags;

          if (inclusionTags.length === 0) return true;
          return inclusionTags.some(tag => routeTagsForCategory.includes(tag));
        });
      }

      return true;
    });
  }, [routes, currentFilters, selectedRoute]);

  // Sort routes
  const sortedRoutes = useMemo(() => {
    if (selectedRoute) return filteredRoutes;

    return [...filteredRoutes].sort((a, b) => {
      const multiplier = sortConfig.option === 'grade' || sortConfig.option === 'left_to_right'
        ? (sortConfig.ascending ? -1 : 1)
        : (sortConfig.ascending ? 1 : -1);

      switch (sortConfig.option) {
        case 'grade':
          return multiplier * (
            GRADE_ORDER.indexOf(normalizeGrade(a.route_grade ?? '')) -
            GRADE_ORDER.indexOf(normalizeGrade(b.route_grade ?? ''))
          );
        case 'stars': {
          const aStars = a.route_stars ?? 0;
          const bStars = b.route_stars ?? 0;
          return -multiplier * (bStars - aStars);
        }
        case 'votes': {
          const aVotes = a.route_votes ?? 0;
          const bVotes = b.route_votes ?? 0;
          return -multiplier * (bVotes - aVotes);
        }
        case 'left_to_right':
          if (a.area_name === b.area_name) {
            const aLr = a.route_lr ?? 0;
            const bLr = b.route_lr ?? 0;
            return multiplier * (aLr - bLr);
          }
          return 0;
        default:
          return 0;
      }
    });
  }, [filteredRoutes, sortConfig, selectedRoute]);

  const displayedRoutes = useMemo(() => {
    return sortedRoutes.slice(0, visibleRoutes);
  }, [sortedRoutes, visibleRoutes]);

  const observer = useRef<IntersectionObserver | null>(null);

  const lastRouteElementRef = useCallback((node: HTMLDivElement | null) => {
    if (loading) return;
    if (observer.current) observer.current.disconnect();

    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting) {
        if (displayedRoutes.length < sortedRoutes.length) {
          // Load more from the local sorted array
          setVisibleRoutes(prev => Math.min(prev + ROUTES_PER_PAGE, sortedRoutes.length));
        } else if (hasMore) {
          // Load next page from API
          setPage(prev => prev + 1);
        }
      }
    });

    if (node) observer.current.observe(node);
  }, [loading, displayedRoutes.length, sortedRoutes.length, hasMore]);

  // Reset visible routes when filters/sort changes
  useEffect(() => {
    setVisibleRoutes(ROUTES_PER_PAGE);
  }, [currentFilters, sortConfig, selectedAreaId, selectedRoute]);

  // When tag filters are active and the filtered result set is sparse, auto-load the
  // next API page so the user doesn't have to scroll for each small batch.
  useEffect(() => {
    if (currentFilters.tags.length === 0) return;
    if (loading || !hasMore) return;
    if (sortedRoutes.length < ROUTES_PER_PAGE) {
      setPage(prev => prev + 1);
    }
  }, [sortedRoutes.length, loading, hasMore, currentFilters.tags.length]);

  const handleFilterChange = (filters: RouteFilters) => {
    setCurrentFilters(filters);
  };

  const handleAreaSelect = (areaId: string | null) => {
    setSelectedRoute(null);
    setSelectedAreaId(areaId);
  };

  const handleRouteSelect = (route: RouteApi) => {
    setSelectedRoute(route);
    setSelectedAreaId(null);
  };

  const clearSelectedRoute = () => {
    setSelectedRoute(null);
  };

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4">
        <OfflineIndicator />
        <InstallPrompt />

        <header className="py-4 text-center">
          <div className="flex flex-col items-center">
            <h1 className="text-xl font-bold mb-2">
              Awesome Climbing Search
            </h1>

            <div className="flex items-center gap-2 flex-wrap justify-center">
              <a
                href="/docs/README.html"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300 hover:bg-blue-200 dark:hover:bg-blue-800"
              >
                <span className="mr-1">i</span>
                INFO
              </a>
            </div>
          </div>

          <p className="text-gray-600 dark:text-gray-400 text-sm mt-2">
            {sortedRoutes.length}{hasMore ? '+' : ''} routes{displayedRoutes.length < sortedRoutes.length ? ` (showing ${displayedRoutes.length})` : ''}
          </p>

          {selectedRoute && (
            <div className="mt-2">
              <button
                onClick={clearSelectedRoute}
                className="text-sm px-3 py-1 bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 rounded-full text-gray-700 dark:text-gray-300"
              >
                Back to all routes
              </button>
            </div>
          )}
        </header>

        <div className="flex flex-col md:flex-row gap-4">
          <div className="md:w-72 flex-shrink-0">
            <div className="sticky top-4">
              <AreaSearch
                onAreaSelect={handleAreaSelect}
                onRouteSelect={handleRouteSelect}
              />
              <FilterPanel
                filters={currentFilters}
                onChange={handleFilterChange}
                sortConfig={sortConfig}
                onSortChange={setSortConfig}
              />
            </div>
          </div>

          <div className="flex-grow">
            {error ? (
              <div className="h-[50vh] flex items-center justify-center">
                <div className="text-center text-red-500 text-sm">
                  {error}
                </div>
              </div>
            ) : loading && routes.length === 0 ? (
              <div className="h-[50vh] flex items-center justify-center">
                <div className="text-center text-gray-500 text-sm">
                  Loading...
                </div>
              </div>
            ) : displayedRoutes.length > 0 ? (
              <div className="space-y-3">
                {displayedRoutes.map((route, index) => (
                  <div key={route.route_url} ref={index === displayedRoutes.length - 1 ? lastRouteElementRef : undefined}>
                    <RouteCard route={route} />
                  </div>
                ))}
                {(displayedRoutes.length < sortedRoutes.length || hasMore) && (
                  <div className="py-4 text-center text-gray-500">
                    {loading ? 'Loading more...' : 'Scroll for more routes...'}
                  </div>
                )}
              </div>
            ) : (
              <div className="h-[50vh] flex items-center justify-center">
                <div className="text-center text-gray-500 text-sm">
                  {(() => {
                    const hasActiveFilters =
                      currentFilters.types.length > 0 ||
                      currentFilters.tags.length > 0 ||
                      !!currentFilters.grades.min ||
                      !!currentFilters.grades.max;
                    if (!selectedAreaId && !selectedRoute && !hasActiveFilters) {
                      return (
                        <div>
                          <p className="mb-2 font-medium">No areas selected</p>
                          <p>Start by searching for an area or route in the sidebar</p>
                          <p className="mt-2">Enter a location or route name and click on a result</p>
                        </div>
                      );
                    }
                    return loading ? 'Loading...' : 'No routes found matching your criteria';
                  })()}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App
