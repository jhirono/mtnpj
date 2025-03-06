#!/bin/bash

# Firebase Climbing Search Setup Script
# This script helps set up dependencies and configure the Firebase project

# Text colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================${NC}"
echo -e "${BLUE}Firebase Climbing Search Setup${NC}"
echo -e "${BLUE}====================================${NC}"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo -e "${RED}Error: npm is not installed${NC}"
    echo "Please install Node.js and npm first from https://nodejs.org/"
    exit 1
fi

# Check if firebase-tools is installed
if ! command -v firebase &> /dev/null; then
    echo -e "${BLUE}Installing Firebase CLI tools...${NC}"
    npm install -g firebase-tools
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to install Firebase tools. Please try manually:${NC}"
        echo "npm install -g firebase-tools"
        exit 1
    fi
    
    echo -e "${GREEN}Firebase CLI tools installed successfully${NC}"
else
    echo -e "${GREEN}Firebase CLI tools already installed${NC}"
fi

# Navigate to project root
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

# Install npm dependencies
echo -e "${BLUE}Installing npm dependencies...${NC}"
npm install

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install dependencies. Please try manually:${NC}"
    echo "npm install"
    exit 1
fi

echo -e "${GREEN}Dependencies installed successfully${NC}"

# Create data directory if it doesn't exist
if [ ! -d "./data" ]; then
    echo -e "${BLUE}Creating data directory...${NC}"
    mkdir -p ./data
    echo -e "${GREEN}Data directory created at:${NC} $PROJECT_ROOT/data"
fi

# Firebase setup
echo -e "${BLUE}Do you want to initialize a new Firebase project? (y/n)${NC}"
read -r init_firebase

if [[ $init_firebase =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Logging into Firebase...${NC}"
    firebase login
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Firebase login failed. Please try again later.${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}Initializing Firebase project...${NC}"
    firebase init
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Firebase initialization failed. Please try manually:${NC}"
        echo "firebase init"
        exit 1
    fi
    
    echo -e "${GREEN}Firebase project initialized successfully${NC}"
    
    # Update Firebase config in the code
    echo -e "${BLUE}Please enter your Firebase configuration:${NC}"
    echo "You can find this in the Firebase console under Project Settings > General > Your apps > Firebase SDK snippet > Config"
    
    echo -e "${BLUE}API Key:${NC}"
    read -r api_key
    
    echo -e "${BLUE}Auth Domain:${NC}"
    read -r auth_domain
    
    echo -e "${BLUE}Project ID:${NC}"
    read -r project_id
    
    echo -e "${BLUE}Storage Bucket:${NC}"
    read -r storage_bucket
    
    echo -e "${BLUE}Messaging Sender ID:${NC}"
    read -r messaging_sender_id
    
    echo -e "${BLUE}App ID:${NC}"
    read -r app_id
    
    # Replace placeholders in firebase.ts
    FIREBASE_CONFIG_FILE="./src/firebase.ts"
    
    if [ -f "$FIREBASE_CONFIG_FILE" ]; then
        echo -e "${BLUE}Updating Firebase configuration in $FIREBASE_CONFIG_FILE...${NC}"
        
        sed -i.bak -e "s/YOUR_API_KEY/$api_key/g" \
            -e "s/YOUR_PROJECT_ID/$project_id/g" \
            -e "s/YOUR_MESSAGING_SENDER_ID/$messaging_sender_id/g" \
            -e "s/YOUR_APP_ID/$app_id/g" \
            -e "s/YOUR_PROJECT_ID.firebaseapp.com/$auth_domain/g" \
            -e "s/YOUR_PROJECT_ID.appspot.com/$storage_bucket/g" \
            "$FIREBASE_CONFIG_FILE"
        
        # Also update the migration script
        MIGRATION_SCRIPT="./scripts/migrate-data.js"
        if [ -f "$MIGRATION_SCRIPT" ]; then
            echo -e "${BLUE}Updating Firebase configuration in $MIGRATION_SCRIPT...${NC}"
            
            sed -i.bak -e "s/YOUR_API_KEY/$api_key/g" \
                -e "s/YOUR_PROJECT_ID/$project_id/g" \
                -e "s/YOUR_MESSAGING_SENDER_ID/$messaging_sender_id/g" \
                -e "s/YOUR_APP_ID/$app_id/g" \
                -e "s/YOUR_PROJECT_ID.firebaseapp.com/$auth_domain/g" \
                -e "s/YOUR_PROJECT_ID.appspot.com/$storage_bucket/g" \
                "$MIGRATION_SCRIPT"
            
            rm "$MIGRATION_SCRIPT.bak"
        fi
        
        rm "$FIREBASE_CONFIG_FILE.bak"
        echo -e "${GREEN}Firebase configuration updated successfully${NC}"
    else
        echo -e "${RED}Firebase configuration file not found at $FIREBASE_CONFIG_FILE${NC}"
        echo "Please update the Firebase configuration manually."
    fi
fi

# Firestore rules setup
echo -e "${BLUE}Do you want to set up basic Firestore security rules? (y/n)${NC}"
read -r setup_rules

if [[ $setup_rules =~ ^[Yy]$ ]]; then
    RULES_FILE="./firestore.rules"
    
    cat > "$RULES_FILE" << EOF
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Allow read access to all documents
    match /{document=**} {
      allow read: if true;
    }
    
    // Restrict write access to authenticated users (if you implement authentication)
    match /areas/{areaId} {
      allow write: if request.auth != null;
    }
    
    match /routes/{routeId} {
      allow write: if request.auth != null;
    }
  }
}
EOF
    
    echo -e "${GREEN}Basic Firestore rules created at:${NC} $PROJECT_ROOT/firestore.rules"
    echo -e "${BLUE}You may want to customize these rules based on your specific security requirements.${NC}"
