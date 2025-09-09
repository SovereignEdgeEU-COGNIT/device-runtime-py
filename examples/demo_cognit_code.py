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
      "FLAVOUR": "Nature",
      "MAX_LATENCY": 30,
      "GEOLOCATION": "59.3294,18.0687"
}

N_ITERATIONS = 20

try:

    rt = device_runtime.DeviceRuntime("./examples/cognit-template.yml")
    rt.init(REQUIREMENTS)

    for i in range(N_ITERATIONS):
        print(f"Iteration {i}")
        result = rt.call(sum, 17, 5)
        print("-----------------------------------------------")
        print("Flavour: " + REQUIREMENTS["FLAVOUR"] + ", Sum sync result: " + str(result))
        print("-----------------------------------------------")
    print("out of for...")
    exit(0)

except Exception as e:
    print("An exception has occured: " + str(e))
    exit(-1)