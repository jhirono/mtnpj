import React, { useState, useCallback, useEffect } from 'react';
import { Area } from '../types';
import { getAreas } from '../firebase.js'; // Import only getAreas
import debounce from 'lodash.debounce';
import './AreaSearch.css';

interface AreaSearchProps {
  selectedAreaIds: string[];
  onAreaSelect: (areaIds: string[]) => void;
}

const AreaSearch: React.FC<AreaSearchProps> = ({ selectedAreaIds, onAreaSelect }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Area[]>([]);
  const [allAreas, setAllAreas] = useState<Area[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [debugInfo, setDebugInfo] = useState<string>('');

  // Load all areas once on component mount
  useEffect(() => {
    const loadAllAreas = async () => {
      try {
        setIsLoading(true);
        console.log("Loading all areas...");
        const areas = await getAreas();
        console.log(`Loaded ${areas.length} areas from Firestore`);
        
        // Debug: Check for data structure issues
        const validAreas = areas.filter(a => a && a.area_name);
        const invalidAreas = areas.filter(a => !a || !a.area_name);
        
        if (invalidAreas.length > 0) {
          console.warn(`Found ${invalidAreas.length} areas with missing names`);
          console.log("Sample invalid area:", invalidAreas[0]);
        }
        
        // Debug: Check for hierarchy structure issues
        const areasWithHierarchy = areas.filter(a => a && a.area_hierarchy && Array.isArray(a.area_hierarchy) && a.area_hierarchy.length > 0);
        console.log(`Areas with hierarchy data: ${areasWithHierarchy.length} of ${areas.length}`);
        
        if (areasWithHierarchy.length > 0) {
          const sampleArea = areasWithHierarchy[0];
          console.log("Sample hierarchy structure:", sampleArea.area_hierarchy);
        }
        
        // Debug: Log a few sample areas
        if (areas.length > 0) {
          console.log("First few areas:", areas.slice(0, 3).map(a => ({ 
            id: a.id, 
            name: a.area_name,
            hasHierarchy: Boolean(a.area_hierarchy && Array.isArray(a.area_hierarchy) && a.area_hierarchy.length > 0),
            hierarchyLength: Array.isArray(a.area_hierarchy) ? a.area_hierarchy.length : 0
          })));
        }
        
        setAllAreas(validAreas);
        updateDebugInfo(`Loaded ${validAreas.length} valid areas from database (${invalidAreas.length} invalid)`);
      } catch (error) {
        console.error("Error loading areas:", error);
        setDebugInfo(`Error loading areas: ${error}`);
      } finally {
        setIsLoading(false);
      }
    };
    
    loadAllAreas();
  }, []);

  // Implement direct search function (not using imported searchAreas)
  const performSearch = async (query: string): Promise<Area[]> => {
    updateDebugInfo(`Searching for "${query}" in ${allAreas.length} areas...`);
    console.log(`Performing search for "${query}" in ${allAreas.length} areas`);
    
    // If query is empty or too short, return empty array
    if (!query || query.trim().length < 2) {
      return [];
    }
    
    // Split search into terms for better matching
    const searchTerms = query.toLowerCase().trim().split(/\s+/);
    console.log("Search terms:", searchTerms);
    
    // Score each area based on match quality
    const scoredAreas = allAreas.map(area => {
      // Skip invalid areas
      if (!area || !area.area_name) {
        return { area, score: 0, matchDetails: ['Invalid area data'] };
      }

      const areaName = (area.area_name || '').toLowerCase();
      const areaDesc = (area.area_description || '').toLowerCase();
      const searchableText = (area.searchable_text || '').toLowerCase();
      
      // Calculate match score (higher is better)
      let score = 0;
      let matchDetails = [];
      
      for (const term of searchTerms) {
        // Exact matches in name are weighted highest
        if (areaName.includes(term)) {
          score += 10;
          matchDetails.push(`Name match: ${term} in ${areaName}`);
          // Bonus for starts with
          if (areaName.startsWith(term)) {
            score += 5;
            matchDetails.push(`Name starts with: ${term}`);
          }
          // Bonus for exact match
          if (areaName === term) {
            score += 10;
            matchDetails.push(`Name exact match: ${term}`);
          }
        }
        
        // Matches in hierarchy names
        const hierarchyMatches = area.area_hierarchy?.filter(
          h => h && h.area_hierarchy_name && typeof h.area_hierarchy_name === 'string' && 
            h.area_hierarchy_name.toLowerCase().includes(term)
        )?.length || 0;
        if (hierarchyMatches > 0) {
          score += hierarchyMatches * 3;
          matchDetails.push(`Hierarchy match: ${term} (${hierarchyMatches} matches)`);
        }
        
        // Matches in description
        if (areaDesc.includes(term)) {
          score += 2;
          matchDetails.push(`Description match: ${term}`);
        }
        
        // Matches in searchable text
        if (searchableText.includes(term)) {
          score += 1;
          matchDetails.push(`Searchable text match: ${term}`);
        }
      }
      
      return { area, score, matchDetails };
    });
    
    // Debug: Log some info about the scoring
    const nonZeroScores = scoredAreas.filter(item => item.score > 0);
    console.log(`Found ${nonZeroScores.length} areas with non-zero scores`);
    
    if (nonZeroScores.length > 0) {
      // Show the top 3 matches with their details
      nonZeroScores
        .sort((a, b) => b.score - a.score)
        .slice(0, 3)
        .forEach(item => {
          console.log(`Match: ${item.area.area_name} (Score: ${item.score})`);
          console.log(`  Details: ${item.matchDetails.join(', ')}`);
        });
    } else {
      // Debug why nothing is matching
      console.log("No matches found. Sample area data:");
      allAreas.slice(0, 3).forEach(area => {
        console.log(`Area: ${area.area_name}`);
        console.log(`  Description: ${area.area_description?.substring(0, 50)}...`);
        console.log(`  Searchable text: ${area.searchable_text?.substring(0, 50)}...`);
        console.log(`  Hierarchy: ${area.area_hierarchy?.map(h => h.area_hierarchy_name).join(' > ')}`);
      });
    }
    
    // Filter out non-matches and sort by score
    const filteredAreas = scoredAreas
      .filter(item => item.score > 0)
      .sort((a, b) => b.score - a.score)
      .map(item => item.area)
      .slice(0, 15); // Limit to 15 results
    
    updateDebugInfo(`Found ${filteredAreas.length} areas matching "${query}"`);
    return filteredAreas;
  };

  // Debounced search function
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const debouncedSearch = useCallback(
    debounce(async (query: string) => {
      // Clear results if query is empty
      if (!query || query.trim().length < 2) {
        setSearchResults([]);
        setIsLoading(false);
        updateDebugInfo('Enter at least 2 characters to search');
        return;
      }

      try {
        console.log("Searching for:", query);
        const results = await performSearch(query);
        console.log("Search results:", results.length);
        
        if (results.length === 0) {
          // Fall back to a very simple search as a last resort
          console.log("No results found with advanced search, trying simple name matching");
          const simpleResults = allAreas.filter(area => 
            area && 
            area.area_name && 
            area.area_name.toLowerCase().includes(query.toLowerCase())
          );
          
          if (simpleResults.length > 0) {
            console.log(`Found ${simpleResults.length} areas with simple name matching`);
            setSearchResults(simpleResults);
            updateDebugInfo(`Found ${simpleResults.length} areas using simple name matching for "${query}"`);
          } else {
            setSearchResults([]);
            updateDebugInfo(`No areas found matching "${query}"`);
          }
        } else {
          setSearchResults(results);
          updateDebugInfo(`Found ${results.length} areas matching "${query}"`);
        }
      } catch (error) {
        console.error('Error searching areas:', error);
        setSearchResults([]);
        updateDebugInfo(`Error during search: ${error instanceof Error ? error.message : String(error)}`);
      } finally {
        setIsLoading(false);
      }
    }, 300),
    [allAreas] // Add allAreas as a dependency
  );

  // Handle search input change
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);
    setIsLoading(true);
    debouncedSearch(query);
  };

  // Toggle area selection
  const toggleAreaSelection = (areaId: string) => {
    // Replace existing selections with just this one area
    onAreaSelect([areaId]);
  };

  // Render an area item with selection radio button
  const renderAreaItem = (area: Area) => (
    <div key={area.id} className="area-item">
      <label className="area-checkbox">
        <input
          type="radio"
          checked={selectedAreaIds.includes(area.id!)}
          onChange={() => toggleAreaSelection(area.id!)}
        />
        <span className="area-name">{area.area_name || 'Unnamed Area'}</span>
      </label>
      {area.area_hierarchy && Array.isArray(area.area_hierarchy) && area.area_hierarchy.length > 0 && (
        <div className="area-hierarchy-info">
          <small>
            {area.area_hierarchy
              .filter(h => h && h.area_hierarchy_name)
              .map(h => h.area_hierarchy_name)
              .join(' > ')}
          </small>
        </div>
      )}
    </div>
  );

  // Simple debugging indicator
  const renderDebugInfo = () => {
    if (!debugInfo) return null;
    
    return (
      <div className="debug-info">
        <small>{debugInfo}</small>
      </div>
    );
  };

  // Keep this utility function to update debug info and log to console
  const updateDebugInfo = (message: string) => {
    console.log(`[DEBUG] ${message}`);
    // Still set the state so it's available for future debugging if needed
    setDebugInfo(message);
  }

  return (
    <div className="area-search">
      <h2>Search Climbing Areas</h2>
      
      <div className="search-container">
        <input
          type="text"
          className="search-input"
          placeholder="Enter area name (e.g., Smoke Bluff, Yosemite)..."
          value={searchQuery}
          onChange={handleSearchChange}
        />
        
        <div className="search-results">
          {isLoading ? (
            <div className="loading">Loading...</div>
          ) : searchResults.length > 0 ? (
            <div className="results-list">
              {searchResults.map(renderAreaItem)}
            </div>
          ) : searchQuery.length > 1 ? (
            <div className="no-results">
              <p>No areas found with "{searchQuery}"</p>
              <p className="suggestion">Try a different search term or check spelling</p>
            </div>
          ) : (
            <div className="search-prompt">Type at least 2 characters to search</div>
          )}
        </div>
      </div>
      
      {selectedAreaIds.length > 0 && (
        <div className="selected-areas">
          <h3>Selected Area</h3>
          <button 
            className="clear-button"
            onClick={() => onAreaSelect([])}
          >
            Clear
          </button>
        </div>
      )}
    </div>
  );
};

export default AreaSearch; 