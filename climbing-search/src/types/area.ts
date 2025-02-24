import type { Route } from './route'
import type { AreaHierarchy } from './route'

export interface Area {
  area_id: string
  area_name: string
  area_url: string
  area_description: string
  area_getting_there: string
  area_tags: string[]
  area_hierarchy: AreaHierarchy[]
  parent_area?: string
  child_areas?: Area[]
  routes: Route[]
}

export function buildAreaTree(areas: Area[]): Area[] {
  const areaMap = new Map<string, Area>()
  const rootAreas: Area[] = []

  areas.forEach(area => {
    areaMap.set(area.area_id, { ...area, child_areas: [] })
  })

  areas.forEach(area => {
    const parentName = area.area_hierarchy[area.area_hierarchy.length - 2]?.area_hierarchy_name
    if (parentName) {
      const parent = Array.from(areaMap.values()).find(a => 
        a.area_hierarchy[a.area_hierarchy.length - 1].area_hierarchy_name === parentName
      )
      if (parent) {
        parent.child_areas?.push(areaMap.get(area.area_id)!)
      }
    } else {
      rootAreas.push(areaMap.get(area.area_id)!)
    }
  })

  return rootAreas
} 