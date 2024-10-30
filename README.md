# Device-runtime
This repository contains the Python implementation of the Device Runtime, an SDK designed to enable devices to communicate seamlessly with the COGNIT platform for task offloading. The Device Runtime provides a highly abstracted layer of communication between the COGNIT platform and end devices, simplifying the interaction process for users.

At the core of this abstraction is a state machine, which autonomously manages all stages of communication without requiring direct user intervention. This allows for efficient and automated handling of the different states involved in the task offloading process.

The communication with the Device Runtime involves two key components: the Cognit Frontend Client and the Edge Cluster Frontend. The Cognit Frontend Client allows the Device Runtime to offload functions that the device may wish to execute in the future, along with a comprehensive set of requirements, policies, and dependencies. Meanwhile, the Edge Cluster Frontend is responsible for executing those previously uploaded functions.

## Developer Setup

This repository has been built using **Python v3.10.6**, therefore it is highly recommended to maintain this Python version for development purposes. 

For setting it up it is recommended installing the module virtualenv or, in order to keep the dependencies isolated from the system. 

```bash
pip install virtualenv
```

After that, one needs create a virtual environment and activate it:

```bash
python -m venv runtime-env
source runtime-env/bin/activate
```

The following installs the needed dependencies from the requirements.txt file:

```bash
pip install -r requirements.txt
```

## Setting up COGNIT module

To set up the COGNIT module the following needs to be executed:

```bash
python setup.py sdist
```

In such a way that for installing it in an empty environment, one should:

```bash
pip install dist/cognit-0.0.0.tar.gz
```

Once done that, COGNIT module's installation will be fully completed. Now is possible to instantiate device runtimes in the same way as follows:

```python
from cognit import device_runtime

my_device_runtime = device_runtime.DeviceRuntime("./examples/cognit-template.yml")
```

## User's manual
There are several folders that might be interesting for a user that is getting acquainted with COGNIT:

### Configuration

The configuration for your COGNIT Device Runtime can be found in `cognit/test/config/cognit.yml`, with an example for running the tests.

### Examples

In the `examples/` folder one can find the minimal example for running a minimal example making use of the COGNIT module. Refer to  examples [README.md](examples/README.md) file for further information.

### Tests

The `cognit/test/`  folder holds the tests for the COGNIT module. More info about how to run them in the [README.md](cognit/test/README.md) file.
