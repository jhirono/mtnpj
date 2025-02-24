import { useState, useMemo } from 'react'
import type { Area } from '../types/area'
import type { RouteFilters } from '../types/filters'
import { GRADE_ORDER, normalizeGrade } from '../types/filters'

export function useSearch(areas: Area[]) {
  const [searchQuery, setSearchQuery] = useState('')
  const [filters, setFilters] = useState<RouteFilters>({
    grades: { min: "5.6", max: "5.13d" },
    types: [],
    tags: []
  })

  const filteredAreas = useMemo(() => {
    console.log('Filtering with:', { searchQuery, filters })
    
    return areas.map(area => ({
      ...area,
      routes: area.routes.filter(route => {
        // Add debug logs for each filter condition
        const matchesSearch = searchQuery === '' || 
          route.route_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          route.route_grade.toLowerCase().includes(searchQuery.toLowerCase()) ||
          route.route_type.toLowerCase().includes(searchQuery.toLowerCase())

        const gradeIndex = GRADE_ORDER.indexOf(normalizeGrade(route.route_grade))
        const minIndex = GRADE_ORDER.indexOf(filters.grades.min)
        const maxIndex = GRADE_ORDER.indexOf(filters.grades.max)
        const matchesGrade = gradeIndex >= minIndex && gradeIndex <= maxIndex

        // Add debug log for grade matching
        if (!matchesGrade) {
          console.log('Grade mismatch:', {
            routeGrade: route.route_grade,
            normalizedGrade: normalizeGrade(route.route_grade),
            gradeIndex,
            minIndex,
            maxIndex
          });
        }

        const matchesType = filters.types.length === 0 || 
          filters.types.includes(route.route_type)

        // Updated tag matching logic
        const matchesTags = filters.tags.length === 0 ||
          filters.tags.every(({ category, selectedTags }) =>
            selectedTags.length === 0 ||
            selectedTags.some(tag => 
              route.route_tags[category]?.includes(tag)  // Changed from route.route_tags[category]?.some(t => t.tag === tag)
            )
          )

        // Debug log for tag matching
        if (!matchesTags) {
          console.log('Tag mismatch for route:', route.route_name, {
            routeTags: route.route_tags,
            filterTags: filters.tags
          })
        }

        return matchesSearch && matchesGrade && matchesType && matchesTags
      })
    })).filter(area => area.routes.length > 0)
  }, [areas, searchQuery, filters])

  return {
    filteredAreas,
    setSearchQuery,
    setFilters
  }
}