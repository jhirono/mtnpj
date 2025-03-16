import { useEffect, useState, useMemo, useRef, useCallback } from 'react'
import { FilterPanel } from './components/FilterPanel'
import { AreaSearch } from './components/AreaSearch'
import { RouteCard } from './components/RouteCard'
import type { Area } from './types/area'
import type { Route } from './types/route'
import type { RouteFilters, SortConfig } from './types/filters'
import { GRADE_ORDER, normalizeGrade } from './types/filters'
import { getDataUrl, indexFilePath } from './config'

// Add these constants at the top of the file
const EXCLUDED_TYPES = ['Aid', 'Boulder', 'Ice', 'Mixed', 'Snow'];
const ROUTES_PER_PAGE = 100; // Number of routes to load at a time

function hasExcludedType(routeType: string): boolean {
  return EXCLUDED_TYPES.some(type => 
    routeType.split(', ').some(rt => rt === type)
  );
}

function matchesRouteType(routeType: string, selectedType: string): boolean {
  const types = routeType.split(', ')
    .filter(type => !type.startsWith('Grade'))  // Ignore Grade specifications
    .map(type => type.trim());

  switch (selectedType) {
    case 'Trad':
      return types.includes('Trad');
    case 'Sport':
      return types.includes('Sport');
    default:
      return false;
  }
}

