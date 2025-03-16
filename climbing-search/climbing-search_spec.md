# Climbing Search Web Application: Technical Documentation

## Overview

Climbing Search is a modern web application built using React, TypeScript, and Vite that provides users with a comprehensive tool for searching and filtering rock climbing routes. The application loads climbing data from JSON files stored either locally or in Cloudflare R2 cloud storage, and offers advanced filtering, searching, and sorting capabilities for rock climbing routes and areas.

## Technology Stack

### Core Technologies
- **Frontend Framework**: React 18.2.0
- **Language**: TypeScript 5.7.2
- **Build Tool**: Vite 6.1.0
- **CSS Framework**: Tailwind CSS 3.4.1
- **Package Manager**: npm
- **Search Library**: Fuse.js 7.1.0
- **Cloud Storage**: Cloudflare R2 (optional)

### Development Tools
- **Linting**: ESLint 9.19.0
- **Styling**: PostCSS 8.4.35, Autoprefixer 10.4.17
- **Forms**: @tailwindcss/forms

### Deployment
- **Containerization**: Docker
- **Web Server**: NGINX
- **Cloud Hosting**: Fly.io
- **CI/CD**: Automated builds via Fly.io

## Architecture

### Directory Structure
```
climbing-search/
├── public/             # Static assets and JSON data files
│   └── data/           # Climbing route and area JSON data
├── src/
│   ├── assets/         # Image assets and icons
│   ├── components/     # React components
│   ├── hooks/          # Custom React hooks
│   ├── types/          # TypeScript type definitions
│   ├── utils/          # Utility functions
│   ├── App.tsx         # Main application component
│   ├── config.ts       # Application configuration
│   └── main.tsx        # Entry point
├── Dockerfile          # Docker configuration for deployment
├── nginx.conf          # NGINX configuration for production
├── fly.toml            # Fly.io deployment configuration
└── package.json        # Dependencies and scripts
```

### Data Model

The application works with three primary data types:

1. **Area**: Represents a climbing area with properties such as:
   - `area_id`, `area_name`, `area_url`
   - `area_description`, `area_getting_there`
   - `area_gps`, `area_hierarchy`
   - `area_tags` (for categorization)
   - Contains an array of `Route` objects

2. **Route**: Represents a climbing route with detailed information:
   - `route_id`, `route_name`, `route_url`
   - `route_grade`, `route_protection_grading`
   - `route_stars`, `route_votes`
   - `route_type` (sport, trad, boulder, etc.)
   - `route_pitches`, `route_length_ft`, `route_length_meter`
   - `route_description`, `route_location`, `route_protection`
   - `route_tags` (organized by category)
   - `route_comments`, `route_tick_comments`

3. **Filter Options**: Structured types for filtering routes:
   - Grade ranges (`min` and `max`)
   - Route types (sport, trad, etc.)
   - Tags by category

### Component Architecture

The application follows a component-based architecture with:

1. **App.tsx**: The main container component that:
   - Loads data from JSON files listed in `index.json`
   - Manages global application state
   - Handles data filtering and search logic
   - Renders child components

2. **Component Structure**:
   - `AreaSearch.tsx`: Integrated search for both areas and routes
   - `FilterPanel.tsx`: Advanced filtering options for routes
   - `RouteCard.tsx`: Displays individual route information
   - `RouteList.tsx`: Renders lists of filtered routes

## Key Features

### Data Loading

The application dynamically loads climbing data from JSON files, with two possible storage options:

1. **Local Storage**:
   - JSON files stored in `public/data/` directory
   - Files listed in `index.json` are loaded at runtime

2. **Cloud Storage (R2)**:
   - Configuration for Cloudflare R2 object storage
   - Toggle between local and R2 storage via `config.ts`
   - Environment variables for R2 credentials

### Integrated Search

The application features a powerful integrated search system that:

1. **Unified Search Interface**: Single search box finds both areas and routes
2. **Multi-term Search**: Supports complex searches with multiple keywords using AND logic
   - All search terms must be present in the result (e.g., "utah sunshine" finds only items containing both words)
   - Results are scored based on relevance and match quality
