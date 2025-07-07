#!/bin/bash

# Simple script to run Locust tests for different cardinalities
# and combine results into a single CSV file

echo "Starting cardinality experiments..."

# Cardinalities to test
CARDINALITIES=(1 5 10 15)

# Create results directory if it doesn't exist
mkdir -p ./stress_results_locust

# Run tests for each cardinality
for cardinality in "${CARDINALITIES[@]}"; do
    echo "============================================="
    echo "Running test for cardinality: $cardinality"
    echo "============================================="
    
    # Check current cardinality first
    current_cardinality=$(oneflow show 306 --json 2>/dev/null | jq -r '.DOCUMENT.TEMPLATE.BODY.roles[] | select(.name=="FaaS") | .cardinality' 2>/dev/null || echo "unknown")
    echo "Current cardinality: $current_cardinality, Target: $cardinality"
    
    if [[ "$current_cardinality" != "$cardinality" ]]; then
        # Scale OneFlow service to target cardinality
        echo "Scaling OneFlow service 306 FaaS role to $cardinality VMs..."
        oneflow scale 306 FaaS $cardinality
        
        # Wait for scaling to complete
        echo "Waiting 30 seconds for scaling to complete..."
        sleep 30
        
        # Verify scaling completed
        final_cardinality=$(oneflow show 306 --json 2>/dev/null | jq -r '.DOCUMENT.TEMPLATE.BODY.roles[] | select(.name=="FaaS") | .cardinality' 2>/dev/null || echo "unknown")
        if [[ "$final_cardinality" != "$cardinality" ]]; then
            echo "Warning: Scaling may not be complete. Expected: $cardinality, Current: $final_cardinality"
            echo "Waiting additional 30 seconds..."
            sleep 30
        else
            echo "Scaling completed successfully ✓"
        fi
    else
        echo "Already at target cardinality, no scaling needed ✓"
    fi
    
    # Run locust test
    echo "Starting Locust test..."
    locust -f stress_cpu_locust.py \
           --host=localhost \
           --users=20 \
           --spawn-rate=1 \
           --run-time=1m \
           --csv=./stress_results_locust/stats_cardinality_${cardinality} \
           --headless \
           --skip-log-setup
    
    echo "Test for cardinality $cardinality completed"
    echo ""
done

echo "All tests completed!"
echo "============================================="

# =============================================================================
# COMBINE RESULTS: Merge all individual CSV files into one master file
# =============================================================================
# This section creates a single CSV file containing results from all cardinality tests.
# Each row will be tagged with its corresponding VM cardinality for easy analysis.

echo "Combining results into final CSV..."

# Define the path for the master CSV file that will contain all results
OUTPUT_FILE="./stress_results_locust/combined_results.csv"

# Create the header row for the master CSV file
# Note: We add "cardinality" as the first column to identify which VM count each row represents
# The rest of the columns match Locust's standard CSV output format
echo "cardinality,Type,Name,Request Count,Failure Count,Median Response Time,Average Response Time,Min Response Time,Max Response Time,Average Content Size,Requests/s,Failures/s,50%,66%,75%,80%,90%,95%,98%,99%,99.9%,99.99%,100%" > "$OUTPUT_FILE"

# Loop through each cardinality that was tested (1, 5, 10, 15)
for cardinality in "${CARDINALITIES[@]}"; do
    # Construct the filename for this cardinality's stats file
    # Example: "./stress_results_locust/stats_cardinality_5_stats.csv"
    STATS_FILE="./stress_results_locust/stats_cardinality_${cardinality}_stats.csv"
    
    # Check if the stats file exists before trying to process it
    if [[ -f "$STATS_FILE" ]]; then
        echo "Processing cardinality $cardinality..."
        
        # Process each line of the individual CSV file:
        # 1. `tail -n +2` = Skip the first line (header row) of the individual CSV
        # 2. `while IFS= read -r line` = Read each remaining line one by one
        # 3. `IFS=` prevents word splitting on spaces/tabs, preserving the line exactly
        # 4. `-r` prevents backslash interpretation, keeping the line as-is
        tail -n +2 "$STATS_FILE" | while IFS= read -r line; do
            # Add the cardinality number as the first column, followed by the original line
            # Example: "5,COGNIT,cognit_stress_cpu,240,0,2100,2064.65,2034,2159,16.83,4.07,0.0,..."
            echo "${cardinality},${line}" >> "$OUTPUT_FILE"
        done
        
        echo "✓ Added data for cardinality $cardinality"
    else
        # Warn if the expected file doesn't exist (indicates test might have failed)
        echo "⚠️  Warning: Stats file not found for cardinality $cardinality"
        echo "    Expected file: $STATS_FILE"
    fi
done

echo ""
echo "📁 Master CSV created: $OUTPUT_FILE"
echo "   This file contains all results with cardinality tags for easy analysis."

echo "============================================="
echo "Results combined into: $OUTPUT_FILE"
echo "============================================="

# Show summary
echo "Summary of results:"
echo "Cardinality | Avg Response Time | Requests/sec"
echo "------------|-------------------|-------------"

for cardinality in "${CARDINALITIES[@]}"; do
    STATS_FILE="./stress_results_locust/stats_cardinality_${cardinality}_stats.csv"
    if [[ -f "$STATS_FILE" ]]; then
        # Extract average response time and requests per second for Aggregated row
        avg_time=$(tail -n 1 "$STATS_FILE" | cut -d',' -f6)   # Average Response Time
        req_per_sec=$(tail -n 1 "$STATS_FILE" | cut -d',' -f10) # Requests/s
        printf "%11s | %17s | %11s\n" "$cardinality" "$avg_time" "$req_per_sec"
    fi
done

echo ""
echo "Individual CSV files are also available:"
for cardinality in "${CARDINALITIES[@]}"; do
    echo "- stats_cardinality_${cardinality}_stats.csv"
    echo "- stats_cardinality_${cardinality}_failures.csv"
done 