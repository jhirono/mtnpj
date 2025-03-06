// Data Migration Script for Firebase Climbing Search
// This script reads climbing area and route data from JSON files and uploads it to Firestore
// Enhanced version with schema optimization and data validation

const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../.env') });

// Use Firebase Admin SDK instead of client SDK
const admin = require('firebase-admin');

// Parse command line arguments
const args = process.argv.slice(2);
const skipAreas = args.includes('--skip-areas');
const skipRoutes = args.includes('--skip-routes');
const forceOverwrite = args.includes('--force');

// Display help if requested
if (args.includes('--help') || args.includes('-h')) {
  console.log(`
Migration Script Usage:
  node scripts/migrate-data.js [options]

Options:
  --skip-areas       Skip uploading areas collection
  --skip-routes      Skip uploading routes collection
  --force            Skip confirmation prompts for overwriting data
  --help, -h         Display this help message

Examples:
  node scripts/migrate-data.js                 # Upload both areas and routes
  node scripts/migrate-data.js --skip-areas    # Upload only routes
  node scripts/migrate-data.js --skip-routes   # Upload only areas
  node scripts/migrate-data.js --force         # Skip all confirmation prompts
  `);
  process.exit(0);
}

// Grade order for sorting (from easiest to hardest)
const GRADE_ORDER = [
  // 5.3-5.9 with variations
  "5.3",
  "5.4",
  "5.5",
  "5.6-", "5.6", "5.6+",
  "5.7-", "5.7", "5.7+",
  "5.8-", "5.8", "5.8+",
  "5.9-", "5.9", "5.9+",
  
  // 5.10-5.16 with all variations
  "5.10-", "5.10a", "5.10a/b", "5.10", "5.10b", "5.10b/c", "5.10c", "5.10c/d", "5.10d", "5.10+",
  "5.11-", "5.11a", "5.11a/b", "5.11", "5.11b", "5.11b/c", "5.11c", "5.11c/d", "5.11d", "5.11+",
  "5.12-", "5.12a", "5.12a/b", "5.12", "5.12b", "5.12b/c", "5.12c", "5.12c/d", "5.12d", "5.12+",
  "5.13-", "5.13a", "5.13a/b", "5.13", "5.13b", "5.13b/c", "5.13c", "5.13c/d", "5.13d", "5.13+",
  "5.14-", "5.14a", "5.14a/b", "5.14", "5.14b", "5.14b/c", "5.14c", "5.14c/d", "5.14d", "5.14+",
  "5.15-", "5.15a", "5.15a/b", "5.15", "5.15b", "5.15b/c", "5.15c", "5.15c/d", "5.15d", "5.15+",
  "5.16-", "5.16a", "5.16a/b", "5.16", "5.16b", "5.16b/c", "5.16c", "5.16c/d", "5.16d", "5.16+"
];

// Excluded route types (for pre-filtering)
const EXCLUDED_TYPES = ['Aid', 'Boulder', 'Ice', 'Mixed', 'Snow'];

// Initialize Firebase Admin with credentials
// There are several ways to initialize:
// 1. Using a service account JSON file (most common)
// 2. Using application default credentials
// 3. Using environment variables

// Initialize with service account if available
const serviceAccountPath = path.resolve(__dirname, '../serviceAccountKey.json');
let serviceAccount;

try {
  if (fs.existsSync(serviceAccountPath)) {
    serviceAccount = require(serviceAccountPath);
    admin.initializeApp({
      credential: admin.credential.cert(serviceAccount),
      projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID,
      storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET
    });
    console.log('Initialized Firebase Admin SDK with service account');
  } else {
    // Try to initialize with application default credentials
    admin.initializeApp({
      projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID,
      storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET
    });
    console.log('Initialized Firebase Admin SDK with application default credentials');
  }
} catch (error) {
  console.error('Error initializing Firebase Admin SDK:', error);
  process.exit(1);
}

// Get Firestore instance
const db = admin.firestore();
const FieldValue = admin.firestore.FieldValue;

// Path to your JSON data files
const DATA_DIR = path.resolve(__dirname, '../data');
const AREAS_FILE = path.join(DATA_DIR, 'areas.json');
const ROUTES_FILE = path.join(DATA_DIR, 'routes.json');

