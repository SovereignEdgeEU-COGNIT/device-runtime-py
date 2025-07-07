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

# Combine results into a single CSV with cardinality column
echo "Combining results into final CSV..."

OUTPUT_FILE="./stress_results_locust/combined_results.csv"

# Create header
echo "cardinality,type,name,request_count,failure_count,median_response_time,average_response_time,min_response_time,max_response_time,average_content_size,requests_per_second,failures_per_second,50_percentile,66_percentile,75_percentile,80_percentile,90_percentile,95_percentile,98_percentile,99_percentile,99.9_percentile,99.99_percentile,100_percentile" > "$OUTPUT_FILE"

# Combine data from each cardinality
for cardinality in "${CARDINALITIES[@]}"; do
    STATS_FILE="./stress_results_locust/stats_cardinality_${cardinality}_stats.csv"
    
    if [[ -f "$STATS_FILE" ]]; then
        # Skip header line and add cardinality column
        tail -n +2 "$STATS_FILE" | while IFS= read -r line; do
            echo "${cardinality},${line}" >> "$OUTPUT_FILE"
        done
        echo "Added data for cardinality $cardinality"
    else
        echo "Warning: Stats file not found for cardinality $cardinality"
    fi
done

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
        avg_time=$(tail -n 1 "$STATS_FILE" | cut -d',' -f8)
        req_per_sec=$(tail -n 1 "$STATS_FILE" | cut -d',' -f12)
        printf "%11s | %17s | %11s\n" "$cardinality" "$avg_time" "$req_per_sec"
    fi
done

echo ""
echo "Individual CSV files are also available:"
for cardinality in "${CARDINALITIES[@]}"; do
    echo "- stats_cardinality_${cardinality}_stats.csv"
    echo "- stats_cardinality_${cardinality}_failures.csv"
done 