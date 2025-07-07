#!/usr/bin/env python3
"""
Simple Locust load test for Cognit stress_cpu function.
"""

import sys
import time
import os
sys.path.append(".")

from locust import User, task, events
from cognit import device_runtime


def stress(duration: int):
    """CPU-intensive function that performs mathematical operations."""
    import time
    import math
    import random

    end_time = time.time() + duration
    result = 0

    while time.time() < end_time:
        x = random.random()
        for _ in range(1000):
            result += math.sqrt(x ** 2 + x)
    return result


class CognitStressUser(User):
    """Simple Locust User for testing Cognit stress function."""
    
    wait_time = lambda self: 2  # Wait 2 seconds between tasks
    
    def on_start(self):
        """Initialize the Cognit device runtime when user starts."""
        # Simple requirements
        reqs_init = {
            "FLAVOUR": "Nature",
            "GEOLOCATION": {
                "latitude": 43.05,
                "longitude": -2.53
            }
        }
        
        # Initialize device runtime
        self.device_runtime = device_runtime.DeviceRuntime("../cognit-template.yml")
        self.device_runtime.init(reqs_init)
        
        # Give it a moment to initialize
        time.sleep(1)

    @task
    def call_stress_function(self):
        """Call the stress function through Cognit."""
        start_time = time.time()
        request_name = "cognit_stress_cpu"
        
        try:
            # Call stress function with 2 second duration
            result = self.device_runtime.call(stress, 2)
            
            # Calculate execution time
            total_time = int((time.time() - start_time) * 1000)  # Convert to milliseconds
            
            if result and hasattr(result, 'result'):
                print(f"Stress result: {result.result}")
                # Fire success event for Locust statistics
                events.request.fire(
                    request_type="COGNIT",
                    name=request_name,
                    response_time=total_time,
                    response_length=len(str(result.result)),
                    exception=None,
                    context={}
                )
            else:
                print("No result returned")
                # Fire failure event
                events.request.fire(
                    request_type="COGNIT",
                    name=request_name,
                    response_time=total_time,
                    response_length=0,
                    exception=Exception("No result returned"),
                    context={}
                )
                
        except Exception as e:
            # Calculate execution time even for failures
            total_time = int((time.time() - start_time) * 1000)
            print(f"Error calling stress function: {e}")
            
            # Fire failure event for Locust statistics
            events.request.fire(
                request_type="COGNIT",
                name=request_name,
                response_time=total_time,
                response_length=0,
                exception=e,
                context={}
            )


if __name__ == "__main__":
    csv_path = "./stress_results_locust/stats"
    print("Simple Locust test for Cognit stress function")
    print(f"\nResults will be saved in: {script_dir}")
    print("\nUsage examples:")
    print("Basic run:")
    print("  locust -f stress_cpu_locust.py --host=localhost --users=5 --spawn-rate=1 --run-time=1m")
    print("\nWith CSV stats output (saves in script directory):")
    print(f"  locust -f stress_cpu_locust.py --host=localhost --users=5 --spawn-rate=1 --run-time=1m --csv={csv_path}")
    print("\nHeadless with CSV (no web UI, saves in script directory):")
    print(f"  locust -f stress_cpu_locust.py --host=localhost --users=5 --spawn-rate=1 --run-time=1m --csv={csv_path} --headless")