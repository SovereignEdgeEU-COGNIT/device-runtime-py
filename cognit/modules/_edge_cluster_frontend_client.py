from cognit.models._edge_cluster_frontend_client import ExecResponse, ExecutionMode, ExecReturnCode
from cognit.modules._faas_parser import FaasParser
from cognit.modules._logger import CognitLogger
import requests as req
import threading
import pydantic
import socket
import json
import time

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import logging
logging.getLogger("urllib3").setLevel(logging.WARNING)

def is_online(host="8.8.8.8", port=53, timeout=3) -> bool:
    """Simple check for Internet connectivity."""
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False

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
        
    def execute_function(self, func_id: str, app_req_id: int, exec_mode: ExecutionMode, callback: callable, params_tuple: tuple, timeout: int = 120) -> None | ExecResponse:
        """
        Triggers the execution of a function described by its id in a certain mode using certain paramters for its execution

        Args:
            func_id (str): Identifier of the function to be executed
            app_req_id (int): Identifier of the requirements associated to the function
            exec_mode (ExecutionMode): Selected mode for offloading (SYNC OR ASYNC)
            params (List[Any]): Arguments needed to call the function

        Returns:
            None | ExecResponse: If the execution mode is ASYNC, the function returns None. If the execution mode is SYNC, the function returns an ExecResponse object.
        """

        self.logger.debug(f"Execute function with ID {func_id}")
        uri = f"{self.address}/v1/functions/{func_id}/execute"

        header = self.get_header(self.token)
        qparams = self.get_qparams(app_req_id, ExecutionMode.SYNC)
        serialized_params = self.get_serialized_params(params_tuple)

        def do_post(result_container: dict):
            """Worker function to execute POST."""
            try:
                try:

                    result_container["response"] = req.post(uri, headers=header, params=qparams, data=json.dumps(serialized_params), timeout=timeout)

                except req.exceptions.SSLError as e:

                    if "CERTIFICATE_VERIFY_FAILED" not in str(e):
                        self.logger.error(f"SSL error during execution: {e}")
                        result_container["error"] = e

                    self.logger.info(f"SSL certificate verification failed, retrying with verify=False for URI: {uri}")
                    result_container["response"] = req.post(uri, headers=header, params=qparams, data=json.dumps(serialized_params), verify=False,timeout=timeout)

            except Exception as e:

                result_container["error"] = e

        # Run request in a background thread if no timeout defined
        result = {"response": None, "error": None}
        thread = threading.Thread(target=do_post, args=(result,), daemon=True)
        thread.start()

        if timeout is None:

            while thread.is_alive():

                if not is_online():
                    self.logger.error("Network disconnection detected during execution.")
                    self.set_has_connection(False)

                    return ExecResponse(ret_code=ExecReturnCode.ERROR, res=None, err="Network disconnection detected.")
                
                time.sleep(3)

            thread.join()
        else:
            thread.join()

        # Handle errors
        if result.get("error"):

            e = result["error"]
            self.logger.error(f"Error during execution: {e}")
            self.set_has_connection(False)
            return ExecResponse(ret_code=ExecReturnCode.ERROR, res=None, err=str(e))

        # Parse response
        response = result["response"]

        try:
            response.raise_for_status()
            response_data = response.json()

            result_obj = pydantic.parse_obj_as(ExecResponse, response_data)
            result_obj.res = self.parser.deserialize(result_obj.res)
            self.evaluate_response(result_obj)
            
        except Exception as e:

            self.logger.error(f"Unexpected error during function execution: {e}")
            self.set_has_connection(False)
            result_obj = ExecResponse(ret_code=ExecReturnCode.ERROR, res=None, err=str(e))

        if exec_mode == ExecutionMode.ASYNC:

            callback(result_obj)
            return None
        
        else:

            return result_obj
    
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

        Returns:
            dict: Dictionary with the header
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

        Returns:
            dict: Dictionary with the query parameters
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

        Returns:
            List[Any]: List of serialized parameters
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
