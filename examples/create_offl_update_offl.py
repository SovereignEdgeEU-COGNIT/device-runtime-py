# This is needed to run the example from the cognit source code
# If you installed cognit with pip, you can remove this
import sys
import time

sys.path.append(".")

import time

from cognit import (
    EnergySchedulingPolicy,
    FaaSState,
    ServerlessRuntimeConfig,
    ServerlessRuntimeContext,
)


def sum(a: int, b: int):
    #time.sleep(20)
    print("This is a test")
    return a + b

def mult(a: int, b: int):
    #time.sleep(20)
    print("This mult is a test")
    return a * b * a * b

def heavy_lifting(x):
    import math
    return math.factorial(x)

# Configure the Serverless Runtime requeriments
sr_conf = ServerlessRuntimeConfig()
sr_conf.name = "Example Serverless Runtime"
sr_conf.scheduling_policies = [EnergySchedulingPolicy(30)]
# This is where the user can define the FLAVOUR to be used within COGNIT to deploy the FaaS node.
sr_conf.faas_flavour = "Energy"

# Request the creation of the Serverless Runtime to the COGNIT Provisioning Engine
try:
    # Set the COGNIT Serverless Runtime instance based on 'cognit.yml' config file
    # (Provisioning Engine address and port...)
    my_cognit_runtime = ServerlessRuntimeContext(config_path="./examples/cognit.yml")
    # Perform the request of generating and assigning a Serverless Runtime to this Serverless Runtime context.
    ret = my_cognit_runtime.create(sr_conf)
except Exception as e:
    print("Error in config file content: {}".format(e))
    exit(1)


# Wait until the runtime is ready

# Checks the status of the request of creating the Serverless Runtime, and sleeps 1 sec if still not available.
while my_cognit_runtime.status != FaaSState.RUNNING:
    time.sleep(1)

print("COGNIT Serverless Runtime ready!")

# Update the Device info and requirements of the SR.
sr_conf = ServerlessRuntimeConfig()
sr_conf.name = "Updated Serverless Runtime"
sr_conf.scheduling_policies = [EnergySchedulingPolicy(80)]

result = my_cognit_runtime.call_sync(sum, 2, 2)
print("Pre-Update offloaded function result", result)

## Use this if you want to update any SR specifying the ID.
#my_cognit_runtime.update(sr_conf, 2395)
# This will update the SR of the context.
my_cognit_runtime.update(sr_conf)

# First, check status is != RUNNING, as there is some lag when reporting in UPDATING state.
print(f"VM state: {my_cognit_runtime.status}")
time.sleep(3)
print(f"VM state: {my_cognit_runtime.status}")
time.sleep(3)
print(f"VM state: {my_cognit_runtime.status}")
time.sleep(3)
while my_cognit_runtime.status != FaaSState.RUNNING:
    print(f"VM state: {my_cognit_runtime.status}")
    time.sleep(3)

print("COGNIT Serverless Runtime ready after Updated!")

# Example offloading a function call to the Serverless Runtime

# call_sync sends to execute sync.ly to the already assigned Serverless Runtime.
# First argument is the function, followed by the parameters to execute it.
result = my_cognit_runtime.call_sync(mult, 4, 5)

print("Post-Update offloaded function result", result)

# This sends a request to delete this COGNIT context.
#my_cognit_runtime.delete()

print("COGNIT Serverless Runtime deleted!")
