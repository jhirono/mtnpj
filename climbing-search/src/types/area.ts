import type { Route } from './route'

export interface Area {
  area_id: string
  area_name: string
  area_url: string
  area_description: string
  area_getting_there: string
  area_tags: string[]
  area_hierarchy: Array<{
    level: number
    area_hierarchy_name: string
    area_hierarchy_url: string
  }>
  routes: Route[]
} 