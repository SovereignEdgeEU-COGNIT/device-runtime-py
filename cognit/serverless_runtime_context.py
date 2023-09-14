import time
from enum import Enum
from typing import Callable, List, Optional

from cognit.models._prov_engine_client import FaaSConfig, FaaSState, ServerlessRuntime
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
        self.policy_name = "energy"
        self.energy_percentage = energy_percentage

    def serialize_requirements(self) -> str:
        return '{"energy":' + str(self.energy_percentage) + "}"


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

    def create(
        self,
        serveless_runtime_config: ServerlessRuntimeConfig,
    ) -> StatusCode:
        ## Create FaasConfig scheduling policies from the user provided objects
        policies = ""
        requirements = ""

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
        )

        new_sr_request = ServerlessRuntime(
            NAME=serveless_runtime_config.name,
            FAAS=faas_config,
        )

        new_sr_response = self.pec.create(new_sr_request)

        if new_sr_response == None:
            cognit_logger.error("Serverless Runtime creation request failed")
            return StatusCode.ERROR

        if new_sr_response.FAAS.STATE != FaaSState.PENDING:
            cognit_logger.error(
                "Serverless Runtime creation request failed: returned state is not PENDING ({0})".format(
                    new_sr_response.FAAS.STATE
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

        if self.sr_instance == None or self.sr_instance.ID == None:
            cognit_logger.error(
                "Serverless Runtime instance has not been requested yet"
            )
            return None

        # Retrieve the Serverless Runtime instance from the Provisioning Engine
        sr_response = self.pec.retrieve(self.sr_instance.ID)

        # Update the Serverless Runtime cached instance
        if sr_response != None:
            self.sr_instance = sr_response

        return self.sr_instance.FAAS.STATE

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
        # **kwargs,
    ) -> ExecResponse:
        """
        Perform the offload of a function to the cognit platform and wait for\
        the result.

        Args:
            func (Callable): The target funtion to be offloaded
            params (List[Any]): Arguments needed to call the function

        Returns:
            ExecResponse: Response Code
        """

        # If the Serverless Runtime client is not initialized,
        # create an instance with the endpoint
        if self.src == None:
            if self.sr_instance == None or self.sr_instance.FAAS.ENDPOINT == None:
                cognit_logger.error(
                    "Serverless Runtime instance has not been requested yet"
                )
                return ExecResponse(ExecReturnCode.ERROR)

            self.src = ServerlessRuntimeClient(self.sr_instance.FAAS.ENDPOINT)

        parser = FaasParser()

        # Serialize the function an the params
        serialized_fc = parser.serialize(func)
        serialized_params = []
        for param in params:
            serialized_params.append(parser.serialize(param))

        # Payload JSON definition
        offload_fc = ExecSyncParams(
            fc=serialized_fc, params=serialized_params, lang="PY"
        )

        # TODO: The client should update the sr status before offloading a function
        # if self.status() ==

        return self.src.faas_execute_sync(offload_fc)

    def call_async(
        self,
        func: Callable,
        *params,
    ) -> AsyncExecResponse:
        """
        Perform the offload of a function to the cognit platform without \
        blocking.

        Args:
            func (Callable): The target funtion to be offloaded
            params (List[Any]): Arguments needed to call the function

        Returns:
            AsyncExecResponse: Async Response Code
        """

        # If the Serverless Runtime client is not initialized,
        # create an instance with the endpoint
        if self.src == None:
            if self.sr_instance == None or self.sr_instance.FAAS.ENDPOINT == None:
                cognit_logger.error(
                    "Serverless Runtime instance has not been requested yet"
                )
                return AsyncExecResponse(
                    status=AsyncExecStatus.READY,
                    res=ExecResponse(ret_code=ExecReturnCode.ERROR),
                    exec_id="0",
                )

            self.src = ServerlessRuntimeClient(self.sr_instance.FAAS.ENDPOINT)

        parser = FaasParser()

        # Serialize the function an the params
        serialized_fc = parser.serialize(func)
        serialized_params = []
        for param in params:
            serialized_params.append(parser.serialize(param))

        # Payload JSON definition
        offload_fc = ExecSyncParams(
            fc=serialized_fc, params=serialized_params, lang="PY"
        )

        # TODO: The client should update the sr status before offloading a function

        return self.src.faas_execute_async(offload_fc)

    def wait(
        self,
        Id: AsyncExecId,
        timeout: float,
    ) -> AsyncExecResponse:
        """
        Wait until an asynchronous (unblocking) task is finished and ready to be
        read.

        Args:
            Id (AsyncExecId): ID of the FaaS to which the function was sent.
            timeout (int): Timeout in secs. after which it will stop querying if the FaaS
            was finished or not.

        Returns:
            AsyncExecResponse: Will return async execution response data type.
        """
        # If the Serverless Runtime client is not initialized,
        # create an instance with the endpoint
        if self.src == None:
            if self.sr_instance == None or self.sr_instance.FAAS.ENDPOINT == None:
                cognit_logger.error(
                    "Serverless Runtime instance has not been requested yet"
                )
                return AsyncExecResponse(
                    status=AsyncExecStatus.READY,
                    res=ExecResponse(ret_code=ExecReturnCode.ERROR),
                    exec_id="000-000-000",
                )

            self.src = ServerlessRuntimeClient(self.sr_instance.FAAS.ENDPOINT)

        parser = FaasParser()

        # Define interval to 1 sec.
        iv = 1
        # Timeout management loop.
        while timeout - iv > 0:
            response = self.src.wait(Id.faas_task_uuid)
            if response.status == AsyncExecStatus.READY:
                return response
            time.sleep(iv)
            timeout -= iv
        return response

    def delete(self, sr_id: int) -> None:
        """
        Deletes the specified ServerlessRuntimeContext on demand.
        """
        self.pec.delete(sr_id)
