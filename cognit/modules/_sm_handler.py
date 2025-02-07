from cognit.modules._device_runtime_state_machine import DeviceRuntimeStateMachine
from cognit.modules._sync_result_queue import SyncResultQueue
from cognit.models._cognit_frontend_client import Scheduling
from cognit.modules._cognitconfig import CognitConfig
from cognit.modules._call_queue import CallQueue
from cognit.modules._logger import CognitLogger
import time

class StateMachineHandler():

    def __init__(self, config: CognitConfig, requirements: Scheduling, call_queue: CallQueue, sync_result_queue: SyncResultQueue):

        # Logger initialization
        self.logger = CognitLogger()

        # Running flag
        self.running = True

        # State machine initialization
        self.sm = DeviceRuntimeStateMachine(config, requirements, call_queue, sync_result_queue)

    def change_requirements(self, new_requirements: Scheduling) -> bool:
        """
        Change the requirements of the Device Runtime

        Args:
            new_requirements (Scheduling): New requirements to be considered when offloading functions
        """

        return self.sm.change_requirements(new_requirements)
    
    def stop(self):
        """
        Stop the Device Runtime
        """
        self.running = False
    
    def run(self, interval=1):

        while self.running:

            self.logger.info("Current state: " + self.sm.current_state.id)
            # Evaluate the conditions of the current state
            self.evaluate_conditions()
            # Wait for the next iteration
            time.sleep(interval)

    def evaluate_conditions(self):
        """
        Evaluate the conditions of the current state to change to another state
        """
        if self.sm.current_state.id == "ready":
            self.handle_ready_state()
        elif self.sm.current_state.id == "init":
            self.handle_init_state()
        elif self.sm.current_state.id == "send_init_request":
            self.handle_send_init_request_state()
        elif self.sm.current_state.id == "get_ecf_address":
            self.handle_get_ecf_address_state()

    def handle_ready_state(self):
        """
        Handle the ready state
        """
        if not self.sm.is_cfc_connected():
            self.sm.token_not_valid_ready()
        elif not self.sm.is_ecf_connected():
            self.sm.token_not_valid_ready_2()
        else:
            if not self.sm.have_requirements_changed():
                self.sm.result_given()
            else:
                self.sm.ready_update_requirements()

    def handle_init_state(self):
        """
        Handle the init state
        """
        if self.sm.is_token_empty():
            self.sm.repeat_auth()
        else:
            self.sm.success_auth()

    def handle_send_init_request_state(self):
        """
        Handle the send_init_request state
        """
        if not self.sm.is_cfc_connected():
            self.sm.token_not_valid_requirements()  # The connection with the CFC is lost, re-authentication is needed
        elif not self.sm.are_requirements_uploaded():
            if self.sm.is_requirement_upload_limit_reached():
                self.sm.limit_requirements_upload()  # The attempt limit has been surpassed, restart the cognit frontend client
            else:
                self.sm.retry_requirements_upload()  # Retry uploading the requirements if the limit hasn't been reached yet
        elif self.sm.have_requirements_changed():
            print("Requirementes_changed: ", self.sm.have_requirements_changed())
            self.sm.send_init_update_requirements()  # The requirements have changed, re-upload the requirements
        else:
            self.sm.requirements_up()  # Requirements were successfully uploaded, proceed to get the ECF address


    def handle_get_ecf_address_state(self):
        """
        Handle the get_ecf_address state
        """
        if not self.sm.is_cfc_connected():
            self.sm.token_not_valid_address()  # The cognit frontend client disconnects, reauthentication is needed
        elif self.sm.is_ecf_connected():
            self.sm.address_obtained()  # The ECF client is connected, proceed to the ready state
        elif self.sm.is_get_address_limit_reached():
            self.sm.limit_get_address()  # The limit to get the address has been surpassed, restart the client
        else:
            self.sm.retry_get_address()  # Try to reconnect to the ECF client to get the address

