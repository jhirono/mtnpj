Core Requirements & Functions
1. Data Loading
Load area and route data from JSON files
Build area hierarchy relationships
Handle async loading with error states
2. Area Selection & Search
Allow searching for climbing areas
Display hierarchical area structure
Enable selection of multiple areas
Build area tree for efficient navigation
3. Route Filtering System
Filter by grade range
Filter by route type (Trad, Sport)
Exclude specific types (Boulder, Aid, etc.)
Tag-based filtering (e.g., exclude sandbag routes)
Custom filter combinations
4. Route Sorting
Sort by grade (easy to hard/hard to easy)
Sort by stars/quality (high to low/low to high)
Sort by vote count (popular to less popular)
Sort by left-to-right position
5. UI Components
FilterPanel: Controls for filtering and sorting routes
AreaSearch: Search interface for finding and selecting areas
RouteCard: Displays individual route information
RouteList: Container for route results
6. Performance Optimization
Infinite scrolling for large result sets
Memoization for filtered and sorted results
Efficient data structures for filtering
Pagination-like approach with ROUTES_PER_PAGE constant
7. Grade Handling
Comprehensive grade system support
Grade normalization for consistent comparison
Grade range filters
Firebase Integration Requirements
For integration with Firebase, you would need:
Firebase Configuration:
Setup Firebase project
Initialize Firebase in the application
Data Storage:
Transfer JSON data to Firestore collections
Organize data hierarchically (Areas -> Routes)
Maintain relationships between entities
Querying:
Implement Firestore queries to replace in-memory filtering
Optimize queries for common filtering patterns
Handle query limits and pagination
Authentication (if needed):
User authentication system
Access control for data writing
Implementation Blocks
For LMAI, here are the key implementation blocks:
Firebase Setup & Configuration
Data Model Definition in Firestore
Data Migration from JSON to Firestore
Area Query Implementation
Route Filtering Implementation with Firestore
Route Sorting Implementation with Firestore
UI Component Integration with Firebase
Performance Optimization for Firebase Queries
Error Handling & Offline Support
Each block represents a logical unit of work that could be passed to LMAI for implementation help when integrating Firebase with the existing climbing search application.