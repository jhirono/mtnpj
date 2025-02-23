import type { Area } from '../types/area'

export async function loadRouteData(): Promise<Area[]> {
  try {
    console.log('Attempting to fetch data...')
    // Use relative path instead of hardcoded port
    const response = await fetch('/data/upper-castle_routes_tagged.json')
    console.log('Response status:', response.status)
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const text = await response.text()
    console.log('Response text length:', text.length)
    
    if (!text) {
      throw new Error('Empty response received')
    }
    
    const data = JSON.parse(text)
    if (!Array.isArray(data)) {
      throw new Error('Expected array but got: ' + typeof data)
    }
    
    console.log('Found', data.length, 'areas')
    return data
  } catch (error) {
    console.error('Error loading route data:', error)
    throw error
  }
} 