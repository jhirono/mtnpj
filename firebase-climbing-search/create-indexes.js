const fs = require("fs");
const indexesFile = "firestore.indexes.json";
const indexes = JSON.parse(fs.readFileSync(indexesFile));

// Function to check if an index already exists
function indexExists(newIndex) {
  return indexes.indexes.some(existingIndex => {
    if (existingIndex.collectionGroup !== newIndex.collectionGroup) return false;
    if (existingIndex.fields.length !== newIndex.fields.length) return false;
    
    return existingIndex.fields.every((field, i) => 
      field.fieldPath === newIndex.fields[i].fieldPath && 
      field.order === newIndex.fields[i].order
    );
  });
}

// Add indexes for route types with various sorts
const routeTypes = [
  [{ fieldPath: "is_trad", order: "ASCENDING" }],
  [{ fieldPath: "is_sport", order: "ASCENDING" }],
  [{ fieldPath: "is_multipitch", order: "ASCENDING" }],
  [{ fieldPath: "is_trad", order: "ASCENDING" }, { fieldPath: "is_sport", order: "ASCENDING" }],
  [{ fieldPath: "is_trad", order: "ASCENDING" }, { fieldPath: "is_multipitch", order: "ASCENDING" }],
  [{ fieldPath: "is_sport", order: "ASCENDING" }, { fieldPath: "is_multipitch", order: "ASCENDING" }],
  [{ fieldPath: "is_trad", order: "ASCENDING" }, { fieldPath: "is_sport", order: "ASCENDING" }, { fieldPath: "is_multipitch", order: "ASCENDING" }]
];

const sortFields = [
  { fieldPath: "grade_numeric", order: "ASCENDING" },
  { fieldPath: "grade_numeric", order: "DESCENDING" },
  { fieldPath: "route_stars", order: "ASCENDING" },
  { fieldPath: "route_stars", order: "DESCENDING" },
  { fieldPath: "route_votes", order: "ASCENDING" },
  { fieldPath: "route_votes", order: "DESCENDING" },
  { fieldPath: "quality_score", order: "ASCENDING" },
  { fieldPath: "quality_score", order: "DESCENDING" },
  { fieldPath: "route_lr", order: "ASCENDING" },
  { fieldPath: "route_lr", order: "DESCENDING" }
];

// Generate all combinations
let count = 0;
for (const routeType of routeTypes) {
  for (const sortField of sortFields) {
    const newIndex = {
      collectionGroup: "routes",
      queryScope: "COLLECTION",
      fields: [...routeType, {...sortField}]
    };
    
    if (!indexExists(newIndex)) {
      indexes.indexes.push(newIndex);
      count++;
    }
  }
}

// Grade filtering indexes
const gradeField = [
  { fieldPath: "grade_numeric", order: "ASCENDING" },
  { fieldPath: "grade_numeric", order: "DESCENDING" }
];

for (const grade of gradeField) {
  for (const routeType of routeTypes) {
    const newIndex = {
      collectionGroup: "routes",
      queryScope: "COLLECTION",
      fields: [{...grade}, ...routeType]
    };
    
    if (!indexExists(newIndex)) {
      indexes.indexes.push(newIndex);
      count++;
    }
  }
  
  // Grade + secondary sort
  for (const sortField of sortFields.filter(f => f.fieldPath !== "grade_numeric")) {
    const newIndex = {
      collectionGroup: "routes",
      queryScope: "COLLECTION",
      fields: [{...grade}, {...sortField}]
    };
    
    if (!indexExists(newIndex)) {
      indexes.indexes.push(newIndex);
      count++;
    }
  }
}

console.log(`Added ${count} new indexes to firestore.indexes.json`);
fs.writeFileSync(indexesFile, JSON.stringify(indexes, null, 2)); 