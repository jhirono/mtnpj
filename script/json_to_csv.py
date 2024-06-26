import json
import sys
import csv

def process_json(input_file):
    with open(input_file, 'r') as f:
        data = json.load(f)

    csv_data = []
    max_hierarchy_levels = 0
    
    # First pass to determine the maximum hierarchy depth
    for area in data:
        hierarchy_length = len(area.get('hierarchy', []))
        if hierarchy_length > max_hierarchy_levels:
            max_hierarchy_levels = hierarchy_length
    
    # Header fields for hierarchy
    hierarchy_headers = [f"Hierarchy Name {i+1}" for i in range(max_hierarchy_levels)]
    hierarchy_url_headers = [f"Hierarchy URL {i+1}" for i in range(max_hierarchy_levels)]
    
    # Full headers
    headers = [
        "Area Name", "Area URL", "GPS", "Area Description", "Getting There",
        "All Hierarchy Names", "All Hierarchy URLs"
    ] + hierarchy_headers + hierarchy_url_headers + [
        "Route Name", "Route URL", "Grade", "Stars", "Votes",
        "Type", "Length", "FA", "Route Description",
        "Location", "Protection", "trad_protection_tags"
    ]
    
    for area in data:
        area_name = area.get('area_name', 'N/A')
        url = area.get('url', 'N/A')
        gps = area.get('gps', 'N/A')
        description = area.get('description', 'N/A')
        getting_there = area.get('getting_there', 'N/A')
        
        hierarchy_names = [h['name'] for h in area.get('hierarchy', [])]
        hierarchy_urls = [h['url'] for h in area.get('hierarchy', [])]
        
        all_hierarchy_names = " > ".join(hierarchy_names)
        all_hierarchy_urls = " > ".join(hierarchy_urls)
        
        hierarchy_names += ['N/A'] * (max_hierarchy_levels - len(hierarchy_names))
        hierarchy_urls += ['N/A'] * (max_hierarchy_levels - len(hierarchy_urls))
        
        for route in area.get('routes', []):
            route_name = route.get('route_name', 'N/A')
            route_url = route.get('route_url', 'N/A')
            grade = route.get('grade', 'N/A')
            stars = route.get('stars', 'N/A')
            votes = route.get('votes', 'N/A')
            route_type = route.get('type', 'N/A')
            length = route.get('length', 'N/A')
            fa = route.get('fa', 'N/A')
            route_description = route.get('description', 'N/A')
            location = route.get('location', 'N/A')
            protection = route.get('protection', 'N/A')
            trad_protection_tags = ", ".join(route.get('trad_protection_tags', []))
            
            csv_data.append([
                area_name, url, gps, description, getting_there,
                all_hierarchy_names, all_hierarchy_urls
            ] + hierarchy_names + hierarchy_urls + [
                route_name, route_url, grade, stars, votes,
                route_type, length, fa, route_description,
                location, protection, trad_protection_tags
            ])

    output_file = input_file.replace('.json', '.csv')
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(csv_data)

    print(f"Processed data saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python json_to_csv.py <input_json_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    process_json(input_file)
