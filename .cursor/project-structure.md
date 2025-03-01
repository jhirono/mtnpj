# Awesome Climbing Search - Project Structure

## Overview
This project is a React-based web application for searching climbing routes across multiple areas. It features advanced filtering, sorting, and lazy loading for improved performance with large datasets.

## Key Directories

### `/climbing-search/src/`
Contains the main application source code:
- `App.tsx`: Main application component with route filtering and display logic
- `/components/`: React components for UI elements
- `/types/`: TypeScript type definitions
- `/utils/`: Utility functions

### `/climbing-search/public/`
Contains static assets:
- `/data/`: JSON data files for climbing routes
  - `index.json`: List of all data files to load
  - `*_routes_tagged.json`: Individual area route data files
- `/docs/`: Documentation files including README.html

### `/tagging/`
Contains scripts for processing and tagging route data:
- `route_area_tagging.py`: Python script for tagging routes using OpenAI API

## Key Files

### Application Core
- `climbing-search/src/App.tsx`: Main application component
- `climbing-search/src/components/RouteCard.tsx`: Component for displaying route information
- `climbing-search/src/components/FilterPanel.tsx`: Component for filtering routes
- `climbing-search/src/components/AreaSearch.tsx`: Component for area selection

### Data Processing
- `tagging/route_area_tagging.py`: Script for processing and tagging route data
- `prompt/route_prompt.txt`: Prompt template for OpenAI API

### Configuration
- `climbing-search/package.json`: NPM package configuration
- `climbing-search/vite.config.ts`: Vite build configuration
- `climbing-search/tailwind.config.js`: Tailwind CSS configuration

## Build and Run
- Development: `cd climbing-search && npm run dev`
- Build: `cd climbing-search && npm run build`
- Preview: `cd climbing-search && npm run preview` 