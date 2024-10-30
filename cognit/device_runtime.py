from typing import Callable

from cognit.modules._device_runtime_state_machine import DeviceRuntimeStateMachine
from cognit.models._edge_cluster_frontend_client import ExecReturnCode
from cognit.models._cognit_frontend_client import Scheduling
from cognit.modules._logger import CognitLogger
from cognit.modules._faas_parser import FaasParser

cognit_logger = CognitLogger()

DEFAULT_CONFIG_PATH = "cognit/config/cognit_v2.yml"

class DeviceRuntime:
    def __init__(
        self,
        config_path=DEFAULT_CONFIG_PATH,
    ) -> None:
        """
        Device Runtime creation based on the configuration file defined in cognit_path

        Args:
            config_path (str): Path of the configuration to be applied to access
            the Cognit Frontend
        """
        self.config_path = config_path
        self.faas_parser = FaasParser()
        self.device_runtime_sm = None


    def init(self, init_reqs: dict):
        """
        Initializes state machine, authorizes to the Cognit Frontend and upload the
        requirements to the Cognit Frontend. 

        Args:
            init_reqs (dict): requirements to be considered when offloading functions
        """
        if init_reqs == None:
            raise TypeError
        # Convert requirements into a Scheduling Object
        init_reqs = Scheduling(**init_reqs)
        # State machine initialization
        if self.device_runtime_sm == None:
            self.device_runtime_sm = DeviceRuntimeStateMachine(self.config_path)
        # Upload initial requirements
        self.device_runtime_sm.update_requirements(init_reqs)

        
    def call(self, function: Callable, *params, new_reqs: dict = None):
        """
        Initializes state machine, authorizes to the Cognit Frontend and upload the
        requirements to the Cognit Frontend. 

        Args:
            function (Callable): The target funtion to be offloaded
            new_reqs (dict): new requirements to be considered when offloading functions
            params (List[Any]): Arguments needed to call the function
        """

        # Check if the SM was initialized
        if self.device_runtime_sm == None:
            raise Exception("call() function cannot be executed. DeviceRuntime has not been initialised.")
        # Update requirements if  provided
        if new_reqs is not None:
            new_reqs = Scheduling(**new_reqs)
            cognit_logger.debug("Requirements provided. Updating requirements if they changed ...")
            self.device_runtime_sm.update_requirements(new_reqs)
        # Offloading provided function 
        result = self.device_runtime_sm.offload_function(function, *params)
        # Return values depending on the execution status
        if result.ret_code == ExecReturnCode.SUCCESS:
            return result.ret_code, self.faas_parser.deserialize(result.res)
        else:
            return result.ret_code, result.err