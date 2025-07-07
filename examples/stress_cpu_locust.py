#!/usr/bin/env python3
"""
Simple Locust load test for Cognit stress_cpu function.

Usage:
    locust -f stress_cpu_locust.py --host=localhost --users=5 --spawn-rate=1 --run-time=30s
"""

import sys
import time
sys.path.append(".")

from locust import User, task
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
        self.device_runtime = device_runtime.DeviceRuntime("./cognit-template.yml")
        self.device_runtime.init(reqs_init)
        
        # Give it a moment to initialize
        time.sleep(1)

    @task
    def call_stress_function(self):
        """Call the stress function through Cognit."""
        try:
            # Call stress function with 10 second duration
            result = self.device_runtime.call(stress, 10)
            
            if result and hasattr(result, 'result'):
                print(f"Stress result: {result.result}")
            else:
                print("No result returned")
                
        except Exception as e:
            print(f"Error calling stress function: {e}")


if __name__ == "__main__":
    print("Simple Locust test for Cognit stress function")
    print("Run with: locust -f stress_cpu_locust.py --host=localhost --users=5 --spawn-rate=1 --run-time=1m") 