from cognit.models._edge_cluster_frontend_client import ExecResponse, ExecutionMode
from cognit.modules._faas_parser import FaasParser
from cognit.modules._logger import CognitLogger
import requests as req
import pydantic
import json

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class EdgeClusterFrontendClient:

    def __init__(self, token: str, address: str):
        """
        Initializes EdgeClusterFrontendClient. 

        Args:
            token (str): Token for the communication between the client 
            and the Edge Cluster Frontend
            address (str): address of the Edge Cluster Frontend
        """
        
        self.logger = CognitLogger()
        self.set_has_connection(True)
        self.parser = FaasParser()

        # Check if the parameters received are not null
        if token == None:
            self.logger.error("Token is Null")
            self.set_has_connection(False)
        if address == None:
            self.logger.error("Address is not given")
            self.set_has_connection(False)

        self.token = token
        self.address = address
        
    def execute_function(self, func_id: str, app_req_id: int, exec_mode: ExecutionMode, callback: callable, params_tuple: tuple, timeout: int) -> None | ExecResponse:
        """
        Triggers the execution of a function described by its id in a certain mode using certain paramters for its execution

        Args:
            func_id (str): Identifier of the function to be executed
            app_req_id (int): Identifier of the requirements associated to the function
            exec_mode (ExecutionMode): Selected mode for offloading (SYNC OR ASYNC)
            params (List[Any]): Arguments needed to call the function
        """

        # Create request
        self.logger.debug(f"Execute function with ID {func_id}")
        uri = f"{self.address}/v1/functions/{func_id}/execute"

        # Header
        header = self.get_header(self.token)
        # Query parameters
        qparams = self.get_qparams(app_req_id, ExecutionMode.SYNC) # Temporaly set to SYNC in order to get the response
        # Encoded parameters
        serialized_params = self.get_serialized_params(params_tuple)

        # Send request
        try:
            try:
                response = req.post(uri, headers=header, params=qparams, data=json.dumps(serialized_params), timeout=timeout)
            except req.exceptions.SSLError as e:
                if "CERTIFICATE_VERIFY_FAILED" not in str(e):
                    raise e
                self.logger.info(f"SSL certificate verification failed, retrying with verify=False for URI: {uri}")
                # Send request with verify=False because the uri uses a self-signed certificate
                response = req.post(uri, headers=header, params=qparams, data=json.dumps(serialized_params), verify=False, timeout=timeout)
            
            # Check if the response is successful
            response.raise_for_status() 
            response_data = response.json()

            # Parse the response to an ExecResponse model
            result = pydantic.parse_obj_as(ExecResponse, response_data)
            
            # Deserialize the response
            result.res = self.parser.deserialize(result.res)

            # Evaluate response
            self.evaluate_response(result)

        except req.exceptions.RequestException as e:
            self.logger.error(f"Error during execution: {e}")
            raise e

        if exec_mode == ExecutionMode.ASYNC:
            # Execute the callback function
            callback(result)
            return None
        else:
            return result

    def send_metrics(self, latency: int) -> bool:
        """
        Collects current device location and latency and sends it to the Edge Cluster Frontend 

        Args:
            location (str): Current location of the device
            latency (int): Current latency of the device
        """   

        # Create request
        self.logger.debug("Sending metrics...")
        uri = self.address + "/v1/device_metrics"
        # Header
        header = self.get_header(self.token)
        # JSON payload
        payload = {"latency": latency} 

        try:
            response = req.post(uri, headers=header, json=payload)
        except req.exceptions.SSLError as e:
            if "CERTIFICATE_VERIFY_FAILED" not in str(e):
                raise e
            self.logger.info(f"SSL certificate verification failed, retrying with verify=False for URI: {uri}")
            
            # Send request with verify=False because the uri uses a self-signed certificate
            response = req.post(uri, headers=header, json=payload, verify=False)

        return response.status_code == 200
    
    def evaluate_response(self, response: ExecResponse): 
        """
        Evaluates the response of the request

        Args:
            response (ExecResponse): Response of the request
        """
        if response.ret_code == 200:
            self.logger.debug("Function execution success")
            self.set_has_connection(True)
        if response.ret_code == 401:
            self.logger.debug("Token not valid, client is unauthorized")
            self.set_has_connection(False)
        if response.ret_code == 400:
            self.logger.debug("Bad request. Has the token been added in the header?")
            self.set_has_connection(False)


    def get_header(self, token: str):
        """
        Generates the header for the request

        Args:
            token (str): Token for the communication between the client 
            and the Edge Cluster Frontend
        """
        return {
            "token": token
        }
    
    def get_qparams(self, app_req_id: int, exec_mode: ExecutionMode):
        """
        Generates the query parameters for the request

        Args:
            app_req_id (int): Identifier of the requirements associated to the function
            exec_mode (ExecutionMode): Selected mode for offloading (SYNC OR ASYNC)
        """
        return {
            "app_req_id": app_req_id,
            "mode": exec_mode.value
        }
    
    def get_serialized_params(self, params_tuple: tuple):
        """
        Serializes the parameters to be sent in the request

        Args:
            params_tuple (tuple): Arguments needed to call the function
        """
        serialized_params = []
        for param in params_tuple:
            serialized_param = self.parser.serialize(param)
            serialized_params.append(serialized_param)
        return serialized_params

    def get_has_connection(self) -> bool:
        """
        Getter for the connection status
        """
        return self._has_connection
    
    def set_has_connection(self, is_connected):
        """
        Setter for the connection status
        """
        self._has_connection = is_connected