// Normalize grade strings and get numeric value for sorting
function normalizeGrade(grade) {
  if (!grade) return { normalized: '', index: 0 };
  
  // Remove any non-grade text (e.g., "5.10a PG13" -> "5.10a")
  grade = grade.split(' ')[0].trim();
  
  // Check if grade is already in standard format
  if (GRADE_ORDER.includes(grade)) {
    return { normalized: grade, index: GRADE_ORDER.indexOf(grade) };
  }
  
  // Try to match to a standard format
  const match = grade.match(/^5\.(\d+)([a-d])?([\/\+\-])?([a-d])?$/i);
  if (!match) return { normalized: grade, index: 0 };
  
  const number = match[1];
  const firstLetter = match[2] ? match[2].toLowerCase() : '';
  const modifier = match[3] || '';
  const secondLetter = match[4] ? match[4].toLowerCase() : '';
  
  // Check different possible normalized forms
  const possibleForms = [];
  
  // Base form: 5.10, 5.10a
  if (firstLetter) {
    possibleForms.push(`5.${number}${firstLetter}`);
  } else {
    possibleForms.push(`5.${number}`);
  }
  
  // Forms with modifiers: 5.10-, 5.10+
  if (modifier === '+' || modifier === '-') {
    possibleForms.push(`5.${number}${firstLetter || ''}${modifier}`);
  }
  
  // Combined forms: 5.10a/b
  if (modifier === '/' && secondLetter) {
    possibleForms.push(`5.${number}${firstLetter}/${secondLetter}`);
  }
  
  // Find the first form that exists in GRADE_ORDER
  for (const form of possibleForms) {
    const index = GRADE_ORDER.indexOf(form);
    if (index >= 0) {
      return { normalized: form, index };
    }
  }
  
  // Default fallback
  return { normalized: grade, index: 0 };
}

// Process route tags into searchable format
function processTags(routeTags) {
  if (!routeTags) return [];
  
  // If routeTags is already an array, return it
  if (Array.isArray(routeTags)) return routeTags;
  
  // If routeTags is an object, flatten the values
  if (typeof routeTags === 'object') {
    // Create a flattened array of all tags
    const flatTags = Object.entries(routeTags).reduce((acc, [category, tags]) => {
      // Add category-prefixed tags for more specific searching
      const prefixedTags = tags.map(tag => `${category}:${tag}`);
      return [...acc, ...tags, ...prefixedTags];
    }, []);
    
    return [...new Set(flatTags)]; // Remove duplicates
  }
  
  return [];
}

// Create a searchable path string from area hierarchy
function createHierarchyPath(hierarchy) {
  if (!Array.isArray(hierarchy) || hierarchy.length === 0) return '';
  
  // Sort by level to ensure correct order
  const sortedHierarchy = [...hierarchy].sort((a, b) => a.level - b.level);
  
  // Create path string (e.g., "USA/California/Yosemite/El Capitan")
  return sortedHierarchy.map(h => h.area_hierarchy_name).join('/');
}

// Process route type into array format
function processRouteType(routeType) {
  if (!routeType) return [];
  
  if (typeof routeType === 'string') {
    return routeType.split(',')
      .map(type => type.trim())
      .filter(type => type && !EXCLUDED_TYPES.includes(type));
  }
  
  if (Array.isArray(routeType)) {
    return routeType.filter(type => type && !EXCLUDED_TYPES.includes(type));
  }
  
  return [];
}

// Validate and clean numeric values
function cleanNumeric(value, defaultValue = 0) {
  if (value === null || value === undefined) return defaultValue;
  
  const num = parseFloat(value);
  return isNaN(num) ? defaultValue : num;
}

