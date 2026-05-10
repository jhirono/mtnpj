#!/usr/bin/env python3
"""
benchmark_models.py — Compare gpt-4o-mini, gpt-5-nano, and gpt-5-mini on a 50-route sample.

Submits 3 batch jobs to the OpenAI Batch API (one per model), polls until all complete,
then writes benchmark_results.json with per-route tag comparison for user review.

Usage:
    cd /Users/jhirono/Dev/mtnpj
    python3 -m tagging.benchmark_models

Requires OPENAI_API_KEY environment variable.
"""

import json
import os
import sys
import time
import random
from datetime import datetime
from typing import List, Dict, Any, Optional

import openai

# OpenAI API configuration
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI()

# Constants
BENCHMARK_MODELS = ["gpt-4o-mini", "gpt-5-nano", "gpt-5-mini"]
SAMPLE_SIZE = 50
OUTPUT_FILE = "benchmark_results.json"
ENRICHED_INPUT = "data/yosemite-national-park_routes_enriched.json"
FALLBACK_INPUT = "data/yosemite-national-park_routes.json"
PROMPT_FILE = "prompt/route_prompt.txt"

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
POLL_INTERVAL = 10  # seconds


# ---------------------------------------------------------------------------
# Sample selection
# ---------------------------------------------------------------------------

def select_sample(data: list, size: int = SAMPLE_SIZE) -> list:
    """
    Flatten all routes from all areas and return a reproducible 50-route sample.
    Ensures mix of routes with and without tick comments (D-02).
    """
    random.seed(42)

    # Flatten areas -> routes
    all_routes = []
    for area in data:
        routes = area.get("routes", [])
        all_routes.extend(routes)

    routes_with_ticks = [r for r in all_routes if r.get("route_tick_comments")]
    routes_without = [r for r in all_routes if not r.get("route_tick_comments")]

    tick_count = min(25, len(routes_with_ticks))
    no_tick_count = size - tick_count

    sample = random.sample(routes_with_ticks, tick_count)
    sample += random.sample(routes_without, min(no_tick_count, len(routes_without)))

    # Shuffle combined sample for variety
    random.shuffle(sample)
    return sample[:size]


# ---------------------------------------------------------------------------
# Batch request creation
# ---------------------------------------------------------------------------

def create_batch_requests_for_model(routes: list, prompt_template: str, model: str) -> list:
    """
    Build OpenAI Batch API request list for a specific model.
    custom_id is prefixed with model name so results from different models
    can be unambiguously identified.
    """
    batch_requests = []

    for route in routes:
        route_id = str(route.get("route_id"))
        input_text = f"""
Route Description: {route.get('route_description', '')}
Route Location: {route.get('route_location', '')}
Route Type: {route.get('route_type', '')}
Route Protection: {route.get('route_protection', '')}
Comments: {route.get('route_tick_comments', '')} {' '.join([c.get('comment_text', '') for c in route.get('route_comments', [])])}
"""
        # gpt-5 models are reasoning models: they burn tokens on internal reasoning
        # before producing visible output. 500 tokens is too small (all goes to
        # reasoning, content is empty). 1500 gives ~200 reasoning + ~300 output.
        # temperature/top_p are also unsupported for gpt-5 models.
        is_gpt5 = model.startswith("gpt-5")
        body: dict = {
            "model": model,
            "messages": [
                {"role": "system", "content": prompt_template},
                {"role": "user", "content": input_text},
            ],
            "max_completion_tokens": 1500 if is_gpt5 else 500,
            "n": 1,
        }
        if not is_gpt5:
            body["temperature"] = 0.3
            body["top_p"] = 0.95
        request = {
            "custom_id": f"{model}__{route_id}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": body,
        }
        batch_requests.append(request)

    return batch_requests


# ---------------------------------------------------------------------------
# Batch submission
# ---------------------------------------------------------------------------

