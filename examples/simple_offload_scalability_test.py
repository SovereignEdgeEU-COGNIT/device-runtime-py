"""
This script is used to test the scalability of the system when offloading functions to the Cognit Frontend.

It is important to note that the COGNIT client is now sending the flavour as parameter in the request.
In this way the NGINX server is able to route the request to the correct backend.
"""

import sys
import time
import os

from cognit import device_runtime

# Functions used to be uploaded
def sum(a: int, b: int):
    return a + b

REQUIREMENTS = {
      "FLAVOUR": "ServerlessRuntime",
      "MAX_LATENCY": 45,
      "GEOLOCATION": "43,2"
}

N_ITERATIONS = 20

try:

    config_path = os.path.join(os.path.dirname(__file__), "cognit-template.yml")
    rt = device_runtime.DeviceRuntime(config_path)
    rt.init(REQUIREMENTS)

    for i in range(N_ITERATIONS):
        print(f"Iteration {i}")
        result = rt.call(sum, 17, 5)
        print("-----------------------------------------------")
        print("Sum sync result: " + str(result))
        print("-----------------------------------------------")

except Exception as e:
    print("An exception has occured: " + str(e))
    exit(-1)