// Process an area for Firestore with enhanced fields
function processArea(area) {
  // Create hierarchy path for efficient querying
  const hierarchyPath = createHierarchyPath(area.area_hierarchy);
  
  // Process tags
  const tags = processTags(area.area_tags);
  
  // Create searchable text field combining multiple text fields
  const searchableText = [
    area.area_name,
    area.area_description,
    ...tags
  ].filter(Boolean).join(' ').toLowerCase();
  
  // Ensure all fields have default values to prevent undefined
  return {
    id: area.area_id || '',
    area_id: area.area_id || '',
    area_url: area.area_url || '',
    area_name: area.area_name || '',
    area_gps: area.area_gps || '',
    area_description: area.area_description || '',
    area_getting_there: area.area_getting_there || '',
    area_tags: tags || [],
    area_hierarchy: Array.isArray(area.area_hierarchy) ? area.area_hierarchy : [],
    area_hierarchy_path: hierarchyPath || '',
    area_hierarchy_levels: Array.isArray(area.area_hierarchy) ? area.area_hierarchy.map(h => h.level || 0) : [],
    area_access_issues: area.area_access_issues || '',
    area_page_views: area.area_page_views || '',
    area_shared_on: area.area_shared_on || '',
    area_comments: Array.isArray(area.area_comments) ? area.area_comments : [],
    searchable_text: searchableText || '',
    created_at: FieldValue.serverTimestamp(),
    updated_at: FieldValue.serverTimestamp(),
  };
}

// Process a route for Firestore with enhanced fields
function processRoute(route, areaName, areaHierarchy) {
  // Normalize grade and get numeric value
  const { normalized: normalizedGrade, index: gradeIndex } = normalizeGrade(route.route_grade);
  
  // Process route type to ensure it's an array
  const routeType = processRouteType(route.route_type);
  
  // Process tags
  const tags = processTags(route.route_tags);
  
  // Create hierarchy path
  const hierarchyPath = createHierarchyPath(areaHierarchy);
  
  // Create searchable text field
  const searchableText = [
    route.route_name,
    route.route_grade,
    areaName,
    route.route_description,
    route.route_location,
    route.route_fa,
    ...routeType,
    ...tags
  ].filter(Boolean).join(' ').toLowerCase();
  
  // Clean numeric values
  const stars = cleanNumeric(route.route_stars);
  const votes = cleanNumeric(route.route_votes, 0);
  const pitches = cleanNumeric(route.route_pitches, 1);
  const lengthFt = cleanNumeric(route.route_length_ft);
  const lengthMeter = cleanNumeric(route.route_length_meter);
  const routeLr = cleanNumeric(route.route_lr);
  
  // Calculate a quality score (for sorting by a combination of stars and votes)
  // This uses a Bayesian average to balance between high ratings and number of votes
  const BAYESIAN_MIN_VOTES = 5; // Minimum votes to consider fully
  const BAYESIAN_MEAN_RATING = 2.5; // Average rating (out of 5)
  
  const qualityScore = (stars * votes + BAYESIAN_MEAN_RATING * BAYESIAN_MIN_VOTES) / 
                       (votes + BAYESIAN_MIN_VOTES);
  
  // Ensure all fields have default values to prevent undefined
  return {
    id: route.route_id || '',
    route_id: route.route_id || '',
    route_name: route.route_name || '',
    route_url: route.route_url || '',
    route_lr: routeLr || 0,
    route_grade: route.route_grade || '',
    normalized_grade: normalizedGrade || '',
    grade_numeric: gradeIndex || 0,
    route_protection_grading: route.route_protection_grading || '',
    route_stars: stars || 0,
    route_votes: votes || 0,
    quality_score: qualityScore || 0,
    route_type: routeType || [],
    route_pitches: pitches || 1,
    route_length_ft: lengthFt || 0,
    route_length_meter: lengthMeter || 0,
    route_fa: route.route_fa || '',
    route_description: route.route_description || '',
    route_location: route.route_location || '',
    route_protection: route.route_protection || '',
    route_page_views: route.route_page_views || '',
    route_shared_on: route.route_shared_on || '',
    route_tags: route.route_tags || {},
    tags: tags || [],
    route_comments: Array.isArray(route.route_comments) ? route.route_comments : [],
    area_id: route.area_id || '',
    area_name: areaName || '',
    area_hierarchy: areaHierarchy || [],
    area_hierarchy_path: hierarchyPath || '',
    is_multipitch: pitches > 1 || false,
    is_trad: routeType.includes('Trad') || false,
    is_sport: routeType.includes('Sport') || false,
    searchable_text: searchableText || '',
    created_at: FieldValue.serverTimestamp(),
    updated_at: FieldValue.serverTimestamp(),
  };
}

