import React, { useState } from 'react';
import { RouteFilters, SortConfig } from '../types';
import './FilterPanel.css';

interface FilterPanelProps {
  filters: RouteFilters;
  onFiltersChange: (filters: RouteFilters) => void;
  sortConfig: SortConfig;
  onSortChange: (sortConfig: SortConfig) => void;
}

// Simplified grade options for the UI
const SIMPLE_GRADES = [
  "5.3",
  "5.4",
  "5.5",
  "5.6", "5.7", "5.8", "5.9",
  "5.10a", "5.10b", "5.10c", "5.10d",
  "5.11a", "5.11b", "5.11c", "5.11d",
  "5.12a", "5.12b", "5.12c", "5.12d",
  "5.13a", "5.13b", "5.13c", "5.13d",
  "5.14a", "5.14b", "5.14c", "5.14d",
  "5.15a", "5.15b", "5.15c", "5.15d"
];

// Route types
const ROUTE_TYPES = [
  { id: 'trad', label: 'Trad' },
  { id: 'sport', label: 'Sport' },
  { id: 'multipitch', label: 'Multipitch' }
];

// Excluded route types
const EXCLUDED_TYPES = [
  { id: 'boulder', label: 'Boulder' },
  { id: 'aid', label: 'Aid' },
  { id: 'ice', label: 'Ice' },
  { id: 'mixed', label: 'Mixed' },
  { id: 'alpine', label: 'Alpine' }
];

// Sort options
const SORT_OPTIONS = [
  { key: 'quality', label: 'Quality (Stars & Votes)' },
  { key: 'grade', label: 'Grade' },
  { key: 'stars', label: 'Stars' },
  { key: 'votes', label: 'Votes' },
  { key: 'lr', label: 'Left to Right' }
];

const FilterPanel: React.FC<FilterPanelProps> = ({ 
  filters, 
  onFiltersChange, 
  sortConfig, 
  onSortChange 
}) => {
  // Local state for form controls
  const [minGrade, setMinGrade] = useState<string>(filters.minGrade || '');
  const [maxGrade, setMaxGrade] = useState<string>(filters.maxGrade || '');
  const [selectedTypes, setSelectedTypes] = useState<string[]>(
    [
      ...(filters.isTrad ? ['trad'] : []),
      ...(filters.isSport ? ['sport'] : []),
      ...(filters.isMultipitch ? ['multipitch'] : [])
    ]
  );
  const [excludedTypes, setExcludedTypes] = useState<string[]>(
    filters.excludedTypes || []
  );

  // Handle grade range changes
  const handleGradeChange = (type: 'min' | 'max', value: string) => {
    if (type === 'min') {
      setMinGrade(value);
      onFiltersChange({
        ...filters,
        minGrade: value || undefined
      });
    } else {
      setMaxGrade(value);
      onFiltersChange({
        ...filters,
        maxGrade: value || undefined
      });
    }
  };

  // Handle route type selection
  const handleTypeChange = (typeId: string, checked: boolean) => {
    let newSelectedTypes;
    
    if (checked) {
      newSelectedTypes = [...selectedTypes, typeId];
    } else {
      newSelectedTypes = selectedTypes.filter(t => t !== typeId);
    }
    
    setSelectedTypes(newSelectedTypes);
    
    // Update filters
    onFiltersChange({
      ...filters,
      isTrad: newSelectedTypes.includes('trad'),
      isSport: newSelectedTypes.includes('sport'),
      isMultipitch: newSelectedTypes.includes('multipitch')
    });
  };

  // Handle excluded types
  const handleExcludedTypeChange = (typeId: string, checked: boolean) => {
    let newExcludedTypes;
    
    if (checked) {
      newExcludedTypes = [...excludedTypes, typeId];
    } else {
      newExcludedTypes = excludedTypes.filter(t => t !== typeId);
    }
    
    setExcludedTypes(newExcludedTypes);
    
    // Update filters
    onFiltersChange({
      ...filters,
      excludedTypes: newExcludedTypes.length > 0 ? newExcludedTypes : undefined
    });
  };

  // Handle sort changes
  const handleSortChange = (key: string) => {
    // If clicking the same key, toggle direction
    const direction = 
      sortConfig.key === key && sortConfig.direction === 'desc' ? 'asc' : 'desc';
    
    onSortChange({
      key: key as 'grade' | 'stars' | 'votes' | 'lr' | 'quality',
      direction
    });
  };

  // Reset all filters
  const handleResetFilters = () => {
    setMinGrade('');
    setMaxGrade('');
    setSelectedTypes([]);
    setExcludedTypes([]);
    
    onFiltersChange({});
  };

  return (
    <div className="filter-panel-container">
      <h2>Filter Routes</h2>
      
      <div className="filter-section">
        <h3>Grade Range</h3>
        <div className="grade-range-controls">
          <div className="grade-select">
            <label htmlFor="min-grade">Min Grade:</label>
            <select 
              id="min-grade"
              value={minGrade}
              onChange={(e) => handleGradeChange('min', e.target.value)}
            >
              <option value="">Any</option>
              {SIMPLE_GRADES.map(grade => (
                <option key={`min-${grade}`} value={grade}>{grade}</option>
              ))}
            </select>
          </div>
          
          <div className="grade-select">
            <label htmlFor="max-grade">Max Grade:</label>
            <select 
              id="max-grade"
              value={maxGrade}
              onChange={(e) => handleGradeChange('max', e.target.value)}
            >
              <option value="">Any</option>
              {SIMPLE_GRADES.map(grade => (
                <option key={`max-${grade}`} value={grade}>{grade}</option>
              ))}
            </select>
          </div>
        </div>
      </div>
      
      <div className="filter-section">
        <h3>Route Type</h3>
        <div className="checkbox-group">
          {ROUTE_TYPES.map(type => (
            <div key={type.id} className="checkbox-item">
              <input
                type="checkbox"
                id={`type-${type.id}`}
                checked={selectedTypes.includes(type.id)}
                onChange={(e) => handleTypeChange(type.id, e.target.checked)}
              />
              <label htmlFor={`type-${type.id}`}>{type.label}</label>
            </div>
          ))}
        </div>
      </div>
      
      <div className="filter-section">
        <h3>Exclude Types</h3>
        <div className="checkbox-group">
          {EXCLUDED_TYPES.map(type => (
            <div key={type.id} className="checkbox-item">
              <input
                type="checkbox"
                id={`exclude-${type.id}`}
                checked={excludedTypes.includes(type.id)}
                onChange={(e) => handleExcludedTypeChange(type.id, e.target.checked)}
              />
              <label htmlFor={`exclude-${type.id}`}>{type.label}</label>
            </div>
          ))}
        </div>
      </div>
      
      <div className="filter-section">
        <h3>Sort By</h3>
        <div className="sort-options">
          {SORT_OPTIONS.map(option => (
            <div 
              key={option.key} 
              className={`sort-option ${sortConfig.key === option.key ? 'active' : ''}`}
              onClick={() => handleSortChange(option.key)}
            >
              {option.label}
              {sortConfig.key === option.key && (
                <span className="sort-direction">
                  {sortConfig.direction === 'asc' ? '↑' : '↓'}
                </span>
              )}
            </div>
          ))}
        </div>
      </div>
      
      <button 
        className="reset-filters-button"
        onClick={handleResetFilters}
      >
        Reset Filters
      </button>
    </div>
  );
};

export default FilterPanel; 