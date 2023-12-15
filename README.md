# Device-runtime
This repository holds the python implementation of the Device Runtime. The Device Runtime provides a SDK to enable the devices to communicate with the COGNIT platform to perform the task offloading. This component communicates with the Provisioning Engine to request/delete/update a Serverless Runtime and, then, it communicates with the provided Serverless Runtime to perform the offloading of functions and the uploading of content to the data-service.

## Developer Setup
Python v3.10.6

For setting it up it is recommended installing the module virtualenv or, in order to keep the dependencies isolated from the system. 

```
pip install virtualenv
```
After that, one needs create a virtual environment and activate it:

```
python -m venv serverless-env
source serverless-env/bin/activate
```
The following installs the needed dependencies from the requirements.txt file:
```
pip install -r requirements.txt
```
## Setting up COGNIT module
To set up the COGNIT module the following needs to be executed:
```
python setup.py sdist
```

In such a way that for installing it in an empty environment, one should:
```
pip install dist/cognit-0.0.0.tar.gz
```
Once done that, COGNIT module's installation will be fully completed, so (for instance) for creating the COGNIT context one needs to, as it can be checked in [examples/](examples/minimal_offload_sync.py):
```
from cognit.serverless_runtime_context import *

sr_conf = cognit.ServerlessRuntimeConfig()
sr_conf.name = "Myruntime"
sr_conf.scheduling_policies = [EnergySchedulingPolicy(50)]
my_cognit_runtime = ServerlessRuntimeContext(config_path="./config/cognit.yml")

response = my_cognit_runtime.create(sr_conf)
```
## User's manual
### Configuration
The configuration for your COGNIT Device Runtime can be found in `cognit/test/config/cognit.yml`, with an example for running the tests.

### Examples
There are several folders that might be interesting for a user that is getting acquainted with COGNIT:
In the `examples/` folder one can find the minimal example for running a minimal example making use of the COGNIT module.

### Tests
The `cognit/test/`  folder holds the tests for the COGNIT module. More info about how to run them in the [README.md](cognit/test/README.md) file.


## Docker Deployment 

1. Install Docker
Install Docker: https://docs.docker.com/get-docker/

2. Deploy Docker stack
```
docker compose build
docker compose up
```