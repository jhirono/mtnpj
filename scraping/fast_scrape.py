#!/usr/bin/env python3

import sys
import os
import json
import argparse
import logging
import concurrent.futures
from tqdm import tqdm

# Import functions from the main script
sys.path.insert(0, os.path.abspath('.'))
from scraping.scrape_mtnpj_working import (
    get_routes, setup_logging, safe_get_routes, 
    REQUEST_DELAY, MAX_RETRIES, MAX_WORKERS
)

def process_url(url, verbose=False):
    """Process a single URL and return its data"""
    if verbose:
        print(f"Processing {url}")
    return safe_get_routes(url)

def process_parallel(urls, max_workers=None, verbose=False):
    """Process URLs in parallel"""
    if max_workers is None:
        max_workers = MAX_WORKERS
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_url = {executor.submit(process_url, url, verbose): url for url in urls}
        
        # Process results as they complete
        for future in tqdm(concurrent.futures.as_completed(future_to_url), 
                          total=len(future_to_url), 
                          desc="Processing areas"):
            url = future_to_url[future]
            try:
                area_data = future.result()
                if area_data:
                    results.append(area_data)
                else:
                    print(f"Warning: Skipping {url} after failed attempts")
            except Exception as e:
                print(f"Error processing {url}: {e}")
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Fast scrape of Mountain Project areas')
    parser.add_argument('urls', nargs='+', help='List of URLs to scrape')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('-o', '--output', help='Output file (JSON)')
    parser.add_argument('-p', '--parallel', action='store_true', help='Process in parallel')
    parser.add_argument('-w', '--workers', type=int, default=MAX_WORKERS, 
                        help='Number of workers for parallel processing')
    parser.add_argument('-d', '--delay', type=float, default=REQUEST_DELAY,
                        help='Delay between requests in seconds')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    urls = args.urls
    print(f"Processing {len(urls)} URLs...")
    
    if args.parallel:
        print(f"Using parallel processing with {args.workers} workers")
        all_areas = process_parallel(urls, max_workers=args.workers, verbose=args.verbose)
    else:
        all_areas = []
        for url in tqdm(urls, desc="Processing areas"):
            area_data = process_url(url, args.verbose)
            if area_data:
                all_areas.append(area_data)
    
    # Determine output file
    if args.output:
        output_file = args.output
    else:
        # Generate a name based on the first URL
        area_name = urls[0].rstrip('/').split('/')[-1]
        if len(urls) > 1:
            area_name += f"_and_{len(urls)-1}_more"
        output_file = f"data/{area_name}_routes.json"
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    
    # Save results
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_areas, f, indent=2, ensure_ascii=False)
    
    print(f"Processed {len(all_areas)} areas successfully")
    print(f"Data saved to {output_file}")

if __name__ == "__main__":
    main() 