fi

# Firestore indexes setup
echo -e "${BLUE}Do you want to set up recommended Firestore indexes? (y/n)${NC}"
read -r setup_indexes

if [[ $setup_indexes =~ ^[Yy]$ ]]; then
    INDEXES_FILE="./firestore.indexes.json"
    
    cat > "$INDEXES_FILE" << EOF
{
  "indexes": [
    {
      "collectionGroup": "routes",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "area_id", "order": "ASCENDING" },
        { "fieldPath": "grade_numeric", "order": "ASCENDING" },
        { "fieldPath": "route_stars", "order": "DESCENDING" }
      ]
    },
    {
      "collectionGroup": "routes",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "area_id", "order": "ASCENDING" },
        { "fieldPath": "route_type", "arrayConfig": "CONTAINS" },
        { "fieldPath": "route_stars", "order": "DESCENDING" }
      ]
    },
    {
      "collectionGroup": "routes",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "area_id", "order": "ASCENDING" },
        { "fieldPath": "tags", "arrayConfig": "CONTAINS" },
        { "fieldPath": "route_stars", "order": "DESCENDING" }
      ]
    }
  ],
  "fieldOverrides": []
}
EOF
    
    echo -e "${GREEN}Recommended Firestore indexes created at:${NC} $PROJECT_ROOT/firestore.indexes.json"
    echo -e "${BLUE}You can deploy these indexes with 'firebase deploy --only firestore:indexes'${NC}"
fi

echo -e "${BLUE}====================================${NC}"
echo -e "${GREEN}Setup completed!${NC}"
echo -e "${BLUE}====================================${NC}"
echo ""
echo -e "Next steps:"
echo -e "1. Place your JSON data files in the ${BLUE}$PROJECT_ROOT/data${NC} directory"
echo -e "   - areas.json: should contain an object with an 'areas' array"
echo -e "   - routes.json: should contain an array of routes"
echo -e ""
echo -e "2. Run the migration script to upload data to Firestore:"
echo -e "   ${BLUE}node scripts/migrate-data.js${NC}"
echo -e ""
echo -e "3. Start the development server:"
echo -e "   ${BLUE}npm run dev${NC}"
echo -e ""
echo -e "4. Deploy to Firebase when ready:"
echo -e "   ${BLUE}npm run build${NC}"
echo -e "   ${BLUE}firebase deploy${NC}"
echo -e ""
echo -e "Happy climbing! 🧗" 