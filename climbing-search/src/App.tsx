import { useEffect, useState, useMemo } from 'react'
import { loadRouteData } from './utils/loadData'
import { useSearch } from './hooks/useSearch'
import { FilterPanel } from './components/FilterPanel'
import { SearchBar } from './components/SearchBar'
import { RouteCard } from './components/RouteCard'
import type { Area } from './types/area'
import type { RouteFilters, SortConfig } from './types/filters'
import { GRADE_ORDER, normalizeGrade } from './types/filters'

function App() {
  const [areas, setAreas] = useState<Area[]>([])
  const { filteredAreas, setSearchQuery, setFilters } = useSearch(areas)
  const [currentFilters, setCurrentFilters] = useState<RouteFilters>({
    grades: { min: "5.6", max: "5.13d" },
    types: [],
    tags: []
  })
  const [sortConfig, setSortConfig] = useState<SortConfig>({
    option: 'left_to_right',
    ascending: true
  })

  // Sort routes
  const sortedRoutes = useMemo(() => {
    const allRoutes = filteredAreas.flatMap(area => area.routes)
    
    return [...allRoutes].sort((a, b) => {
      const multiplier = sortConfig.ascending ? 1 : -1

      switch (sortConfig.option) {
        case 'grade':
          return multiplier * (
            GRADE_ORDER.indexOf(normalizeGrade(a.route_grade)) - 
            GRADE_ORDER.indexOf(normalizeGrade(b.route_grade))
          )
        case 'stars':
          return multiplier * (b.route_stars - a.route_stars)
        case 'votes':
          return multiplier * (b.route_votes - a.route_votes)
        case 'left_to_right':
          return multiplier * (
            (a.route_lr || 0) - (b.route_lr || 0)
          )
        default:
          return 0
      }
    })
  }, [filteredAreas, sortConfig])

  useEffect(() => {
    loadRouteData().then(setAreas)
  }, [])

  const handleFilterChange = (filters: RouteFilters) => {
    setCurrentFilters(filters)
    setFilters(filters)
  }

  return (
    <div className="min-h-screen">
      {/* Smaller header with less padding */}
      <header className="py-4 text-center">
        <h1 className="text-xl font-bold">Awesome Climbing Route Search</h1>
        <p className="text-gray-600 text-sm mt-1">
          {filteredAreas.reduce((total, area) => total + area.routes.length, 0)} routes found
        </p>
      </header>

      <div className="max-w-7xl mx-auto px-3 py-4">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search and Filter Panel */}
          <div className="md:w-72 flex-shrink-0">
            <div className="sticky top-4">
              <SearchBar onSearch={setSearchQuery} />
              <FilterPanel
                filters={currentFilters}
                onChange={handleFilterChange}
                sortConfig={sortConfig}
                onSortChange={setSortConfig}
                areas={areas}
              />
            </div>
          </div>

          {/* Routes List with less spacing */}
          <div className="flex-grow">
            {sortedRoutes.length > 0 ? (
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
