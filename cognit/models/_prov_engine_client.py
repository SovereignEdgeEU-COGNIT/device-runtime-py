from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class FaaSState(str, Enum):
    """
    ServerlessRuntimeState representation
    """

    PENDING = "PENDING"
    # RUNNING = "ACTIVE"
    RUNNING = "RUNNING"
    NO_STATE = ""


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
        default="nature",
        description="String describing the flavour of the Runtime. There is one identifier per DaaS and FaaS corresponding to the different use cases",
    )
    ENDPOINT: str = Field(
        default="",
        description="String containing the HTTP URL of the Runtime. Must be empty or nonexistent in creation.",
    )
    STATE: Optional[FaaSState] = Field(
        #default="PENDING",
        description="String containing the state of the VM containing the Runtime. It can be any state defined by the Cloud/Edge Manager, the relevant subset is “pending” and “running”",
    )
    VM_ID: Optional[str] = Field(
        #default=0,
        description="String containing the ID of the VM containing the Serverless Runtime, running in the Cloud/Edge Manager.",
    )


class DaaSConfig(BaseModel):
    CPU: Optional[int] = Field(
        default="",
        description="Integer describing the number of CPUs allocated to the VM serving the Runtime",
    )
    MEMORY: Optional[int] = Field(
        description="Integer describing the RAM in MB of CPUs allocated to the VM serving the Runtime",
    )
    DISK_SIZE: Optional[int] = Field(
        description="Integer describing the size in MB of the disk allocated to the VM serving the Runtime",
    )
    FLAVOUR: str = Field(
        default="",
        description="String describing the flavour of the Runtime. There is one identifier per DaaS and FaaS corresponding to the different use cases",
    )
    ENDPOINT: str = Field(
        "",
        description="String containing the HTTP URL of the Runtime. Must be empty or nonexistent in creation.",
    )
    STATE: str = Field(
        "",
        description="String containing the state of the VM containing the Runtime. It can be any state defined by the Cloud/Edge Manager, the relevant subset is “pending” and “running”",
    )
    VM_ID: str = Field(
        "",
        description="String containing the ID of the VM containing the Serverless Runtime, running in the Cloud/Edge Manager.",
    )


class Scheduling(BaseModel):
    POLICY: Optional[str] = Field(
        default="",
        description="String describing the policy applied to scheduling. Eg: “energy, latency” will optimise the placement according to those two criteria",
    )
    REQUIREMENTS: Optional[str] = Field(
        default="",
        description="String describing the requirements of the placement. For instance, “energy_renewal” will only consider hypervisors powered by renewable energy.",
    )


class DeviceInfo(BaseModel):
    LATENCY_TO_PE: int = Field(
        ...,
        description="Integer describing in ms the latency from the client device to the Provisioning Engine endpoint",
    )
    GEOGRAPHIC_LOCATION: Optional[str] = Field(
        default="",
        description="String describing the geographic location of the client device in WGS84",
    )


class Empty(BaseModel):
    ...


class ServerlessRuntimeData(BaseModel):
    NAME: Optional[str] = Field(
        description="Name of the Serverless Runtime. Must be empty or nonexistent in creation",
    )
    ID: Optional[int | Empty] = Field(
        description="Integer describing a unique identifier for the Serverless Runtime. ",
    )

    FAAS: FaaSConfig = Field(description="FaaS Config")
    # DAAS: Optional[DaaSConfig] = Field(description="DaaS Config")
    DAAS: Optional[Empty]

    SCHEDULING: Optional[Scheduling | Empty]

    DEVICE_INFO: Optional[DeviceInfo | Empty]


class ServerlessRuntime(BaseModel):
    SERVERLESS_RUNTIME: ServerlessRuntimeData = Field(
        # TODO: DEVICE_INFO and SCHEDULING should not be hardcoded to empty. Next commented example should be implemented.
        ServerlessRuntimeData(FAAS=FaaSConfig(), DEVICE_INFO=DeviceInfo(), SCHEDULING=Scheduling()),
        #ServerlessRuntimeData(
        #    FAAS=FaaSConfig(), DEVICE_INFO=Empty(), SCHEDULING=Empty()
        #),
        description="Serverless Runtime object",
    )
