import React, { useState } from 'react';
import AreaSearch from './components/AreaSearch';
import FilterPanel from './components/FilterPanel';
import RouteList from './components/RouteList';
import { RouteFilters, SortConfig } from './types';
import './App.css';

const App: React.FC = () => {
  const [selectedAreaIds, setSelectedAreaIds] = useState<string[]>([]);
  const [filters, setFilters] = useState<RouteFilters>({});
  const [sortConfig, setSortConfig] = useState<SortConfig>({
    key: 'quality',
    direction: 'desc'
  });

  // Handle filter changes
  const handleFiltersChange = (newFilters: RouteFilters) => {
    console.log('Filters updated:', newFilters);
    setFilters(newFilters);
  };

  // Handle sort changes
  const handleSortChange = (newSortConfig: SortConfig) => {
    console.log('Sort updated:', newSortConfig);
    setSortConfig(newSortConfig);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Climbing Route Search</h1>
      </header>
      
      <main className="app-content">
        <div className="search-container">
          <div className="area-search-wrapper">
            <AreaSearch 
              selectedAreaIds={selectedAreaIds}
              onAreaSelect={setSelectedAreaIds}
            />
          </div>
          
          <div className="filter-panel-wrapper">
            <FilterPanel 
              filters={filters}
              onFiltersChange={handleFiltersChange}
              sortConfig={sortConfig}
              onSortChange={handleSortChange}
            />
          </div>
          
          <div className="results-panel">
            <RouteList 
              selectedAreaIds={selectedAreaIds}
              filters={filters}
              sortConfig={sortConfig}
            />
          </div>
        </div>
      </main>
      
      <footer className="app-footer">
        <p>Climbing Route Search App</p>
      </footer>
    </div>
  );
};

export default App; 