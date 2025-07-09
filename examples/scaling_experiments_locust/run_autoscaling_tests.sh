#!/bin/bash

# =============================================================================
# AUTO-SCALING LOAD TESTS
# =============================================================================
# This script tests OneFlow elasticity policies by varying USER LOAD instead 
# of manually setting VM cardinality. It lets the auto-scaling system decide
# how many VMs to deploy based on CPU usage.
# =============================================================================

echo "Starting auto-scaling experiments..."
echo "This script will test different USER LOADS and let auto-scaling handle VM count"

# Configuration
ONEFLOW_SERVICE_ID="306"        # OneFlow service ID with elasticity policies
USER_SCENARIOS=("1" "5")  # Different user loads to test

# Longer test duration to allow scaling events
TEST_DURATION="3m"              # 3 minutes to see scaling in action
SPAWN_RATE="1"                  # Users spawned per second

# Create results directory if it doesn't exist
mkdir -p ./stress_results_autoscaling

echo "============================================="
echo "AUTO-SCALING EXPERIMENT CONFIGURATION"
echo "============================================="
echo "Service ID: $ONEFLOW_SERVICE_ID"
echo "Test duration: $TEST_DURATION (allows time for scaling)"
echo "User scenarios: ${USER_SCENARIOS[*]}"

# Check if service has elasticity policies
echo "Checking if elasticity policies are configured..."
policies=$(oneflow show $ONEFLOW_SERVICE_ID --json 2>/dev/null | jq -r '.DOCUMENT.TEMPLATE.BODY.roles[] | select(.name=="FaaS") | .elasticity_policies' 2>/dev/null)

if [[ "$policies" == "null" || "$policies" == "" ]]; then
    echo "❌ ERROR: No elasticity policies found on service $ONEFLOW_SERVICE_ID"
    echo "   Please configure auto-scaling policies before running this test."
    echo "   Use run_cardinality_tests.sh for manual scaling tests instead."
    exit 1
else
    echo "✅ Elasticity policies detected - ready for auto-scaling test"
fi

declare -A FINAL_VMS_PER_SCENARIO

# Reset to baseline (1 VM) before starting
echo "Resetting service to baseline (1 VM)..."
oneflow scale $ONEFLOW_SERVICE_ID FaaS 1
echo "Waiting 30 seconds for baseline reset..."
sleep 30

# Run tests for each user scenario
for users in "${USER_SCENARIOS[@]}"; do
    echo ""
    echo "============================================="
    echo "Testing load scenario: $users concurrent users"
    echo "============================================="
    
    # Check current VM count before test
    current_vms=$(oneflow show $ONEFLOW_SERVICE_ID --json 2>/dev/null | jq -r '.DOCUMENT.TEMPLATE.BODY.roles[] | select(.name=="FaaS") | .cardinality' 2>/dev/null || echo "unknown")
    echo "Starting VMs: $current_vms"
    
    # Run locust test with specific user load
    echo "Starting Locust test with $users users for $TEST_DURATION..."
    echo "Auto-scaling will adjust VMs based on CPU load..."
    
    locust -f stress_cpu_locust.py \
           --host=localhost \
           --users=$users \
           --spawn-rate=$SPAWN_RATE \
           --run-time=$TEST_DURATION \
           --csv=./stress_results_autoscaling/autoscale_${users}users \
           --headless \
           --skip-log-setup \
           --loglevel ERROR
    
    # Check final VM count after test
    final_vms=$(oneflow show $ONEFLOW_SERVICE_ID --json 2>/dev/null | jq -r '.DOCUMENT.TEMPLATE.BODY.roles[] | select(.name=="FaaS") | .cardinality' 2>/dev/null || echo "unknown")
    echo "Final VMs: $final_vms - auto-scaled from $current_vms"
    FINAL_VMS_PER_SCENARIO[$users]=$final_vms
    
    echo "Test completed for $users users"
    
    # Brief pause between tests to allow system to stabilize
    echo "Waiting for cleanup and stabilization..."
    
    # Kill any lingering locust processes (just in case)
    pkill -f "locust.*stress_cpu_locust.py" 2>/dev/null || true
    
    # Reset to baseline for the next test
    echo "Resetting service to baseline (1 VM)..."
    oneflow scale $ONEFLOW_SERVICE_ID FaaS 1
    echo "Waiting 30 seconds for baseline reset..."
    sleep 30
done

echo ""
echo "All auto-scaling tests completed!"
echo "============================================="

# =============================================================================
# COMBINE RESULTS: Merge all individual CSV files into one master file
# =============================================================================

echo "Combining results into final CSV..."

OUTPUT_FILE="./stress_results_autoscaling/combined_autoscaling_results.csv"

# Create header with "users" and "final_vms"
echo "users,final_vms,Type,Name,Request Count,Failure Count,Median Response Time,Average Response Time,Min Response Time,Max Response Time,Average Content Size,Requests/s,Failures/s,50%,66%,75%,80%,90%,95%,98%,99%,99.9%,99.99%,100%" > "$OUTPUT_FILE"

# Process each user scenario
for users in "${USER_SCENARIOS[@]}"; do
    STATS_FILE="./stress_results_autoscaling/autoscale_${users}users_stats.csv"
    
    if [[ -f "$STATS_FILE" ]]; then
        echo "Processing $users users scenario..."
        vms=${FINAL_VMS_PER_SCENARIO[$users]:-"N/A"}
        
        # Add user count and final_vms as first columns
        tail -n +2 "$STATS_FILE" | while IFS= read -r line; do
            echo "${users},${vms},${line}" >> "$OUTPUT_FILE"
        done
        
        echo "✓ Added data for $users users"
    else
        echo "⚠️  Warning: Stats file not found for $users users"
        echo "    Expected file: $STATS_FILE"
    fi
done

echo ""
echo "📁 Auto-scaling results: $OUTPUT_FILE"

echo "============================================="
echo "AUTO-SCALING RESULTS SUMMARY"
echo "============================================="

echo "Users | Avg Response Time | Requests/sec | VMs Used"
echo "------|-------------------|--------------|----------"

for users in "${USER_SCENARIOS[@]}"; do
    STATS_FILE="./stress_results_autoscaling/autoscale_${users}users_stats.csv"
    if [[ -f "$STATS_FILE" ]]; then
        # Extract metrics
        avg_time=$(tail -n 1 "$STATS_FILE" | cut -d',' -f6)
        req_per_sec=$(tail -n 1 "$STATS_FILE" | cut -d',' -f10)
        vms=${FINAL_VMS_PER_SCENARIO[$users]:-"N/A"}
        
        # Note: VM count would need to be tracked during test for accurate reporting
        printf "%5s | %17s | %12s | %8s\n" "$users" "$avg_time" "$req_per_sec" "$vms"
    fi
done

echo ""
echo "---"
echo "Generated files:"
for users in "${USER_SCENARIOS[@]}"; do
    echo "- autoscale_${users}users_stats.csv"
    echo "- autoscale_${users}users_failures.csv"
done