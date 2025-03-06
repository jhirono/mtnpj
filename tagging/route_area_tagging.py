#!/usr/bin/env python3
import json
import sys
import re
import openai
import os
import time
from datetime import datetime
from typing import List, Dict, Any, Set
import traceback
import argparse
import shutil

# OpenAI API configuration
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI()

# Constants
MAX_BATCH_SIZE = 50000  # Batch API limit
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
LOG_FILE = "tagging_validation.log"  # Log file for tag validation

# Define allowed tags for each category
ALLOWED_TAGS = {
    "Weather & Conditions": {"sun_am", "sun_pm", "tree_filtered_sun_am", "tree_filtered_sun_pm", 
                           "sunny_all_day", "shady_all_day", "dries_fast", "dry_in_rain", 
                           "seepage_problem", "windy_exposed"},
    "Access & Restrictions": {"seasonal_closure"},  # Note: seasonal_closure_* variants are handled specially in validate_tags
    "Crowds & Popularity": {"low_crowds", "classic_route", "polished_rock", "new_routes"},
    "Difficulty & Safety": {"stick_clip", "loose_rock", "rope_drag_warning", "runout_dangerous", 
                           "sandbag", "first_in_grade"},
    "Approach & Accessibility": {"approach_none", "approach_short", "approach_moderate", 
                                "approach_long"},
    "Multi-Pitch, Anchors & Descent": {"single_pitch", "short_multipitch", "long_multipitch", "bolted_anchor", "walk_off", "tricky_rappel"},
    "Route Style & Angle": {"slab", "vertical", "gentle_overhang", "steep_roof", 
                           "tower_climbing", "sporty_trad"},
    "Crack Climbing": {"finger", "thin_hand", "wide_hand", "offwidth", "chimney", "layback"},
    "Hold & Movement Type": {"reachy", "dynamic_moves", "pumpy_sustained", "technical_moves", 
                            "powerful_bouldery", "pockets_holes", "small_edges", "slopey_holds"},
    "Rope Length": {"rope_60m", "rope_70m", "rope_80m"}
}

