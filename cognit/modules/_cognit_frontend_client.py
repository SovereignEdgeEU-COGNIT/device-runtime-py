from cognit.models._cognit_frontend_client import Scheduling, UploadFunctionDaaS, FunctionLanguage, EdgeClusterFrontendResponse
from cognit.modules._latency_calculator import LatencyCalculator
from cognit.modules._cognitconfig import CognitConfig
from cognit.modules._faas_parser import FaasParser
from cognit.modules._logger import CognitLogger
from requests.auth import HTTPBasicAuth
from typing import Callable
import requests as req
import pydantic
import hashlib
import json

import logging
logging.getLogger("urllib3").setLevel(logging.WARNING)
                         
def filter_empty_values(data):
    if isinstance(data, dict):
        return {key: filter_empty_values(value) for key,\
                value in data.items() if value is not None}
    else:
        return data
    
"""
Class to interact with the Cognit Frontend Engine.
It is used to upload the requirements of the application, get the address of the Edge Cluster Frontend Engine
"""
class CognitFrontendClient:

    def __init__(self, config: CognitConfig):
        """
        Initializes app_req_id to None (it is updated when the user calls init())
        Initializes token to None (it is updated when the user calls init())
        
        Args:
            config: CognitConfig object containing a valid Cognit user and pwd
        """

        self.config = config
        self.endpoint = self.config.cognit_frontend_engine_endpoint
        self.latency_calculator = LatencyCalculator()
        self.is_max_latency_activated = False
        self.logger = CognitLogger()
        self._has_connection = False
        self.parser = FaasParser()
        self.app_req_id = None
        self.token = None
        
        # Storage
        self.offloaded_funs_hash_map = {}
        self.available_ecfs = []
    
    def init(self, reqs: Scheduling) -> bool:
        """
        Authenticates using loaded credentials to get a JWT token
        and creates or updates the application requirements in the Cognit Frontend Engine.

        Args:
            reqs: 'Scheduling' object containing the requirements of the app

        Returns:
            True if response.status_code is the expected (200)
            False otherwise
        """

        if not isinstance(reqs, Scheduling):
            self.logger.error("Reqs must be of type Scheduling")
            return False
        
        if self.token is None:
            self.logger.debug("Token is None, setting connection to False")
            self.set_has_connection(False)
            return False
        
        if reqs.GEOLOCATION is None:
            self.logger.error("GEOLOCATION is required to initialize Cognit")
            return False
        
        if reqs.MAX_LATENCY is not None:
            self.logger.debug("Max latency is activated, setting is_max_latency_activated to True")
            self.is_max_latency_activated = True
        else:
            self.logger.debug("Max latency is not activated, setting is_max_latency_activated to False")
            self.is_max_latency_activated = False

        header = self.get_header(self.token)
        
        try:

            if self.app_req_id is None:

                uri = f'{self.endpoint}/v1/app_requirements'

                self.logger.debug(f"Application requirements do not exist, creating them at {uri}")
                response = req.post(uri, headers=header, data=reqs.json(exclude_unset=True))

                self.app_req_id = response.json()

            else:

                uri = f'{self.endpoint}/v1/app_requirements/{self.app_req_id}'
                self.logger.debug(f"Application requirements already exist, updating them at {uri}")
                response = req.put(uri, headers=header, data=reqs.json(exclude_unset=True))   

        except Exception as e:
            
            self.logger.error(f"Error in app requirements creation: {e}")
            return False
        
        if not self.app_req_id:
            self.logger.error("Application ID could not be retrieved from the response")
            return False
        
        if response.status_code != 200:
            self._inspect_response(response)
            
        self.set_has_connection(response.status_code < 400)
        return response.status_code == 200  

    def get_edge_cluster_frontends_available(self) -> list[str]:
        """
        Interacts with the Cognit Frontend Engine to get a list of valid Edge Cluster Frontend Engine addresses
        available for the current application requirements.
        
        Returns:
            List of strings containing the addresses of the Edge Cluster Frontend Engines available
        """

        uri = f'{self.endpoint}/v1/app_requirements/{self.app_req_id}/ec_fe'
        headers = self.get_header(self.token)

        try:

            response = req.get(uri, headers=headers)

        except req.exceptions.RequestException as e:

            self.logger.error(f"Error in getting Edge Cluster Frontend Engine addresses: {e}")
            self.set_has_connection(False)
            return None

        self.set_has_connection(response.status_code < 400)

        if response.status_code >= 300:

            self.logger.warning(f"App req update returned {response.status_code}")
            self._inspect_response(response, "_app_req_update.warning")
            return None
        
        try:
            
            data = response.json()
            self.available_ecfs = []
            self.logger.debug(f"Response from get_ECFE: {data}")

            for item in data:

                self.logger.debug(f"Item in response: {item}")

                if not isinstance(item, dict):
                    self.logger.error(f"Item in response is not a dict: {item}")
                    return []
                
                template = item.get('TEMPLATE', None)
                name = item.get('NAME', None)

                if template is None:

                    self.logger.warning(f"TEMPLATE not found in item {name}")
                    continue
                
                edge_cluster_fe = template.get('EDGE_CLUSTER_FRONTEND', None)

                if edge_cluster_fe is None:

                    self.logger.warning(f"EDGE_CLUSTER_FRONTEND not found in template of item {name}")
                    continue

                self.logger.debug(f"Edge Cluster Frontend Engine: {edge_cluster_fe}")
                
                self.available_ecfs.append(edge_cluster_fe)
            
            return self.available_ecfs
        
        except Exception as e:

            self.logger.error(f"Error in get_ECFE response handling: {e}")
            return []
    
    def _get_edge_cluster_address(self) -> str:
        """
        Gets the address of the Edge Cluster Frontend Engine with the lowest latency (If max latency is activated).
        
        If max latency is not activated, it returns the first Edge Cluster Frontend Engine available (the nearest).
        
        Returns:
            The address of the Edge Cluster Frontend Engine with the lowest latency, or the first one if max latency is not activated.
            Returns None if no Edge Cluster Frontend Engines are available.
        """

        self.available_ecfs = self.get_edge_cluster_frontends_available()

        if not self.available_ecfs:

            self.logger.error("No Edge Cluster Frontend Engines available")
            return None
        
        if self.is_max_latency_activated:

            self.logger.debug("Max latency is activated, calculating latency for Edge Cluster Frontend Engines")
            # Calculate latency for each Edge Cluster Frontend Engine
            cluster_latencies = self.latency_calculator.get_latency_for_clusters(self.available_ecfs)

            if not cluster_latencies:

                self.logger.error("No valid latencies found for Edge Cluster Frontend Engines")
                return None

            # Send latencies to Cognit Frontend Engine

            # self.logger.debug("Sending latencies to Cognit Frontend Engine")
            # are_sent = self._send_latency_measurements(cluster_latencies)

            # if not are_sent:

            #     self.logger.error("Latencies could not be sent to Cognit Frontend Engine")
            #     return None
            
            # self.logger.debug("Latencies sent successfully to Cognit Frontend Engine")
            
            self.logger.debug(f"Latencies for Edge Cluster Frontend Engines: {cluster_latencies}")

            # Get the Edge Cluster Frontend Engine with the lowest latency
            lowest_latency_ecfe = min(cluster_latencies, key=cluster_latencies.get)
            self.logger.debug(f"Edge Cluster Frontend Engine with lowest latency: {lowest_latency_ecfe}")
            # lowest_latency_ecfe = "https://nature4hivemind.ddns.info"
            return lowest_latency_ecfe
        
        else:

            self.logger.debug(f"Max latency is not activated, returning first Edge Cluster Frontend Engine: {self.available_ecfs[0]}")
            # Return the first Edge Cluster Frontend Engine
            return self.available_ecfs[0] if self.available_ecfs else None
        
    def _authenticate(self) -> str:
        """
        Authenticate against Cognit FE to get a valid JWT Token

        Returns:
            Token: JSON dict containing the JWT Token
        """

        self.logger.debug(f"Requesting token for {self.config._cognit_frontend_engine_usr}")
        uri = f'{self.endpoint}/v1/authenticate'

        # Authenticate using HTTPBasicAuth if username and password are provided
        try:
            response = req.post(url=uri, auth=HTTPBasicAuth(self.config._cognit_frontend_engine_usr, self.config.cognit_frontend_engine_cfe_pwd))

            if response.status_code not in [200, 201]:
                self.logger.critical(f"Token creation failed with status code: {response.status_code}")
                self._inspect_response(response, "_authenticate.error")
                return None
            
        except req.exceptions.RequestException as e:
            self.logger.critical(f"Token creation failed with exception: {e}")
            self.set_has_connection(False)
            return None
        
        self.token = response.json()

        if self.token:
            self.set_has_connection(True)
            return self.token
        else:
            self.logger.critical("Token creation failed")
            self.set_has_connection(False)
            return None
        
    def _app_req_read(self) -> Scheduling | None:
        """
        Reads the app requirements using the application ID

        Returns:
            A dictionary containing the requested data of the app requirements
        """

        uri = f'{self.endpoint}/v1/app_requirements/{self.app_req_id}'
        headers = {"token": self.token}
        response = req.get(uri, headers=headers)
        
        if response.status_code != 200: # something went wrong

            self.logger.error(f"Read response code was not expected one with status_code: {response.status_code}")
            self._inspect_response(response, "_app_req_read.error")
            return None
        
        self.set_has_connection(response.status_code < 400)
        try:
            response = pydantic.parse_obj_as(Scheduling, response.json())
        except pydantic.ValidationError as e:
            self.logger.error(e)
        
        return response
    
    def _app_req_delete(self) -> bool:
        """
        Deletes the app requirements using the application ID

        Returns:
            True if response.status_code is the expected (204)
            False otherwise
        """
        self.logger.debug(f"Deleting application requirements {self.app_req_id}")

        uri = f'{self.endpoint}/v1/app_requirements/{self.app_req_id}'
        headers = {"token": self.token}

        response = req.delete(uri, headers=headers)
        if response.status_code >= 300:
            self.logger.warning(f"App req delete returned {response.status_code} with body: {response.json()}")
        
        self.set_has_connection(response.status_code < 400)
        return response.status_code == 204
    
    def upload_function_to_daas(self, function: Callable) -> int:
        """
        Serializes the function and uploads it to the Daas Gateway

        Args:
            func: Function to be serialized and uploaded

        Returns:
            The ID of the function in the Daas Gateway if successful, None otherwise
        """

        # Serialize function
        serialized_fc = self.parser.serialize(function)

        # Get hash of the function
        function_hash = hashlib.sha256(function.__code__.co_code).hexdigest()

        # Check if the function is already uploaded
        if self.is_function_uploaded(function_hash):
            self.logger.debug("Function already in local HASH map")
            return self.offloaded_funs_hash_map[function_hash]
        
        # Create UploadFunctionDaaS object
        function_data = UploadFunctionDaaS (
            LANG=FunctionLanguage.PY,
            FC=serialized_fc,
            FC_HASH=function_hash
        )

        # Send function to Daas
        cognit_fc_id = self.send_funtion_to_daas(function_data)
        self.logger.debug(f"Function uploaded with ID: {cognit_fc_id}")

        # Check if the function was uploaded
        if cognit_fc_id != None:
            # Add function to local HASH map
            self.offloaded_funs_hash_map[function_hash] = cognit_fc_id
            return cognit_fc_id
        else:
            self.logger.error("Function could not be uploaded")
            return None
    
    def send_funtion_to_daas(self, data: UploadFunctionDaaS) -> int:
        """
        Uploads the function to the Daas Gateway
        
        Args:
            data: UploadFunctionDaaS object containing the function data

        Returns:
            The ID of the function in the Daas Gateway if successful, None otherwise
        """

        self.logger.debug(f"Uploading function: {data}")

        uri = f'{self.endpoint}/v1/daas/upload'
        header = self.get_header(self.token)

        # Send data to DaaS
        response = req.post(uri, headers=header, data=data.json())

        if response.status_code != 200:
            self._inspect_response(response)
            return None
        
        # Get function ID
        function_id = response.json()
        return function_id
    
    def _send_latency_measurements(self, latencies: str) -> bool:
        """
        Sends the latencies to the Cognit Frontend Engine
        
        Args:
            latencies: String containing the latencies in JSON format

        Returns:
            True if the request was successful, False otherwise
        """
    
        uri = f'{self.endpoint}/v1/latency'
        header = self.get_header(self.token)

        try:

            response = req.post(uri, headers=header, json=json.loads(latencies))

            if response.status_code != 200:
                self._inspect_response(response, "_send_latency_measurements.error")
                return False
            
            return True
        
        except req.exceptions.RequestException as e:
            self.logger.error(f"Error in sending latencies: {e}")
            return False
    
    def _inspect_response(self, response: req.Response, requestFun: str = ""):
        """
        Prints response of a request. For debugging purpouses only 

        Args:
            response: Response object of the request
            requestFun: String containing the name of the request
        """
        self.logger.error(f"[{requestFun}] Response Code: {response.status_code}")
        if response.status_code != 204:
            try:
                self.logger.error(f"[{requestFun}] Response Body: {response.json()}")
            except json.JSONDecodeError:
                self.logger.error(f"[{requestFun}] Response Text: {response.text}")
        
    def is_function_uploaded(self, func_hash: str) -> bool:
        """
        Checks if the function is already uploaded

        Args:
            func_hash: Hash of the function

        Returns:
            True if the function is already uploaded, False otherwise
        """

        return func_hash in self.offloaded_funs_hash_map.keys()
    
    def get_header(self, token: str) -> dict:
        """
        Returns the header for the requests

        Args:
            token (str): Token for the communication between the client and the Edge Cluster Frontend

        Returns:
            dict: Dictionary with the header
        """
        
        return {
            "token": token
        }

    def get_has_connection(self) -> bool:
        """
        Returns the connection status of the client
        """
        return self._has_connection
    
    def set_has_connection(self, new_value: bool):
        """
        Sets the connection status of the client
        """
        self._has_connection = new_value
    
    def set_token(self, token) -> str:
        """
        Sets the token of the client
        """
        self.token = token

    def get_app_requirements_id(self) -> int:
        """
        Get the app requirements id of the function
        """
        return self.app_req_id
        