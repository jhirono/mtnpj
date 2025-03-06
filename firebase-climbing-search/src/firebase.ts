import { initializeApp } from 'firebase/app';
import { 
  getFirestore, 
  collection, 
  getDocs, 
  query, 
  where, 
  orderBy, 
  limit, 
  startAfter,
  doc,
  getDoc,
  DocumentData,
  QueryDocumentSnapshot,
  serverTimestamp,
  enableIndexedDbPersistence
} from 'firebase/firestore';
import { Area, Route, RouteFilters, SortConfig } from './types';
import { normalizeGrade, gradeToNumeric } from './utils/gradeUtils';

// Your web app's Firebase configuration
// Replace with your actual Firebase config
const firebaseConfig = {
  apiKey: process.env.REACT_APP_FIREBASE_API_KEY,
  authDomain: process.env.REACT_APP_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID,
  storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.REACT_APP_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.REACT_APP_FIREBASE_APP_ID,
  measurementId: process.env.REACT_APP_FIREBASE_MEASUREMENT_ID
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const db = getFirestore(app);

// Enable offline persistence
enableIndexedDbPersistence(db)
  .catch((err) => {
    if (err.code === 'failed-precondition') {
      console.warn('Offline persistence failed: Multiple tabs open');
    } else if (err.code === 'unimplemented') {
      console.warn('Offline persistence not available in this browser');
    } else {
      console.error('Offline persistence failed:', err);
    }
  });

// Cache for frequently accessed data
const areaCache = new Map<string, Area>();
const areaHierarchyCache = new Map<string, Area[]>();

/**
 * Fetches all climbing areas from Firestore
 */
export async function getAreas(): Promise<Area[]> {
  try {
    console.log("getAreas: Fetching areas from Firestore...");
    const areasCollection = collection(db, 'areas');
    const areasQuery = query(areasCollection, orderBy('area_name', 'asc'));
    
    console.log("getAreas: Executing query...");
    const areasSnapshot = await getDocs(areasQuery);
    console.log(`getAreas: Retrieved ${areasSnapshot.docs.length} area documents from Firestore`);
    
    if (areasSnapshot.empty) {
      console.warn("getAreas: No areas found in the Firestore collection");
      return [];
    }
    
    const areas = areasSnapshot.docs.map(doc => {
      const data = doc.data();
      console.log(`getAreas: Processing area document: ${doc.id}, name: ${data.area_name || 'unnamed'}`);
      
      const area = { 
        id: doc.id, 
        ...data 
      } as Area;
      
      // Update cache
      areaCache.set(area.id!, area);
      
      return area;
    });
    
    console.log(`getAreas: Successfully processed ${areas.length} areas`);
    
    // Debug: Log a sample area to see its structure
    if (areas.length > 0) {
      const sampleArea = areas[0];
      console.log("getAreas: Sample area structure:", {
        id: sampleArea.id,
        name: sampleArea.area_name,
        hasHierarchy: Boolean(sampleArea.area_hierarchy && sampleArea.area_hierarchy.length > 0),
        hierarchyLength: sampleArea.area_hierarchy?.length || 0,
        hasSearchableText: Boolean(sampleArea.searchable_text)
      });
    }
    
    return areas;
  } catch (error) {
    console.error('Error getting areas:', error);
    throw error;
  }
}

/**
 * Fetches areas by hierarchy path
 * @param parentPath The parent path to search under (e.g., "USA/California")
 */
export async function getAreasByPath(parentPath: string): Promise<Area[]> {
  try {
    // Check cache first
    if (areaHierarchyCache.has(parentPath)) {
      return areaHierarchyCache.get(parentPath)!;
    }
    
    const areasCollection = collection(db, 'areas');
    const areasQuery = query(
      areasCollection,
      where('area_hierarchy_path', '>=', parentPath),
      where('area_hierarchy_path', '<', parentPath + '\uf8ff'),
      orderBy('area_hierarchy_path', 'asc'),
      limit(100)
    );
    
    const areasSnapshot = await getDocs(areasQuery);
    
    const areas = areasSnapshot.docs.map(doc => {
      const area = { 
        id: doc.id, 
        ...doc.data() 
      } as Area;
      
      // Update individual area cache
      areaCache.set(area.id!, area);
      
      return area;
    });
    
    // Update hierarchy cache
    areaHierarchyCache.set(parentPath, areas);
    
    return areas;
  } catch (error) {
    console.error('Error getting areas by path:', error);
    throw error;
  }
}

/**
 * Search areas by text query with improved relevance
 * @param searchText The text to search for
 * @param limit Maximum number of results to return
 */
export async function searchAreas(searchText: string, limit: number = 15): Promise<Area[]> {
  try {
    // If search text is empty or too short, return empty array
    if (!searchText || searchText.trim().length < 2) {
      return [];
    }
    
    // Split search into terms for better matching
    const searchTerms = searchText.toLowerCase().trim().split(/\s+/);
    
    // Get all areas (ideally we'd use a proper search index like Algolia,
    // but for simplicity we'll implement a client-side search)
    const areasCollection = collection(db, 'areas');
    const areasQuery = query(areasCollection, orderBy('area_name', 'asc'));
    const areasSnapshot = await getDocs(areasQuery);
    
    // Map areas and score them based on how well they match search terms
    const scoredAreas = areasSnapshot.docs.map(doc => {
      const area = { id: doc.id, ...doc.data() } as Area;
      const areaName = area.area_name?.toLowerCase() || '';
      const areaDesc = area.area_description?.toLowerCase() || '';
      const searchableText = area.searchable_text?.toLowerCase() || '';
      
      // Calculate match score (higher is better)
      let score = 0;
      
      for (const term of searchTerms) {
        // Exact matches in name are weighted highest
        if (areaName.includes(term)) {
          score += 10;
          // Bonus for starts with
          if (areaName.startsWith(term)) {
            score += 5;
          }
          // Bonus for exact match
          if (areaName === term) {
            score += 10;
          }
        }
        
        // Matches in hierarchy names
        const hierarchyMatches = area.area_hierarchy?.filter(
          h => h.area_hierarchy_name.toLowerCase().includes(term)
        )?.length || 0;
        score += hierarchyMatches * 3;
        
        // Matches in description
        if (areaDesc.includes(term)) {
          score += 2;
        }
        
        // Matches in searchable text
        if (searchableText.includes(term)) {
          score += 1;
        }
      }
      
      return { area, score };
    });
    
    // Filter out non-matches and sort by score
    const filteredAreas = scoredAreas
      .filter(item => item.score > 0)
      .sort((a, b) => b.score - a.score)
      .map(item => item.area)
      .slice(0, limit);
    
    return filteredAreas;
  } catch (error) {
    console.error('Error searching areas:', error);
    throw error;
  }
}

/**
 * Fetches routes for the selected areas with optional filtering
 */
export async function getRoutesForAreas(
  filters: RouteFilters,
  sortConfig: SortConfig,
  lastVisible: QueryDocumentSnapshot<DocumentData> | null = null,
  pageSize: number = 20
): Promise<{
  routes: Route[],
  lastVisible: QueryDocumentSnapshot<DocumentData> | null,
  hasMore: boolean
}> {
  try {
    // Build query constraints
    const constraints: any[] = [];
    
    // Area filtering
    if (filters.areaIds && filters.areaIds.length > 0) {
      // Firestore can only handle 'in' queries with up to 10 values
      if (filters.areaIds.length <= 10) {
        constraints.push(where('area_id', 'in', filters.areaIds));
      } else {
        // For more than 10 areas, we'll need to do multiple queries and combine results
        // This is a limitation we'll handle in the client for now
        constraints.push(where('area_id', 'in', filters.areaIds.slice(0, 10)));
      }
    } else if (filters.areaPath) {
      // Use hierarchy path for more efficient area filtering
      constraints.push(where('area_hierarchy_path', '>=', filters.areaPath));
      constraints.push(where('area_hierarchy_path', '<', filters.areaPath + '\uf8ff'));
    }
    
    // Boolean filters - these are more efficient than array contains
    if (filters.isMultipitch) {
      constraints.push(where('is_multipitch', '==', true));
    }
    
    if (filters.isTrad) {
      constraints.push(where('is_trad', '==', true));
    }
    
    if (filters.isSport) {
      constraints.push(where('is_sport', '==', true));
    }
    
    // Check if we have a grade range filter
    const hasGradeFilter = filters.minGrade || filters.maxGrade;
    
    // Grade range filter
    if (filters.minGrade && filters.maxGrade) {
      // For min grade, we want that grade and harder ones (>=)
      // For max grade, we want that grade and easier ones (<=)
      const minGradeValue = gradeToNumeric(filters.minGrade);
      const maxGradeValue = gradeToNumeric(filters.maxGrade);
      
      // Debug logging
      console.log(`Filtering grades: ${filters.minGrade} (${minGradeValue}) to ${filters.maxGrade} (${maxGradeValue})`);
      
      constraints.push(where('grade_numeric', '>=', minGradeValue));
      constraints.push(where('grade_numeric', '<=', maxGradeValue));
    } else if (filters.minGrade) {
      // For min grade only, we want that grade and harder ones (>=)
      const minGradeValue = gradeToNumeric(filters.minGrade);
      console.log(`Filtering grades harder than: ${filters.minGrade} (${minGradeValue})`);
      constraints.push(where('grade_numeric', '>=', minGradeValue));
    } else if (filters.maxGrade) {
      // For max grade only, we want that grade and easier ones (<=)
      const maxGradeValue = gradeToNumeric(filters.maxGrade);
      console.log(`Filtering grades easier than: ${filters.maxGrade} (${maxGradeValue})`);
      constraints.push(where('grade_numeric', '<=', maxGradeValue));
    }
    
    // Add sorting with special handling for grade filters
    let primarySortField: string;
    let primarySortDirection: 'asc' | 'desc' = sortConfig.direction;
    
    // When we have a grade filter, we MUST sort by grade_numeric first
    // This is a Firestore constraint - the field with inequality filter must be the first sort field
    if (hasGradeFilter) {
      primarySortField = 'grade_numeric';
      constraints.push(orderBy(primarySortField, primarySortDirection));
      
      // If the user wants to sort by a different field, add it as a secondary sort
      if (sortConfig.key !== 'grade') {
        let secondarySortField: string;
        
        switch (sortConfig.key) {
          case 'stars':
            secondarySortField = 'route_stars';
            break;
          case 'votes':
            secondarySortField = 'route_votes';
            break;
          case 'quality':
            secondarySortField = 'quality_score';
            break;
          case 'lr':
            secondarySortField = 'route_lr';
            break;
          default:
            secondarySortField = 'quality_score';
        }
        
        // Add secondary sort
        constraints.push(orderBy(secondarySortField, sortConfig.direction));
      }
    } else {
      // No grade filter, we can sort by any field
      switch (sortConfig.key) {
        case 'grade':
          primarySortField = 'grade_numeric';
          break;
        case 'stars':
          primarySortField = 'route_stars';
          break;
        case 'votes':
          primarySortField = 'route_votes';
          break;
        case 'quality':
          primarySortField = 'quality_score';
          break;
        case 'lr':
          primarySortField = 'route_lr';
          break;
        default:
          primarySortField = 'quality_score';
      }
      
      // Add primary sort
      constraints.push(orderBy(primarySortField, primarySortDirection));
    }
    
    // Add __name__ for consistent pagination
    constraints.push(orderBy('__name__', 'asc'));
    
    // Add pagination
    constraints.push(limit(pageSize + 1)); // Get one extra to check if there are more
    
    // Add startAfter if we have a last document
    if (lastVisible) {
      constraints.push(startAfter(lastVisible));
    }
    
    // Create and execute query
    const routesCollection = collection(db, 'routes');
    const routesQuery = query(routesCollection, ...constraints);
    const routesSnapshot = await getDocs(routesQuery);
    
    // Check if there are more results
    const hasMore = routesSnapshot.docs.length > pageSize;
    const routeDocs = hasMore ? routesSnapshot.docs.slice(0, pageSize) : routesSnapshot.docs;
    
    // Get the last visible document for pagination
    const newLastVisible = routeDocs.length > 0 ? routeDocs[routeDocs.length - 1] : null;
    
    // Map documents to Route objects
    let routes = routeDocs.map(doc => ({ id: doc.id, ...doc.data() } as Route));
    
    // Apply client-side filtering for complex criteria
    // Note: We try to do as much filtering as possible on the server,
    // but some complex filters need to be done client-side
    if (filters.tags && filters.tags.length > 0) {
      routes = routes.filter(route => {
        return filters.tags!.every(tag => route.tags?.includes(tag));
      });
    }
    
    if (filters.excludedTypes && filters.excludedTypes.length > 0) {
      routes = routes.filter(route => {
        return !filters.excludedTypes!.some(type => 
          route.route_type.includes(type)
        );
      });
    }
    
    // For area filtering with more than 10 areas
    if (filters.areaIds && filters.areaIds.length > 10) {
      routes = routes.filter(route => 
        filters.areaIds!.includes(route.area_id)
      );
    }
    
    return {
      routes,
      lastVisible: newLastVisible,
      hasMore
    };
  } catch (error) {
    console.error("Error fetching routes:", error);
    throw error;
  }
}

/**
 * Fetches a single route by ID
 */
export async function getRouteById(routeId: string): Promise<Route | null> {
  try {
    const routeRef = doc(db, 'routes', routeId);
    const routeSnap = await getDoc(routeRef);
    
    if (!routeSnap.exists()) {
      return null;
    }
    
    return { id: routeSnap.id, ...routeSnap.data() } as Route;
  } catch (error) {
    console.error("Error fetching route:", error);
    throw error;
  }
}

/**
 * Fetches a single area by ID
 */
export async function getAreaById(areaId: string): Promise<Area | null> {
  try {
    // Check cache first
    if (areaCache.has(areaId)) {
      return areaCache.get(areaId)!;
    }
    
    const areaRef = doc(db, 'areas', areaId);
    const areaSnap = await getDoc(areaRef);
    
    if (!areaSnap.exists()) {
      return null;
    }
    
    const area = { id: areaSnap.id, ...areaSnap.data() } as Area;
    
    // Update cache
    areaCache.set(areaId, area);
    
    return area;
  } catch (error) {
    console.error('Error getting area by ID:', error);
    throw error;
  }
}

/**
 * Search routes by text query
 */
export async function searchRoutes(
  searchText: string,
  filters: RouteFilters = {},
  sortConfig: SortConfig = { key: 'quality', direction: 'desc' },
  pageSize: number = 20
): Promise<Route[]> {
  try {
    if (!searchText || searchText.trim().length < 2) {
      return [];
    }
    
    const searchTerms = searchText.toLowerCase().trim().split(/\s+/);
    
    // Build base query with filters
    const constraints: any[] = [];
    
    // Apply area filters if specified
    if (filters.areaIds && filters.areaIds.length > 0 && filters.areaIds.length <= 10) {
      constraints.push(where('area_id', 'in', filters.areaIds.slice(0, 10)));
    } else if (filters.areaPath) {
      constraints.push(where('area_hierarchy_path', '>=', filters.areaPath));
      constraints.push(where('area_hierarchy_path', '<', filters.areaPath + '\uf8ff'));
    }
    
    // Add sorting
    let sortField: string;
    switch (sortConfig.key) {
      case 'grade':
        sortField = 'grade_numeric';
        break;
      case 'stars':
        sortField = 'route_stars';
        break;
      case 'votes':
        sortField = 'route_votes';
        break;
      case 'quality':
        sortField = 'quality_score';
        break;
      default:
        sortField = 'quality_score';
    }
    
    constraints.push(orderBy(sortField, sortConfig.direction));
    constraints.push(limit(100)); // Get more routes for client-side filtering
    
    // Execute query
    const routesCollection = collection(db, 'routes');
    const routesQuery = query(routesCollection, ...constraints);
    const routesSnapshot = await getDocs(routesQuery);
    
    // Get routes and filter by search terms
    let routes = routesSnapshot.docs.map(doc => ({ id: doc.id, ...doc.data() } as Route));
    
    // Client-side text search
    routes = routes.filter(route => {
      const searchableText = route.searchable_text || '';
      return searchTerms.every(term => searchableText.includes(term));
    });
    
    // Apply additional client-side filters
    if (filters.minGrade || filters.maxGrade) {
      routes = routes.filter(route => {
        const gradeValue = route.grade_numeric;
        
        if (filters.minGrade && filters.maxGrade) {
          const minValue = gradeToNumeric(filters.minGrade);
          const maxValue = gradeToNumeric(filters.maxGrade);
          return gradeValue >= minValue && gradeValue <= maxValue;
        } else if (filters.minGrade) {
          return gradeValue >= gradeToNumeric(filters.minGrade);
        } else if (filters.maxGrade) {
          return gradeValue <= gradeToNumeric(filters.maxGrade);
        }
        
        return true;
      });
    }
    
    if (filters.isMultipitch) {
      routes = routes.filter(route => route.is_multipitch);
    }
    
    if (filters.isTrad) {
      routes = routes.filter(route => route.is_trad);
    }
    
    if (filters.isSport) {
      routes = routes.filter(route => route.is_sport);
    }
    
    if (filters.tags && filters.tags.length > 0) {
      routes = routes.filter(route => {
        return filters.tags!.every(tag => route.tags?.includes(tag));
      });
    }
    
    // Limit results to requested page size
    return routes.slice(0, pageSize);
  } catch (error) {
    console.error('Error searching routes:', error);
    throw error;
  }
}

/**
 * Get the area tree structure
 * @returns A nested tree of areas
 */
export async function getAreaTree(): Promise<Area[]> {
  try {
    // Get all areas
    const areas = await getAreas();
    
    // Create a map for fast lookup
    const areaMap = new Map<string, Area>();
    areas.forEach(area => {
      areaMap.set(area.id!, { ...area, children: [] });
    });
    
    // Build tree structure
    const rootAreas: Area[] = [];
    
    areas.forEach(area => {
      const hierarchyLength = area.area_hierarchy?.length || 0;
      
      if (hierarchyLength === 0) {
        // This is a root area
        rootAreas.push({ ...area, children: [] });
      } else {
        // Find parent area
        const parentHierarchy = area.area_hierarchy[hierarchyLength - 1];
        const parentName = parentHierarchy.area_hierarchy_name;
        
        // Find the parent area by matching name
        const parentArea = areas.find(a => 
          a.area_name === parentName && 
          (a.area_hierarchy?.length || 0) === hierarchyLength - 1
        );
        
        if (parentArea && parentArea.id) {
          // Add as child to parent
          const parent = areaMap.get(parentArea.id);
          if (parent) {
            if (!parent.children) {
              parent.children = [];
            }
            parent.children.push({ ...area, children: [] });
          }
        } else {
          // If we can't find parent, add to root
          rootAreas.push({ ...area, children: [] });
        }
      }
    });
    
    return rootAreas;
  } catch (error) {
    console.error('Error getting area tree:', error);
    throw error;
  }
}

/**
 * Get popular areas by visit count or route popularity
 * @param limitCount Maximum number of areas to return
 */
export async function getPopularAreas(limitCount: number = 10): Promise<Area[]> {
  try {
    // In a real app, we might have a popularity metric
    // For now we'll just return areas with the most routes or best average rating
    const areasCollection = collection(db, 'areas');
    const areasQuery = query(areasCollection, orderBy('area_name'), limit(limitCount));
    const areasSnapshot = await getDocs(areasQuery);
    
    return areasSnapshot.docs.map(doc => ({ 
      id: doc.id, 
      ...doc.data() 
    } as Area));
  } catch (error) {
    console.error('Error getting popular areas:', error);
    throw error;
  }
} 