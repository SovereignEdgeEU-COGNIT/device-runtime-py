from cognit.models._device_runtime import Call, FunctionLanguage, ExecResponse, ExecutionMode
from cognit.modules._sync_result_queue import SyncResultQueue
from cognit.models._cognit_frontend_client import Scheduling
from cognit.modules._sm_handler import StateMachineHandler
from cognit.modules._cognitconfig import CognitConfig
from cognit.modules._call_queue import CallQueue
from cognit.modules._logger import CognitLogger
from threading import Thread
from typing import Callable

DEFAULT_CONFIG_PATH = "cognit/config/cognit_v2.yml"

"""
Class to manage the Device Runtime. It is responsible for offloading functions to the Cognit Frontend
"""
class DeviceRuntime:
    
    def __init__(self, config_path=DEFAULT_CONFIG_PATH) -> None:
        """
        Device Runtime creation based on the configuration file defined in cognit_path

        Args:
            config_path (str): Path of the configuration to be applied to access
            the Cognit Frontend
        """
        self.cognit_config = CognitConfig(config_path)
        self.sync_result_queue = SyncResultQueue()
        self.cognit_logger = CognitLogger()
        self.call_queue = CallQueue()
        self.current_reqs = None
        self.sm_handler = None
        self.sm_thread = None

    def init(self, init_reqs: dict) -> bool:
        """
        Launches SM thread 

        Args:
            init_reqs (dict): requirements to be considered when offloading functions
        """

        # Check if sm is already running
        if self.sm_thread != None:
            self.cognit_logger.error("DeviceRuntime is already running")
            return False
        
        # Check if init_reqs were provided
        if init_reqs == None:
            self.cognit_logger.error("init_reqs not provided")
            return False
        
        # Convert requirements into a Scheduling Object
        self.current_reqs = Scheduling(**init_reqs)

        # State machine initialization
        if self.sm_handler == None:
            self.sm_handler = StateMachineHandler(self.cognit_config, self.current_reqs, self.call_queue, self.sync_result_queue)

        # Launch SM thread
        try:
            self.sm_thread = Thread(target=self.sm_handler.run)
            self.sm_thread.start()
        except Exception as e:
            raise Exception(f"DeviceRuntime could not be initialized: {e}")
        
        self.cognit_logger.info("DeviceRuntime initialized")
        return True
    
    def stop(self) -> bool:
        """
        Stops the SM thread

        Returns:
            bool: True if the SM thread was stopped successfully, False otherwise
        """

        if self.sm_thread == None:
            self.cognit_logger.error("DeviceRuntime is not running")
            return False

        # Stop the SM thread
        self.sm_handler.stop()
        self.sm_thread.join()
        self.sm_thread = None
        self.sm_handler = None
        self.cognit_logger.info("DeviceRuntime stopped")
        return True
    
    def update_requirements(self, new_reqs: dict) -> bool:
        """
        Relaunches the SM thread with the new requirements

        Args:
            new_reqs (dict): new requirements to be considered when offloading functions
        """

        # Check if new_reqs were provided
        if new_reqs == None:
            self.cognit_logger.error("new_reqs not provided")
            return False
        
        if self.sm_thread == None:
            self.cognit_logger.error("DeviceRuntime is not running")
            return False

        # Convert requirements into a Scheduling Object
        new_reqs = Scheduling(**new_reqs)

        # Check new_reqs are different from the current ones
        if self.current_reqs == new_reqs:
            self.cognit_logger.error("New requirements are the same as the current ones")
            return False
        
        # Update the current requirements
        are_updated = self.sm_handler.change_requirements(new_reqs)
        if not are_updated:
            self.cognit_logger.error("Requirements could not be updated")
            return False
        self.current_reqs = new_reqs
        return True

    def call_async(self, function: Callable, callback: Callable, *params: tuple) -> bool:
        """
        Offloads a function asynchronously

        Args:
            function (Callable): The target funtion to be offloaded
            callback (Callable): The callback function to be executed after the offloaded function finishes
            params (List[Any]): Arguments needed to call the function
        """

        # Create a Call object
        call = Call(function=function, fc_lang=FunctionLanguage.PY, mode=ExecutionMode.ASYNC, callback=callback, params=params, timeout=None)

        # Add the call to the queue
        if self.call_queue.add_call(call):
            self.cognit_logger.debug("Function added to the queue")
            return True
        else:
            self.cognit_logger.error("Function could not be added to the queue")
            return False
        
    def call(self, function: Callable, *params: tuple, timeout: int = None) -> ExecResponse:
        """
        Offloads a function synchronously

        Args:
            function (Callable): The target funtion to be offloaded
            params (List[Any]): Arguments needed to call the function
        """

        # Create a Call object
        call = Call(function=function, fc_lang=FunctionLanguage.PY, mode=ExecutionMode.SYNC, callback=None, params=params, timeout=timeout)

        # Add the call to the queue
        if self.call_queue.add_call(call):
            self.cognit_logger.debug("Function added to the queue")
        else:
            self.cognit_logger.error("Function could not be added to the queue")
            return None
        
        # Wait for the result
        return self.sync_result_queue.get_sync_result()