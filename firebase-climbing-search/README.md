# Firebase Climbing Route Search

A web application for searching and filtering rock climbing routes using Firebase Firestore as the backend database.

## Features

- Search for climbing areas by name
- Select multiple climbing areas to search within
- Filter routes by:
  - Grade range (5.3 to 5.16+)
  - Route type (Sport, Trad, Boulder, etc.)
  - Route features/tags
- Sort routes by:
  - Star rating (popularity)
  - Grade 
  - Name
- Infinite scroll for pagination
- Responsive design for mobile and desktop

## Tech Stack

- **Frontend**: React with TypeScript
- **Backend**: Firebase Firestore
- **Hosting**: Firebase Hosting
- **Styling**: Tailwind CSS

## Project Structure

```
firebase-climbing-search/
├── data/                   # JSON data files for migration
├── public/                 # Static files
├── scripts/                # Utility scripts
│   ├── migrate-data.js     # Data migration script
│   └── setup.sh            # Setup script
├── src/
│   ├── components/         # React components
│   │   ├── AreaSearch.tsx  # Area search component
│   │   ├── FilterPanel.tsx # Filtering controls
│   │   └── RouteCard.tsx   # Route display card
│   ├── utils/
│   │   └── gradeUtils.ts   # Climbing grade utilities
│   ├── App.tsx             # Main application component
│   ├── firebase.ts         # Firebase configuration and utilities
│   ├── index.tsx           # Application entry point
│   └── types.ts            # TypeScript interfaces
└── README.md               # Project documentation
```

## Getting Started

### Prerequisites

- Node.js and npm installed
- Firebase account

### Setup

1. Clone the repository:
   ```
   git clone <repository-url>
   cd firebase-climbing-search
   ```

2. Run the setup script:
   ```
   ./scripts/setup.sh
   ```
   This script will:
   - Install dependencies
   - Set up Firebase CLI tools if needed
   - Initialize your Firebase project
   - Configure Firebase settings
   - Set up recommended Firestore rules and indexes

3. Prepare your data:
   - Place your climbing data in the following format:
     - `data/areas.json`: Contains an object with an `areas` array
     - `data/routes.json`: Contains an array of routes

4. Migrate the data to Firestore:
   ```
   node scripts/migrate-data.js
   ```

5. Start the development server:
   ```
   npm run dev
   ```

6. Open your browser at http://localhost:3000

### Data Format

#### Area Format:
```json
{
  "areas": [
    {
      "area_id": "unique-area-id",
      "area_name": "Area Name",
      "area_url": "http://example.com/area",
      "area_description": "Description of the area",
      "area_hierarchy": [
        {
          "level": 1,
          "area_hierarchy_name": "Parent Area",
          "area_hierarchy_url": "http://example.com/parent"
        }
      ],
      "area_tags": ["tag1", "tag2"]
    }
  ]
}
```

#### Route Format:
```json
[
  {
    "route_id": "unique-route-id",
    "route_name": "Route Name",
    "route_url": "http://example.com/route",
    "route_grade": "5.10a",
    "route_stars": 3.5,
    "route_votes": 100,
    "route_type": ["Sport", "Trad"],
    "route_length_ft": 100,
    "route_length_meter": 30,
    "route_pitches": 1,
    "route_fa": "First Ascensionist",
    "route_description": "Description of the route",
    "route_tags": {
      "features": ["juggy", "crimpy"],
      "environment": ["sunny", "morning_sun"]
    },
    "area_id": "unique-area-id"
  }
]
```

## Deployment

1. Build the application:
   ```
   npm run build
   ```

2. Deploy to Firebase:
   ```
   firebase deploy
   ```

## Customization

### Firestore Rules

You can customize the Firestore security rules in `firestore.rules`. The default rules allow:
- Read access to anyone
- Write access only to authenticated users

### Firestore Indexes

The recommended indexes are defined in `firestore.indexes.json`. If you add more complex queries, you may need to create additional indexes.

## Troubleshooting

### Firebase Configuration

If you need to update your Firebase configuration:
1. Go to the Firebase console > Project settings > General > Your apps
2. Copy the configuration
3. Update in `src/firebase.ts`

### Migration Issues

If you encounter issues with data migration:
1. Check that your data files follow the expected format
2. Verify your Firebase configuration
3. Check Firestore permissions

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Inspired by the climbing community
- Built with Firebase and React 