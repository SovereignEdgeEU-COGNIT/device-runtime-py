import time, re, hashlib
import geocoder
from enum import Enum
from typing import Callable, List, Optional
from ipaddress import ip_address as ipadd, IPv4Address, IPv6Address

from cognit.models._prov_engine_client import (
    Empty,
    DeviceInfo,
    Scheduling,
    FaaSConfig,
    FaaSState,
    ServerlessRuntime,
    ServerlessRuntimeData,
)
from cognit.models._serverless_runtime_client import (
    AsyncExecResponse,
    AsyncExecStatus,
    ExecReturnCode,
    ExecSyncParams,
)
from cognit.modules._cognitconfig import DEFAULT_CONFIG_PATH, CognitConfig
from cognit.modules._faas_parser import FaasParser
from cognit.modules._logger import CognitLogger
from cognit.modules._prov_engine_client import ProvEngineClient
from cognit.modules._serverless_runtime_client import (
    AsyncExecId,
    ExecResponse,
    ServerlessRuntimeClient,
)

cognit_logger = CognitLogger()

class StatusCode(Enum):
    SUCCESS = (0,)
    ERROR = 1
    PENDING = 2

class Geolocator:
    """
    Geolocator representation:

    Args:
        None
    Properties:
        country (str): Country name
        city (str): City name
    """

    def __init__(self):
        self.country = ""
        self.city = ""
        g = geocoder.ip("me")
        self.geo = g.geojson["features"][0]["properties"]["raw"]
        cognit_logger.warning(str(g.geojson["features"][0]["properties"]["raw"]))

class SchedulingPolicy:
    """
    Serverless runtime scheduling policies representation:
    """

    def __init__(self) -> None:
        self.policy_name = "default_policy"

    def serialize_requirements(self) -> str:
        raise NotImplementedError("Child classes must override this method")


class EnergySchedulingPolicy(SchedulingPolicy):
    """
    Serverless runtime scheduling policies representation:
    """

    def __init__(self, energy_percentage=0) -> None:
        """
        _summary_

        Args:
            energy_percentage (int, optional): Defines in which percentage should
            the serverless runtime be powered by renewable energy. Defaults to 0.
        """
        super().__init__()
        self.policy_name = "ENERGY"
        self.energy_percentage = energy_percentage

    def serialize_requirements(self) -> str:
        #return "[ENERGY=" + str(self.energy_percentage) + "]"
        return "ENERGY_RENEWABLE=YES"


class ServerlessRuntimeConfig:
    """
    ServerlessRuntimeConfig representation:

    Args:
        energy (int): Defines in which percentage should the serverless
    runtime be powered by renewable energy.

        name (str): Defines the name of the serverless runtime to be created
    """

    scheduling_policies: List[SchedulingPolicy] = []
    name: str = ""
    faas_flavour = "Nature"
    daas_flavour = "default"


