import { useState, useEffect, useMemo } from 'react'
import type { RouteFilters, GradeRange, SortConfig, SortOption } from '../types/filters'
import type { Area } from '../types/area'
import { GRADE_ORDER, SIMPLE_GRADES } from '../types/filters'

// Add type declaration for the Buy Me a Coffee button
declare global {
  interface Window {
    createBMCButton?: (options: {
      target: string;
      data: Record<string, string>;
    }) => void;
  }
}

interface FilterPanelProps {
  filters: RouteFilters;
  onChange: (filters: RouteFilters) => void;
  sortConfig: SortConfig;
  onSortChange: (sort: SortConfig) => void;
  areas: Area[];
}

export function FilterPanel({ filters, onChange, sortConfig, onSortChange, areas }: FilterPanelProps) {
  // Initialize with categories expanded based on screen size
  const [expandedCategories, setExpandedCategories] = useState<string[]>([])
  const [availableTags, setAvailableTags] = useState<Record<string, Set<string>>>({})
  // Add state for grade filter enabled
  const [gradeFilterEnabled, setGradeFilterEnabled] = useState(false);

  // Set expanded categories based on screen size
  useEffect(() => {
    const handleResize = () => {
      const isMobile = window.innerWidth < 768; // Standard mobile breakpoint
      
      if (isMobile) {
        // On mobile, collapse all categories by default to save space
        setExpandedCategories([]);
      } else {
        // On desktop, expand common categories
        setExpandedCategories([
          'grades',
          'Crowds & Popularity',
          'Difficulty & Safety',
          'Multi-Pitch, Anchors & Descent'
        ]);
      }
    };
    
    // Set initial state
    handleResize();
    
    // Add event listener for window resize
    window.addEventListener('resize', handleResize);
    
    // Clean up
    return () => window.removeEventListener('resize', handleResize);
  }, []);

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

    "Difficulty & Safety": ["first_in_grade", "exclude_sandbag", "exclude_runout_dangerous"]
      .filter(tag => tag || availableTags["Difficulty & Safety"]?.has("sandbag") || availableTags["Difficulty & Safety"]?.has("runout_dangerous"))
      .map(tag => ({
        value: tag,
        label: tag === "first_in_grade" ? "Good for Breaking into Grade" : 
               tag === "exclude_sandbag" ? "Exclude Sandbag Routes" :
               tag === "exclude_runout_dangerous" ? "Exclude Dangerous Routes" : ""
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
      })),

    "Crack Climbing": ["finger", "thin_hand", "wide_hand", "offwidth", "chimney"]  // Specified order
      .filter(tag => availableTags["Crack Climbing"]?.has(tag))
      .map(tag => ({
        value: tag,
        label: tag.split('_').join(' ')
      })),

    "Route Style & Angle": ["slab", "vertical", "gentle_overhang", "steep_roof", 
                           "tower_climbing", "sporty_trad"]
      .filter(tag => availableTags["Route Style & Angle"]?.has(tag))
      .map(tag => ({
        value: tag,
        label: tag.split('_').join(' ')
      })),

    "Hold & Movement Type": ["reachy", "dynamic_moves", "pumpy_sustained", "technical_moves", 
                            "powerful_bouldery", "pockets_holes", "small_edges", "slopey_holds"]
      .filter(tag => availableTags["Hold & Movement Type"]?.has(tag))
      .map(tag => ({
        value: tag,
        label: tag.split('_').join(' ')
      })),

    "Weather & Conditions": ["sun_am", "sun_pm", "tree_filtered_sun_am", "tree_filtered_sun_pm", 
                           "sunny_all_day", "shady_all_day", "dries_fast", "dry_in_rain", 
                           "seepage_problem", "windy_exposed"]
      .filter(tag => availableTags["Weather & Conditions"]?.has(tag))
      .map(tag => ({
        value: tag,
        label: tag.split('_').join(' ')
      })),

    "Rope Length": ["rope_60m", "rope_70m", "rope_80m"]
      .filter(tag => availableTags["Rope Length"]?.has(tag))
      // Sort to ensure correct order regardless of availableTags order
      .sort((a, b) => {
        const order = ["rope_60m", "rope_70m", "rope_80m"];
        return order.indexOf(a) - order.indexOf(b);
      })
      .map(tag => ({
        value: tag,
        label: tag.replace('rope_', '') // Convert rope_60m to 60m for display
      })),
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

  // Remove the Buy Me a Book button initialization
  useEffect(() => {
    // Check if the BMC script is loaded
    if (typeof window !== 'undefined' && window.document && document.getElementById('bmc-container')) {
      // If the BMC button already exists, remove it first to prevent duplicates
      const existingButton = document.querySelector('#bmc-container .bmc-button');
      if (existingButton) {
        existingButton.remove();
      }
      
      // Create the button if the BMC script is loaded
      if (typeof window.createBMCButton === 'function') {
        window.createBMCButton({
          target: '#bmc-container',
          data: {
            name: 'bmc-button',
            slug: 'bonvi',
            color: '#5F7FFF',
            emoji: '📖',
            font: 'Cookie',
            text: 'Buy me a book',
            'outline-color': '#000000',
            'font-color': '#ffffff',
            'coffee-color': '#FFDD00'
          }
        });
      }
    }
  }, []);

  return (
    <div className="space-y-2.5 p-2.5 bg-white dark:bg-gray-800 rounded-lg shadow text-sm overflow-y-auto max-h-[calc(100vh-120px)]">
      {/* Sorting Options - Now in one row with reverse order checkbox */}
      <div className="filter-group">
        <div className="flex items-center gap-2">
          <h3 className="font-medium text-gray-900 dark:text-gray-100 whitespace-nowrap">Sort by</h3>
          <select
            value={sortConfig.option}
            onChange={(e) => onSortChange({ 
              ...sortConfig, 
              option: e.target.value as SortOption 
            })}
            className="flex-1 p-1.5 border rounded text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600"
          >
            <option value="grade">Grade</option>
            <option value="stars">Stars</option>
            <option value="votes"># of Votes</option>
            <option value="left_to_right">Left to Right</option>
          </select>
          <label className="flex items-center text-sm text-gray-700 dark:text-gray-300 whitespace-nowrap">
            <input
              type="checkbox"
              checked={sortConfig.ascending}
              onChange={() => onSortChange({ 
                ...sortConfig, 
                ascending: !sortConfig.ascending 
              })}
              className="mr-1.5"
            />
            Reverse
          </label>
        </div>
      </div>

      {/* Route Type - In one row */}
      <div className="filter-group">
        <div className="flex items-center">
          <h3 className="font-medium text-gray-900 dark:text-gray-100 mr-3">Type</h3>
          <div className="flex gap-3 text-gray-700 dark:text-gray-300">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={filters.types.includes('Trad')}
                onChange={() => toggleType('Trad')}
                className="mr-1.5"
              />
              Trad
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={filters.types.includes('Sport')}
                onChange={() => toggleType('Sport')}
                className="mr-1.5"
              />
              Sport
            </label>
          </div>
        </div>
      </div>

      {/* Grade Filter - Moved below Type with closer checkbox */}
      <div className="filter-group">
        <div className="flex items-center gap-2">
          <h3 className="font-medium text-gray-900 dark:text-gray-100">Grade Filter</h3>
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
          />
        </div>
        
        {gradeFilterEnabled && (
          <div className="mt-1.5 space-y-1 text-gray-700 dark:text-gray-300">
            <div className="flex items-center gap-3">
              <div className="flex-1">
                <label className="block text-sm font-medium mb-0.5">Min Grade</label>
                <select
                  value={filters.grades.min}
                  onChange={(e) => updateGradeRange({ 
                    ...filters.grades, 
                    min: e.target.value,
                    max: GRADE_ORDER.indexOf(e.target.value) <= GRADE_ORDER.indexOf(filters.grades.max) 
                      ? filters.grades.max 
                      : e.target.value
                  })}
                  className="w-full p-1.5 border rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600"
                >
                  {SIMPLE_GRADES.map(grade => (
                    <option key={grade} value={grade}>
                      {grade}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex-1">
                <label className="block text-sm font-medium mb-0.5">Max Grade</label>
                <select
                  value={filters.grades.max}
                  onChange={(e) => updateGradeRange({ 
                    ...filters.grades, 
                    max: e.target.value,
                    min: GRADE_ORDER.indexOf(e.target.value) >= GRADE_ORDER.indexOf(filters.grades.min)
                      ? filters.grades.min
                      : e.target.value
                  })}
                  className="w-full p-1.5 border rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600"
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
      </div>

      {/* Tags Section Header */}
      <div className="filter-group mt-3 border-t pt-2.5 border-gray-200 dark:border-gray-700">
        <h3 className="font-medium mb-1.5 text-gray-900 dark:text-gray-100">
          Tags
        </h3>
      </div>

      {/* Tag Categories - Render in specific order */}
      {(["Crowds & Popularity", "Difficulty & Safety", "Multi-Pitch, Anchors & Descent"] as const)
        .filter(category => category in nonEmptyCategories)
        .map(category => (
          <div key={category} className="filter-group">
            <button 
              className="w-full flex justify-between items-center py-1.5 px-2.5 bg-gray-100 rounded text-sm text-gray-700 dark:bg-gray-700 dark:text-gray-300"
              onClick={() => toggleCategory(category)}
            >
              <span>
                {category === "Difficulty & Safety" ? "Difficulty" :
                 category === "Multi-Pitch, Anchors & Descent" ? "Multi-Pitch" :
                 category}
              </span>
              <span>{expandedCategories.includes(category) ? '▼' : '▶'}</span>
            </button>
            {expandedCategories.includes(category) && (
              <div className="mt-1 space-y-1 pl-2.5 text-gray-700 dark:text-gray-300">
                {nonEmptyCategories[category]?.map(({ value, label }) => (
                  <label key={value} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={isTagSelected(category, value)}
                      onChange={() => toggleTag(category, value)}
                      className="mr-1.5"
                    />
                    {label}
                  </label>
                ))}
              </div>
            )}
          </div>
        ))}

      {/* Crack Climbing Category */}
      {nonEmptyCategories["Crack Climbing"] && (
        <div className="filter-group">
          <button 
            className="w-full flex justify-between items-center py-1.5 px-2.5 bg-gray-100 rounded text-sm text-gray-700 dark:bg-gray-700 dark:text-gray-300"
            onClick={() => toggleCategory("Crack Climbing")}
          >
            <span>Crack Climbing</span>
            <span>{expandedCategories.includes("Crack Climbing") ? '▼' : '▶'}</span>
          </button>
          {expandedCategories.includes("Crack Climbing") && (
            <div className="mt-1 space-y-1 pl-2.5 text-gray-700 dark:text-gray-300">
              {nonEmptyCategories["Crack Climbing"]?.map(({ value, label }) => (
                <label key={value} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={isTagSelected("Crack Climbing", value)}
                    onChange={() => toggleTag("Crack Climbing", value)}
                    className="mr-1.5"
                  />
                  {label}
                </label>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Style & Angle Category */}
      <div className="filter-group">
        <button 
          className="w-full flex justify-between items-center py-1.5 px-2.5 bg-gray-100 rounded text-sm text-gray-700 dark:bg-gray-700 dark:text-gray-300"
          onClick={() => toggleCategory("Route Style & Angle")}
        >
          <span>Style & Angle</span>
          <span>{expandedCategories.includes("Route Style & Angle") ? '▼' : '▶'}</span>
        </button>
        {expandedCategories.includes("Route Style & Angle") && (
          <div className="mt-1 space-y-1 pl-2.5 text-gray-700 dark:text-gray-300">
            {Array.from(availableTags["Route Style & Angle"] || []).map(tag => (
              <label key={tag} className="flex items-center">
                <input
                  type="checkbox"
                  checked={isTagSelected("Route Style & Angle", tag)}
                  onChange={() => toggleTag("Route Style & Angle", tag)}
                  className="mr-1.5"
                />
                {tag}
              </label>
            ))}
            {(!availableTags["Route Style & Angle"] || availableTags["Route Style & Angle"].size === 0) && (
              <span className="text-xs text-gray-500 dark:text-gray-400">No tags available</span>
            )}
          </div>
        )}
      </div>
      
      {/* Hold & Movement Type Category */}
      <div className="filter-group">
        <button 
          className="w-full flex justify-between items-center py-1.5 px-2.5 bg-gray-100 rounded text-sm text-gray-700 dark:bg-gray-700 dark:text-gray-300"
          onClick={() => toggleCategory("Hold & Movement Type")}
        >
          <span>Holds & Movement</span>
          <span>{expandedCategories.includes("Hold & Movement Type") ? '▼' : '▶'}</span>
        </button>
        {expandedCategories.includes("Hold & Movement Type") && (
          <div className="mt-1 space-y-1 pl-2.5 text-gray-700 dark:text-gray-300">
            {Array.from(availableTags["Hold & Movement Type"] || []).map(tag => (
              <label key={tag} className="flex items-center">
                <input
                  type="checkbox"
                  checked={isTagSelected("Hold & Movement Type", tag)}
                  onChange={() => toggleTag("Hold & Movement Type", tag)}
                  className="mr-1.5"
                />
                {tag}
              </label>
            ))}
            {(!availableTags["Hold & Movement Type"] || availableTags["Hold & Movement Type"].size === 0) && (
              <span className="text-xs text-gray-500 dark:text-gray-400">No tags available</span>
            )}
          </div>
        )}
      </div>

      {/* Experimental Tags Section */}
      <div className="filter-group mt-3 border-t pt-2.5 border-gray-200 dark:border-gray-700">
        <h3 className="font-medium mb-1.5 text-gray-900 dark:text-gray-100">
          Experimental Tags
        </h3>
        
        {/* Rope Length Category */}
        <div className="filter-group mb-1.5">
          <button 
            className="w-full flex justify-between items-center py-1.5 px-2.5 bg-gray-100 rounded text-sm text-gray-700 dark:bg-gray-700 dark:text-gray-300"
            onClick={() => toggleCategory("Rope Length")}
          >
            <span>Rope Length</span>
            <span>{expandedCategories.includes("Rope Length") ? '▼' : '▶'}</span>
          </button>
          {expandedCategories.includes("Rope Length") && (
            <div className="mt-1 space-y-1 pl-2.5 text-gray-700 dark:text-gray-300">
              {Array.from(availableTags["Rope Length"] || [])
                // Sort to ensure correct order regardless of availableTags order
                .sort((a, b) => {
                  const order = ["rope_60m", "rope_70m", "rope_80m"];
                  return order.indexOf(a) - order.indexOf(b);
                })
                .map(tag => (
                <label key={tag} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={isTagSelected("Rope Length", tag)}
                    onChange={() => toggleTag("Rope Length", tag)}
                    className="mr-1.5"
                  />
                  {tag}
                </label>
              ))}
              {(!availableTags["Rope Length"] || availableTags["Rope Length"].size === 0) && (
                <span className="text-xs text-gray-500 dark:text-gray-400">No tags available</span>
              )}
            </div>
          )}
        </div>
        
        {/* Weather & Conditions Category */}
        <div className="filter-group mb-1.5">
          <button 
            className="w-full flex justify-between items-center py-1.5 px-2.5 bg-gray-100 rounded text-sm text-gray-700 dark:bg-gray-700 dark:text-gray-300"
            onClick={() => toggleCategory("Weather & Conditions")}
          >
            <span>Weather & Conditions</span>
            <span>{expandedCategories.includes("Weather & Conditions") ? '▼' : '▶'}</span>
          </button>
          {expandedCategories.includes("Weather & Conditions") && (
            <div className="mt-1 space-y-1 pl-2.5 text-gray-700 dark:text-gray-300">
              {Array.from(availableTags["Weather & Conditions"] || []).map(tag => (
                <label key={tag} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={isTagSelected("Weather & Conditions", tag)}
                    onChange={() => toggleTag("Weather & Conditions", tag)}
                    className="mr-1.5"
                  />
                  {tag}
                </label>
              ))}
              {(!availableTags["Weather & Conditions"] || availableTags["Weather & Conditions"].size === 0) && (
                <span className="text-xs text-gray-500 dark:text-gray-400">No tags available</span>
              )}
            </div>
          )}
        </div>

        {/* Approach & Accessibility Category */}
        <div className="filter-group">
          <button 
            className="w-full flex justify-between items-center py-1.5 px-2.5 bg-gray-100 rounded text-sm text-gray-700 dark:bg-gray-700 dark:text-gray-300"
            onClick={() => toggleCategory("Approach & Accessibility")}
          >
            <span>Approach & Accessibility</span>
            <span>{expandedCategories.includes("Approach & Accessibility") ? '▼' : '▶'}</span>
          </button>
          {expandedCategories.includes("Approach & Accessibility") && (
            <div className="mt-1 space-y-1 pl-2.5 text-gray-700 dark:text-gray-300">
              {Array.from(availableTags["Approach & Accessibility"] || [])
                .map(tag => (
                <label key={tag} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={isTagSelected("Approach & Accessibility", tag)}
                    onChange={() => toggleTag("Approach & Accessibility", tag)}
                    className="mr-1.5"
                  />
                  {tag}
                </label>
              ))}
              {(!availableTags["Approach & Accessibility"] || availableTags["Approach & Accessibility"].size === 0) && (
                <span className="text-xs text-gray-500 dark:text-gray-400">No tags available</span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
} 