import { useState, useEffect, useMemo } from 'react';
import type { Area } from '../types/area';

interface AreaSearchProps {
  areas: Area[];
  onAreaSelect: (selectedIds: string[]) => void;
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

export function AreaSearch({ areas, onAreaSelect }: AreaSearchProps) {
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

  // Filter areas based on search term
  const filteredAreas = useMemo(() => {
    if (!searchTerm) return [];
    
    return allAreaPaths.filter(path => 
      path.toLowerCase().includes(searchTerm.toLowerCase())
    ).slice(0, 10); // Limit to 10 results
  }, [searchTerm, allAreaPaths]);

  // Handle area selection
  const handleAreaSelect = (areaPath: string) => {
    setSelectedAreas(prev => {
      const newSelection = prev.includes(areaPath)
        ? prev.filter(a => a !== areaPath)
        : [...prev, areaPath];
      
      onAreaSelect(newSelection);
      return newSelection;
    });
    
    setSearchTerm('');
    setIsOpen(false);
  };

  // Handle removing a selected area
  const handleRemoveArea = (areaPath: string) => {
    setSelectedAreas(prev => {
      const newSelection = prev.filter(a => a !== areaPath);
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

  return (
    <div className="mb-3 bg-white dark:bg-gray-800 rounded-lg shadow p-2">
      <div className="relative">
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
          placeholder="Search for areas and click to select..."
          className="w-full py-1 px-2 text-sm border rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600"
        />
        
        {isOpen && filteredAreas.length > 0 && (
          <div className="absolute z-10 w-full mt-0.5 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded shadow-lg max-h-48 overflow-y-auto text-sm">
            <div className="py-1 px-2 text-xs text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
              Click on an area to select it
            </div>
            {filteredAreas.map(area => (
              <div
                key={area}
                className={`py-1 px-2 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 ${
                  selectedAreas.includes(area) ? 'bg-blue-100 dark:bg-blue-900' : ''
                }`}
                onClick={() => handleAreaSelect(area)}
                title={area}
              >
                <span className="text-gray-900 dark:text-gray-100 text-xs flex items-center justify-between">
                  <span>{formatAreaPath(area)}</span>
                  <span className="ml-1 text-blue-500 dark:text-blue-400">
                    {selectedAreas.includes(area) ? '✓' : '+'}
                  </span>
                </span>
              </div>
            ))}
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