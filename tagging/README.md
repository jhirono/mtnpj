# Climbing Route Tagging System Technical Documentation

## Overview

The Route Area Tagging System is a Python-based application that processes climbing route and area data, enriching it with AI-generated tags by utilizing OpenAI's API. The system handles large datasets efficiently by implementing batch processing, rate limiting, automatic tag validation, and hierarchical tag inheritance.

## System Architecture

The system consists of several components:

1. **Tagging Engine**: Core tagging functionality to process routes and areas
2. **Batch Processing**: Manages API batches, handling splitting, and sequential execution
3. **Tag Validation**: Ensures tags conform to an allowed set
4. **Tag Inheritance**: Propagates area-level tags to routes
5. **Queue Management**: Handles a queue of areas to process sequentially

## Key Files

- **route_area_tagging.py**: Main processing script containing tagging logic
- **batch_queue.py**: Queue management for processing multiple areas in sequence
- **process_all_areas.sh**: Helper script to add all areas to the queue
- **process_california.sh**: Helper script to process only California data

## Main Workflows

### 1. Submit Mode

When run in submit mode (`python route_area_tagging.py <input_json_file>`), the system:

1. Loads areas and routes from the input file
2. Filters routes to only include sport and trad routes
3. Creates area and route batch requests for OpenAI's API
4. Submits the batch (splitting if necessary)
5. Returns a batch ID for later retrieval

### 2. Retrieve Mode

When run in retrieve mode (`python route_area_tagging.py <input_json_file> <batch_id>`), the system:

1. Loads areas and routes from the input file
2. Retrieves batch results from OpenAI's API
3. Validates tags against allowed sets
4. Applies manual tags
5. Inherits tags from areas to routes
6. Saves the tagged data to a new file

### 3. Batch Queue Processing

When using the batch queue (`python batch_queue.py run`), the system:

1. Checks for ongoing batches
2. Processes each area sequentially
3. Handles pending batches automatically
4. Provides status updates on batch processing

## Core Components

### Tag Categories and Allowed Tags

The system defines allowed tags for various categories:

```python
ALLOWED_TAGS = {
    "Weather & Conditions": {"sun_am", "sun_pm", ...},
    "Access & Restrictions": {"seasonal_closure"},
    "Crowds & Popularity": {"low_crowds", "classic_route", ...},
    "Difficulty & Safety": {"stick_clip", "loose_rock", ...},
    "Approach & Accessibility": {"approach_none", "approach_short", ...},
    "Multi-Pitch, Anchors & Descent": {"single_pitch", "bolted_anchor", ...},
    "Route Style & Angle": {"slab", "vertical", ...},
    "Crack Climbing": {"finger", "thin_hand", ...},
    "Hold & Movement Type": {"reachy", "dynamic_moves", ...},
    "Rope Length": {"rope_60m", "rope_70m", "rope_80m"}
}
```

### Batch Processing and Splitting

The system intelligently handles large batches by:

1. Estimating batch size based on request count
2. Automatically splitting batches that exceed OpenAI's limits
3. Processing batches sequentially to avoid rate limits
4. Tracking batch status for continued processing

```
Split Algorithm:
- First Batch: 40% of requests
- Second Batch: 60% of requests
```

### Tag Inheritance Logic

The system implements a hierarchical tag inheritance model where routes inherit certain tags from their parent areas:

- Weather & Conditions
- Access & Restrictions
- Approach & Accessibility

This ensures consistency and reduces redundancy in tagging.

## Key Functions

### `process_areas_and_routes`

Main function that orchestrates the tagging process for areas and routes.

**Parameters:**
- `input_file`: JSON file containing areas and routes data
- `route_prompt_file`: File containing the prompt for route tagging
- `area_prompt_file`: File containing the prompt for area tagging
- `retrieve_only`: Whether to only retrieve batch results (default: False)
- `batch_id`: Batch ID for retrieval mode (default: None)

### `validate_tags`

Validates tags against the allowed tags for each category, removing invalid tags.

**Special Handling:**
- `seasonal_closure_*` tags: Allows dynamic variants for seasonal closures

### `inherit_area_tags`

Propagates area-level tags to routes for specific categories.

**Categories Inherited:**
- Weather & Conditions
- Access & Restrictions
- Approach & Accessibility

### `split_and_submit_batches`

Splits large batches into smaller ones to avoid OpenAI's size limits.

**Strategy:**
- Splits into exactly 2 batches (40%/60% distribution)
- Submits first batch immediately
- Saves remaining batch for later processing

### `continue_pending_batches`

Continues processing pending batches after the first batch completes.

**Process:**
1. Checks if first batch is complete
2. Submits next batch when ready
3. Saves any remaining batches for future processing

## Batch Queue System

The batch queue system manages the sequential processing of multiple areas:

### `process_queue`

Processes the queue by:
1. Checking for pending batches
2. Monitoring current batch status
3. Moving to the next area when complete

### `run_queue_processor`

Runs the queue processor continuously:
1. Checks for pending batches every minute
2. Performs full queue check at longer intervals
3. Provides status updates during processing

## Command-Line Interface

The system provides a command-line interface with several options:

```
python route_area_tagging.py <input_file> [batch_id] [--check] [--batch-only] [--continue-batch FILE]
```

**Options:**
- `input_file`: JSON file containing areas and routes data
- `batch_id`: Batch ID to retrieve results (optional)
- `--check`: Check batch status without waiting
- `--batch-only`: Only retrieve batch results without processing
- `--continue-batch`: Continue processing pending batches

## Error Handling

The system implements robust error handling:

1. Batch size validation and automatic splitting
2. Retry logic for API failures
3. Validation of input files
4. Protection against quota limits
5. Recovery from batch failures

## Tag Validation and Special Cases

### Tag Validation Rules

1. Only allows tags defined in `ALLOWED_TAGS`
2. Has special handling for `seasonal_closure_*` tags
3. Logs and removes invalid tags

### Special Tag Handling

- **`stick_clip`**: Only applied to Sport routes, removed from Trad routes
- **`seasonal_closure_*`**: Accepts dynamic variants with specific reasons

## Data Flow

1. **Input**: JSON file with areas and routes
2. **Processing**: Tag validation, batch processing, AI tagging
3. **Inheritance**: Area tags propagate to routes
4. **Output**: Tagged JSON file with validated tags

## Performance Considerations

1. Batch splitting to manage file size limits (209MB max)
2. Sequential processing to avoid token-per-minute limits
3. Intelligent filtering to reduce unnecessary API calls
4. Efficient tag validation for large datasets

## Future Extensions

Possible extensions to the system include:

1. Support for more tag categories
2. Enhanced validation rules
3. Integration with a web interface
4. More sophisticated tag inheritance models
5. Improved batch size estimation

## Troubleshooting

Common issues and resolutions:

1. **Batch Size Errors**: Use `--continue-batch` to process remaining batches
2. **Rate Limit Errors**: Wait for current batch to complete before submitting next
3. **Tag Validation Errors**: Check logs for details on invalid tags
4. **Queue Processing Issues**: Use status command to check queue state

## Conclusion

The Route Area Tagging System provides a robust solution for processing and tagging climbing routes and areas. Its architecture handles large datasets efficiently while ensuring tag validity and consistency through inheritance. 