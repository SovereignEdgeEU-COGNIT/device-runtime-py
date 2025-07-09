import sys
import time
sys.path.append(".")

from cognit import device_runtime

def stress(duration: int):
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

REQS_INIT = {
      "FLAVOUR": "Nature",
      "GEOLOCATION": {
            "latitude": 43.05,
            "longitude": -2.53
        } 
}

my_device_runtime = device_runtime.DeviceRuntime("./examples/cognit-template.yml")
my_device_runtime.init(REQS_INIT)

result = my_device_runtime.call(stress, 15)

print("-----------------------------------------------")
print("Sum sync result: " + str(result))
print("-----------------------------------------------")
