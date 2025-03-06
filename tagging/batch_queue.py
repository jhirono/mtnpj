#!/usr/bin/env python3
import os
import sys
import time
import json
import argparse
from typing import List, Dict, Any
from datetime import datetime
import route_area_tagging as rat
import glob

# Constants
QUEUE_FILE = "batch_queue.json"
STATUS_FILE = "batch_status.json"
SLEEP_INTERVAL = 300  # 5 minutes between status checks

def log_message(message: str):
    """Log a message to both console and log file"""
    print(message)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(rat.LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def save_queue(queue: List[Dict[str, Any]]):
    """Save the current queue to a file"""
    with open(QUEUE_FILE, "w") as f:
        json.dump(queue, f, indent=4)

def load_queue() -> List[Dict[str, Any]]:
    """Load the queue from a file"""
    if not os.path.exists(QUEUE_FILE):
        return []
    with open(QUEUE_FILE, "r") as f:
        return json.load(f)

def save_status(status: Dict[str, Any]):
    """Save the current status to a file"""
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f, indent=4)

def load_status() -> Dict[str, Any]:
    """Load the status from a file"""
    if not os.path.exists(STATUS_FILE):
        return {"current_batch": None, "completed_batches": [], "failed_batches": []}
    with open(STATUS_FILE, "r") as f:
        return json.load(f)

def add_to_queue(input_files: List[str]):
    """Add input files to the processing queue"""
    queue = load_queue()
    
    # Add new files to queue if not already present
    for input_file in input_files:
        if not os.path.exists(input_file):
            log_message(f"Warning: File {input_file} does not exist, skipping")
            continue
            
        # Check if already in queue
        if any(item["input_file"] == input_file for item in queue):
            log_message(f"File {input_file} is already in the queue, skipping")
            continue
            
        # Add to queue
        queue.append({
            "input_file": input_file,
            "status": "pending",
            "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "route_prompt_file": "prompt/route_prompt.txt",
            "area_prompt_file": "prompt/area_prompt.txt"
        })
        log_message(f"Added {input_file} to the processing queue")
    
    save_queue(queue)
    log_message(f"Queue updated with {len(input_files)} new files. Total queue size: {len(queue)}")

def is_batch_running(batch_id: str) -> bool:
    """
    Check if a batch is still running
    Can handle single batch ID or comma-separated multiple batch IDs
    """
    try:
        # If it's multiple batch IDs
        if "," in batch_id:
            batch_ids = batch_id.split(",")
            log_message(f"Checking status of {len(batch_ids)} batches")
            
            # Check each batch ID
            for single_id in batch_ids:
                log_message(f"Checking batch {single_id}")
                # Use the retrieve_batch_status function to get status
                status = retrieve_batch_status(single_id)
                if status == "in_progress":
                    return True
                elif status == "failed" or status == "cancelled":
                    log_message(f"Batch {single_id} failed or was cancelled")
            
            # If we get here, none of the batches are running
            return False
        else:
            # Get batch status
            status = retrieve_batch_status(batch_id)
            return status == "in_progress"
            
    except Exception as e:
        log_message(f"Error checking batch status: {e}")
        return False

def retrieve_batch_status(batch_id):
    """Get the status of a batch directly from the API"""
    try:
        # Import rat only when needed to avoid circular imports
        import route_area_tagging as rat
        
        # Get the batch from the API
        batch = rat.client.batches.retrieve(batch_id)
        log_message(f"Batch {batch_id} status: {batch.status}")
        return batch.status
    except Exception as e:
        log_message(f"Error retrieving batch status: {e}")
        return "unknown"

def check_pending_batches():
    """Check for pending batch files and process them if the first batch is complete"""
    # Look for pending_batches_*.json files
    pending_files = glob.glob("pending_batches_*.json")
    
    if not pending_files:
        return False
    
    log_message(f"Found {len(pending_files)} pending batch files")
    
    for pending_file in pending_files:
        try:
            # Try to continue the pending batches
            result = rat.continue_pending_batches(pending_file)
            if result:
                # Successfully continued, no need to check others
                return True
        except Exception as e:
            log_message(f"Error processing pending batch file {pending_file}: {e}")
    
    return False

