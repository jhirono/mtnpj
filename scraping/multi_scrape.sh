#!/bin/bash

# Example usage:
# ./scraping/multi_scrape.sh --mode=parallel "https://url1" "https://url2" "https://url3"
# Or with direct mode (skips area discovery):
# ./scraping/multi_scrape.sh --direct --mode=parallel "https://url1" "https://url2" "https://url3"

# Extract common options (everything except the URLs)
OPTIONS=()
URLS=()
DIRECT_MODE=false

for arg in "$@"; do
  if [[ $arg == "--direct" ]]; then
    DIRECT_MODE=true
  elif [[ $arg == http* ]]; then
    URLS+=("$arg")
  else
    OPTIONS+=("$arg")
  fi
done

# Check if we have any URLs
if [ ${#URLS[@]} -eq 0 ]; then
  echo "Error: No URLs provided"
  echo "Usage: $0 [options] url1 url2 url3 ..."
  echo "  --direct   Skip area discovery and treat URLs as lowest-level areas"
  exit 1
fi

# Process each URL
for ((i=0; i<${#URLS[@]}; i++)); do
  url="${URLS[$i]}"
  echo -e "\n=================================================="
  echo "Processing URL $((i+1))/${#URLS[@]}: $url"
  echo -e "==================================================\n"
  
  if [ "$DIRECT_MODE" = true ]; then
    # In direct mode, we'll create a temporary Python script to process just this URL
    temp_script=$(mktemp)
    cat > "$temp_script" << EOF
#!/usr/bin/env python3
import sys
import json
import os
sys.path.insert(0, os.path.abspath('.'))
from scraping.scrape_mtnpj_working import get_routes, save_all_areas

# Process single URL directly
url = "$url"
print(f"Directly processing: {url}")
area_data = get_routes(url)
if area_data:
    # Save area data
    all_areas = [area_data]
    area_name = url.rstrip('/').split('/')[-1]
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{area_name}_routes.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_areas, f, indent=2, ensure_ascii=False)
    print(f"Data saved to {output_file}")
EOF
    
    # Run the temporary script
    python3 "$temp_script"
    
    # Clean up
    rm "$temp_script"
  else
    # Regular mode: run the original script
    python3 scraping/scrape_mtnpj_working.py "$url" "${OPTIONS[@]}"
  fi
  
  # Check if the command succeeded
  if [ $? -ne 0 ]; then
    echo "Error processing URL: $url"
    echo "Continuing with the next URL..."
  fi
done

echo -e "\nAll URLs have been processed."