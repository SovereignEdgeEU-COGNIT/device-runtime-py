import sys
sys.path.append(".")
from cognit.modules._edge_cluster_frontend_client import EdgeClusterFrontendClient
from cognit.modules._cognit_frontend_client import CognitFrontendClient, Scheduling
from cognit.models._edge_cluster_frontend_client import ExecutionMode
from cognit.modules._cognitconfig import CognitConfig
from cognit.modules._logger import CognitLogger
from statemachine import StateMachine, State
from typing import Callable

class DeviceRuntimeStateMachine(StateMachine):

    # States definition #

    init = State(initial=True)
    send_init_request = State()
    get_ecf_address = State()
    ready = State()
    
    # Transitions definition #

    # 1. Initialize
    # 1.1 Get credentials and authenticate to the cognit frontend
    success_auth = init.to(send_init_request, unless=["is_token_empty"])
    # 1.2 Token is empty, therefore, authentication was not done correctly
    repeat_auth = init.to.itself(cond=["is_token_empty"])
    # 2. Apply requirements
    # 2.1 If the requirements were succesfully uploaded, it is time to obtain the address
    requirements_up = send_init_request.to(get_ecf_address, cond=["is_cfc_connected", "are_requirements_uploaded"], unless=["have_requirements_changed"])
    # 2.2 The connection with the CFC is lost, re-authentication is needed
    token_not_valid_requirements = send_init_request.to(init, unless="is_cfc_connected")
    # 2.3 The requirements could not be uploaded but the attempt limit has not reached, retry
    retry_requirements_upload = send_init_request.to.itself(cond=["is_cfc_connected", "have_requirements_changed"], unless=["are_requirements_uploaded", "is_requirement_upload_limit_reached"])
    # 2.4 The attempt limit has been traspased, then the cognit frontend client is restarted
    limit_requirements_upload = send_init_request.to(init, cond=["is_cfc_connected", "is_requirement_upload_limit_reached"], unless=["are_requirements_uploaded"])
    # 2.5 If the requirements have changed and cognit frontend client is still connected, upload new requirements
    send_init_update_requirements = send_init_request.to.itself(cond=["is_cfc_connected", "have_requirements_changed"])
    # 3. Get ECF IP
    # 3.1 The ECF Client is connected. Therefore, the device runtime is ready to offload functions.
    address_obtained = get_ecf_address.to(ready, cond=["is_ecf_connected", "is_cfc_connected"], unless=["have_requirements_changed"])
    # 3.2 The cognit frontend client disconnects, it is needed to authenticate again
    token_not_valid_address = get_ecf_address.to(init, unless="is_cfc_connected")
    # 3.3 If the ECF client is not connected, try to reconnect
    retry_get_address = get_ecf_address.to.itself(cond=["is_cfc_connected"], unless=["is_ecf_connected", "is_get_address_limit_reached"])
    # 3.4 If the process has been done over a limit times, restart the client
    limit_get_address = get_ecf_address.to(init, cond=["is_get_address_limit_reached", "is_cfc_connected"], unless=["is_ecf_connected"])
    # 3.5 If the requirements have changed and the client is connected, upload new requirements
    address_update_requirements = get_ecf_address.to(send_init_request, cond=["have_requirements_changed", "is_cfc_connected"])
    # 4. Upload function
    # 4.1 Request another function if the clients are connected
    result_given = ready.to.itself(cond=["is_cfc_connected", "is_ecf_connected"], unless= "have_requirements_changed")
    # 4.2 Request new token if the one of the clients lost its connection
    token_not_valid_ready = ready.to(init, unless=["is_cfc_connected"])
    token_not_valid_ready_2 = ready.to(init, unless=["is_ecf_connected"])
    # 4.3 If the requirements have changed and token still valid, upload new requirements
    ready_update_requirements = ready.to(send_init_request, cond=["is_cfc_connected", "is_ecf_connected", "have_requirements_changed"])

    def __init__(self, cognit_conf_path):
        # Clients
        self.cfc = None
        self.ecf = None
        # Communication parameters
        self.token = None
        self.requirements = None
        self.config = CognitConfig(cognit_conf_path)
        #Counters
        self.up_req_counter = 0
        self.get_address_counter = 0
        # Logger
        self.logger = CognitLogger()
        # Booleans for conditioners
        self.requirements_uploaded = False
        self.requirements_changed = False
        super().__init__()

    # Get credentials by instantiating a CognitFrontendClient and authenticates to the Cognit Frontend  
    def on_enter_init(self):
        self.logger.debug("Entering INIT state")
        # Reset counters
        self.up_req_counter = 0
        self.get_address_counter = 0
        # Instantiate Cognit Frontend Client
        self.cfc = CognitFrontendClient(self.config)
        # This function will return if the client successfull authenticates or not
        self.token = self.cfc._authenticate()
        # self.logger.warning(f"\n\n[SMtk] ---- {self.token}\n\n")
        self.logger.debug("Token: " + str(self.token))

    # Upload processing requirements 
    def on_enter_send_init_request(self):
        self.logger.debug("Entering INIT_REQUEST state")
        self.logger.debug("SM: Setting sm.token to cfc token")
        self.cfc.set_token(self.token)
        self.logger.debug("SM: CFC Token succesfully set")
        
        # Upload requirements
        self.logger.debug("Uploading requirements: " + str(self.requirements))
        self.requirements_uploaded = self.cfc.init(self.requirements)
        # Increment attempt counter
        self.up_req_counter += 1

    # Get the edge cluster address 
    def on_enter_get_ecf_address(self):
        self.logger.debug("Entering GET_ECF_ADDRESS state")
        self.up_req_counter = 0
        # Get Edge Cluster Frontend 
        self.ecc_address = self.cfc._get_edge_cluster_address()
        # Initialize Edge Cluster client
        self.ecf = EdgeClusterFrontendClient(self.token, self.ecc_address)
        # Reset attemps counter
        self.get_address_counter += 1

    # State that waits for user functions offloading
    def on_enter_ready(self):
        self.logger.debug("Entering READY state")
        self.get_address_counter = 0

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
    
    def have_requirements_changed(self):
        self.logger.debug("Requirements changed: " + str(self.requirements_changed))
        return self.requirements_changed
    
    def update_requirements(self, requirements: Scheduling):
        """
        Manages the process leading to the loading of device requirements

        Args:
            requirements (Scheduling): The requirements to be uploaded
        """

        # Do not update requirements if they have not changed
        if requirements == self.requirements:
            self.requirements_changed = False
            self.logger.info("Requirements have not changed. Clients are not restarted.")
            return
        
        if requirements == None or type(requirements) is not Scheduling:
            self.logger.info("The requirements provided are not valid.")
            return
        self.requirements_changed = True
        self.requirements = requirements
        self.logger.info("Requirements have changed! Applying...")
        # New requirements cannot be considered as uploaded until update_requirements executes successfully
        self.requirements_uploaded = False

        # Check if CF client is connected before the other states are checked
        if not self.cfc.get_has_connection():
            self.logger.error("Frontend client is not connected: requirements could not be uploaded.")
            self.requirements = None
            if self.ready.is_active:
                self.token_not_valid_ready()
            elif self.get_ecf_address.is_active:
                self.token_not_valid_address()
            elif self.send_init_request.is_active:
                self.token_not_valid_requirements()
            return
        
        # Transitions depending on the current state of the SM
        
        # SEND_INIT_REQUEST
        if self.send_init_request.is_active:
            self.send_init_update_requirements()

        # INIT
        if self.init.is_active:
            self.success_auth()

        # READY
        if self.ready.is_active:
            self.up_req_counter = 0
            self.ready_update_requirements()

        # GET_ECF_ADDRESS
        if self.get_ecf_address.is_active:
            self.address_update_requirements()

        while not self.requirements_uploaded:
            self.logger.error("Counter: "+ str(self.up_req_counter))
            self.logger.error("Limit reached: "+ str(self.is_requirement_upload_limit_reached()))
            self.logger.error("Requirements upload failed. Retrying...")
            # Verify the limit of attemps has not been reached
            if self.is_requirement_upload_limit_reached():
                self.logger.error("Number of attempts reached: unable to upload requirements. State machine is now in init state.")
                self.requirements = None
                self.limit_requirements_upload()
                self.requirements_changed = False
                return
            self.retry_requirements_upload()

        self.logger.info("Requirements successfully uploaded! Entering GET_ECF_ADDRESS state...")
        self.requirements_changed = False
        self.requirements_up()
        # Reset requirements_changed flag
        self.requirements_changed = False


    # In charge of offloading a function
    def offload_function(self, func: Callable, *params):
        """
        Handles the process that derive in the execution of a function in the cloud-edge continuum

        Args:
            function (Callable): The function to be offloaded
            params (List[Any]): Arguments needed to call the function
        """

        # If the state machine is able to offload functions
        if self.ready.is_active:
            response = self._execute_function_offloading(func, *params)
            return response  # Return response when ready
        else:
            self.logger.debug("State is not READY. Handling transitions...")
            self._handle_transitions()
            self.logger.debug("Retrying function offload after state transitions...")
            # Retry function offloading after handling transitions
            return self.offload_function(func, *params)  # Return the recursive call

    # Uploads and executes the function
    def _execute_function_offloading(self, func: Callable, *params):
        app_req_id, function_id = self.cfc._serialize_and_upload_fc_to_daas_gw(func)
        self.logger.debug("Waiting for result...")
        self.response = self.ecf.execute_function(function_id, app_req_id, ExecutionMode.SYNC, params)
        if self.response.res is not None:
            self.logger.info(f"Result: {self.response.res}")
        else:
            self.logger.info("Result not given!")
        return self.response

    # Manage the transitions based on the current state (eventually will reach ready state)
    def _handle_transitions(self):
        if self.send_init_request.is_active:
            self._handle_send_init_request_state()
        elif self.get_ecf_address.is_active:
            self._handle_get_ecf_address_state()
        elif self.ready.is_active:
            self._handle_ready_state()
        elif self.init.is_active:
            self.logger.debug("Client is in INIT state, re-authenticating and initializing...")
            self._handle_init_state()

    # Handles init state
    def _handle_init_state(self):
        if not self.is_token_empty():
            self.success_auth()
        else:
            self.repeat_auth()

    # Handles send_init_request state
    def _handle_send_init_request_state(self):
        if self.cfc.get_has_connection():
            if self.have_requirements_changed():
                self.logger.debug("Requirements have changed, re-uploading...")
                self.send_init_update_requirements()
            else:
                if self.is_requirement_upload_limit_reached():
                    self.logger.debug("Requirement upload limit reached, restarting client.")
                    self.limit_requirements_upload()
                elif not self.are_requirements_uploaded():
                    self.logger.debug("Retrying to upload requirements...")
                    self.retry_requirements_upload()
                else:
                    self.logger.debug("Requirements uploaded successfully, moving to get ECF address.")
                    self.requirements_up()
        else:
            self.logger.debug("Cognit Frontend Client disconnected, re-authenticating...")
            self.token_not_valid_requirements()

    # Handles get_ecf_address state
    def _handle_get_ecf_address_state(self):
        if self.cfc.get_has_connection():
            if self.have_requirements_changed():
                self.logger.debug("Requirements changed during address fetch, re-uploading...")
                self.address_update_requirements()
            else:
                if self.is_get_address_limit_reached():
                    self.logger.debug("ECF address fetch limit reached, restarting client.")
                    self.limit_get_address()
                elif not self.ecf.get_has_connection():
                    self.logger.debug("Retrying to fetch ECF address...")
                    self.retry_get_address()
                else:
                    self.logger.debug("ECF address obtained, transitioning to READY.")
                    self.address_obtained()
        else:
            self.logger.debug("Cognit Frontend Client disconnected, re-authenticating...")
            self.token_not_valid_address()

    # Handles ready state
    def _handle_ready_state(self):
        if self.have_requirements_changed():
            self.logger.debug("Requirements changed, uploading updated requirements...")
            self.ready_update_requirements()
        elif not self.cfc.get_has_connection():
            self.logger.debug("Cognit Frontend Client disconnected, re-authenticating...")
            self.token_not_valid_ready()
        elif not self.ecf.get_has_connection():
            self.logger.debug("Edge Cluster Frontend Client disconnected, re-authenticating...")
            self.token_not_valid_ready_2()

    # Checks if the SM is able to offload functions
    def is_offloading_possible(self):
        return self.is_ready() 