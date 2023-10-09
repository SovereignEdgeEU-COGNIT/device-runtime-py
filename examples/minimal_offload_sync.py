# This is needed to run the example from the cognit source code
# If you installed cognit with pip, you can remove this
import sys

sys.path.append(".")

import time

from cognit.models._prov_engine_client import (
    FaaSState,
)
from cognit.serverless_runtime_context import (
    EnergySchedulingPolicy,
    ServerlessRuntimeConfig,
    ServerlessRuntimeContext,
)

def sum(a: int, b: int):
    return a + b


# Configure the serverless runtime requeriments
sr_conf = ServerlessRuntimeConfig()
sr_conf.name = "Example Serverless Runtime"
sr_conf.scheduling_policies = [EnergySchedulingPolicy(50)]

# Request the creation of the serverless runtime to the Cognit provisioning engine
try:
    my_cognit_runtime = ServerlessRuntimeContext(config_path="./examples/cognit.yml")
    ret = my_cognit_runtime.create(sr_conf)
except Exception as e:
    print("Error: {}".format(e))
    exit(1)


# Wait until the runtime is ready

while my_cognit_runtime.status != FaaSState.RUNNING:
    time.sleep(1)

print("Cognit runtime ready!")

# Example offloading a function call to the serverless runtime

result = my_cognit_runtime.call_sync(sum, 2, 2)

print("Offloaded function result", result)

my_cognit_runtime.delete() # Fill in with the ID of your created Serverless Runtime

print("Cognit runtime deleted!")
