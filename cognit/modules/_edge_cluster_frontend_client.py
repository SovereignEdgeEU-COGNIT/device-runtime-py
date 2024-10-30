import requests as req
import pydantic
import json

from cognit.models._edge_cluster_frontend_client import ExecResponse, ExecutionMode
from cognit.modules._faas_parser import FaasParser
from cognit.modules._logger import CognitLogger

cognit_logger = CognitLogger()

class EdgeClusterFrontendClient:

    def __init__(self, token: str, address: str):
        """
        Initializes EdgeClusterFrontendClient. 

        Args:
            token (str): Token for the communication between the client 
            and the Edge Cluster Frontend
            address (str): address of the Edge Cluster Frontend
        """
        self.parser = FaasParser()
        self.set_has_connection(True)
        # Check if the parameters received are not null
        if token == None:
            cognit_logger.error("Token is Null")
            self.set_has_connection(False)
        if address == None:
            cognit_logger.error("Address is not given")
            self.set_has_connection(False)
        self.token = token
        # cognit_logger.warning(f"\n\n[ECFC] ---- {self.token}\n\n")
        self.address = address
        
    def execute_function(self, func_id: str, app_req_id: int, exec_mode: ExecutionMode, params_tuple: tuple) -> ExecResponse:
        """
        Triggers the execution of a function described by its id in a certain mode using certain paramters for its execution

        Args:
            func_id (str): Identifier of the function to be executed
            app_req_id (int): Identifier of the requirements associated to the function
            exec_mode (ExecutionMode): Selected mode for offloading (SYNC OR ASYNC)
            params (List[Any]): Arguments needed to call the function
        """

        # Create request
        cognit_logger.debug(f"Execute function with ID {func_id}")
        uri = f"{self.address}/v1/functions/{func_id}/execute"
        # Header
        headers = {
            "token": self.token
        }
        # Query parameters
        qparams = {
            "app_req_id": app_req_id,
            "mode": exec_mode.value
        }
        # Encode parameters
        serialized_params = []
        for param in params_tuple:
            serialized_param = self.parser.serialize(param)
            serialized_params.append(serialized_param)
        # Send request
        try:
            cognit_logger.debug(f"Sending function execution order...")
            response = req.post(uri, headers=headers, params=qparams, data=json.dumps(serialized_params))
            response.raise_for_status() 
            response_data = response.json()
            # Parse the response to an ExecResponse model
            response_obj = pydantic.parse_obj_as(ExecResponse, response_data)
            cognit_logger.debug(f"Result obtained {func_id}")
            # Evaluate response
            self.evaluate_response(response_obj)
        except req.exceptions.RequestException as e:
            cognit_logger.error(f"Error during execution: {e}")
            raise
        return response_obj

    def send_metrics(self):
        """
        Collects current device location and latency and sends it to the Edge Cluster Frontend 
        """   

        # Create request
        cognit_logger.debug("Retriving metrics...")
        uri = self.address + "/v1/device_metrics" 
        headers = {"token": self.token}
        # TODO: Add current location and latency to the request

        # Wait for the response
        response = req.post(uri, headers=headers)
        # Evaluate response
        self.evaluate_response(response)
        return response

    def evaluate_response(self, response: ExecResponse): 

        # Client has connection depending on the answer given by the ECF
        if response.ret_code == 200:
            cognit_logger.debug("Function execution success")
            self.set_has_connection(True)
        if response.ret_code == 401:
            cognit_logger.debug("Token not valid, client is unauthorized")
            self.set_has_connection(False)
        if response.ret_code == 400:
            cognit_logger.debug("Bad request. Has the token been added in the header?")
            self.set_has_connection(False)

    def get_has_connection(self):
        return self.has_connection
    
    def set_has_connection(self, is_connected):
        self.has_connection = is_connected