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
    return a + b


# Configure the Serverless Runtime requeriments
sr_conf = ServerlessRuntimeConfig()
sr_conf.name = "Example Serverless Runtime"
sr_conf.scheduling_policies = [EnergySchedulingPolicy(50)]

# Request the creation of the Serverless Runtime to the COGNIT Provisioning Engine
try:
    # Set the COGNIT Serverless Runtime instance based on 'cognit.yml' config file
    # (Provisioning Engine address and port...)
    my_cognit_runtime = ServerlessRuntimeContext(config_path="./examples/cognit.yml")
    # Perform the request of generating and assigning a Serverless Runtime to this Serverless Runtime context.
    ret = my_cognit_runtime.create(sr_conf)
except Exception as e:
    print("Error: {}".format(e))
    exit(1)


# Wait until the runtime is ready

# Checks the status of the request of creating the Serverless Runtime, and sleeps 1 sec if still not available.
while my_cognit_runtime.status != FaaSState.RUNNING:
    time.sleep(1)

print("COGNIT Serverless Runtime ready!")

# Example offloading a function call to the Serverless Runtime

# call_sync sendsto execute sync.ly to the already assigned Serverless Runtime.
# First argument is the function, followed by the parameters to execute it.
time.sleep(15)
result = my_cognit_runtime.call_sync(sum, 2, 2)

print("Offloaded function result", result)

# This sends a request to delete this COGNIT context.
my_cognit_runtime.delete()

print("COGNIT Serverless Runtime deleted!")
