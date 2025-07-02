from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class Geolocation(BaseModel):
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")

class Scheduling(BaseModel): # Called 'class AppRequirements' in dann1 code
    FLAVOUR: str = Field(
        default="Nature",
        description="String describing the flavour of the Runtime. There is oneidentifier per DaaS and FaaS corresponding to the different use cases")
    MAX_LATENCY: Optional[int] = Field(
        default=None,
        description="Maximum latency in miliseconds")
    MAX_FUNCTION_EXECUTION_TIME: Optional[float] = Field(
        default=1.0,
        description="Max execution time allowed for the function")
    MIN_ENERGY_RENEWABLE_USAGE: Optional[int] = Field(
        default=80,
        description="Minimum energy renewable percentage")
    GEOLOCATION: Geolocation = Field(
        default=None,
        description="Geolocation info with latitude and longitude.")
    
class FunctionLanguage(str, Enum):
    PY = "PY"
    C = "C"

class UploadFunctionDaaS(BaseModel):
    LANG: FunctionLanguage = Field(
        description="Programming Language of the function"
    )
    FC: str = Field(
        description="Function bytes serialized and encoded in base64"
    )
    FC_HASH: str = Field(
        description="Function contents hash. Acts as a function ID."
    )
    
class EdgeClusterFrontendResponse(BaseModel):
    ID: int = Field(description='Cluster ID in the Cloud Edge Manager cluster pool')
    NAME: str = Field(description='Cluster name')
    HOSTS: list[int] = Field(
        description='Hypervisor nodes ID belonging to the cluster')
    DATASTORES: list[int] = Field(
        description='Datastores ID belonging to the cluster')
    VNETS: list[int] = Field(
        description='Virtual Networks ID belonging to the cluster')
    TEMPLATE: dict = Field(
        description='Additional misc information of the cluster')
