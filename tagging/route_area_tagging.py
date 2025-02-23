#!/usr/bin/env python3
import json
import sys
import re
import openai
import os
import time
from datetime import datetime
from typing import List, Dict, Any

# OpenAI API configuration
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI()

# Constants
MAX_BATCH_SIZE = 50000  # Batch API limit
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

def parse_grade(grade_str):
    """
    Parses a grade string (e.g., "5.9", "5.10a", "5.10b", "5.10c") into a tuple
    for comparison. Returns a tuple (minor, mod_val, letter_val).
    """
    m = re.match(r'5\.(\d+)([+-]?)([a-d]?)', grade_str)
    if m:
        minor = int(m.group(1))
        mod = m.group(2)
        letter = m.group(3)
        mod_val = 0 if mod == "-" else (2 if mod == "+" else 1)
        letter_val = ord(letter) - ord('a') + 1 if letter else 0
        return (minor, mod_val, letter_val)
    else:
        return (999, 999, 999)

def is_higher(suggested, official):
    return parse_grade(suggested) > parse_grade(official)

def is_lower(suggested, official):
    return parse_grade(suggested) < parse_grade(official)

def manual_tagging(data):
    """Manual tagging logic implementation"""
    month_dict = {"Jan":1, "Feb":2, "Mar":3, "Apr":4, "May":5, "Jun":6,
                  "Jul":7, "Aug":8, "Sep":9, "Oct":10, "Nov":11, "Dec":12}
    
    for area in data:
        area["manual_tags"] = {}
        for route in area.get("routes", []):
            manual_tags = {}

            # Rule 1: Rope Length
            if route.get("route_pitches", 1) == 1 and route.get("route_length_meter") is not None:
                length = route["route_length_meter"]
                if 30 < length <= 35:
                    manual_tags.setdefault("Rope Length", []).append("rope_70m")
                elif 35 < length <= 40:
                    manual_tags.setdefault("Rope Length", []).append("rope_80m")

            # Rule 2: Multipitch Tagging
            if route.get("route_pitches", 1) > 1:
                pitches = route["route_pitches"]
                if pitches < 5:
                    manual_tags.setdefault("Multipitch", []).append("short_multipitch")
                else:
                    manual_tags.setdefault("Multipitch", []).append("long_multipitch")

            # Rule 3: Protection Grading
            pg = route.get("route_protection_grading", "").upper()
            if pg in ["PG13", "R", "X"]:
                manual_tags.setdefault("Difficulty & Safety", []).append("runout_dangerous")

            # Rule 4: Rating Analysis
            if route.get("route_votes", 0) >= 5:
                official = route.get("route_grade", "").strip()
                suggested = route.get("route_suggested_ratings", {})
                same = suggested.get(official, 0)
                higher = sum(count for key, count in suggested.items() if key != official and is_higher(key, official))
                lower = sum(count for key, count in suggested.items() if key != official and is_lower(key, official))
                if higher > same and higher > lower:
                    manual_tags.setdefault("Difficulty & Safety", []).append("sandbag")
                elif lower > same and lower > higher:
                    manual_tags.setdefault("Difficulty & Safety", []).append("first_in_grade")

            # Rule 5: Classic Route
            if route.get("route_stars", 0) >= 3 and route.get("route_votes", 0) >= 5:
                manual_tags.setdefault("Crowds & Popularity", []).append("classic_route")

            # Rule 6: New Routes
            shared = route.get("route_shared_on", "").strip()
            if shared:
                try:
                    month_abbr, year_str = shared.split(",")
                    year = int(year_str.strip())
                    month = month_dict.get(month_abbr.strip(), 0)
                    if (year > 2022) or (year == 2022 and month > 1):
                        manual_tags.setdefault("Crowds & Popularity", []).append("new_routes")
                except Exception:
                    pass

            route["manual_tags"] = manual_tags
    return data

def create_batch_requests(routes: List[Dict[str, Any]], prompt_template: str) -> List[Dict[str, Any]]:
    """Create batch requests for the OpenAI Batch API"""
    batch_requests = []
    
    for route in routes:
        input_text = f"""
Route Description: {route.get('route_description', '')}
Route Location: {route.get('route_location', '')}
Route Type: {route.get('route_type', '')}
Route Protection: {route.get('route_protection', '')}
Comments: {route.get('route_tick_comments', '')} {' '.join([c.get('comment_text', '') for c in route.get('route_comments', [])])}
"""
        request = {
            "custom_id": str(route.get('route_id')),
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": prompt_template},
                    {"role": "user", "content": input_text}
                ],
                "temperature": 0.3,
                "max_tokens": 500,
                "top_p": 0.95,
                "n": 1
            }
        }
        batch_requests.append(request)
    
    return batch_requests