def log_message(message: str):
    """Log a message to both console and log file"""
    print(message)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def validate_tags(tags_dict: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    Validates tags against the allowed tags for each category.
    Removes any tags that are not in the allowed list.
    Special handling for seasonal_closure_* tags.
    """
    valid_tags = {}
    invalid_tags_found = False
    
    for category, tags in tags_dict.items():
        if category not in ALLOWED_TAGS:
            log_message(f"Warning: Category '{category}' is not in the allowed list")
            continue
            
        valid_category_tags = []
        for tag in tags:
            # Special handling for seasonal closure tags
            if category == "Access & Restrictions" and tag.startswith("seasonal_closure_"):
                valid_category_tags.append(tag)
                continue
                
            if tag in ALLOWED_TAGS[category]:
                valid_category_tags.append(tag)
            else:
                log_message(f"Warning: Removed invalid tag '{tag}' from category '{category}'")
                invalid_tags_found = True
                
        if valid_category_tags:
            valid_tags[category] = valid_category_tags
    
    if invalid_tags_found:
        log_message("Some invalid tags were removed from the results")
        
    return valid_tags

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
                if length <= 30:
                    manual_tags.setdefault("Rope Length", []).append("rope_60m")
                elif 30 < length <= 35:
                    manual_tags.setdefault("Rope Length", []).append("rope_70m")
                elif 35 < length <= 40:
                    manual_tags.setdefault("Rope Length", []).append("rope_80m")

            # Rule 2: Multipitch Tagging
            if route.get("route_pitches", 1) > 1:
                pitches = route["route_pitches"]
                if pitches < 5:
                    manual_tags.setdefault("Multi-Pitch, Anchors & Descent", []).append("short_multipitch")
                else:
                    manual_tags.setdefault("Multi-Pitch, Anchors & Descent", []).append("long_multipitch")
            else:
                # Add single_pitch tag for routes with 1 pitch
                manual_tags.setdefault("Multi-Pitch, Anchors & Descent", []).append("single_pitch")

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

def wait_for_batch_completion(batch_id, check_only=False):
    """
    Wait for batch completion and return results.
    If check_only is True, just return the batch status without waiting for completion.
    """
    print("Checking batch status...")
    max_retries = 3
    retry_count = 0
    
    # Handle comma-separated batch IDs
    if "," in batch_id:
        batch_ids = batch_id.split(",")
        log_message(f"Processing multiple batch IDs: {batch_ids}")
        
        if check_only:
            statuses = {}
            for bid in batch_ids:
                status_result = wait_for_batch_completion(bid.strip(), check_only=True)
                statuses[bid.strip()] = status_result
            return {"status": "multiple", "batch_statuses": statuses}
        
        # For actual retrieval, collect results from all batches
        all_results = []
        for bid in batch_ids:
            bid = bid.strip()
            log_message(f"Retrieving results for batch ID: {bid}")
            batch_results = wait_for_batch_completion(bid)
            if batch_results:
                log_message(f"Retrieved {len(batch_results)} results from batch {bid}")
                all_results.extend(batch_results)
            else:
                log_message(f"WARNING: No results retrieved from batch {bid}")
        
        log_message(f"Total results from all batches: {len(all_results)}")
        return all_results
    
    # Single batch ID processing
    while retry_count < max_retries:
        try:
            # Check batch status
            batch = client.batches.retrieve(batch_id)
            print(f"Batch status: {batch.status}")
            
            # If check_only, just return the batch object
            if check_only:
                return {"status": batch.status, "batch": batch}
            
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
            print(f"Error checking batch status (attempt {retry_count + 1}): {e}")
            retry_count += 1
            if retry_count >= max_retries:
                print(f"Max retries ({max_retries}) exceeded while checking batch status")
                raise
            time.sleep(RETRY_DELAY * retry_count)
    
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
                log_message(f"No content found for {custom_id}")
                continue
                
            try:
                # Parse the JSON string content
                tags_data = json.loads(response)
                llm_tags = tags_data.get("llm_tags", {})
                
                # Log the raw tags before validation
                log_message(f"Raw tags for {custom_id}: {json.dumps(llm_tags)}")
                
                # Validate the tags against allowed tags
                valid_llm_tags = validate_tags(llm_tags)
                
                # Log the validated tags
                log_message(f"Validated tags for {custom_id}: {json.dumps(valid_llm_tags)}")
                
                # Check if this is an area or route based on the ID format
                if custom_id.startswith("area_"):
                    area_tags[custom_id] = valid_llm_tags
                    log_message(f"Processed area tags for {custom_id}")
                else:
                    route_tags[custom_id] = valid_llm_tags
                    log_message(f"Processed route tags for {custom_id}")
                    
            except json.JSONDecodeError as e:
                log_message(f"Error parsing JSON content for {custom_id}: {e}")
                continue
                
        except Exception as e:
            log_message(f"Error processing result for {custom_id}: {e}")
            continue
    
    log_message(f"Processed {len(area_tags)} areas and {len(route_tags)} routes")
    return area_tags, route_tags

def map_category(manual_category):
    """Map manual tag categories to LLM tag categories"""
    # This function is kept as a placeholder for future category mappings if needed
    # Currently all manual categories match LLM categories directly
    category_mapping = {
        # Add mappings here if needed in the future
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
    """Create batch requests for the OpenAI Batch API for areas"""
    batch_requests = []
    
    for area in areas:
        input_text = f"""
Area Description: {area.get('area_description', '')}
Getting There: {area.get('area_getting_there', '')}
Access Issues: {area.get('area_access_issues', '')}
Page Views: {area.get('area_page_views', '')}
Area Share Date: {area.get('area_shared_on', '')}
Comments: {' '.join([c.get('comment_text', '') for c in area.get('area_comments', [])])}
"""
        request = {
            "custom_id": f"area_{area.get('area_id')}",
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

def inherit_approach_tags(data):
    """Inherit approach tags from areas to routes"""
    for area in data:
        area_approach_tags = []
        
        # Extract approach tags from area_tags
        if "area_tags" in area and "Approach & Accessibility" in area["area_tags"]:
            area_approach_tags = area["area_tags"]["Approach & Accessibility"]
        
        # Apply area approach tags to all routes in the area
        if area_approach_tags:
            for route in area.get("routes", []):
                if "route_tags" not in route:
                    route["route_tags"] = {}
                # Ensure route_tags is a dictionary, not a list
                elif not isinstance(route["route_tags"], dict):
                    route["route_tags"] = {}
                
                if "Approach & Accessibility" not in route["route_tags"]:
                    route["route_tags"]["Approach & Accessibility"] = []
                
                # Add area approach tags to route approach tags (avoiding duplicates)
                route_approach_tags = route["route_tags"]["Approach & Accessibility"]
                for tag in area_approach_tags:
                    if tag not in route_approach_tags:
                        route_approach_tags.append(tag)
    
    return data

def process_stick_clip_tag(data):
    """Ensure stick_clip tag is only applied to sport routes"""
    for area in data:
        for route in area.get("routes", []):
            if "route_tags" in route and "Difficulty & Safety" in route["route_tags"]:
                # Check if route is not a sport route
                if "stick_clip" in route["route_tags"]["Difficulty & Safety"]:
                    if "Sport" not in route.get("route_type", ""):
                        # Remove stick_clip tag from non-sport routes
                        route["route_tags"]["Difficulty & Safety"].remove("stick_clip")
                        log_message(f"Removed stick_clip tag from non-sport route: {route.get('route_name')}")
    
    return data

def should_process_route(route):
    """
    Determine if a route should be processed by the LLM tagger.
    Only process routes that contain 'trad' or 'sport' in their route types.
    """
    route_type = route.get("route_type", "").lower()
    return "trad" in route_type or "sport" in route_type

def process_areas_and_routes(input_file: str, route_prompt_file: str, area_prompt_file: str, retrieve_only: bool = False, batch_id: str = None):
    """Process areas and routes for tagging"""
    # Load data
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    with open(route_prompt_file, 'r') as f:
        route_prompt = f.read()
    
    with open(area_prompt_file, 'r') as f:
        area_prompt = f.read()
    
    if retrieve_only and batch_id:
        # Get batch results
        results = wait_for_batch_completion(batch_id)
        log_message(f"Retrieved {len(results)} results from batch(es)")
        
        # Process batch results
        area_tags, route_tags = process_batch_results(results)
        log_message(f"Processed {len(area_tags)} area tags and {len(route_tags)} route tags")
        
        # Create a backup of existing tagged file if it exists
        output_file = input_file.replace('.json', '_tagged.json')
        if os.path.exists(output_file):
            backup_file = f"{output_file}.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            log_message(f"Creating backup of existing tagged file: {backup_file}")
            shutil.copy2(output_file, backup_file)
            
            # If we're processing a second batch, load the existing data to merge
            log_message(f"Loading existing tagged data to merge with new results")
            with open(output_file, 'r') as f:
                try:
                    existing_data = json.load(f)
                    
                    # Preserve existing tags by merging them with our current data
                    for area_idx, area in enumerate(data):
                        area_id = area.get('area_id')
                        # Find matching area in existing data
                        for ex_area in existing_data:
                            if ex_area.get('area_id') == area_id:
                                # If area has existing tags, preserve them
                                if 'area_tags' in ex_area:
                                    if 'area_tags' not in area:
                                        area['area_tags'] = {}
                                    # Merge existing area tags with new ones
                                    if isinstance(ex_area['area_tags'], dict):
                                        for category, tags in ex_area['area_tags'].items():
                                            if category not in area['area_tags']:
                                                area['area_tags'][category] = tags
                                    elif isinstance(ex_area['area_tags'], list):
                                        # Handle case where area_tags is a list
                                        log_message(f"Found area tags as list for area {area_id}, converting to dict")
                                        # For list tags, we don't have category info, so we skip them
                                    
                                    # Process routes - preserve existing route tags
                                    for route in area.get('routes', []):
                                        route_id = route.get('route_id')
                                        # Find matching route in existing data
                                        for ex_route in ex_area.get('routes', []):
                                            if ex_route.get('route_id') == route_id:
                                                # If route has existing tags and doesn't have new ones
                                                if 'route_tags' in ex_route:
                                                    if 'route_tags' not in route:
                                                        route['route_tags'] = {}
                                                    
                                                    # Merge existing route tags with new ones
                                                    if isinstance(ex_route['route_tags'], dict):
                                                        for category, tags in ex_route['route_tags'].items():
                                                            if category not in route['route_tags']:
                                                                route['route_tags'][category] = tags
                                                    elif isinstance(ex_route['route_tags'], list):
                                                        # Handle case where route_tags is a list
                                                        log_message(f"Found route tags as list for route {route_id}, converting to dict")
                                                        # For list tags, we don't have category info, so we skip them
                                                break
                                        break
                except json.JSONDecodeError:
                    log_message(f"Warning: Existing tagged file is not valid JSON. Starting fresh.")
        
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
                log_message(f"Added tags to area: {area_id}")
                areas_updated += 1
            else:
                log_message(f"No tags found for area: {area_id}")
            
            # Process route tags
            for route in area.get('routes', []):
                route_id = route.get('route_id')
                
                # Initialize route_tags if not present
                if 'route_tags' not in route:
                    route['route_tags'] = {}
                # Ensure route_tags is a dictionary, not a list
                elif not isinstance(route['route_tags'], dict):
                    route['route_tags'] = {}
                
                # For routes that should be processed by LLM
                if should_process_route(route):
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
                            
                            # Special handling for Rope Length tags based on route_pitches
                            if llm_category == "Rope Length":
                                # For single-pitch routes, manual tags take priority
                                if route.get('route_pitches', 1) == 1:
                                    combined_tags[llm_category] = tags
                                # For multi-pitch routes, LLM tags take priority (already added)
                                continue
                            
                            # For all other categories, combine tags
                            if llm_category in combined_tags:
                                existing_tags = combined_tags[llm_category]
                                combined_tags[llm_category] = combine_tags(existing_tags, tags)
                            else:
                                combined_tags[llm_category] = tags
                        
                        route['route_tags'] = combined_tags
                        routes_updated += 1
                    else:
                        # Route should be processed but wasn't in the results
                        # Apply manual tags only
                        log_message(f"Route {route_id} should be processed but no LLM tags found")
                        manual_tags = route.get('manual_tags', {})
                        if manual_tags:
                            for manual_category, tags in manual_tags.items():
                                llm_category = map_category(manual_category)
                                if llm_category not in route['route_tags']:
                                    route['route_tags'][llm_category] = []
                                route['route_tags'][llm_category] = combine_tags(route['route_tags'].get(llm_category, []), tags)
                # For routes that don't meet the criteria, just apply manual tags
                else:
                    manual_tags = route.get('manual_tags', {})
                    if manual_tags:
                        for manual_category, tags in manual_tags.items():
                            llm_category = map_category(manual_category)
                            if llm_category not in route['route_tags']:
                                route['route_tags'][llm_category] = []
                            route['route_tags'][llm_category] = combine_tags(route['route_tags'].get(llm_category, []), tags)
        
        log_message(f"Updated {areas_updated} areas and {routes_updated} routes with tags")
        
        # Apply additional tag processing
        data = inherit_approach_tags(data)
        data = process_stick_clip_tag(data)
        
        # Count routes by type
        total_routes = 0
        sport_trad_routes = 0
        for area in data:
            for route in area.get('routes', []):
                total_routes += 1
                if should_process_route(route):
                    sport_trad_routes += 1
        
        log_message(f"Summary: Processed {sport_trad_routes}/{total_routes} routes ({sport_trad_routes/total_routes*100:.2f}% of total)")
        log_message(f"Skipped {total_routes - sport_trad_routes} routes that were not sport or trad")
        
        # Write output
        output_file = input_file.replace('.json', '_tagged.json')
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=4)
        log_message(f"Tagged data written to {output_file}")
        
        return data
    
    else:
        # Create batch requests for both areas and routes
        area_requests = create_area_batch_requests(data, area_prompt)
        route_requests = []
        total_routes = 0
        filtered_routes_count = 0
        
        for area in data:
            area_routes = area.get('routes', [])
            total_routes += len(area_routes)
            # Filter routes to only include those with trad or sport
            filtered_routes = [route for route in area_routes if should_process_route(route)]
            filtered_routes_count += len(filtered_routes)
            route_requests.extend(create_batch_requests(filtered_routes, route_prompt))
        
        log_message(f"Filtered routes: {filtered_routes_count}/{total_routes} ({filtered_routes_count/total_routes*100:.2f}% of total)")
        
        # Combine requests
        all_requests = area_requests + route_requests
        
        if not all_requests:
            log_message("No items to process")
            return data
        
        # Force splitting for large data files
        # California data is specifically known to exceed the limit
        force_split = "california" in input_file.lower() or len(all_requests) > 25000
        
        if force_split:
            log_message(f"Large batch detected with {len(all_requests)} requests")
            log_message(f"Forcing split due to known size limits for this data")
            
            # Use split_and_submit_batches to handle large batches
            batch_id = split_and_submit_batches(all_requests)
            log_message(f"Batch splitting process initiated with first batch ID: {batch_id}")
        else:
            # For smaller states, estimate if splitting is needed
            est_size_per_request = 6500  # Estimated bytes per request in the JSON file (increased for safety)
            est_total_size = len(all_requests) * est_size_per_request
            max_size = 200000000  # Conservative limit (~200MB instead of 209.7MB)
            
            if est_total_size > max_size:
                log_message(f"Large batch detected with {len(all_requests)} requests")
                log_message(f"Estimated batch size ({est_total_size} bytes) exceeds conservative limit ({max_size} bytes)")
                
                # Use split_and_submit_batches to handle large batches
                batch_id = split_and_submit_batches(all_requests)
                log_message(f"Batch splitting process initiated with first batch ID: {batch_id}")
            else:
                # Submit as a single batch for smaller requests
                log_message(f"Batch size within limits, submitting as a single batch")
                batch_id = submit_batch(all_requests)
                log_message(f"Submitted batch with ID: {batch_id}")
        
        return data

def split_and_submit_batches(batch_requests: List[Dict[str, Any]]) -> str:
    """
    Split a large batch into exactly 2 batches to handle size and token limitations:
    - Maximum file size: 209,715,200 bytes
    - Maximum tokens: 40,000,000 across all active jobs
    Returns a batch ID for the first batch.
    """
    # More conservative splitting - first batch slightly smaller than second 
    # to ensure we're well under the limit
    first_batch_size = len(batch_requests) * 2 // 5  # 40% in first batch
    second_batch_size = len(batch_requests) - first_batch_size  # 60% in second batch
    
    log_message(f"=== BATCH SPLITTING ===")
    log_message(f"Splitting {len(batch_requests)} requests into exactly 2 batches:")
    log_message(f"First batch: {first_batch_size} requests (40%)")
    log_message(f"Second batch: {second_batch_size} requests (60%)")
    
    # Create exactly 2 batches
    first_batch = batch_requests[:first_batch_size]
    second_batch = batch_requests[first_batch_size:]
    
    # Submit only the first batch
    log_message(f"=== SUBMITTING FIRST BATCH ===")
    log_message(f"Submitting first batch with {len(first_batch)} requests")
    first_batch_id = submit_batch(first_batch)
    log_message(f"First batch submitted with ID: {first_batch_id}")
    
    # Save information about the second batch for later submission
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pending_batches_file = f"pending_batches_{timestamp}.json"
    
    with open(pending_batches_file, "w") as f:
        pending_data = {
            "first_batch_id": first_batch_id,
            "remaining_batches": [second_batch],
            "timestamp": timestamp
        }
        json.dump(pending_data, f)
    
    log_message(f"=== NEXT STEPS ===")
    log_message(f"First batch submitted with {len(first_batch)} requests.")
    log_message(f"Second batch with {len(second_batch)} requests saved to {pending_batches_file}")
    log_message(f"The system will wait for the first batch to COMPLETE before submitting the second one.")
    log_message(f"To continue with the second batch after the first one completes, run:")
    log_message(f"python tagging/route_area_tagging.py --continue-batch {pending_batches_file}")
    
    return first_batch_id

def continue_pending_batches(pending_batches_file: str) -> str:
    """
    Continue processing the second batch after the first batch has completed.
    Waits for the first batch to complete successfully before submitting the second one.
    """
    try:
        # Load the pending batches information
        with open(pending_batches_file, 'r') as f:
            pending_data = json.load(f)
        
        first_batch_id = pending_data.get("first_batch_id")
        remaining_batches = pending_data.get("remaining_batches", [])
        
        if not first_batch_id or not remaining_batches:
            log_message("Invalid pending batches file or no remaining batches")
            return None
        
        # Check if the first batch is complete
        log_message(f"=== BATCH STATUS CHECK ===")
        log_message(f"Checking status of first batch {first_batch_id}...")
        
        # Wait for the batch to complete (not just check)
        log_message(f"Waiting for first batch {first_batch_id} to complete. This may take some time.")
        results = wait_for_batch_completion(first_batch_id)
        
        if not results:
            log_message(f"ERROR: First batch {first_batch_id} failed or was cancelled")
            log_message("Please check the OpenAI dashboard for more details")
            return None
        
        log_message(f"SUCCESS: First batch {first_batch_id} completed successfully!")
        log_message(f"Retrieved {len(results)} results from the first batch")
        
        # Submit the second batch immediately
        log_message(f"=== SUBMITTING SECOND BATCH ===")
        log_message(f"Proceeding to submit the second batch immediately...")
        
        # Submit the second batch
        second_batch = remaining_batches[0]
        second_batch_id = submit_batch(second_batch)
        log_message(f"Second batch submitted with ID: {second_batch_id}")
        log_message(f"All batches have been submitted!")
        
        return second_batch_id
    
    except Exception as e:
        log_message(f"Error continuing with second batch: {e}")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Process areas and routes for tagging")
    parser.add_argument("input_file", nargs="?", help="JSON file containing areas and routes data")
    parser.add_argument("batch_id", nargs="?", help="Batch ID to retrieve results (optional, for retrieve mode)")
    parser.add_argument("--check", action="store_true", help="Check batch status without waiting")
    parser.add_argument("--batch-only", action="store_true", help="Only retrieve a specific batch, don't process results")
    parser.add_argument("--continue-batch", help="Continue processing pending batches from a previous split operation")
    
    args = parser.parse_args()
    
    # Handle continue-batch mode
    if args.continue_batch:
        log_message(f"Continuing with pending batches from {args.continue_batch}")
        continue_pending_batches(args.continue_batch)
        sys.exit(0)
    
    if not args.input_file:
        parser.print_help()
        sys.exit(1)
    
    input_file = args.input_file
    route_prompt_file = "prompt/route_prompt.txt"
    area_prompt_file = "prompt/area_prompt.txt"
    
    # Validate input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' does not exist.")
        sys.exit(1)
    
    # Validate prompt files exist
    if not os.path.exists(route_prompt_file):
        print(f"Error: Route prompt file '{route_prompt_file}' does not exist.")
        sys.exit(1)
    
    if not os.path.exists(area_prompt_file):
        print(f"Error: Area prompt file '{area_prompt_file}' does not exist.")
        sys.exit(1)
    
    try:
        if args.batch_id:
            # Retrieve mode
            if args.check:
                # Just check batch status
                log_message(f"Checking status for batch ID(s): {args.batch_id}")
                wait_for_batch_completion(args.batch_id, check_only=True)
            elif args.batch_only:
                # Just retrieve batch results
                log_message(f"Retrieving results for batch ID(s): {args.batch_id}")
                results = wait_for_batch_completion(args.batch_id)
                if results:
                    log_message(f"Retrieved {len(results)} results")
                    # Save raw results to file
                    output_file = f"batch_results_{args.batch_id.replace(',', '_')}.json"
                    with open(output_file, 'w') as f:
                        json.dump(results, f, indent=4)
                    log_message(f"Raw results saved to {output_file}")
            else:
                # Retrieve and process
                log_message(f"Running in retrieve mode with batch ID(s): {args.batch_id}")
                process_areas_and_routes(input_file, route_prompt_file, area_prompt_file, retrieve_only=True, batch_id=args.batch_id)
        else:
            # Submit mode
            log_message(f"Running in submit mode with input file: {input_file}")
            process_areas_and_routes(input_file, route_prompt_file, area_prompt_file)
    except Exception as e:
        log_message(f"Error processing batch: {str(e)}")
        traceback.print_exc()
        sys.exit(1)