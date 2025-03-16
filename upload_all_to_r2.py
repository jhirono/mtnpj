#!/usr/bin/env python
"""
Upload all JSON files to Cloudflare R2

This script uploads all JSON files from climbing-search/public/data to Cloudflare R2,
with better error handling and progress reporting.
"""

import os
import sys
import json
import time
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
    
    # Get list of JSON files
    json_files = sorted([f for f in data_dir.glob("*.json")])
    
    if not json_files:
        print(f"No JSON files found in {data_dir}")
        sys.exit(1)
    
    print(f"Found {len(json_files)} JSON files to upload:")
    for i, file_path in enumerate(json_files):
        size_mb = file_path.stat().st_size / (1024 * 1024)
        print(f"  {i+1}. {file_path.name} ({size_mb:.2f} MB)")
    
    print("\nStarting upload process...")
    
    # Create R2 client
    client = r2_config.get_r2_client()
    
    # Track successful and failed uploads
    successful = []
    failed = []
    
    # Upload each file
    for i, file_path in enumerate(json_files):
        file_name = file_path.name
        size_mb = file_path.stat().st_size / (1024 * 1024)
        
        print(f"\n[{i+1}/{len(json_files)}] Uploading {file_name} ({size_mb:.2f} MB)...")
        
        try:
            start_time = time.time()
            
            # Upload the file
            url = r2_config.upload_file(file_path)
            
            elapsed = time.time() - start_time
            speed = size_mb / elapsed if elapsed > 0 else 0
            
            print(f"✅ Upload complete: {file_name} in {elapsed:.2f} seconds ({speed:.2f} MB/s)")
            print(f"   URL: {url}")
            
            successful.append({
                "name": file_name,
                "size_mb": size_mb,
                "elapsed_seconds": elapsed,
                "url": url
            })
            
        except Exception as e:
            print(f"❌ Error uploading {file_name}: {e}")
            failed.append({
                "name": file_name,
                "size_mb": size_mb,
                "error": str(e)
            })
    
    # Create a summary of uploaded files
    summary = {
        "bucket": r2_config.R2_BUCKET_NAME,
        "total_files": len(json_files),
        "successful": len(successful),
        "failed": len(failed),
        "successful_files": successful,
        "failed_files": failed
    }
    
    # Save the summary to a file
    with open("r2_upload_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    # Print summary
    print("\n=== Upload Summary ===")
    print(f"Total files: {len(json_files)}")
    print(f"Successfully uploaded: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if failed:
        print("\nFailed uploads:")
        for file_info in failed:
            print(f"  - {file_info['name']}: {file_info['error']}")
    
    print("\nUpload URLs:")
    for file_info in successful:
        print(f"  - {file_info['name']}: {file_info['url']}")
    
    print(f"\nSummary saved to r2_upload_summary.json")

if __name__ == "__main__":
    main() 