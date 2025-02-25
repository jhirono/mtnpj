import { useEffect, useState, useMemo } from 'react'
import { FilterPanel } from './components/FilterPanel'
import { AreaSearch } from './components/AreaSearch'
import { RouteCard } from './components/RouteCard'
import type { Area } from './types/area'
import type { Route } from './types/route'
import type { RouteFilters, SortConfig } from './types/filters'
import { GRADE_ORDER, normalizeGrade } from './types/filters'

// Add these constants at the top of the file
const EXCLUDED_TYPES = ['Aid', 'Boulder', 'Ice', 'Mixed', 'Snow'];

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

  // Get routes from selected areas and apply filters
  const filteredRoutes = useMemo(() => {
    // First, get routes from selected areas
    const routesFromSelectedAreas = selectedAreaIds.length === 0
      ? areas.flatMap(area => area.routes)
      : areas
          .filter(area => {
            // If no selections, include all areas
            if (selectedAreaIds.length === 0) return true;

            // Group selections by their parent hierarchy
            const hierarchyGroups = new Map<string, string[]>();
            
            selectedAreaIds.forEach(selectedId => {
              const parts = selectedId.split(' / ');
              // Skip if it's just a single level
              if (parts.length <= 1) return;
              
              // Find if this selection is a child of any existing selection
              const parentSelection = selectedAreaIds.find(otherId => 
                selectedId !== otherId && selectedId.startsWith(otherId)
              );

              if (parentSelection) {
                // Add to parent's group
                if (!hierarchyGroups.has(parentSelection)) {
                  hierarchyGroups.set(parentSelection, []);
                }
                hierarchyGroups.get(parentSelection)!.push(selectedId);
              }
            });

            // Get standalone selections (those without children selected)
            const standaloneSelections = selectedAreaIds.filter(selectedId => {
              return !Array.from(hierarchyGroups.values())
                .flat()
                .includes(selectedId);
            });

            const areaHierarchyPath = area.area_hierarchy
              .map(h => h.area_hierarchy_name)
              .join(' / ');

            // Check standalone selections first (OR condition)
            const matchesStandalone = standaloneSelections.some(selectedId => 
              !hierarchyGroups.has(selectedId) && areaHierarchyPath.startsWith(selectedId)
            );

            if (matchesStandalone) return true;

            // Check each hierarchy group (AND condition within group)
            return Array.from(hierarchyGroups.entries()).some(([parentPath, childPaths]) => {
              // Must match parent AND at least one child
              return areaHierarchyPath.startsWith(parentPath) && 
                     childPaths.some(childPath => areaHierarchyPath.startsWith(childPath));
            });
          })
          .flatMap(area => area.routes);

    // Pre-filter to remove excluded types
    const preFilteredRoutes = routesFromSelectedAreas.filter(route => 
      !hasExcludedType(route.route_type)
    );

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
            if (selectedTags.includes("exclude_sandbag")) {
              return !routeTagsForCategory.includes("sandbag");
            }
          }

          // Special handling for "Multi-Pitch, Anchors & Descent" category
          if (category === "Multi-Pitch, Anchors & Descent") {
            if (selectedTags.includes("single_pitch")) {
              return route.route_pitches === 1;
            }
          }
          
          // Normal handling for other tags
          return selectedTags.some(tag => routeTagsForCategory.includes(tag));
        });
      }

      return true;
    });
  }, [areas, selectedAreaIds, currentFilters]);

  // Sort routes
  const sortedRoutes = useMemo(() => {
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
  }, [filteredRoutes, sortConfig])

  useEffect(() => {
    const loadAreas = async () => {
      try {
        const areaFiles = [
          '/data/castle-rock_routes_tagged.json',
          '/data/indian-creek_routes_tagged.json',
          '/data/squamish_routes_tagged.json'
        ];

        const loadedAreas: Area[] = [];
        
        for (const file of areaFiles) {
          try {
            const response = await fetch(file);
            if (!response.ok) {
              console.error(`Failed to load ${file}: ${response.status} ${response.statusText}`);
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
            console.error(`Error loading ${file}:`, fileErr);
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

  return (
    <div className="min-h-screen">
      <header className="py-4 text-center">
        <h1 className="text-xl font-bold">Awesome Climbing Route Search</h1>
        <p className="text-gray-600 text-sm mt-1">
          {sortedRoutes.length} routes found
        </p>
      </header>

      <div className="max-w-7xl mx-auto px-3 py-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="md:w-72 flex-shrink-0">
            <div className="sticky top-4">
              <AreaSearch 
                areas={areas}
                onAreaSelect={setSelectedAreaIds}
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
            ) : sortedRoutes.length > 0 ? (
              <div className="space-y-3">
                {sortedRoutes.map(route => (
                  <RouteCard
                    key={route.route_url}
                    route={route}
                  />
                ))}
              </div>
            ) : (
              <div className="h-[50vh] flex items-center justify-center">
                <div className="text-center text-gray-500 text-sm">
                  No routes found matching your criteria
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