def _submit_raw(batch_requests: list, retry_count: int = 0) -> str:
    """
    Write JSONL, upload to OpenAI Files API, create batch job.
    Returns batch.id string.
    Raises on unrecoverable error after MAX_RETRIES.

    NOTE: Does NOT catch PermissionDeniedError — callers handle that.
    """
    if retry_count >= MAX_RETRIES:
        raise Exception("Max retries exceeded while trying to submit batch")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_file = f"batch_input_{timestamp}.jsonl"

    try:
        with open(batch_file, "w") as f:
            for request in batch_requests:
                f.write(json.dumps(request) + "\n")

        with open(batch_file, "rb") as f:
            uploaded = client.files.create(file=f, purpose="batch")

        # PermissionDeniedError may raise here — propagate to caller
        batch = client.batches.create(
            input_file_id=uploaded.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
        )
        return batch.id

    except openai.PermissionDeniedError:
        # Re-raise so submit_batch_for_model can handle gracefully
        raise

    except Exception as e:
        print(f"Error during batch submission (attempt {retry_count + 1}): {e}")
        time.sleep(RETRY_DELAY * (retry_count + 1))
        return _submit_raw(batch_requests, retry_count + 1)

    finally:
        if os.path.exists(batch_file):
            os.remove(batch_file)


def submit_batch_for_model(batch_requests: list, model: str) -> Optional[str]:
    """
    Submit a batch for the given model. Returns batch_id on success, None on 403.
    Gracefully handles openai.PermissionDeniedError (expected for gpt-5-mini in some accounts).
    Fallback snapshot: 'gpt-5-mini-2025-08-07'
    """
    try:
        batch_id = _submit_raw(batch_requests)
        print(f"[OK] Submitted batch for {model}: {batch_id}")
        return batch_id
    except openai.PermissionDeniedError:
        print(
            f"[WARNING] {model} batch access denied (403). "
            f"Try snapshot ID 'gpt-5-mini-2025-08-07' or create a new API project."
        )
        print("Benchmark will continue with remaining models. "
              f"{model} result will be missing.")
        return None


# ---------------------------------------------------------------------------
# Batch polling
# ---------------------------------------------------------------------------

def wait_for_batch_completion(batch_id: str) -> Optional[list]:
    """
    Poll until batch.status == 'completed', then return parsed results list.
    Returns None on unrecoverable failure.
    """
    print(f"Polling batch {batch_id}...")
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            batch = client.batches.retrieve(batch_id)
            print(f"  Status: {batch.status}")

            if batch.status == "completed":
                output_file_id = batch.output_file_id
                if not output_file_id:
                    raise Exception("No output_file_id in completed batch")
                response = client.files.content(output_file_id)
                results = []
                for line in response.text.splitlines():
                    if not line.strip():
                        continue
                    try:
                        results.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        print(f"  [WARN] Could not parse JSONL line: {e}")
                print(f"  Loaded {len(results)} results from batch {batch_id}")
                return results

            elif batch.status in ("failed", "expired", "cancelled"):
                raise Exception(f"Batch ended with status: {batch.status}")

            # Still processing — wait and loop
            time.sleep(POLL_INTERVAL)

        except Exception as e:
            retry_count += 1
            print(f"  Error checking batch (attempt {retry_count}): {e}")
            if retry_count >= max_retries:
                print(f"  Max retries exceeded for batch {batch_id}")
                return None
            time.sleep(RETRY_DELAY * retry_count)

    return None


# ---------------------------------------------------------------------------
# Result parsing
# ---------------------------------------------------------------------------

