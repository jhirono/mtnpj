#!/usr/bin/env python3
import json
import os
import sys
import time
from pathlib import Path

def filter_sport_trad_routes(input_filename):
    """
    Filter JSON file to keep only routes with 'trad' or 'sport' in route_type.
    Remove areas with no routes after filtering.
    
    Args:
        input_filename: Path to the input JSON file
    
    Returns:
        tuple: (filtered_data, routes_kept, routes_total, areas_kept, areas_total)
    """
    print(f"Processing {input_filename}...")
    
    try:
        # Load the JSON file
        with open(input_filename, 'r') as f:
            data = json.load(f)
        
        # Track statistics
        routes_total = 0
        routes_kept = 0
        areas_total = len(data)
        areas_kept = 0
        
        # Create a new filtered list
        filtered_areas = []
        
        # Process each area
        for area in data:
            # Create a new area with filtered routes
            new_area = area.copy()
            
            # If there are no routes in this area, skip it
            if 'routes' not in area:
                continue
            
            # Filter routes in this area
            filtered_routes = []
            
            for route in area['routes']:
                routes_total += 1
                
                # Check if route_type contains 'trad' or 'sport' (case insensitive)
                if 'route_type' in route and isinstance(route['route_type'], str):
                    route_type_lower = route['route_type'].lower()
                    if 'trad' in route_type_lower or 'sport' in route_type_lower:
                        filtered_routes.append(route)
                        routes_kept += 1
            
            # Only include areas that have at least one route after filtering
            if filtered_routes:
                # Update the area with filtered routes
                new_area['routes'] = filtered_routes
                filtered_areas.append(new_area)
                areas_kept += 1
        
        print(f"Kept {routes_kept} out of {routes_total} routes ({routes_kept/routes_total*100:.2f}%)")
        print(f"Kept {areas_kept} out of {areas_total} areas ({areas_kept/areas_total*100:.2f}%)")
        return filtered_areas, routes_kept, routes_total, areas_kept, areas_total
    
    except Exception as e:
        print(f"Error processing {input_filename}: {e}")
        return None, 0, 0, 0, 0

def main():
    # Get the directories for input and output
    source_dir = Path("climbing-search/public/data/old")
    output_dir = Path("climbing-search/public/data")
    
    # Ensure the output directory exists
    output_dir.mkdir(exist_ok=True)
    
    # Ensure the backup directory exists
    backup_dir = output_dir / "backup"
    backup_dir.mkdir(exist_ok=True)
    
    # Create a summary of the filtering process
    summary = []
    
    # Process each JSON file (excluding index.json)
    for json_file in source_dir.glob("*_routes_tagged.json"):
        if json_file.name == "index.json":
            continue
        
        # Get base name without extension
        base_name = json_file.stem.replace("_routes_tagged", "")
        
        # Define output filename
        output_filename = output_dir / f"{base_name}_sport_trad.json"
        
        # Create a backup of the original file if it doesn't already exist
        backup_file = backup_dir / json_file.name
        if not backup_file.exists():
            print(f"Creating backup of {json_file.name}...")
            try:
                with open(json_file, 'rb') as src, open(backup_file, 'wb') as dst:
                    dst.write(src.read())
            except Exception as e:
                print(f"Error creating backup: {e}")
                continue
        
        # Filter the file
        start_time = time.time()
        filtered_data, routes_kept, routes_total, areas_kept, areas_total = filter_sport_trad_routes(json_file)
        elapsed_time = time.time() - start_time
        
        if filtered_data is not None:
            # Save the filtered data
            try:
                with open(output_filename, 'w') as f:
                    json.dump(filtered_data, f)
                print(f"Saved filtered data to {output_filename}")
                
                # Add to summary
                summary.append({
                    "file": json_file.name,
                    "original_size_mb": os.path.getsize(json_file) / (1024 * 1024),
                    "filtered_size_mb": os.path.getsize(output_filename) / (1024 * 1024),
                    "routes_total": routes_total,
                    "routes_kept": routes_kept,
                    "routes_percentage": routes_kept / routes_total * 100 if routes_total > 0 else 0,
                    "areas_total": areas_total,
                    "areas_kept": areas_kept,
                    "areas_percentage": areas_kept / areas_total * 100 if areas_total > 0 else 0,
                    "processing_time_sec": elapsed_time
                })
            except Exception as e:
                print(f"Error saving filtered data: {e}")
    
    # Print summary
    print("\nFiltering Summary:")
    print("-" * 120)
    print(f"{'Filename':<30} {'Original Size':<15} {'Filtered Size':<15} {'Routes Kept':<15} {'Routes %':<10} {'Areas Kept':<15} {'Areas %':<10} {'Time (s)':<10}")
    print("-" * 120)
    
    for item in summary:
        print(f"{item['file']:<30} {item['original_size_mb']:.2f} MB {item['filtered_size_mb']:.2f} MB {item['routes_kept']}/{item['routes_total']:<15} {item['routes_percentage']:.2f}% {item['areas_kept']}/{item['areas_total']:<15} {item['areas_percentage']:.2f}% {item['processing_time_sec']:.2f}")
    
    print("-" * 120)
    total_original = sum(item['original_size_mb'] for item in summary)
    total_filtered = sum(item['filtered_size_mb'] for item in summary)
    total_routes_kept = sum(item['routes_kept'] for item in summary)
    total_routes = sum(item['routes_total'] for item in summary)
    total_areas_kept = sum(item['areas_kept'] for item in summary)
    total_areas = sum(item['areas_total'] for item in summary)
    
    routes_percentage = total_routes_kept / total_routes * 100 if total_routes > 0 else 0
    areas_percentage = total_areas_kept / total_areas * 100 if total_areas > 0 else 0
    
    print(f"Total: {total_original:.2f} MB → {total_filtered:.2f} MB | Routes: {total_routes_kept}/{total_routes} ({routes_percentage:.2f}%) | Areas: {total_areas_kept}/{total_areas} ({areas_percentage:.2f}%)")

if __name__ == "__main__":
    main() 