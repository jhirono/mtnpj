# Cloudflare R2 Setup for Climbing Search

This document explains how the Cloudflare R2 storage is set up and used in the Climbing Search application.

## Overview

The application now uses Cloudflare R2 for storing and serving the JSON data files, which provides several benefits:

1. **Reduced server load**: The static JSON files are served directly from Cloudflare's global network
2. **Improved performance**: R2 provides low-latency access from anywhere in the world
3. **Cost efficiency**: No egress fees for data transfer
4. **Scalability**: Can handle large files and high traffic without issues

## Files Uploaded to R2

The following files have been uploaded to the R2 bucket `awesomeclimbingsearch`:

- `california_routes_tagged.json` (131.25 MB)
- `canada_routes_tagged.json` (65.12 MB)
- `castle-rock_routes_tagged.json` (0.26 MB)
- `colorado_routes_tagged.json` (100.03 MB)
- `index.json` (0.00 MB)
- `nevada_routes_tagged.json` (21.04 MB)
- `oregon_routes_tagged.json` (15.67 MB)
- `washington_routes_tagged.json` (33.80 MB)

## Application Configuration

The application has been updated to use R2 for data storage. The key changes are:

1. Added a `config.ts` file with R2 configuration
2. Updated `App.tsx` to use the R2 URLs for fetching data
3. Added environment variables for R2 credentials

### Environment Variables

The following environment variables are used:

- `VITE_R2_ACCOUNT_ID`: The Cloudflare account ID
- `VITE_R2_BUCKET_NAME`: The R2 bucket name

These are set in:
- `.env.local` for local development
- `fly.toml` for production deployment

## Scripts for Managing R2

Several Python scripts have been created to manage the R2 storage:

- `r2_config.py`: Core functionality for R2 operations
- `upload_all_to_r2.py`: Uploads all JSON files to R2
- `test_upload.py`: Tests uploading a small file to R2

### Uploading New Files

To upload new or updated JSON files to R2:

1. Make sure the virtual environment is activated:
   ```
   source venv/bin/activate
   ```

2. Run the upload script:
   ```
   python upload_all_to_r2.py
   ```

3. Update the `index.json` file if necessary:
   ```
   python -c "import r2_config; r2_config.upload_file('climbing-search/public/data/index.json')"
   ```

## Fallback Mechanism

The application includes a fallback mechanism to use local files if R2 is not available. This is controlled by the `useR2Storage` flag in `config.ts`.

## CORS Configuration

The R2 bucket is configured to allow cross-origin requests from the application domain. This is necessary for the browser to be able to fetch the JSON files directly from R2.

## Future Improvements

Potential future improvements:

1. Add a CDN in front of R2 for even better performance
2. Implement caching strategies to reduce bandwidth usage
3. Add versioning to the data files for easier updates 