from cognit.modules._edge_cluster_frontend_client import EdgeClusterFrontendClient
from cognit.modules._cognit_frontend_client import CognitFrontendClient, Scheduling
from cognit.modules._latency_calculator import LatencyCalculator
from cognit.modules._sync_result_queue import SyncResultQueue
from cognit.modules._cognitconfig import CognitConfig
from cognit.modules._call_queue import CallQueue
from cognit.modules._logger import CognitLogger
from cognit.models._device_runtime import Call
from statemachine import StateMachine, State
import threading

import sys

sys.path.append(".")

class DeviceRuntimeStateMachine(StateMachine):

    # States definition #

    init = State(initial=True)
    send_init_request = State()
    get_ecf_address = State()
    ready = State()
    
    # Transitions definition #

    # 1. Login and authenticate

    # 1.1 Get credentials and authenticate to the cognit frontend
    success_auth = init.to(send_init_request, unless=["is_token_empty"])
    # 1.2 Token is empty, therefore, authentication was not done correctly
    repeat_auth = init.to.itself(cond=["is_token_empty"])

    # 2. Upload requirements

    # 2.1 If the requirements were succesfully uploaded, it is time to obtain the address
    requirements_up = send_init_request.to(get_ecf_address, cond=["is_cfc_connected", "are_requirements_uploaded"], unless=["have_requirements_changed"])
    # 2.2 The connection with the CFC is lost, re-authentication is needed
    token_not_valid_requirements = send_init_request.to(init, unless="is_cfc_connected")
    # 2.3 The requirements could not be uploaded but the attempt limit has not reached, retry
    retry_requirements_upload = send_init_request.to.itself(cond=["is_cfc_connected"], unless=["are_requirements_uploaded", "is_requirement_upload_limit_reached"])
    # 2.4 The attempt limit has been traspased, then the cognit frontend client is restarted
    limit_requirements_upload = send_init_request.to(init, cond=["is_cfc_connected", "is_requirement_upload_limit_reached"], unless=["are_requirements_uploaded"])
    # 2.5 The requirements have changed, therefore, the requirements are uploaded again
    send_init_update_requirements = send_init_request.to.itself(cond=["is_cfc_connected", "have_requirements_changed"])

    # 3. Get Edge Cluster Frontend address

    # 3.1 The ECF Client is connected. Therefore, the device runtime is ready to offload functions.
    address_obtained = get_ecf_address.to(ready, cond=["is_ecf_connected", "is_cfc_connected"], unless=["have_requirements_changed"])
    # 3.2 The cognit frontend client disconnects, reauthentication is needed
    token_not_valid_address = get_ecf_address.to(init, unless="is_cfc_connected")
    # 3.3 If the ECF client is not connected, try to reconnect
    retry_get_address = get_ecf_address.to.itself(cond=["is_cfc_connected"], unless=["is_ecf_connected", "is_get_address_limit_reached"])
    # 3.4 If the process has been done over a limit times, restart the client
    limit_get_address = get_ecf_address.to(init, cond=["is_get_address_limit_reached", "is_cfc_connected"], unless=["is_ecf_connected"])
    # 3.5 The requirements have changed, therefore, the requirements are uploaded again
    get_address_update_requirements = get_ecf_address.to(send_init_request, cond=["is_cfc_connected", "have_requirements_changed"])

    # 4. Upload functions

    # 4.1 Request another function if the clients are connected
    result_given = ready.to.itself(cond=["is_cfc_connected", "is_ecf_connected"], unless=["have_requirements_changed"])
    # 4.2 Request new token if the one of the clients lost its connection
    token_not_valid_ready = ready.to(init, unless=["is_cfc_connected"])
    token_not_valid_ready_2 = ready.to(init, unless=["is_ecf_connected"])
    # 4.3 The requirements have changed, therefore, the requirements are uploaded again
    ready_update_requirements = ready.to(send_init_request, cond=["is_cfc_connected", "is_ecf_connected", "have_requirements_changed"])
  
    def __init__(self, config: CognitConfig, requirements: Scheduling, call_queue: CallQueue, sync_result_queue: SyncResultQueue):
        # Clients
        self.cfc = None
        self.ecf = None

        # Communication parameters
        self.token = None
        self.requirements = requirements
        self.new_requirements = None
        self.config = config

        # Counters
        self.up_req_counter = 0
        self.get_address_counter = 0

        # Logger
        self.logger = CognitLogger()

        # Booleans for conditioners
        self.requirements_uploaded = False
        self.requirements_changed = False

        # Get queues
        self.call_queue = call_queue
        self.sync_results_queue = sync_result_queue

        # Latency thread
        self.latency_calculator = None
        self.lc_thread = None
        super().__init__()

    # Get credentials by instantiating a CognitFrontendClient and authenticates to the Cognit Frontend  
    def on_enter_init(self):

        # Reset counter
        self.up_req_counter = 0
        self.get_address_counter = 0

        if self.latency_calculator is not None:
            self.latency_calculator.stop()
            self.latency_calculator = None
            self.lc_thread.join()
            self.lc_thread = None

        # Instantiate Cognit Frontend Client
        self.cfc = CognitFrontendClient(self.config)

        # This function will return if the client successfull authenticates or not
        self.token = self.cfc._authenticate()
        self.logger.debug("Token: " + str(self.token))

    # Upload processing requirements 
    def on_enter_send_init_request(self):

        if self.latency_calculator is not None:
            self.latency_calculator.stop()
            self.latency_calculator = None
            self.lc_thread.join()
            self.lc_thread = None
            
        # Set token to the CFC client
        self.logger.debug("SM: Setting sm.token to cfc token")
        self.cfc.set_token(self.token)

        if self.requirements_changed:
            self.requirements = self.new_requirements

        # Upload requirements
        self.logger.debug("Uploading requirements: " + str(self.requirements))
        self.requirements_uploaded = self.cfc.init(self.requirements)

        if self.requirements_uploaded:
            self.requirements_changed = False
            self.new_requirements = None
        
        # Increment attempt counter
        self.up_req_counter += 1   

    # Get the edge cluster address 
    def on_enter_get_ecf_address(self):

        # Reset counter
        self.up_req_counter = 0

        if self.latency_calculator is not None:
            self.latency_calculator.stop()
            self.latency_calculator = None
            self.lc_thread.join()
            self.lc_thread = None

        # Get Edge Cluster Frontend 
        self.ecc_address = self.cfc._get_edge_cluster_address()

        # Initialize Edge Cluster client
        self.ecf = EdgeClusterFrontendClient(self.token, self.ecc_address)

        if self.latency_calculator is None and self.ecf.get_has_connection():

            # Launch latency calculator
            self.latency_calculator = LatencyCalculator(self.ecf)
            self.lc_thread = threading.Thread(target=self.latency_calculator.run)
            self.lc_thread.start()

        # Reset attemps counter
        self.get_address_counter += 1

    # State that waits for user functions offloading
    def on_enter_ready(self):

        # Reset counter
        self.get_address_counter = 0

        # Get Call
        call = self.call_queue.get_call()  # type: Call

        # If there is a call, offload it
        if call is not None:

            # Get the app requirements id
            app_req_id = self.cfc.get_app_requirements_id()

            # Upload function to the ECF
            function_id = self.cfc.upload_function_to_daas(call.function)
            
            # Execute function
            if function_id is None:
                self.logger.error("Function could not be uploaded")
                
            else:
                try:
                    if call.mode == "sync":
                        # Execute function
                        result = self.ecf.execute_function(function_id, app_req_id, call.mode, call.callback, call.params) 
                        # Add result to the queue
                        self.sync_results_queue.add_sync_result(result)
                    else:
                        self.ecf.execute_function(function_id, app_req_id, call.mode, call.callback, call.params)
                except Exception as e:
                    self.logger.error("There was a request error. Detailed message: {0}".format(e))
                         
    # Checks if CF client has connection with the CF
    def is_cfc_connected(self):
        self.logger.debug("Cognit Frontend Client connected: " + str(self.cfc.get_has_connection()))
        return self.cfc.get_has_connection()

    # Checks if ECF client has connection with the ECF
    def is_ecf_connected(self):
        self.logger.debug("Edge Cluster Frontend connected: " + str(self.ecf.get_has_connection()))
        return self.ecf.get_has_connection()
    
    # Check if the token received is empty
    def is_token_empty(self):
        return self.token is None
    
    # Check if three requirement upload attemps have been made 
    def is_requirement_upload_limit_reached(self):
        self.logger.debug("Number of attempts uploading requirements: " + str(self.up_req_counter))
        self.has_requirements_upload_limit_reached = self.up_req_counter == 3
        return self.has_requirements_upload_limit_reached 
    
    # Check if the requirements are uploaded or not
    def are_requirements_uploaded(self):
        self.logger.debug("Requirements uploaded: " + str(self.requirements_uploaded))
        return self.requirements_uploaded
    
    # Check if three attemps have been made for getting the address
    def is_get_address_limit_reached(self):
        self.logger.debug("Number of attempts getting Edge Cluster address: " + str(self.get_address_counter))
        self.has_address_request_limit_reached = self.get_address_counter == 3
        return self.has_address_request_limit_reached
    
    # Check if the requirements have changed
    def have_requirements_changed(self):
        self.logger.debug("Requirements changed: " + str(self.requirements_changed))
        return self.requirements_changed

    # Change the requirements of the Device Runtime
    def change_requirements(self, new_requirements: Scheduling):
        if self.requirements == new_requirements:
            self.logger.error("New requirements are the same as the current ones")
            return False
        elif self.requirements is None:
            self.logger.error("Requirements are None")
            return False
        else:
            self.logger.debug("Changing requirements")
            self.new_requirements = new_requirements
            self.requirements_changed = True
            return True
        

        
