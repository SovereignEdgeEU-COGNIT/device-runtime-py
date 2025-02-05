from cognit.modules._device_runtime_state_machine import DeviceRuntimeStateMachine
from cognit.models._edge_cluster_frontend_client import Scheduling
from cognit.modules._cognitconfig import CognitConfig
from cognit.modules._call_queue import CallQueue
from cognit.modules._logger import CognitLogger
import time

class StateMachineHandler():

    def __init__(self, config: CognitConfig, requirements: Scheduling, call_queue: CallQueue):
        self.logger = CognitLogger()
        # State machine initialization
        self.sm = DeviceRuntimeStateMachine(config, requirements, call_queue)

    # Run sm thread
    def run(self, interval: int = 1):
        while True:
            self.logger.debug(f"Current State: {self.sm.current_state.id}")
            # Try to execute the transitions of the current state
            for transition in self.sm.current_state.transitions:
                # Check if the transition is valid
                if transition.dest:  
                    try:
                        transition()  
                        self.logger.debug(f"Executed transition: {transition.identifier}")
                        break  # Stop the loop if a transition was executed
                    except Exception:
                        pass  # If the transition is not valid, try the next one
    
            # Some time between transitions to avoid high CPU usage
            time.sleep(interval)  