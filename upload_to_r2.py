#!/usr/bin/env python
"""
Upload JSON files to Cloudflare R2

This script uploads the JSON files from climbing-search/public/data to Cloudflare R2.
"""

import os
import sys
import json
from pathlib import Path
import r2_config

def main():
    """Main function to upload files to R2"""
    # Check if we need to set up credentials
    if not all([r2_config.R2_ACCESS_KEY, r2_config.R2_SECRET_KEY, 
                r2_config.R2_ACCOUNT_ID, r2_config.R2_BUCKET_NAME]):
        print("R2 credentials not found. Running setup...")
        r2_config.setup_credentials()
    
    # Path to the data directory
    data_dir = Path("climbing-search/public/data")
    
    if not data_dir.exists():
        print(f"Error: Directory not found: {data_dir}")
        sys.exit(1)
    
    print(f"Uploading files from {data_dir} to R2 bucket {r2_config.R2_BUCKET_NAME}...")
    
    # Upload all files in the directory
    uploaded_files = r2_config.upload_directory(data_dir)
    
    # Create a summary of uploaded files
    summary = {
        "bucket": r2_config.R2_BUCKET_NAME,
        "files": [{"name": name, "url": url} for name, url in uploaded_files]
    }
    
    # Save the summary to a file
    with open("r2_upload_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nUploaded {len(uploaded_files)} files to R2 bucket {r2_config.R2_BUCKET_NAME}")
    print(f"Summary saved to r2_upload_summary.json")
    
    # Print URLs for each file
    print("\nFile URLs:")
    for name, url in uploaded_files:
        print(f"{name}: {url}")

if __name__ == "__main__":
    main() 