class ServerlessRuntimeContext:
    def __init__(
        self,
        config_path=DEFAULT_CONFIG_PATH,
    ) -> None:
        """
        Serverless Runtime context creation based on info
        provided by Provisioning Engine

        Args:
            config_path (str): Path of the configuration to be applied to access
            the Prov. Engine.
        """
        self.config = CognitConfig(config_path)
        self.pec = ProvEngineClient(self.config)
        self.src = None
        self.sr_instance = None
        self.url_proto = "http://"

    def create(
        self,
        serveless_runtime_config: ServerlessRuntimeConfig,
    ) -> StatusCode:
        ## Create FaasConfig scheduling policies from the user provided objects
        policies = ""
        requirements = ""
        geoloc = Geolocator()
        geolocation = str(geoloc.geo)

        for policy in serveless_runtime_config.scheduling_policies:
            policies += policy.policy_name
            requirements += policy.serialize_requirements()
            # Add only comma if is the last one
            if policy != serveless_runtime_config.scheduling_policies[-1]:
                policies += ","
                requirements += ","

        faas_config = FaaSConfig(
            name=serveless_runtime_config.name,
            policies=policies,
            requirements=requirements,
            FLAVOUR=serveless_runtime_config.faas_flavour,
        )

        cognit_logger.warning(f'¡ATTENTION! Your Requirements {requirements}\
                are NOT being sent to COGNIT Scheduler.')
        cognit_logger.warning(f'¡ATTENTION! This is a temporary measure until\
                Schduler is working full steam.')
        new_sr_data = ServerlessRuntimeData(
            NAME=serveless_runtime_config.name,
            FAAS=faas_config,
            #DEVICE_INFO=DeviceInfo(GEOGRAPHIC_LOCATION=geolocation,\
            #        LATENCY_TO_PE=int(float(self.pec.latency_to_pe) * 1000)),
            DEVICE_INFO=DeviceInfo(GEOGRAPHIC_LOCATION=geolocation,\
                    LATENCY_TO_PE=float(self.pec.latency_to_pe)),
            #SCHEDULING=Scheduling(POLICY=policies, REQUIREMENTS=requirements),
            SCHEDULING=Scheduling(POLICY=policies),
        )

        new_sr_request = ServerlessRuntime(SERVERLESS_RUNTIME=new_sr_data)

        new_sr_response = self.pec.create(new_sr_request)

        if new_sr_response == None:
            cognit_logger.error("Serverless Runtime creation request failed")
            return StatusCode.ERROR

        if not new_sr_response.SERVERLESS_RUNTIME.FAAS.STATE in (
            FaaSState.PENDING,
            FaaSState.NO_STATE,
        ):
            cognit_logger.error(
                "Serverless Runtime creation request failed: returned state\
                        is not PENDING ({0})".format(
                    new_sr_response.SERVERLESS_RUNTIME.FAAS.STATE
                )
            )
            return StatusCode.ERROR

        # Store the Serverless Runtime instance
        self.sr_instance = new_sr_response

        return StatusCode.SUCCESS

    def update(
        self,
        serveless_runtime_config: ServerlessRuntimeConfig,
        sr_id: int=0,
    ) -> StatusCode:
        ## Create FaasConfig scheduling policies from the user provided objects
        policies = ""
        requirements = ""
        geoloc = Geolocator()
        geolocation = str(geoloc.geo)

        for policy in serveless_runtime_config.scheduling_policies:
            policies += policy.policy_name
            requirements += policy.serialize_requirements()
            # Add only comma if is the last one
            if policy != serveless_runtime_config.scheduling_policies[-1]:
                policies += ","
                requirements += ","

        faas_config = FaaSConfig(
            name=serveless_runtime_config.name,
            policies=policies,
            requirements=requirements,
            # FLAVOUR should not be updated on the fly for now.
            FLAVOUR="",
            #FLAVOUR=serveless_runtime_config.faas_flavour,
            ENDPOINT=""
        )

        # If the user is trying to change the Serverless Runtime ID, warn him
        # Otherwise, keep the current ID
        if sr_id != 0 and self.sr_instance.SERVERLESS_RUNTIME.ID != sr_id:
            cognit_logger.warning("You are changing the Serverless Runtime ID!")
        else:
            sr_id = self.sr_instance.SERVERLESS_RUNTIME.ID

        cognit_logger.warning(f'¡ATTENTION! Your Requirements {requirements}\
                are NOT being sent to COGNIT Scheduler.')
        cognit_logger.warning(f'¡ATTENTION! This is a temporary measure until\
                Scheduler is working full steam.')
        new_sr_data = ServerlessRuntimeData(
            NAME=serveless_runtime_config.name,
            ID=sr_id,
            FAAS=faas_config,
            #DEVICE_INFO=DeviceInfo(GEOGRAPHIC_LOCATION=geolocation,\
            #        LATENCY_TO_PE=int(float(self.pec.latency_to_pe) * 1000)),
            DEVICE_INFO=DeviceInfo(GEOGRAPHIC_LOCATION=geolocation,\
                    LATENCY_TO_PE=float(self.pec.latency_to_pe)),
            #SCHEDULING=Scheduling(POLICY=policies, REQUIREMENTS=requirements),
            SCHEDULING=Scheduling(POLICY=policies),
        )

        update_sr_request = ServerlessRuntime(SERVERLESS_RUNTIME=new_sr_data)

        new_sr_response = self.pec.update(update_sr_request)

        if new_sr_response == None:
            cognit_logger.error("Serverless Runtime update failed")
            return StatusCode.ERROR

        if not new_sr_response.SERVERLESS_RUNTIME.FAAS.STATE in (
            FaaSState.PENDING,
            FaaSState.RUNNING,
            FaaSState.NO_STATE,
        ):
            cognit_logger.error(
                "Serverless Runtime update failed: returned state is not PENDING ({0})".format(
                    new_sr_response.SERVERLESS_RUNTIME.FAAS.STATE
                )
            )
            return StatusCode.ERROR

        # Store the Serverless Runtime instance
        self.sr_instance = new_sr_response

        return StatusCode.SUCCESS

    @property
    def status(self) -> Optional[FaaSState]:
        """
        _summary_

        Returns:
            StatusCode: The current Serverless Runtime status
        """

        if self.sr_instance == None or self.sr_instance.SERVERLESS_RUNTIME.ID == None:
            cognit_logger.error(
                "Serverless Runtime instance has not been requested yet"
            )
            return None

        # Retrieve the Serverless Runtime instance from the Provisioning Engine
        sr_response = self.pec.retrieve(self.sr_instance.SERVERLESS_RUNTIME.ID)

        # Update the Serverless Runtime cached instance
        # Make sure that endpoint's URL contains protocol and port on it
        # and IP version compliant.
        try:
            if sr_response != None:
                ip_version = ipadd(sr_response.SERVERLESS_RUNTIME.FAAS.ENDPOINT)
                if type(ip_version) == IPv4Address:
                    sr_response.SERVERLESS_RUNTIME.FAAS.ENDPOINT = self.url_proto\
                            + sr_response.SERVERLESS_RUNTIME.FAAS.ENDPOINT \
                        + ":" + str(self.config._servl_runt_port)
                elif type(ip_version) == IPv6Address:
                    sr_response.SERVERLESS_RUNTIME.FAAS.ENDPOINT = self.url_proto\
                            + "["+ sr_response.SERVERLESS_RUNTIME.FAAS.ENDPOINT \
                        + "]:" + str(self.config._servl_runt_port)
        except ValueError as e:
            cognit_logger.warning("Serverless runtime endpoint's Ip address\
                    differs from IPv4 or IPv6")

        # Update the Serverless Runtime instance
        self.sr_instance = sr_response

        return self.sr_instance.SERVERLESS_RUNTIME.FAAS.STATE

    # TODO: Not implemented yet.
    def copy(self, src, dst) -> StatusCode:
        """
        Copies src into dst

        Args:
            src (_type_): _description_
            dst (_type_): _description_
        """
        raise NotImplementedError

    def call_sync(
        self,
        func: Callable,
        *params,
        **kwargs,
    ) -> Optional[ExecResponse]:
        """
        Perform the offload of a function to the cognit platform and wait for\
        the result.

        Args:
            func (Callable): The target funtion to be offloaded
            params (List[Any]): Arguments needed to call the function

        Returns:
            ExecResponse: Response Code
            or None
        """

        # If the Serverless Runtime client is not initialized,
        # create an instance with the endpoint
        if self.src == None:
            if (
                self.sr_instance == None
                or self.sr_instance.SERVERLESS_RUNTIME.FAAS.ENDPOINT == None
            ):
                cognit_logger.error(
                    "Serverless Runtime instance has not been requested yet"
                )
                return None

            self.src = ServerlessRuntimeClient(
                self.sr_instance.SERVERLESS_RUNTIME.FAAS.ENDPOINT
            )

        parser = FaasParser()

        # Serialize the function and the params
        # TODO: Include FaaS + DaaS dependencies management.
        ## First dependency management.
        #include_deps = []
        #exclude_deps = []
        #if kwargs.__len__() > 0:
        #    if "include_modules" in kwargs and type(kwargs[include_modules]) is list:
        #        include_deps = kwargs["include_modules"]
        #    if "exclude_modules" in kwargs and type(kwargs[exclude_modules]) is list:
        #        exclude_deps = kwargs["exclude_modules"]

        # TODO: Implement Hashing of function.
        func_hash = hashlib.sha256(func.__code__.co_code).hexdigest()


        # TODO: Think on implementing separated serialize method for function serialization.
        # for better dependency management.
        #serialized_fc = parser.serialize_func(func, include_deps, exclude_deps)
        serialized_fc = parser.serialize(func)
        serialized_params = []
        for param in params:
            serialized_params.append(parser.serialize(param))

        # Payload JSON definition
        offload_fc = ExecSyncParams(
            fc=serialized_fc, params=serialized_params, lang="PY", fc_hash=func_hash
        )

        # TODO: The client should update the sr status before offloading a function
        # if self.status() ==

        resp = self.src.faas_execute_sync(offload_fc)

        # Handle http error codes (if resp.res=None there is nothing to deserialize)
        if resp.res is not None:
            resp.res = parser.deserialize(resp.res)
        else:
            cognit_logger.error("Sync request error; {0}".format(resp.err))

        return resp

    def call_async(
        self,
        func: Callable,
        *params,
        **kwargs,
    ) -> Optional[AsyncExecResponse]:
        """
        Perform the offload of a function to the cognit platform without \
        blocking.

        Args:
            func (Callable): The target funtion to be offloaded
            params (List[Any]): Arguments needed to call the function

        Returns:
            AsyncExecResponse: Async Response Code
            or None
        """

        # If the Serverless Runtime client is not initialized,
        # create an instance with the endpoint
        if self.src == None:
            if (
                self.sr_instance == None
                or self.sr_instance.SERVERLESS_RUNTIME.FAAS.ENDPOINT == None
            ):
                cognit_logger.error(
                    "Serverless Runtime instance has not been requested yet"
                )
                return None

            self.src = ServerlessRuntimeClient(
                self.sr_instance.SERVERLESS_RUNTIME.FAAS.ENDPOINT
            )

        parser = FaasParser()

        # Serialize the function an the params
        serialized_fc = parser.serialize(func)
        serialized_params = []
        for param in params:
            serialized_params.append(parser.serialize(param))

        func_hash = hashlib.sha256(func.__code__.co_code).hexdigest()

        # Payload JSON definition
        offload_fc = ExecSyncParams(
            fc=serialized_fc, params=serialized_params, lang="PY", fc_hash=func_hash
        )

        # TODO: The client should update the sr status before offloading a function

        return self.src.faas_execute_async(offload_fc)

    def wait(
        self,
        Id: AsyncExecId,
        timeout: float,
    ) -> Optional[AsyncExecResponse]:
        """
        Wait until an asynchronous (unblocking) task is finished and ready to be
        read.

        Args:
            Id (AsyncExecId): ID of the FaaS to which the function was sent.
            timeout (int): Timeout in milisecs. after which it will stop
            querying if the FaaS was finished or not.

        Returns:
            AsyncExecResponse: Will return async execution response data type.
            or None
        """
        # If the Serverless Runtime client is not initialized,
        # create an instance with the endpoint
        if self.src == None:
            if (
                self.sr_instance == None
                or self.sr_instance.SERVERLESS_RUNTIME.FAAS.ENDPOINT == None
            ):
                cognit_logger.error(
                    "Serverless Runtime instance has not been requested yet"
                )
                return None

            self.src = ServerlessRuntimeClient(
                self.sr_instance.SERVERLESS_RUNTIME.FAAS.ENDPOINT
            )

        parser = FaasParser()

        # Define interval to 1 milisec.
        iv = 1
        # Timeout management loop.
        while timeout - iv > 0:
            response = self.src.wait(Id.faas_task_uuid)
            if response != None and response.status == AsyncExecStatus.READY:
                if response.res.res != None:
                    response.res.res = parser.deserialize(response.res.res)
                return response
            time.sleep(iv / 1000.0)
            timeout -= iv
        return response

    def delete(self) -> None:
        """
        Deletes the specified ServerlessRuntimeContext on demand.
        """
        if self.sr_instance == None or self.sr_instance.SERVERLESS_RUNTIME.ID == None:
            cognit_logger.error(
                "Serverless Runtime instance has not been requested yet"
            )
            return None
        self.pec.delete(self.sr_instance.SERVERLESS_RUNTIME.ID)