def parse_tags_from_result(result: dict) -> dict:
    """
    Extract parsed tag dict from a single batch result entry.
    Mirrors process_batch_results() in route_area_tagging.py.
    Returns {"error": "parse_failed"} on any failure.
    """
    try:
        content = (
            result.get("response", {})
            .get("body", {})
            .get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        if not content:
            return {"error": "empty_content"}
        # T-03-05 mitigation: wrap json.loads in try/except JSONDecodeError
        return json.loads(content)
    except json.JSONDecodeError:
        return {"error": "parse_failed"}
    except Exception:
        return {"error": "parse_failed"}


# ---------------------------------------------------------------------------
# Core benchmark orchestration
# ---------------------------------------------------------------------------

def run_benchmark(data: list, prompt_template: str) -> dict:
    """
    1. Sample 50 routes.
    2. Submit one batch per model.
    3. Poll all batches to completion.
    4. Return {model: results_list | None}.
    """
    sample = select_sample(data, SAMPLE_SIZE)
    tick_count = sum(1 for r in sample if r.get("route_tick_comments"))
    print(f"\nSample: {len(sample)} routes — {tick_count} with ticks, "
          f"{len(sample) - tick_count} without ticks\n")

    batch_ids: Dict[str, Optional[str]] = {}

    for model in BENCHMARK_MODELS:
        print(f"--- Submitting batch for {model} ---")
        requests = create_batch_requests_for_model(sample, prompt_template, model)
        batch_id = submit_batch_for_model(requests, model)
        batch_ids[model] = batch_id

    print("\nAll batches submitted. IDs:")
    for model, bid in batch_ids.items():
        print(f"  {model}: {bid or 'SKIPPED (403)'}")

    print("\nPolling for completion (this may take 5-15 minutes)...\n")

    results: Dict[str, Optional[list]] = {}
    for model, batch_id in batch_ids.items():
        if batch_id is None:
            results[model] = None
            continue
        model_results = wait_for_batch_completion(batch_id)
        results[model] = model_results

    return results, sample


def write_comparison(sample: list, results: dict, output_path: str) -> None:
    """
    Write side-by-side comparison JSON for user review.
    """
    comparison = []

    for route in sample:
        route_id = str(route.get("route_id"))
        entry = {
            "route_id": route_id,
            "route_name": route.get("route_name", ""),
            "route_type": route.get("route_type", ""),
            "has_ticks": bool(route.get("route_tick_comments")),
            "models": {},
        }

        for model, model_results in results.items():
            if model_results is None:
                entry["models"][model] = {"error": "PermissionDeniedError (403)"}
            else:
                match = next(
                    (r for r in model_results
                     if r.get("custom_id") == f"{model}__{route_id}"),
                    None,
                )
                entry["models"][model] = (
                    parse_tags_from_result(match) if match else {"error": "no result"}
                )

        comparison.append(entry)

    with open(output_path, "w") as f:
        json.dump(comparison, f, indent=2)

    print(f"\nBenchmark results written to {output_path} — review and select winning model")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    # Security: verify API key present (T-03-04 mitigation — never log the key value)
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable is not set.")
        print("Set it with: export OPENAI_API_KEY=<your-key>")
        sys.exit(1)

    # Input file selection
    input_file = ENRICHED_INPUT if os.path.exists(ENRICHED_INPUT) else FALLBACK_INPUT
    print(f"Using input: {input_file}")

    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)

    # Load prompt template
    if not os.path.exists(PROMPT_FILE):
        print(f"Error: Prompt file not found: {PROMPT_FILE}")
        print("Run from the project root: cd /Users/jhirono/Dev/mtnpj")
        sys.exit(1)

    with open(PROMPT_FILE, "r") as f:
        prompt_template = f.read()

    # Load route data
    with open(input_file, "r") as f:
        data = json.load(f)

    # Estimate sample composition before submitting
    all_routes = [r for area in data for r in area.get("routes", [])]
    routes_with_ticks = [r for r in all_routes if r.get("route_tick_comments")]
    print(f"Total routes available: {len(all_routes)}")
    print(f"  With tick comments:    {len(routes_with_ticks)}")
    print(f"  Without tick comments: {len(all_routes) - len(routes_with_ticks)}")
    print(f"\nModels to benchmark: {BENCHMARK_MODELS}")
    print(f"Sample size: {SAMPLE_SIZE} routes")
    print(f"Estimated cost: < $0.05 total across all models\n")

    # Run benchmark
    results, sample = run_benchmark(data, prompt_template)

    # Write output
    write_comparison(sample, results, OUTPUT_FILE)

    print("\nDone. Next step:")
    print("  1. Review benchmark_results.json")
    print("  2. Select winning model: gpt-4o-mini | gpt-5-nano | gpt-5-mini")
    print("  3. Report selection to proceed with Wave 2 (Plan 03-03)")


if __name__ == "__main__":
    main()
