import { useState, useEffect, useMemo } from 'react'
import type { RouteFilters, GradeRange, SortConfig, SortOption } from '../types/filters'
import type { Area } from '../types/area'
import { GRADE_ORDER, SIMPLE_GRADES } from '../types/filters'

interface FilterPanelProps {
  filters: RouteFilters;
  onChange: (filters: RouteFilters) => void;
  sortConfig: SortConfig;
  onSortChange: (sort: SortConfig) => void;
  areas: Area[];
}

export function FilterPanel({ filters, onChange, sortConfig, onSortChange, areas }: FilterPanelProps) {
  // Initialize with all categories expanded
  const [expandedCategories, setExpandedCategories] = useState<string[]>([
    'grades',
    'Crowds & Popularity',
    'Difficulty & Safety',
    'Crack Climbing',
    'Multi-Pitch, Anchors & Descent'
  ])
  const [availableTags, setAvailableTags] = useState<Record<string, Set<string>>>({})
  // Add state for grade filter enabled
  const [gradeFilterEnabled, setGradeFilterEnabled] = useState(false);

  // First, collect available tags
  useEffect(() => {
    const tags: Record<string, Set<string>> = {}
    
    // Debug first route's tags
    console.log('First route tags:', areas[0]?.routes[0]?.route_tags)
    
    areas.forEach(area => {
      area.routes.forEach(route => {
        // Debug log for these specific categories
        console.log('Route:', route.route_name)
        console.log('Difficulty tags:', route.route_tags["Difficulty & Safety"])
        console.log('Multi-pitch tags:', route.route_tags["Multi-Pitch, Anchors & Descent"])
        
        Object.entries(route.route_tags).forEach(([category, tagList]) => {
          if (!tags[category]) {
            tags[category] = new Set()
          }
          // Each tag item is a string
          tagList.forEach(tagItem => {
            console.log('Adding tag:', category, tagItem)
            tags[category].add(tagItem)
          })
        })
      })
    })

    // Log the specific categories we're interested in
    console.log('Available Difficulty tags:', tags["Difficulty & Safety"])
    console.log('Available Multi-pitch tags:', tags["Multi-Pitch, Anchors & Descent"])
    
    setAvailableTags(tags)
  }, [areas])

  // Define tag categories based on availableTags
  const tagCategories = useMemo(() => ({
    "Crowds & Popularity": ["low_crowds", "classic_route", "new_routes"]
      .filter(tag => tag && availableTags["Crowds & Popularity"]?.has(tag))
      .map(tag => ({
        value: tag,
        label: tag === "low_crowds" ? "Less Crowded" :
              tag === "classic_route" ? "Classic Route" :
              "New Route (since 2022)"
      })),

    "Difficulty & Safety": ["first_in_grade", "exclude_sandbag"]
      .filter(tag => tag || availableTags["Difficulty & Safety"]?.has("sandbag"))
      .map(tag => ({
        value: tag,
        label: tag === "first_in_grade" ? "Good for Breaking into Grade" : 
               tag === "exclude_sandbag" ? "Exclude Sandbag Routes" : ""
      })),

    "Crack Climbing": ["finger", "thin_hand", "wide_hand", "offwidth", "chimney"]  // Specified order
      .filter(tag => availableTags["Crack Climbing"]?.has(tag))
      .map(tag => ({
        value: tag,
        label: tag.split('_').join(' ')
      })),

    "Multi-Pitch, Anchors & Descent": ["single_pitch", "short_multipitch", "long_multipitch"]
      .filter(tag => {
        if (tag === "single_pitch") return true;
        return tag && availableTags["Multi-Pitch, Anchors & Descent"]?.has(tag);
      })
      .map(tag => ({
        value: tag,
        label: tag === "single_pitch" ? "Single Pitch" :
               tag === "short_multipitch" ? "Short (2-4 pitches)" : 
               "Long (5+ pitches)"
      }))
  }), [availableTags])

  // Filter out empty categories
  const nonEmptyCategories = useMemo(() => 
    Object.entries(tagCategories)
      .filter(([_, tags]) => tags.length > 0)
      .reduce((acc, [category, tags]) => ({
        ...acc,
        [category]: tags
      }), {} as typeof tagCategories)
  , [tagCategories])

  const toggleCategory = (category: string) => {
    setExpandedCategories(prev => 
      prev.includes(category)
        ? prev.filter(c => c !== category)
        : [...prev, category]
    )
  }

  const toggleTag = (category: string, tag: string) => {
    const categoryFilters = filters.tags.find(t => t.category === category)
    const newTags = categoryFilters
      ? categoryFilters.selectedTags.includes(tag)
        ? categoryFilters.selectedTags.filter(t => t !== tag)
        : [...categoryFilters.selectedTags, tag]
      : [tag]

    const newTagFilters = filters.tags
      .filter(t => t.category !== category)
      .concat(newTags.length ? [{ category, selectedTags: newTags }] : [])

    onChange({
      ...filters,
      tags: newTagFilters
    })
  }

  const isTagSelected = (category: string, tag: string) => {
    return filters.tags.some(t => 
      t.category === category && t.selectedTags.includes(tag)
    )
  }

  const toggleType = (type: 'Trad' | 'Sport') => {
    const newTypes = filters.types.includes(type)
      ? filters.types.filter(t => t !== type)
      : [...filters.types, type]
    
    onChange({
      ...filters,
      types: newTypes
    })
  }

  const updateGradeRange = (range: GradeRange) => {
    onChange({
      ...filters,
      grades: range
    })
  }

  return (
    <div className="space-y-3 p-3 bg-white rounded-lg shadow text-sm">
      {/* Sorting Options */}
      <div className="filter-group">
        <h3 className="font-medium mb-1">Sort by</h3>
        <select
          value={sortConfig.option}
          onChange={(e) => onSortChange({ 
            ...sortConfig, 
            option: e.target.value as SortOption 
          })}
          className="w-full p-1.5 border rounded mb-1 text-sm"
        >
          <option value="grade">Grade</option>
          <option value="stars">Stars</option>
          <option value="votes"># of Votes</option>
          <option value="left_to_right">Left to Right</option>
        </select>
        <label className="flex items-center text-sm">
          <input
            type="checkbox"
            checked={sortConfig.ascending}
            onChange={() => onSortChange({ 
              ...sortConfig, 
              ascending: !sortConfig.ascending 
            })}
            className="mr-1.5"
          />
          Reverse order
        </label>
      </div>

      {/* Grade Range Selector */}
      <div className="filter-group">
        <div className="flex items-center gap-2 mb-2">
          <input
            type="checkbox"
            checked={gradeFilterEnabled}
            onChange={(e) => {
              setGradeFilterEnabled(e.target.checked);
              // Clear grade filters when disabled
              if (!e.target.checked) {
                onChange({
                  ...filters,
                  grades: { min: "", max: "" }
                });
              } else {
                // Set default range when enabled
                onChange({
                  ...filters,
                  grades: { min: "5.10a", max: "5.11a" }
                });
              }
            }}
            className="mr-1"
          />
          <label className="text-sm font-medium">Enable Grade Filter</label>
        </div>
        
        {gradeFilterEnabled && (
          <>
            <button 
              className="w-full flex justify-between items-center py-1.5 px-3 bg-gray-100 rounded text-sm"
              onClick={() => toggleCategory('grades')}
            >
              <span>Grade: {filters.grades.min} - {filters.grades.max}</span>
              <span>{expandedCategories.includes('grades') ? '▼' : '▶'}</span>
            </button>
            {expandedCategories.includes('grades') && (
              <div className="mt-1 space-y-1 pl-3">
                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <label className="block text-sm font-medium mb-1">Min Grade</label>
                    <select
                      value={filters.grades.min}
                      onChange={(e) => updateGradeRange({ 
                        ...filters.grades, 
                        min: e.target.value,
                        max: GRADE_ORDER.indexOf(e.target.value) <= GRADE_ORDER.indexOf(filters.grades.max) 
                          ? filters.grades.max 
                          : e.target.value
                      })}
                      className="w-full p-2 border rounded"
                    >
                      {SIMPLE_GRADES.map(grade => (
                        <option key={grade} value={grade}>
                          {grade}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="flex-1">
                    <label className="block text-sm font-medium mb-1">Max Grade</label>
                    <select
                      value={filters.grades.max}
                      onChange={(e) => updateGradeRange({ 
                        ...filters.grades, 
                        max: e.target.value,
                        min: GRADE_ORDER.indexOf(e.target.value) >= GRADE_ORDER.indexOf(filters.grades.min)
                          ? filters.grades.min
                          : e.target.value
                      })}
                      className="w-full p-2 border rounded"
                    >
                      {SIMPLE_GRADES.map(grade => (
                        <option key={grade} value={grade}>
                          {grade}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Route Type */}
      <div className="filter-group">
        <h3 className="font-medium mb-1">Type</h3>
        <div className="flex gap-3">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={filters.types.includes('Trad')}
              onChange={() => toggleType('Trad')}
              className="mr-2"
            />
            Trad
          </label>
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={filters.types.includes('Sport')}
              onChange={() => toggleType('Sport')}
              className="mr-2"
            />
            Sport
          </label>
        </div>
      </div>

      {/* Tag Categories */}
      {Object.entries(nonEmptyCategories).map(([category, tags]) => (
        <div key={category} className="filter-group">
          <button 
            className="w-full flex justify-between items-center py-1.5 px-3 bg-gray-100 rounded text-sm"
            onClick={() => toggleCategory(category)}
          >
            <span>{category}</span>
            <span>{expandedCategories.includes(category) ? '▼' : '▶'}</span>
          </button>
          {expandedCategories.includes(category) && (
            <div className="mt-1 space-y-1 pl-3">
              {tags.map(({ value, label }) => (
                <label key={value} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={isTagSelected(category, value)}
                    onChange={() => toggleTag(category, value)}
                    className="mr-2"
                  />
                  {label}
                </label>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  )
} 