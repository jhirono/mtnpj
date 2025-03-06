/**
 * Firebase Index Generator
 * 
 * This script helps automate the generation of Firestore indexes based on error messages.
 * It extracts the index URL from error messages and updates the firestore.indexes.json file.
 * 
 * Usage:
 * 1. Copy the error message containing the index URL
 * 2. Run: node scripts/generate-indexes.js "error-message-or-url"
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');

// Path to the Firestore indexes file
const INDEXES_FILE_PATH = path.join(__dirname, '..', 'firestore.indexes.json');

/**
 * Extract the index URL from an error message
 * @param {string} errorMessage - The error message containing the index URL
 * @returns {string|null} The extracted URL or null if not found
 */
function extractIndexUrl(errorMessage) {
  // Check if the input is already a URL
  if (errorMessage.startsWith('https://console.firebase.google.com')) {
    return errorMessage;
  }

  // Extract URL from error message
  const urlMatch = errorMessage.match(/https:\/\/console\.firebase\.google\.com\/v1\/r\/project\/[^/]+\/firestore\/indexes\?[^\s"]+/);
  return urlMatch ? urlMatch[0] : null;
}

/**
 * Parse the index information from a Firebase index URL
 * @param {string} url - The Firebase index URL
 * @returns {Object|null} The parsed index information or null if parsing failed
 */
function parseIndexFromUrl(url) {
  try {
    // Extract the index parameters from the URL
    const urlParams = new URL(url).search.substring(1);
    const params = new URLSearchParams(urlParams);
    
    // Check if we have the create_composite parameter
    const createComposite = params.get('create_composite');
    if (!createComposite) {
      return null;
    }
    
    // The create_composite parameter is base64 encoded
    const decodedComposite = Buffer.from(createComposite, 'base64').toString('utf-8');
    console.log('Decoded composite:', decodedComposite);
    
    // Extract collection group
    const collectionGroupMatch = decodedComposite.match(/collectionGroups\/([^/]+)\/indexes/);
    if (!collectionGroupMatch) {
      return null;
    }
    
    const collectionGroup = collectionGroupMatch[1];
    
    // Extract fields from the decoded string
    const fields = [];
    
    // Look for field patterns in the decoded string
    // This is a simplified parser that attempts to extract field info
    const fieldMatches = decodedComposite.match(/(\w+)_(\w+)\s*EA[A-Z]|\w+\s*EA[A-Z]|__name__\s*EA[A-Z]/g) || [];
    
    for (const match of fieldMatches) {
      console.log('Field match:', match);
      
      if (match.includes('__name__')) {
        fields.push({ fieldPath: '__name__', order: 'ASCENDING' });
        continue;
      }
      
      // Extract field name
      const fieldNameMatch = match.match(/^(\w+)_?(\w+)?/);
      if (!fieldNameMatch) continue;
      
      const fieldName = fieldNameMatch[1];
      
      // Determine field type based on the suffix or pattern
      if (match.includes('area_id') || match.endsWith('EAA')) {
        fields.push({ fieldPath: fieldName, order: 'ASCENDING' });
      } else if (match.endsWith('EAB') || match.includes('_numeric') && !match.includes('ASCENDING')) {
        fields.push({ fieldPath: fieldName, order: 'DESCENDING' });
      } else if (match.endsWith('EAE')) {
        fields.push({ fieldPath: fieldName, arrayConfig: 'CONTAINS' });
      } else {
        // Default case
        fields.push({ fieldPath: fieldName, order: 'ASCENDING' });
      }
    }
    
    // If we couldn't parse the fields properly, let's try to use the URL itself
    if (fields.length === 0) {
      // Directly check for common fields in the URL
      if (url.includes('area_id')) {
        fields.push({ fieldPath: 'area_id', order: 'ASCENDING' });
      }
      
      if (url.includes('grade_numeric')) {
        fields.push({ fieldPath: 'grade_numeric', order: url.includes('grade_numericEAB') ? 'DESCENDING' : 'ASCENDING' });
      }
      
      if (url.includes('route_stars')) {
        fields.push({ fieldPath: 'route_stars', order: url.includes('route_starsEAB') ? 'DESCENDING' : 'ASCENDING' });
      }
      
      if (url.includes('route_lr')) {
        fields.push({ fieldPath: 'route_lr', order: url.includes('route_lrEAB') ? 'DESCENDING' : 'ASCENDING' });
      }
      
      if (url.includes('__name__')) {
        fields.push({ fieldPath: '__name__', order: 'ASCENDING' });
      }
    }
    
    if (fields.length === 0) {
      console.error('Could not parse any fields from the URL');
      return null;
    }
    
    return {
      collectionGroup,
      queryScope: 'COLLECTION',
      fields
    };
  } catch (error) {
    console.error('Error parsing index URL:', error);
    return null;
  }
}

/**
 * Update the firestore.indexes.json file with a new index
 * @param {Object} indexInfo - The index information to add
 */
function updateIndexesFile(indexInfo) {
  // Read the current indexes file
  let indexesJson;
  try {
    const fileContent = fs.readFileSync(INDEXES_FILE_PATH, 'utf8');
    indexesJson = JSON.parse(fileContent);
  } catch (error) {
    console.error('Error reading indexes file:', error);
    return;
  }
  
  // Check if the index already exists
  const indexExists = indexesJson.indexes.some(existingIndex => {
    if (existingIndex.collectionGroup !== indexInfo.collectionGroup) {
      return false;
    }
    
    // Check if fields match
    if (existingIndex.fields.length !== indexInfo.fields.length) {
      return false;
    }
    
    return existingIndex.fields.every((field, index) => {
      const otherField = indexInfo.fields[index];
      return field.fieldPath === otherField.fieldPath && 
             field.order === otherField.order && 
             field.arrayConfig === otherField.arrayConfig;
    });
  });
  
  // If the index doesn't exist, add it
  if (!indexExists) {
    indexesJson.indexes.push(indexInfo);
    
    // Write the updated file
    fs.writeFileSync(INDEXES_FILE_PATH, JSON.stringify(indexesJson, null, 2), 'utf8');
    console.log('Index added successfully!');
  } else {
    console.log('Index already exists in the file.');
  }
}

/**
 * Process a batch of error messages or URLs
 * @param {string[]} items - Array of error messages or URLs to process
 */
async function processBatch(items) {
  for (const item of items) {
    const url = extractIndexUrl(item);
    if (!url) {
      console.error(`No index URL found in: ${item.substring(0, 50)}...`);
      continue;
    }
    
    console.log(`\nProcessing URL: ${url}`);
    
    const indexInfo = parseIndexFromUrl(url);
    if (!indexInfo) {
      console.error(`Failed to parse index from URL: ${url}`);
      continue;
    }
    
    console.log('Parsed index information:');
    console.log(JSON.stringify(indexInfo, null, 2));
    
    // Automatically add the index without prompting
    updateIndexesFile(indexInfo);
  }
}

/**
 * Main function to process command line arguments
 */
async function main() {
  // Check if we have arguments
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    // If no arguments, prompt for input
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });
    
    const errorMessage = await new Promise(resolve => {
      rl.question('Paste the error message or index URL: ', answer => {
        rl.close();
        resolve(answer);
      });
    });
    
    await processBatch([errorMessage]);
  } else if (args[0] === '--batch') {
    // Process a batch of URLs from a file
    const filename = args[1];
    if (!filename) {
      console.error('Please provide a filename for batch processing');
      return;
    }
    
    try {
      const content = fs.readFileSync(filename, 'utf8');
      const lines = content.split(/\r?\n/).filter(line => line.trim());
      await processBatch(lines);
    } catch (error) {
      console.error('Error reading batch file:', error);
    }
  } else {
    // Process all arguments as separate items
    await processBatch(args);
  }
}

// Run the main function
main().catch(console.error); 