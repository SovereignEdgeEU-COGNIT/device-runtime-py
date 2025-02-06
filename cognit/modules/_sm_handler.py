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

        # State machine initialization
        self.sm = DeviceRuntimeStateMachine(config, requirements, call_queue, sync_result_queue)
    
    def run(self, interval=1):

        while True:

            self.logger.info("Current state: " + self.sm.current_state.id)
            # Evaluar las condiciones de transición para cambiar de estado
            self.evaluate_conditions()
            # Esperar un segundo antes de evaluar nuevamente
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
        if self.sm.is_cfc_connected() and self.sm.is_ecf_connected():
            self.sm.result_given()
        elif not self.sm.is_cfc_connected():
            self.sm.token_not_valid_ready()
        elif not self.sm.is_ecf_connected():
            self.sm.token_not_valid_ready_2()

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
        if self.sm.is_cfc_connected() and self.sm.are_requirements_uploaded():
            self.sm.requirements_up()
        elif not self.sm.is_cfc_connected():
            self.sm.token_not_valid_requirements()
        elif self.sm.is_cfc_connected() and not self.sm.are_requirements_uploaded() and not self.sm.is_requirement_upload_limit_reached():
            self.sm.retry_requirements_upload()
        elif self.sm.is_cfc_connected() and not self.sm.are_requirements_uploaded() and self.sm.is_requirement_upload_limit_reached():
            self.sm.limit_requirements_upload()

    def handle_get_ecf_address_state(self):
        """
        Handle the get_ecf_address state
        """
        if self.sm.is_cfc_connected() and self.sm.is_ecf_connected():
            self.sm.address_obtained()
        elif not self.sm.is_cfc_connected():
            self.sm.token_not_valid_address()
        elif self.sm.is_cfc_connected() and not self.sm.is_ecf_connected() and not self.sm.is_get_address_limit_reached():
            self.sm.retry_get_address()
        elif self.sm.is_cfc_connected() and not self.sm.is_ecf_connected() and self.sm.is_get_address_limit_reached():
            self.sm.limit_get_address()