def process_queue():
    """Process the queue, one item at a time"""
    # First check if there are any pending batches to continue
    if check_pending_batches():
        log_message("Successfully continued a pending batch. Will check queue again later.")
        return
    
    queue = load_queue()
    status = load_status()
    
    # Check if there's a current batch running
    if status["current_batch"]:
        batch_id = status["current_batch"]["batch_id"]
        input_file = status["current_batch"]["input_file"]
        
        log_message(f"Checking status of current batch {batch_id} for {input_file}")
        
        batch_status = retrieve_batch_status(batch_id)
        if batch_status == "in_progress":
            log_message(f"Batch {batch_id} is still running. Waiting...")
            return
        elif batch_status == "failed" or batch_status == "cancelled":
            log_message(f"Batch {batch_id} has {batch_status}. Updating status and moving to next item.")
            # Mark as failed
            status["failed_batches"].append({
                "batch_id": batch_id,
                "input_file": input_file,
                "error": f"Batch status: {batch_status}",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            status["current_batch"] = None
            save_status(status)
            
            # Update queue
            for item in queue:
                if item["input_file"] == input_file:
                    item["status"] = "failed"
                    item["error"] = f"Batch status: {batch_status}"
            save_queue(queue)
            return
        elif batch_status == "completed":
            # Batch is complete, process the results
            log_message(f"Batch {batch_id} is complete. Processing results...")
            try:
                # Process the results
                rat.process_areas_and_routes(
                    input_file=status["current_batch"]["input_file"],
                    route_prompt_file=status["current_batch"]["route_prompt_file"],
                    area_prompt_file=status["current_batch"]["area_prompt_file"],
                    retrieve_only=True,
                    batch_id=batch_id
                )
                
                # Update status
                status["completed_batches"].append(status["current_batch"])
                status["current_batch"] = None
                save_status(status)
                
                # Update queue
                for item in queue:
                    if item["input_file"] == input_file:
                        item["status"] = "completed"
                        save_queue(queue)
                        break
                        
                log_message(f"Processed batch {batch_id} for {input_file}")
            except Exception as e:
                log_message(f"Error processing batch results: {e}")
                # Mark as failed
                status["failed_batches"].append({
                    "batch_id": batch_id,
                    "input_file": input_file,
                    "error": str(e),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                status["current_batch"] = None
                save_status(status)
                
                # Update queue
                for item in queue:
                    if item["input_file"] == input_file:
                        item["status"] = "failed"
                        item["error"] = str(e)
                save_queue(queue)
        else:
            log_message(f"Unexpected batch status: {batch_status}. Waiting for status update...")
            return
    
    # If no current batch, start the next one
    if not status["current_batch"]:
        # Find the next pending item
        next_item = next((item for item in queue if item["status"] == "pending"), None)
        
        if next_item:
            input_file = next_item["input_file"]
            log_message(f"Starting new batch for {input_file}")
            
            try:
                # Submit the batch
                data = rat.process_areas_and_routes(
                    input_file=input_file,
                    route_prompt_file=next_item["route_prompt_file"],
                    area_prompt_file=next_item["area_prompt_file"]
                )
                
                # Get the batch ID from the log file (this is a bit hacky)
                with open(rat.LOG_FILE, "r") as f:
                    log_lines = f.readlines()
                
                # Find the most recent batch ID
                batch_id = None
                for line in reversed(log_lines):
                    if "Submitted batch with ID:" in line:
                        batch_id = line.split("Submitted batch with ID:")[1].strip()
                        break
                
                if not batch_id:
                    raise Exception("Could not find batch ID in log file")
                
                # Update status
                status["current_batch"] = {
                    "batch_id": batch_id,
                    "input_file": input_file,
                    "route_prompt_file": next_item["route_prompt_file"],
                    "area_prompt_file": next_item["area_prompt_file"],
                    "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                save_status(status)
                
                # Update queue
                next_item["status"] = "processing"
                next_item["batch_id"] = batch_id
                save_queue(queue)
                
                log_message(f"Successfully submitted batch {batch_id} for {input_file}")
            except Exception as e:
                log_message(f"Error submitting batch: {e}")
                next_item["status"] = "failed"
                next_item["error"] = str(e)
                save_queue(queue)
        else:
            log_message("No pending items in the queue")

def run_queue_processor():
    """Run the queue processor continuously"""
    log_message("Starting queue processor")
    
    # Check for pending batches and queue items every minute
    PENDING_CHECK_INTERVAL = 60  # 1 minute
    last_check_time = 0
    
    while True:
        try:
            current_time = time.time()
            
            # Always check for pending batches
            pending_batch_processed = check_pending_batches()
            
            # Only process the queue if we didn't just process a pending batch
            # and if it's time for a full queue check
            if not pending_batch_processed and current_time - last_check_time >= SLEEP_INTERVAL:
                process_queue()
                last_check_time = current_time
                log_message(f"Next full queue check in {SLEEP_INTERVAL} seconds")
            elif pending_batch_processed:
                # If we processed a pending batch, wait a bit before checking again
                log_message(f"Processed a pending batch, checking again in {PENDING_CHECK_INTERVAL} seconds")
                time.sleep(PENDING_CHECK_INTERVAL)
            else:
                # If we're just waiting for the next full check
                remaining_time = SLEEP_INTERVAL - (current_time - last_check_time)
                log_message(f"Checking for pending batches in {PENDING_CHECK_INTERVAL} seconds, full queue check in {remaining_time:.0f} seconds")
                time.sleep(PENDING_CHECK_INTERVAL)
                
        except Exception as e:
            log_message(f"Error in queue processor: {e}")
            time.sleep(PENDING_CHECK_INTERVAL)

def main():
    parser = argparse.ArgumentParser(description="Batch queue processor for route tagging")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Add files to the queue")
    add_parser.add_argument("files", nargs="+", help="Input files to process")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run the queue processor")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show queue status")
    
    args = parser.parse_args()
    
    if args.command == "add":
        add_to_queue(args.files)
    elif args.command == "run":
        run_queue_processor()
    elif args.command == "status":
        queue = load_queue()
        status = load_status()
        
        print("\n=== BATCH QUEUE STATUS ===\n")
        
        print("Current Batch:")
        if status["current_batch"]:
            print(f"  File: {status['current_batch']['input_file']}")
            print(f"  Batch ID: {status['current_batch']['batch_id']}")
            print(f"  Started: {status['current_batch']['started_at']}")
        else:
            print("  None")
        
        print("\nQueue:")
        for i, item in enumerate(queue):
            print(f"  {i+1}. {item['input_file']} - {item['status']}")
            if item.get("error"):
                print(f"     Error: {item['error']}")
        
        print(f"\nCompleted Batches: {len(status['completed_batches'])}")
        print(f"Failed Batches: {len(status['failed_batches'])}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 