#!/bin/bash

# Process California data using optimized 2-batch approach
# Usage: ./process_california.sh

# Set the directory
cd "$(dirname "$0")/.."

# Activate the existing virtual environment
source venv/bin/activate

# Add only California to the queue
echo "Adding California data to the queue..."
python tagging/batch_queue.py add data/california_routes.json

# Start the queue processor in the background
echo "Starting queue processor..."
nohup python tagging/batch_queue.py run > california_tagging_queue.log 2>&1 &
QUEUE_PID=$!
echo "Queue processor started with PID $QUEUE_PID. Logs will be written to california_tagging_queue.log"
echo "The queue processor will now handle the batches sequentially using the optimized 2-batch approach."
echo ""
echo "IMPORTANT NOTES:"
echo "1. To check queue status: python tagging/batch_queue.py status"
echo "2. To check for pending batches: ls pending_batches_*.json"
echo "3. To manually continue the second batch after the first completes: python tagging/route_area_tagging.py --continue-batch <pending_batch_file>"
echo "4. To stop the queue processor: kill $QUEUE_PID"
echo ""
echo "The system will:"
echo "- Split the California data into exactly 2 equal batches to satisfy size limits"
echo "- Process the first batch completely before submitting the second one"
echo "- Wait for both batches to complete before processing the next state in the queue" 