function App() {
  const [areas, setAreas] = useState<Area[]>([])
  const [selectedAreaIds, setSelectedAreaIds] = useState<string[]>([])
  const [selectedRoute, setSelectedRoute] = useState<Route | null>(null)
  const [currentFilters, setCurrentFilters] = useState<RouteFilters>({
    grades: { min: "", max: "" },  // Start with empty grade range
    types: [],
    tags: []
  })
  const [sortConfig, setSortConfig] = useState<SortConfig>({
    option: 'votes',
    ascending: false  // Default to descending for stars (high to low)
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [visibleRoutes, setVisibleRoutes] = useState<number>(ROUTES_PER_PAGE)

  // Get routes from selected areas and apply filters
  const filteredRoutes = useMemo(() => {
    // If a specific route is selected, only include that one
    if (selectedRoute) {
      return [selectedRoute];
    }
    
    // Log selected areas for debugging
    console.log('Filtering with selected areas:', selectedAreaIds);
    
    // First, get routes from selected areas
    const routesFromSelectedAreas = selectedAreaIds.length === 0
      ? areas.flatMap(area => area.routes)
      : areas
          .filter(area => {
            // If no selections, include all areas
            if (selectedAreaIds.length === 0) return true;

            // Get the area's hierarchy path
            const areaHierarchyPath = area.area_hierarchy
              .map(h => h.area_hierarchy_name)
              .join(' / ');
            
            // Check if any of the selected area IDs match the beginning of this area's path
            // This ensures we include child areas of any selected parent area
            const isMatch = selectedAreaIds.some(selectedId => 
              areaHierarchyPath.startsWith(selectedId)
            );
            
            // For debugging
            if (isMatch) {
              console.log(`Area matched: ${area.area_name} (${areaHierarchyPath})`);
            }
            
            return isMatch;
          })
          .flatMap(area => area.routes);
          
    console.log(`Found ${routesFromSelectedAreas.length} routes from selected areas`);

    // Pre-filter to remove excluded types
    const preFilteredRoutes = routesFromSelectedAreas.filter(route => 
      !hasExcludedType(route.route_type)
    );
    
    console.log(`After filtering excluded types: ${preFilteredRoutes.length} routes`);

    // Then apply other filters
    return preFilteredRoutes.filter(route => {
      // Grade filter
      const routeGradeNum = GRADE_ORDER.indexOf(normalizeGrade(route.route_grade));
      
      // Skip routes with unparseable grades
      if (routeGradeNum === -1) {
        console.log('Could not parse grade for:', route.route_name, route.route_grade);
        return true;
      }

      // Apply min grade filter if set
      const minGrade = normalizeGrade(currentFilters.grades.min);
      if (minGrade && GRADE_ORDER.indexOf(minGrade) !== -1) {
        if (routeGradeNum < GRADE_ORDER.indexOf(minGrade)) {
          return false;
        }
      }

      // Apply max grade filter if set
      const maxGrade = normalizeGrade(currentFilters.grades.max);
      if (maxGrade && GRADE_ORDER.indexOf(maxGrade) !== -1) {
        if (routeGradeNum > GRADE_ORDER.indexOf(maxGrade)) {
          return false;
        }
      }

      // Type filter with new matching logic
      if (currentFilters.types.length > 0) {
        const matchesType = currentFilters.types.some(type => 
          matchesRouteType(route.route_type, type)
        );
        if (!matchesType) return false;  // Only return false here, continue checking other filters
      }

      // Tags filter
      if (currentFilters.tags.length > 0) {
        return currentFilters.tags.every(({ category, selectedTags }) => {
          const routeTagsForCategory = route.route_tags[category] || [];
          
          // Special handling for "Difficulty & Safety" category
          if (category === "Difficulty & Safety") {
            // Check for exclude_sandbag filter
            if (selectedTags.includes("exclude_sandbag")) {
              if (routeTagsForCategory.includes("sandbag")) {
                return false;
              }
            }
            
            // Check for exclude_runout_dangerous filter
            if (selectedTags.includes("exclude_runout_dangerous")) {
              if (routeTagsForCategory.includes("runout_dangerous")) {
                return false;
              }
            }
            
            // If we're only using exclusion filters, return true
            if (selectedTags.every(tag => tag === "exclude_sandbag" || tag === "exclude_runout_dangerous")) {
              return true;
            }
          }

          // Special handling for "Multi-Pitch, Anchors & Descent" category
          if (category === "Multi-Pitch, Anchors & Descent") {
            // Remove special handling for single_pitch as it's now in the manual tags
            // The tag will be present in the route tags directly
          }
          
          // Filter out exclusion tags for normal handling
          const nonExclusionTags = selectedTags.filter(
            tag => tag !== "exclude_sandbag" && tag !== "exclude_runout_dangerous"
          );
          
          // If there are no non-exclusion tags left, return true
          if (nonExclusionTags.length === 0) {
            return true;
          }
          
          // Normal handling for other tags
          return nonExclusionTags.some(tag => routeTagsForCategory.includes(tag));
        });
      }

      return true;
    });
  }, [areas, selectedAreaIds, currentFilters, selectedRoute]);

  // Sort routes
  const sortedRoutes = useMemo(() => {
    // If we have a selected route, don't sort (return as is)
    if (selectedRoute) {
      return filteredRoutes;
    }

    return [...filteredRoutes].sort((a, b) => {
      // Default sort directions without needing the checkbox:
      // grade: ascending (easy to hard) when unchecked
      // stars: descending (high to low) when unchecked
      // votes: descending (high to low) when unchecked
      // left_to_right: ascending (left to right) when unchecked
      const multiplier = sortConfig.option === 'grade' || sortConfig.option === 'left_to_right'
        ? (sortConfig.ascending ? -1 : 1)    // For grade and left_to_right
        : (sortConfig.ascending ? 1 : -1);   // For stars and votes

      switch (sortConfig.option) {
        case 'grade':
          return multiplier * (
            GRADE_ORDER.indexOf(normalizeGrade(a.route_grade)) - 
            GRADE_ORDER.indexOf(normalizeGrade(b.route_grade))
          )
        case 'stars':
          const aStars = a.route_stars || 0
          const bStars = b.route_stars || 0
          return -multiplier * (bStars - aStars)  // Note the negative here
        case 'votes':
          const aVotes = a.route_votes || 0
          const bVotes = b.route_votes || 0
          return -multiplier * (bVotes - aVotes)  // Note the negative here
        case 'left_to_right':
          if (a.area_name === b.area_name) {
            const aLr = typeof a.route_lr === 'string' ? parseInt(a.route_lr, 10) : (a.route_lr || 0)
            const bLr = typeof b.route_lr === 'string' ? parseInt(b.route_lr, 10) : (b.route_lr || 0)
            return multiplier * (aLr - bLr)
          }
          return 0
        default:
          return 0
      }
    })
  }, [filteredRoutes, sortConfig, selectedRoute])

  // Create a sliced version of sorted routes for display
  const displayedRoutes = useMemo(() => {
    return sortedRoutes.slice(0, visibleRoutes);
  }, [sortedRoutes, visibleRoutes]);

  // Observer for infinite scrolling
  const observer = useRef<IntersectionObserver | null>(null);
  
  // Set up intersection observer for infinite scrolling
  const lastRouteElementRef = useCallback((node: HTMLDivElement | null) => {
    if (loading) return;
    
    if (observer.current) observer.current.disconnect();
    
    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && displayedRoutes.length < sortedRoutes.length) {
        // Load more routes when we reach the bottom
        setVisibleRoutes(prev => Math.min(prev + ROUTES_PER_PAGE, sortedRoutes.length));
      }
    });
    
    if (node) observer.current.observe(node);
  }, [loading, displayedRoutes.length, sortedRoutes.length]);

  // Reset visible routes when filters or sort changes
  useEffect(() => {
    setVisibleRoutes(ROUTES_PER_PAGE);
  }, [currentFilters, sortConfig, selectedAreaIds, selectedRoute]);

  useEffect(() => {
    const loadAreas = async () => {
      try {
        // First, get the list of data files from index.json
        const indexResponse = await fetch(indexFilePath);
        if (!indexResponse.ok) {
          throw new Error(`Failed to load index.json: ${indexResponse.status} ${indexResponse.statusText}`);
        }
        
        const dataFiles = await indexResponse.json();
        if (!Array.isArray(dataFiles) || dataFiles.length === 0) {
          throw new Error('No data files found in index.json');
        }
        
        const loadedAreas: Area[] = [];
        
        for (const fileName of dataFiles) {
          const filePath = getDataUrl(fileName);
          try {
            const response = await fetch(filePath);
            if (!response.ok) {
              console.error(`Failed to load ${filePath}: ${response.status} ${response.statusText}`);
              continue;
            }
            const data = await response.json();
            
            if (Array.isArray(data)) {
              const areasWithContext = data.map(area => ({
                ...area,
                routes: area.routes.map((route: Route) => ({
                  ...route,
                  area_name: area.area_name,
                  area_hierarchy: area.area_hierarchy
                }))
              }));
              loadedAreas.push(...areasWithContext);
            } else {
              loadedAreas.push({
                ...data,
                routes: data.routes.map((route: Route) => ({
                  ...route,
                  area_name: data.area_name,
                  area_hierarchy: data.area_hierarchy
                }))
              });
            }
          } catch (fileErr) {
            console.error(`Error loading ${filePath}:`, fileErr);
          }
        }

        if (loadedAreas.length === 0) {
          throw new Error('No areas could be loaded');
        }

        setAreas(loadedAreas);
        setLoading(false);
      } catch (err) {
        console.error('Error loading data:', err);
        setError('Error loading area data');
        setLoading(false);
      }
    };

    loadAreas();
  }, []);

  const handleFilterChange = (filters: RouteFilters) => {
    setCurrentFilters(filters)
  }

  // Handle area selection in the App component
  const handleAreaSelect = (selectedIds: string[]) => {
    console.log('App received area selection update:', selectedIds);
    // Clear any selected route when area selection changes
    setSelectedRoute(null);
    // Update selected area IDs with the new selection
    setSelectedAreaIds(selectedIds);
  }

  // Handle when a route is selected from search
  const handleRouteSelect = (route: Route) => {
    setSelectedRoute(route);
    // Clear any area selections when viewing a specific route
    setSelectedAreaIds([]);
  }

  // Function to clear selected route
  const clearSelectedRoute = () => {
    setSelectedRoute(null);
  }

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4">
        <header className="py-4 text-center">
          {/* Responsive header layout */}
          <div className="flex flex-col items-center">
            {/* Title row */}
            <h1 className="text-xl font-bold mb-2">
              Awesome Climbing Search
            </h1>
            
            {/* Badges row - will stack on mobile, side by side on desktop */}
            <div className="flex items-center gap-2 flex-wrap justify-center">
              <a 
                href="/docs/README.html" 
                target="_blank" 
                rel="noopener noreferrer"
                className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300 hover:bg-blue-200 dark:hover:bg-blue-800"
              >
                <span className="mr-1">ⓘ</span>
                INFO
              </a>
            </div>
          </div>
          
          <p className="text-gray-600 dark:text-gray-400 text-sm mt-2">
            {sortedRoutes.length} routes found (showing {displayedRoutes.length})
          </p>
          
          {/* Show a clear button when a route is selected */}
          {selectedRoute && (
            <div className="mt-2">
              <button 
                onClick={clearSelectedRoute}
                className="text-sm px-3 py-1 bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 rounded-full text-gray-700 dark:text-gray-300"
              >
                ← Back to all routes
              </button>
            </div>
          )}
        </header>

        <div className="flex flex-col md:flex-row gap-4">
          <div className="md:w-72 flex-shrink-0">
            <div className="sticky top-4">
              <AreaSearch 
                areas={areas}
                onAreaSelect={handleAreaSelect}
                onRouteSelect={handleRouteSelect}
              />
              <FilterPanel
                filters={currentFilters}
                onChange={handleFilterChange}
                sortConfig={sortConfig}
                onSortChange={setSortConfig}
                areas={areas}
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
            ) : loading ? (
              <div className="h-[50vh] flex items-center justify-center">
                <div className="text-center text-gray-500 text-sm">
                  Loading...
                </div>
              </div>
            ) : displayedRoutes.length > 0 ? (
              <div className="space-y-3">
                {displayedRoutes.map((route, index) => (
                  <div key={route.route_url} ref={index === displayedRoutes.length - 1 ? lastRouteElementRef : undefined}>
                    <RouteCard
                      route={route}
                    />
                  </div>
                ))}
                {displayedRoutes.length < sortedRoutes.length && (
                  <div className="py-4 text-center text-gray-500">
                    Scroll for more routes...
                  </div>
                )}
              </div>
            ) : (
              <div className="h-[50vh] flex items-center justify-center">
                <div className="text-center text-gray-500 text-sm">
                  {selectedAreaIds.length === 0 && !selectedRoute ? (
                    <div>
                      <p className="mb-2 font-medium">No areas selected</p>
                      <p>Start by searching for an area or route in the sidebar</p>
                      <p className="mt-2">↖ Enter a location or route name and click on a result</p>
                    </div>
                  ) : (
                    "No routes found matching your criteria"
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
