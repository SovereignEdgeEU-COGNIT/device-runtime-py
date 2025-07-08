# FaaS Scaling Experiment

## Quick Start
```bash
./run_cardinality_tests.sh
```

or
```bash
./run_autoscaling_tests.sh
```

In the case of `run_autoscaling_tests.sh`, remember to adapt the timeout of the `stress` function to the evaluation period of your scaling policy. In the case of autoscaling tests, the scaling policy used is the following one:
```
"cooldown": 10,
"elasticity_policies": [
    {
        "expression": "CPU > 70",
        "type": "CHANGE",
        "adjust": 2,
        "period_number": 1,
        "period": 10,
    },
    {
        "expression": "CPU < 30",
        "type": "CHANGE",
        "adjust": -1,
        "period_number": 1,
        "period": 10,
    }
]
```

with a stress timeout of 30 seconds (line of the file cognit-client-locust/examples/scaling_experiments_locust/stress_cpu_locust.py)


## Configuration

### Change OneFlow Service ID
```bash
ONEFLOW_SERVICE_ID="306"    # Your OneFlow service ID
```

### Change VM Cardinalities
```bash
CARDINALITIES=(1 2 4 8 16)  # Test different VM counts
```

### Change Locust Parameters
```bash
--users=20          # Concurrent users
--spawn-rate=1      # Users spawned per second  
--run-time=1m       # Test duration
```

## Results

### Expected Pattern
```
Cardinality | Avg Response Time | Requests/sec
          1 |             8000ms|         1.5
          4 |             3000ms|         4.2  
          8 |             2100ms|         6.8
```

**Good scaling**: ↑ VMs = ↓ Response Time + ↑ Throughput

### Files Generated
- `combined_results.csv` - All results with cardinality column
- `stats_cardinality_N_*.csv` - Individual test results

## Key Metrics
- **Average Response Time**: Lower is better
- **Requests/s**: Higher is better  
- **Failure Count**: Should be 0 