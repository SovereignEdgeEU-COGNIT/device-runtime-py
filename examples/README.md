# Cognit Device Runtime Example

This folder contains examples of the usage of the COGNIT library

## Minimal example

The file [minimal_offload_sync](minimal_offload_sync.py) demonstrates the basic usage of the COGNIT library. In this example, you’ll learn how to upload requirements to the COGNIT environment and execute functions within it.

### Uploading requirements

Requirements can be uploaded in two ways:

1. Using the `init()` function with a JSON containing the requirements following [Scheduling](../cognit/models/_cognit_frontend_client.py#L9) model:

    ```python
    my_device_runtime.init(TEST_REQS_INIT)
    ```

2. Once initialized, requirements can be updated anytime using the `update_requirements()` function passing the JSON with the updated requirements:

    ```python
    my_device_runtime.update_requirements(NEW_TEST_REQS)
    ```

This example also shows that requirements can be updated dynamically whenever needed.

### Running the script

First make sure to activate the virtual environment:

```bash
cd /path/to/device-runtime-py-folder
source .venv/bin/activate
```

If you have not built a virtual environment please go to [developer setup guide](../README.md#developer-setup).

To execute the script, navigate to the examples directory and run the following command:

```bash
cd ./examples
python3 minimal_offload_sync.py
```

## Run example with Docker

This example can also be executed within Docker. A Dockerfile named `minimal_offload_sync.dockerfile` is provided to build the image along with a Docker Compose file to help run it.

### Steps to run with Docker

1. **Install Docker**

    Follow the official Docker installation instructions: [Docker Installation Guide](https://docs.docker.com/get-docker/)

2. **Deploy Docker stack**

    To build and run the image, make sure you are located in the examples directory. Then type the following commands:

    ```bash
    cd ./examples
    docker compose build
    docker compose up
    ```

> **Important**  
> Make sure the configuration file `cognit-template.yml` has the correct parameters.
