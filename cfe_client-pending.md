This document demostrates the incompatibilities between the `AppRequirements` model implemented in the Cognit Frontend Engine (CFE) and the one that was being used in v1 in the Cognit Frontend Engine Client (CFEClient).

## Questions / Pending topics:
- There are incompatibilities between the `AppRequirements` model used in the CFE and the ones used in the CFClient.
- Will the `FaaSConfig` info be included in the `AppRequirements` (as until v2)? If no, we need to define a way to define the FunctionRequirements of each ofloaded function. 

## CFClient & CFE  integration error with current models
Below, a screenshot demostrating the integration error is shown.
```bash
cognit-frontend$ ./src/main.py 
/etc/cognit-frontend.conf not found. Using default configuration.
INFO:     Started server process [8360]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:1338 (Press CTRL+C to quit)
INFO:     127.0.0.1:50464 - "POST /v1/authenticate HTTP/1.1" 201 Created
INFO:     127.0.0.1:50466 - "POST /v1/app_requirements HTTP/1.1" 422 Unprocessable Entity
```


## Current CFE AppRequirements model
The current CFE model includes a *REQUIREMENT* and a *SCHEDULING_POLICY* field:
```python
# cognit_models.py
class AppRequirements(BaseModel):
    REQUIREMENT: str = Field(
        description=DESCRIPTIONS['app_requirement']['requirement'])
    SCHEDULING_POLICY: str = Field(
        description=DESCRIPTIONS['app_requirement']['scheduling'])
```

For example:
```json
{
    "REQUIREMENT": "hypervisor = KVM",
    "SCHEDULING_POLICY": "ENERGY"
}
```

## Current CFE Client AppRequirements model
However, the CFCLient defines other models, having different Keys and as a result giving an error in the CFE server.

`ServerlessRuntime` is used as the Base class of the requirements. Currently implemented as `ServerlessRuntime`, but it could change to `AppRequirements` to have the same semantics as the CFE.

```python
class ServerlessRuntime(BaseModel):
    SERVERLESS_RUNTIME: ServerlessRuntimeData = Field(
        ServerlessRuntimeData(FAAS=FaaSConfig(), DEVICE_INFO=DeviceInfo(), SCHEDULING=Scheduling()),
        description="Serverless Runtime object",
    )

# This could be changed to `AppRequirementsData`
class ServerlessRuntimeData(BaseModel):
    NAME: Optional[str] = Field(
        description="Name of the Serverless Runtime. Must be empty or nonexistent in creation",
    )
    ID: Optional[int | Empty] = Field(
        description="Integer describing a unique identifier for the Serverless Runtime. ",
    )
    FAAS: FaaSConfig = Field(description="FaaS Config")
    SCHEDULING: Optional[Scheduling | Empty]
    DEVICE_INFO: Optional[DeviceInfo | Empty]

# Class used to define the configuration of each function to be offloaded
class FaaSConfig(BaseModel):
    CPU: int = Field(
        default=1,
        description="Integer describing the number of CPUs allocated to the VM serving the Runtime",
    )
    MEMORY: int = Field(
        default=768,
        description="Integer describing the RAM in MB of CPUs allocated to the VM serving the Runtime",
    )
    DISK_SIZE: int = Field(
        default=3072,
        description="Integer describing the size in MB of the disk allocated to the VM serving the Runtime",
    )
    FLAVOUR: str = Field(
        default="Nature",
        description="String describing the flavour of the Runtime. There is one identifier per DaaS and FaaS corresponding to the different use cases",
    )
    ENDPOINT: str = Field(
        default="",
        description="String containing the HTTP URL of the Runtime. Must be empty or nonexistent in creation.",
    )
    STATE: Optional[FaaSState] = Field(
        description="String containing the state of the VM containing the Runtime. It can be any state defined by the Cloud/Edge Manager, the relevant subset is “pending” and “running”",
    )
    VM_ID: Optional[str] = Field(
        description="String containing the ID of the VM containing the Serverless Runtime, running in the Cloud/Edge Manager.",
    )

# `Scheduling` is similar to the class `AppRequirements` defined by OpenNebula
class Scheduling(BaseModel): 
    SCHEDULING_POLICY: str = Field(
        default="",
        description="String describing the policy applied to scheduling. Eg: “energy, latency” will optimise the placement according to those two criteria",
    )
    REQUIREMENT: str = Field(
        default="",
        description="String describing the requirements of the placement. For instance, “energy_renewal” will only consider hypervisors powered by renewable energy.",
    )

# Used to add Geolocation info.
class DeviceInfo(BaseModel):
    LATENCY_TO_PE: float = Field( # Not required
        default = 0.0,
        description="Integer describing in ms the latency from the client device to the Provisioning Engine endpoint",
    )
    GEOGRAPHIC_LOCATION: Optional[str] = Field(
        default="",
        description="String describing the geographic location of the client device in WGS84",
    )
```

## CFClient post request example (previous to v2 architecture)
```python
# def ProvEngineClient.create(ServerlessRuntime):
r = req.post(
            url,
            auth=(self.config._prov_engine_pe_usr, self.config._prov_engine_pe_pwd),
            json=ServerlessRuntime.dict(),
            timeout=REQ_TIMEOUT,
        )
```



<!-- ```python

``` -->