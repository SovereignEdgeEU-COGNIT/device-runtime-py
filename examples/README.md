## Cognit Device Runtime Example
This folders contains useful turnkey examples that may show to the first time user how to make use of COGNIT module.

### Minimal example
Running `python3 minimal_offload_sync.py` the user can run this minimal version that tests the very basic functionalities of the Device Runtime.
## Run example with Docker

To run easly the example, we provide a Dockerfile and a docker-compose file that build a Docker image with all the dependencies needed to run the example.

1. Install Docker
Install Docker: https://docs.docker.com/get-docker/

2. Deploy Docker stack

```
docker compose build
docker compose up
```
Make sure the configuration file `cognit.yml` is correct before building the image or modif the example to use your own configuration file. 