// Main migration function
async function migrateData() {
  try {
    console.log('Starting data migration...');
    console.log('Options:');
    if (skipAreas) console.log('- Skipping areas collection');
    if (skipRoutes) console.log('- Skipping routes collection');
    if (forceOverwrite) console.log('- Force overwrite enabled (skipping confirmations)');
    
    // Check if data files exist
    if (!fs.existsSync(DATA_DIR)) {
      fs.mkdirSync(DATA_DIR, { recursive: true });
      console.error(`Data directory doesn't exist. Created: ${DATA_DIR}`);
      console.error('Please place your areas.json and routes.json files in the data directory and run again.');
      return;
    }
    
    if (!fs.existsSync(AREAS_FILE)) {
      console.error(`Areas file doesn't exist: ${AREAS_FILE}`);
      return;
    }
    
    if (!fs.existsSync(ROUTES_FILE)) {
      console.error(`Routes file doesn't exist: ${ROUTES_FILE}`);
      return;
    }
    
    // Read and parse data files
    console.log('Reading data files...');
    const areasData = JSON.parse(fs.readFileSync(AREAS_FILE, 'utf8'));
    const routesData = JSON.parse(fs.readFileSync(ROUTES_FILE, 'utf8'));
    
    // Check if we have areas and routes
    if (!areasData.areas || !Array.isArray(areasData.areas)) {
      console.error('Invalid areas data: Expected an object with "areas" array');
      return;
    }
    
    if (!Array.isArray(routesData)) {
      console.error('Invalid routes data: Expected an array of routes');
      return;
    }
    
    console.log(`Found ${areasData.areas.length} areas and ${routesData.length} routes`);
    
    // Check for existing data to support resuming migration
    console.log('Checking for existing data in Firestore...');
    
    let hasExistingAreas = false;
    let hasExistingRoutes = false;
    
    if (!skipAreas) {
      const existingAreasSnapshot = await db.collection('areas').limit(1).get();
      hasExistingAreas = !existingAreasSnapshot.empty;
    }
    
    if (!skipRoutes) {
      const existingRoutesSnapshot = await db.collection('routes').limit(1).get();
      hasExistingRoutes = !existingRoutesSnapshot.empty;
    }
    
    if ((hasExistingAreas || hasExistingRoutes) && !forceOverwrite) {
      console.log('Found existing data in Firestore:');
      if (hasExistingAreas) console.log('- Areas collection has data');
      if (hasExistingRoutes) console.log('- Routes collection has data');
      
      // Ask for confirmation to continue
      const readline = require('readline');
      const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
      });
      
      const answer = await new Promise(resolve => {
        rl.question('Do you want to continue and potentially overwrite existing data? (y/n): ', resolve);
      });
      
      rl.close();
      
      if (answer.toLowerCase() !== 'y' && answer.toLowerCase() !== 'yes') {
        console.log('Migration aborted by user.');
        return;
      }
      
      console.log('Continuing with migration...');
    }
    
    // Process and upload areas in batches
    console.log('Processing and uploading areas...');
    const areaMap = new Map(); // Store area info for routes
    
    // Helper function for retrying batch operations
    const commitBatchWithRetry = async (batch, operationName, maxRetries = 3) => {
      let retries = 0;
      while (retries < maxRetries) {
        try {
          await batch.commit();
          return true;
        } catch (error) {
          retries++;
          console.error(`Error committing ${operationName} (attempt ${retries}/${maxRetries}):`, error.message);
          
          if (retries >= maxRetries) {
            console.error(`Failed to commit ${operationName} after ${maxRetries} attempts`);
            throw error;
          }
          
          // Wait before retrying (exponential backoff)
          const waitTime = Math.min(1000 * Math.pow(2, retries), 10000);
          console.log(`Retrying in ${waitTime/1000} seconds...`);
          await new Promise(resolve => setTimeout(resolve, waitTime));
        }
      }
    };
    
    const uploadAreas = async () => {
      const areasCollection = db.collection('areas');
      let batch = db.batch();
      let count = 0;
      let batchCount = 0;
      let validCount = 0;
      let invalidCount = 0;
      const totalAreas = areasData.areas.length;
      
      for (const area of areasData.areas) {
        // Skip areas without required fields
        if (!area.area_id || !area.area_name) {
          console.warn(`Skipping area with missing required fields: ${area.area_id || 'unknown'}`);
          invalidCount++;
          continue;
        }
        
        const processedArea = processArea(area);
        const areaRef = areasCollection.doc(processedArea.id);
        
        batch.set(areaRef, processedArea);
        count++;
        validCount++;
        
        // Store area info for routes
        areaMap.set(area.area_id, {
          name: area.area_name,
          hierarchy: area.area_hierarchy || []
        });
        
        // Show progress every 100 areas
        if (count % 100 === 0) {
          console.log(`Progress: ${count}/${totalAreas} areas processed (${Math.round(count/totalAreas*100)}%)`);
        }
        
        // Firestore batches can only contain up to 500 operations
        if (count % 500 === 0) {
          await commitBatchWithRetry(batch, `areas batch ${batchCount + 1}`);
          console.log(`Uploaded areas batch ${++batchCount}`);
          batch = db.batch();
        }
      }
      
      // Commit any remaining areas
      if (count % 500 !== 0) {
        await commitBatchWithRetry(batch, 'final areas batch');
        console.log(`Uploaded final areas batch`);
      }
      
      console.log(`Uploaded ${validCount} areas (skipped ${invalidCount} invalid areas)`);
    };
    
    // Process and upload routes in batches
    const uploadRoutes = async () => {
      const routesCollection = db.collection('routes');
      let batch = db.batch();
      let count = 0;
      let batchCount = 0;
      let validCount = 0;
      let invalidCount = 0;
      const totalRoutes = routesData.length;
      
      for (const route of routesData) {
        // Skip routes without required fields
        if (!route.route_id || !route.route_name || !route.area_id) {
          console.warn(`Skipping route with missing required fields: ${route.route_id || 'unknown'}`);
          invalidCount++;
          continue;
        }
        
        // Skip routes with excluded types
        const routeType = route.route_type || '';
        if (typeof routeType === 'string' && EXCLUDED_TYPES.some(type => routeType.includes(type))) {
          console.log(`Skipping excluded route type: ${route.route_name} (${routeType})`);
          continue;
        }
        
        // Get area info from map
        const areaInfo = areaMap.get(route.area_id) || { name: '', hierarchy: [] };
        
        const processedRoute = processRoute(route, areaInfo.name, areaInfo.hierarchy);
        const routeRef = routesCollection.doc(processedRoute.id);
        
        batch.set(routeRef, processedRoute);
        count++;
        validCount++;
        
        // Show progress every 500 routes
        if (count % 500 === 0) {
          console.log(`Progress: ${count}/${totalRoutes} routes processed (${Math.round(count/totalRoutes*100)}%)`);
        }
        
        // Firestore batches can only contain up to 500 operations
        if (count % 500 === 0) {
          await commitBatchWithRetry(batch, `routes batch ${batchCount + 1}`);
          console.log(`Uploaded routes batch ${++batchCount}`);
          batch = db.batch();
        }
      }
      
      // Commit any remaining routes
      if (count % 500 !== 0) {
        await commitBatchWithRetry(batch, 'final routes batch');
        console.log(`Uploaded final routes batch`);
      }
      
      console.log(`Uploaded ${validCount} routes (skipped ${invalidCount} invalid routes)`);
    };
    
    // Execute uploads
    if (!skipAreas) {
      await uploadAreas();
    } else {
      console.log('Skipping areas upload as requested');
      
      // If we're skipping areas but uploading routes, we need to load area data for routes
      if (!skipRoutes) {
        console.log('Loading area data for routes...');
        const areasSnapshot = await db.collection('areas').get();
        areasSnapshot.forEach(doc => {
          const area = doc.data();
          areaMap.set(area.id, {
            name: area.name,
            hierarchy: area.hierarchy || []
          });
        });
        console.log(`Loaded ${areaMap.size} areas for route processing`);
      }
    }
    
    if (!skipRoutes) {
      await uploadRoutes();
    } else {
      console.log('Skipping routes upload as requested');
    }
    
    console.log('Data migration completed successfully!');
  } catch (error) {
    console.error('Error during migration:', error);
  }
}

// Run the migration
migrateData()
  .then(() => {
    console.log('Migration script completed.');
    process.exit(0);
  })
  .catch(error => {
    console.error('Migration script failed:', error);
    process.exit(1);
  }); 