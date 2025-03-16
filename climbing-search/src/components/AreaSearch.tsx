import { useState, useEffect, useMemo } from 'react';
import type { Area } from '../types/area';
import type { Route } from '../types/route';

interface AreaSearchProps {
  areas: Area[];
  onAreaSelect: (selectedIds: string[]) => void;
  onRouteSelect?: (route: Route) => void;
}

// Add this helper function near the top of the file
function formatAreaPath(path: string): string {
  // Split the path into segments
  const segments = path.split(' / ');
  
  // Remove "All Locations" from the segments
  const filteredSegments = segments.filter(segment => segment !== "All Locations");
  
  // Truncate long segments (over 15 characters)
  const truncatedSegments = filteredSegments.map(segment => 
    segment.length > 15 ? `${segment.substring(0, 12)}...` : segment
  );
  
  // Join the segments back together
  return truncatedSegments.join(' / ');
}

// Interface to represent a search result which can be either an area or a route
interface SearchResult {
  type: 'area' | 'route';
  id: string;
  text: string;
  path?: string; // Only for areas
  route?: Route; // Only for routes
  score: number; // Used for sorting results by relevance
}

export function AreaSearch({ areas, onAreaSelect, onRouteSelect }: AreaSearchProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAreas, setSelectedAreas] = useState<string[]>([]);
  const [isOpen, setIsOpen] = useState(false);

  // Build a hierarchical structure of all areas
  const areaHierarchy = useMemo(() => {
    const hierarchy: Record<string, string[]> = {};
    
    areas.forEach(area => {
      if (!area.area_hierarchy) return;
      
      // Build path for each level of the hierarchy
      let currentPath = '';
      area.area_hierarchy.forEach((level) => {
        const levelName = level.area_hierarchy_name;
        const newPath = currentPath ? `${currentPath} / ${levelName}` : levelName;
        
        if (!hierarchy[currentPath]) {
          hierarchy[currentPath] = [];
        }
        
        if (!hierarchy[currentPath].includes(newPath)) {
          hierarchy[currentPath].push(newPath);
        }
        
        currentPath = newPath;
      });
    });
    
    return hierarchy;
  }, [areas]);

  // Get all unique area paths for search
  const allAreaPaths = useMemo(() => {
    const paths = new Set<string>();
    
    // Add all paths from the hierarchy
    Object.values(areaHierarchy).forEach(children => {
      children.forEach(path => paths.add(path));
    });
    
    return Array.from(paths);
  }, [areaHierarchy]);

  // Get all routes for search
  const allRoutes = useMemo(() => {
    return areas.flatMap(area => area.routes || []);
  }, [areas]);

  // Search for both areas and routes based on search term
  const searchResults = useMemo(() => {
    if (!searchTerm || searchTerm.trim().length < 2) return []; // Require at least 2 characters
    
    // Split the search term into individual words for multi-term search
    const searchTerms = searchTerm.toLowerCase().trim().split(/\s+/).filter(term => term.length > 0);
    
    // Function to check if a field contains ALL search terms (AND condition)
    const containsAllTerms = (field: string): boolean => {
      const fieldLower = field.toLowerCase();
      return searchTerms.every(term => fieldLower.includes(term));
    };
    
    // Calculate a score based on matches quality (assuming all terms match)
    const calculateScore = (field: string): number => {
      // First check if the field contains all search terms - if not, return -1
      if (!containsAllTerms(field)) {
        return -1;
      }
      
      const fieldLower = field.toLowerCase();
      let score = 0;
      let exactMatchBonus = 0;
      
      // Check if the entire search term is in the field (highest priority)
      if (fieldLower.includes(searchTerm.toLowerCase())) {
        exactMatchBonus = 100;
      }
      
      // Calculate match score for individual terms
      for (const term of searchTerms) {
        // Add to score based on term length (longer terms are more significant)
        score += term.length * 2;
        
        // Bonus points if term is at the start of the field or after a separator
        if (fieldLower.startsWith(term) || fieldLower.includes(` ${term}`) || 
            fieldLower.includes(`/${term}`) || fieldLower.includes(`-${term}`)) {
          score += 5;
        }
      }
      
      return score + exactMatchBonus;
    };
    
    const results: SearchResult[] = [];
    
    // Search in areas
    const matchingAreas = allAreaPaths
      .map(path => {
        const score = calculateScore(path);
        return { path, score };
      })
      .filter(item => item.score > 0) // Only include results with positive scores
      .sort((a, b) => b.score - a.score) // Sort by score descending
      .slice(0, 5) // Take top 5
      .map(({ path, score }) => ({
        type: 'area' as const,
        id: path,
        text: formatAreaPath(path),
        path,
        score
      }));
    
    results.push(...matchingAreas);
    
    // Search in routes (by name)
    const matchingRoutes = allRoutes
      .map(route => {
        // For routes, check both the route name and area hierarchy
        const routeNameScore = calculateScore(route.route_name);
        
        // Only process area hierarchy if the route name already matches all terms
        let areaScore = 0;
        if (routeNameScore > 0 && route.area_hierarchy) {
          const areaPath = route.area_hierarchy.map(h => h.area_hierarchy_name).join(' / ');
          // For area path, we don't require all terms to match, just calculate bonus points
          const fieldLower = areaPath.toLowerCase();
          for (const term of searchTerms) {
            if (fieldLower.includes(term)) {
              areaScore += term.length;
            }
          }
        }
        
        // If route name doesn't match all terms, return negative score
        if (routeNameScore < 0) {
          return { route, score: -1 };
        }
        
        // Combined score - route name is primary, area is secondary
        const score = routeNameScore * 2 + areaScore;
        
        return { route, score };
      })
      .filter(item => item.score > 0) // Only include results with positive scores
      .sort((a, b) => b.score - a.score) // Sort by score descending
      .slice(0, 5) // Take top 5
      .map(({ route, score }) => ({
        type: 'route' as const,
        id: route.route_id,
        text: route.route_name,
        route,
        score
      }));
    
    results.push(...matchingRoutes);
    
    // Sort all results by score
    return results.sort((a, b) => b.score - a.score);
  }, [searchTerm, allAreaPaths, allRoutes]);

  // Handle area selection
  const handleAreaSelect = (areaPath: string) => {
    setSelectedAreas(prev => {
      // Create a copy of the current selected areas
      const newSelection = [...prev];
      
      // Check if the area is already selected
      const index = newSelection.indexOf(areaPath);
      
      // Toggle the selection
      if (index !== -1) {
        // If already selected, remove it
        newSelection.splice(index, 1);
      } else {
        // If not selected, add it
        newSelection.push(areaPath);
      }
      
      // Log the new selection for debugging
      console.log('Selected areas:', newSelection);
      
      // Update the parent component
      onAreaSelect(newSelection);
      
      return newSelection;
    });
    
    setSearchTerm('');
    setIsOpen(false);
  };

  // Handle route selection
  const handleRouteSelect = (route: Route) => {
    if (onRouteSelect) {
      onRouteSelect(route);
    }
    setSearchTerm('');
    setIsOpen(false);
  };

  // Handle removing a selected area
  const handleRemoveArea = (areaPath: string) => {
    setSelectedAreas(prev => {
      // Create a copy of the current selection
      const newSelection = [...prev];
      
      // Find and remove the specified area
      const index = newSelection.indexOf(areaPath);
      if (index !== -1) {
        newSelection.splice(index, 1);
      }
      
      // Log for debugging
      console.log('After removal, selected areas:', newSelection);
      
      // Update the parent component
      onAreaSelect(newSelection);
      
      return newSelection;
    });
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = () => {
      setIsOpen(false);
    };
    
    document.addEventListener('click', handleClickOutside);
    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, []);

  // Group results by type for display
  const areaResults = searchResults.filter(result => result.type === 'area');
  const routeResults = searchResults.filter(result => result.type === 'route');

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
            placeholder="Search for areas or routes... (e.g. 'utah sunshine')"
            className="w-full py-1 pl-9 pr-2 text-sm border rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600"
          />
        </div>
        
        {isOpen && searchResults.length > 0 && (
          <div className="absolute z-10 w-full mt-0.5 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded shadow-lg max-h-64 overflow-y-auto text-sm">
            <div className="py-1 px-2 text-xs text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
              Search results - click to select
            </div>
            
            {/* Show area results with a header */}
            {areaResults.length > 0 && (
              <div className="py-0.5 px-2 text-xs text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
                Areas:
              </div>
            )}
            {areaResults.map(result => (
              <div
                key={result.id}
                className={`py-1 px-2 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 ${
                  selectedAreas.includes(result.path!) ? 'bg-blue-100 dark:bg-blue-900' : ''
                }`}
                onClick={() => handleAreaSelect(result.path!)}
                title={result.path}
              >
                <span className="text-gray-900 dark:text-gray-100 text-xs flex items-center">
                  <span className="inline-block w-4 text-gray-500 mr-1">📁</span>
                  <span>{result.text}</span>
                  <span className="ml-auto text-blue-500 dark:text-blue-400">
                    {selectedAreas.includes(result.path!) ? '✓' : '+'}
                  </span>
                </span>
              </div>
            ))}
            
            {/* Show route results with a header */}
            {routeResults.length > 0 && (
              <div className="py-0.5 px-2 text-xs text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
                Routes:
              </div>
            )}
            {routeResults.map(result => (
              <div
                key={result.id}
                className="py-1 px-2 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700"
                onClick={() => handleRouteSelect(result.route!)}
                title={`${result.text} (${result.route!.route_grade})`}
              >
                <span className="text-gray-900 dark:text-gray-100 text-xs flex items-center">
                  <span className="inline-block w-4 text-gray-500 mr-1">🧗</span>
                  <span>{result.text}</span>
                  <span className="ml-1 text-gray-500">
                    {result.route!.route_grade}
                  </span>
                </span>
                <div className="text-xs text-gray-500 pl-5">
                  {result.route!.area_hierarchy && 
                   formatAreaPath(result.route!.area_hierarchy.map(h => h.area_hierarchy_name).join(' / '))}
                </div>
              </div>
            ))}
            
            {/* Show no matches message if search term exists but no results */}
            {searchTerm && searchResults.length === 0 && (
              <div className="py-2 px-3 text-gray-500 text-xs">
                No matching areas or routes found
              </div>
            )}
          </div>
        )}
      </div>
      
      {selectedAreas.length > 0 && (
        <div className="mt-1.5">
          <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">
            Selected Areas (showing routes from these locations):
          </div>
          <div className="flex flex-wrap gap-1">
            {selectedAreas.map(area => (
              <div
                key={area}
                className="flex items-center gap-0.5 py-0.5 px-1.5 bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded text-xs"
              >
                <span>{formatAreaPath(area).split(' / ').pop()}</span>
                <button
                  onClick={() => handleRemoveArea(area)}
                  className="inline-flex items-center justify-center w-3 h-3 ml-0.5 rounded-full bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 text-gray-500 dark:text-gray-400 text-[10px] leading-none"
                  aria-label="Remove"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
} 