3. **Smart Scoring System**:
   - Exact phrase matches get highest priority
   - Matches at the beginning of terms or after separators get bonus points
   - Longer search terms have more weight than shorter ones
4. **Categorized Results**:
   - Results clearly separated into "Areas" and "Routes" sections
   - Area results show hierarchy information
   - Route results show grade and location information

### Area Selection

1. **Multiple Area Selection**:
   - Select multiple areas simultaneously to show combined routes
   - Each selected area displays routes from itself and all child areas
   - Areas can be added or removed independently
2. **Visual Indicators**:
   - Selected areas shown as tags below the search bar
   - One-click removal of selected areas

### Route Selection

1. **Direct Route Access**:
   - Search for and select specific routes by name
   - When a route is selected, it becomes the sole displayed route
   - "Back to all routes" button returns to area-based filtering

### Filtering and Sorting

Robust filtering capabilities include:

1. **Grade Filtering**: Min/max climbing grade selection
2. **Type Filtering**: Filter routes by type (sport, trad, etc.)
3. **Tag Filtering**: Filter by route characteristics 
4. **Sorting**: Multiple sort options:
   - By grade (ascending/descending)
   - By stars/rating (ascending/descending)
   - By number of votes
   - By physical location (left-to-right)

### Responsive UI

A responsive user interface built with Tailwind CSS provides:

1. **Mobile-First Design**: Works on devices of all sizes
2. **Filtering Panel**: Collapsible filtering options
3. **Route Cards**: Visually formatted route information
4. **Intuitive Navigation**: Easy browsing of climbing areas

## Configuration

### Environment Variables

The application uses the following environment variables:

- `VITE_R2_ACCOUNT_ID`: Cloudflare account ID for R2 storage
- `VITE_R2_BUCKET_NAME`: R2 bucket name for storing JSON files

These are configured in:
- `.env.local` for local development
- `fly.toml` for production deployment

### Build and Deployment

1. **Development**:
   - `npm run dev`: Start development server
   - `npm run build`: Build for production
   - `npm run preview`: Preview production build

2. **Production Deployment**:
   - Docker-based deployment to Fly.io
   - NGINX serves static files in production
   - Automatic HTTPS via Fly.io

## Integration with Cloudflare R2

The application supports integration with Cloudflare R2 object storage:

1. **Configuration**: 
   - Toggle `useR2Storage` in `config.ts`
   - Provide account ID and bucket name via environment variables

2. **Data Access**:
   - `getDataUrl()` function builds URLs for data files
   - Fallback to local files if R2 is not available

3. **CORS Configuration**:
   - R2 bucket must be configured with appropriate CORS settings
   - Supports direct browser access to R2 objects

## Performance Optimizations

1. **Data Optimization**:
   - Optional filtering script to create sport/trad-only JSON files, reducing file sizes by ~50%
   - Lazy loading of routes as user scrolls
2. **Search Performance**:
   - Efficient search algorithms with intelligent scoring
   - Minimum character threshold to prevent excessive searching
   - Result limiting to maintain responsiveness
3. **UI Optimizations**:
   - Memoization of filtered and sorted routes
   - Virtual scrolling for long route lists
   - Debounced search inputs
4. **Cloud Delivery**:
   - R2 integration provides global edge distribution

## Deployment Architecture

The application is deployed as a containerized static website:

1. **Build Process**:
   - Node.js builds the React application
   - Production assets are generated with Vite

2. **Container**:
   - NGINX serves static files
   - Configured with appropriate caching headers
   - Optimized for performance

3. **Hosting**:
   - Deployed on Fly.io's global network
   - Scales based on demand
   - Automatic HTTPS certificates

## Conclusion

The Climbing Search application is a modern, feature-rich web application built with React, TypeScript, and Vite. It provides robust search and filtering capabilities for rock climbing routes and areas, with support for both local and cloud-based data storage. The integrated search system allows users to find areas or specific routes using multiple keywords with AND logic, while the multiple area selection feature enables users to view routes from various locations simultaneously. The application is designed for performance, usability, and scalability, making it an excellent tool for climbers looking to discover new routes.
