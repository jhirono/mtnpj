import { useState, useMemo } from 'react';
import type { Area } from '../types/area';
import type { AreaHierarchy } from '../types/route';

interface AreaSearchProps {
  areas: Area[];
  onAreaSelect: (areaIds: string[]) => void;
}

interface SearchResult {
  id: string;
  displayName: string;
  fullPath: string;
  hierarchy: AreaHierarchy[];
}

function shortenHierarchy(hierarchy: AreaHierarchy[]): string {
  // Skip "All Locations" and keep only relevant parts
  const relevantHierarchy = hierarchy
    .filter(h => h.area_hierarchy_name !== "All Locations")
    .map(h => h.area_hierarchy_name);

  // If hierarchy is longer than 3 levels, show only last 3 with ellipsis
  if (relevantHierarchy.length > 3) {
    return '...' + relevantHierarchy.slice(-3).join(' / ');
  }

  return relevantHierarchy.join(' / ');
}

export function AreaSearch({ areas, onAreaSelect }: AreaSearchProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAreas, setSelectedAreas] = useState<string[]>([]);

  // Prepare searchable items
  const searchableItems = useMemo(() => {
    const items: SearchResult[] = [];

    areas.forEach(area => {
      // Add each hierarchy level
      area.area_hierarchy.forEach((_, index) => {
        const hierarchySlice = area.area_hierarchy.slice(0, index + 1);
        // Skip if it's just "All Locations"
        if (hierarchySlice.length === 1 && 
            hierarchySlice[0].area_hierarchy_name === "All Locations") {
          return;
        }
        
        items.push({
          id: hierarchySlice.map(h => h.area_hierarchy_name).join(' / '),
          displayName: hierarchySlice[hierarchySlice.length - 1].area_hierarchy_name,
          fullPath: shortenHierarchy(hierarchySlice),
          hierarchy: hierarchySlice
        });
      });
    });

    // Remove duplicates
    return Array.from(new Map(items.map(item => [item.id, item])).values());
  }, [areas]);

  // Filter items based on search term
  const searchResults = useMemo(() => {
    if (!searchTerm) return [];
    
    const searchLower = searchTerm.toLowerCase();
    return searchableItems.filter(item => 
      item.fullPath.toLowerCase().includes(searchLower)
    );
  }, [searchableItems, searchTerm]);

  const handleSelect = (item: SearchResult) => {
    const newSelected = selectedAreas.includes(item.id)
      ? selectedAreas.filter(id => id !== item.id)
      : [...selectedAreas, item.id];
    
    setSelectedAreas(newSelected);
    onAreaSelect(newSelected);
  };

  return (
    <div className="mb-3">
      <div className="relative">
        <input
          type="text"
          placeholder="Search locations..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full py-1.5 px-2 pr-6 border rounded text-sm"
        />
        {searchTerm && (
          <button
            onClick={() => setSearchTerm('')}
            className="absolute right-2 top-[50%] -translate-y-[50%] text-gray-400 hover:text-gray-600 w-4 h-4 flex items-center justify-center text-base leading-[0]"
            aria-label="Clear search"
          >
            ×
          </button>
        )}
      </div>
      
      {/* Show selected areas */}
      {selectedAreas.length > 0 && (
        <div className="mt-2">
          <h3 className="text-xs font-medium mb-1">Selected Areas:</h3>
          <div className="space-y-0.5">
            {selectedAreas.map(id => {
              const item = searchableItems.find(i => i.id === id);
              return item && (
                <div key={id} className="flex items-center text-xs bg-gray-50 py-0.5 px-1.5 rounded">
                  <span className="flex-grow truncate">{item.fullPath}</span>
                  <button
                    onClick={() => handleSelect(item)}
                    className="ml-1.5 text-gray-400 hover:text-gray-600"
                  >
                    ×
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Search results */}
      {searchTerm && (
        <div className="mt-1 max-h-48 overflow-y-auto border rounded text-sm">
          {searchResults.length > 0 ? (
            searchResults.map(item => (
              <button
                key={item.id}
                onClick={() => handleSelect(item)}
                className={`w-full text-left py-1 px-2 hover:bg-gray-50 ${
                  selectedAreas.includes(item.id) ? 'bg-gray-50' : ''
                }`}
              >
                <div className="text-xs truncate">{item.fullPath}</div>
              </button>
            ))
          ) : (
            <div className="py-1 px-2 text-xs text-gray-500">No results found</div>
          )}
        </div>
      )}
    </div>
  );
} 