def submit_batch(batch_requests: List[Dict[str, Any]], retry_count: int = 0) -> str:
    """Submit requests to Batch API and return batch ID with retry logic"""
    if retry_count >= MAX_RETRIES:
        raise Exception("Max retries exceeded while trying to submit batch")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_file = f"batch_input_{timestamp}.jsonl"
    
    try:
        # Write batch requests to JSONL file
        with open(batch_file, "w") as f:
            for request in batch_requests:
                f.write(json.dumps(request) + "\n")
        
        try:
            # Upload file to OpenAI
            with open(batch_file, "rb") as f:
                file = client.files.create(
                    file=f,
                    purpose="batch"
                )
            
            # Create batch job
            batch = client.batches.create(
                input_file_id=file.id,
                endpoint="/v1/chat/completions",
                completion_window="24h"
            )
            
            return batch.id
            
        except Exception as e:
            print(f"Error during batch submission (attempt {retry_count + 1}): {e}")
            time.sleep(RETRY_DELAY * (retry_count + 1))
            return submit_batch(batch_requests, retry_count + 1)
            
    finally:
        # Clean up temporary file
        if os.path.exists(batch_file):
            os.remove(batch_file)

def wait_for_batch_completion(batch_id):
    """Wait for batch completion and return results"""
    print("Checking batch status...")
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Check batch status
            batch = client.batches.retrieve(batch_id)
            print(f"Batch status: {batch.status}")
            
            if batch.status == "completed":
                # Get the output file ID from the batch
                output_file_id = batch.output_file_id
                if not output_file_id:
                    raise Exception("No output file ID found in completed batch")
                    
                # Get the results from the output file
                response = client.files.content(output_file_id)
                
                # Parse the JSONL content
                results = []
                for line in response.text.splitlines():
                    if not line.strip():
                        continue
                    try:
                        result = json.loads(line)
                        results.append(result)
                    except json.JSONDecodeError as e:
                        print(f"Error parsing JSONL line: {e}")
                        continue
                
                print(f"Successfully loaded {len(results)} results from batch")
                return results
                
            elif batch.status in ["failed", "expired", "cancelled"]:
                raise Exception(f"Batch failed with status: {batch.status}")
                
            # If still processing, wait and retry
            print("Batch still processing, waiting...")
            time.sleep(10)
            continue
                
        except Exception as e:
            print(f"Error retrieving batch results (attempt {retry_count + 1}/{max_retries}): {str(e)}")
            retry_count += 1
            if retry_count < max_retries:
                time.sleep(5)
                continue
            return None

def process_batch_results(results):
    """Process batch results, separating area and route tags"""
    area_tags = {}
    route_tags = {}
    
    for result in results:
        try:
            custom_id = result.get("custom_id")
            # Navigate through the nested response structure
            response = result.get("response", {}).get("body", {}).get("choices", [{}])[0].get("message", {}).get("content")
            
            if not response:
                print(f"No content found for {custom_id}")
                continue
                
            try:
                # Parse the JSON string content
                tags_data = json.loads(response)
                llm_tags = tags_data.get("llm_tags", {})
                
                # Check if this is an area or route based on the ID format
                if custom_id.startswith("area_"):
                    area_tags[custom_id] = llm_tags
                    print(f"Processed area tags for {custom_id}")
                else:
                    route_tags[custom_id] = llm_tags
                    print(f"Processed route tags for {custom_id}")
                    
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON content for {custom_id}: {e}")
                continue
                
        except Exception as e:
            print(f"Error processing result for {custom_id}: {e}")
            continue
    
    print(f"Processed {len(area_tags)} areas and {len(route_tags)} routes")
    return area_tags, route_tags

def map_category(manual_category):
    """Map manual tag categories to LLM tag categories"""
    category_mapping = {
        "Multipitch": "Multi-Pitch, Anchors & Descent",
        "Difficulty & Safety": "Difficulty & Safety"
        # Add more mappings as needed
    }
    return category_mapping.get(manual_category, manual_category)

def combine_tags(tags1, tags2):
    """Combine two sets of tags while removing duplicates"""
    # Convert inputs to lists if they're strings or other types
    def to_list(tags):
        if not tags:  # Handle None or empty
            return []
        if isinstance(tags, str):
            return [tags]
        if isinstance(tags, list):
            return tags
        if isinstance(tags, dict):
            # If it's a dict, extract values or convert the dict itself to a list item
            if 'tag' in tags:  # Handle {"tag": "some_tag", "description": "..."} format
                return [tags['tag']]
            return [tags]  # Fallback: treat the whole dict as a tag
        return [str(tags)]  # Fallback for other types
    
    # Convert both inputs to lists and flatten them
    tags1_list = to_list(tags1)
    tags2_list = to_list(tags2)
    
    # Convert to sets to remove duplicates
    # For dicts, convert to tuple of items for hashing
    def make_hashable(tag):
        if isinstance(tag, dict):
            return tuple(sorted(tag.items()))
        return tag
    
    all_tags = {make_hashable(tag) for tag in tags1_list} | {make_hashable(tag) for tag in tags2_list}
    
    # Convert back to original format
    def unmake_hashable(tag):
        if isinstance(tag, tuple):
            return dict(tag)
        return tag
    
    return [unmake_hashable(tag) for tag in all_tags]

