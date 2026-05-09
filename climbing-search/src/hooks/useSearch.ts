import { useState } from 'react'
import type { RouteFilters } from '../types/filters'

/**
 * useSearch: lightweight hook for managing filter state.
 * Actual data fetching is now done via routeApi in App.tsx.
 * This hook is kept for compatibility but no longer does in-memory filtering.
 */
export function useSearch() {
  const [filters, setFilters] = useState<RouteFilters>({
    grades: { min: '5.6', max: '5.13d' },
    types: [],
    tags: []
  })

  return {
    filters,
    setFilters
  }
}