def create_area_batch_requests(areas: List[Dict[str, Any]], prompt_template: str) -> List[Dict[str, Any]]:
    """Create batch requests for area tagging"""
    batch_requests = []
    
    for area in areas:
        input_text = f"""
Area Description: {area.get('area_description', '')}
Getting There: {area.get('area_getting_there', '')}
Access Issues: {area.get('area_access_issues', '')}
Page Views: {area.get('area_page_views', '')}
Shared On: {area.get('area_shared_on', '')}
Comments: {' '.join([c.get('comment_text', '') for c in area.get('area_comments', [])])}
"""
        request = {
            "custom_id": f"area_{area.get('area_id')}",  # Add area_ prefix
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": prompt_template},
                    {"role": "user", "content": input_text}
                ],
                "temperature": 0.3,
                "max_tokens": 500,
                "top_p": 0.95,
                "n": 1
            }
        }
        batch_requests.append(request)
    
    return batch_requests

def process_areas_and_routes(input_file: str, route_prompt_file: str, area_prompt_file: str, retrieve_only: bool = False, batch_id: str = None):
    """Process both areas and routes"""
    # Load data and prompts
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    with open(route_prompt_file, 'r') as f:
        route_prompt = f.read()
    
    with open(area_prompt_file, 'r') as f:
        area_prompt = f.read()
    
    if retrieve_only and batch_id:
        results = wait_for_batch_completion(batch_id)
        area_tags, route_tags = process_batch_results(results)
        
        # Apply manual tagging
        data = manual_tagging(data)
        
        # Update areas and routes with LLM tags
        areas_updated = 0
        routes_updated = 0
        
        for area in data:
            # Process area tags - directly use the tags
            area_id = f"area_{area.get('area_id')}"
            if area_id in area_tags:
                area['area_tags'] = area_tags[area_id]  # Use area_tags instead of llm_tags
                print(f"Added tags to area: {area_id}")
                areas_updated += 1
            else:
                print(f"No tags found for area: {area_id}")
            
            # Process route tags
            for route in area.get('routes', []):
                route_id = route.get('route_id')
                if route_id in route_tags:
                    if 'llm_tags' not in route:
                        route['llm_tags'] = {}
                    route['llm_tags'] = route_tags[route_id]
                    
                    # Combine tags
                    manual_tags = route.get('manual_tags', {})
                    llm_tags = route['llm_tags']
                    combined_tags = {}
                    combined_tags.update(llm_tags)
                    
                    for manual_category, tags in manual_tags.items():
                        llm_category = map_category(manual_category)
                        if llm_category in combined_tags:
                            existing_tags = combined_tags[llm_category]
                            combined_tags[llm_category] = combine_tags(existing_tags, tags)
                        else:
                            combined_tags[llm_category] = tags
                    
                    route['route_tags'] = combined_tags
                    routes_updated += 1
        
        print(f"Updated {areas_updated} areas and {routes_updated} routes with tags")
        
        # Write output
        output_file = input_file.replace('.json', '_tagged.json')
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Tagged data written to {output_file}")
        
        return data
    
    else:
        # Create batch requests for both areas and routes
        area_requests = create_area_batch_requests(data, area_prompt)
        route_requests = []
        for area in data:
            route_requests.extend(create_batch_requests(area.get('routes', []), route_prompt))
        
        # Combine requests
        all_requests = area_requests + route_requests
        
        if not all_requests:
            print("No items to process")
            return data
        
        # Submit batch
        batch_id = submit_batch(all_requests)
        print(f"Submitted batch with ID: {batch_id}")
        
        return data

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage:")
        print("  To submit: python route_tagging.py <input_json_file>")
        print("  To retrieve: python route_tagging.py <input_json_file> <batch_id>")
        sys.exit(1)
        
    input_file = sys.argv[1]
    route_prompt_file = "prompt/route_prompt.txt"
    area_prompt_file = "prompt/area_prompt.txt"
    
    if len(sys.argv) == 3:
        # Retrieve mode
        batch_id = sys.argv[2]
        process_areas_and_routes(input_file, route_prompt_file, area_prompt_file, retrieve_only=True, batch_id=batch_id)
    else:
        # Submit mode
        process_areas_and_routes(input_file, route_prompt_file, area_prompt_file)