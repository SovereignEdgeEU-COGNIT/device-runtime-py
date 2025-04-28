from cognit.models._cognit_frontend_client import Scheduling, UploadFunctionDaaS, FunctionLanguage, EdgeClusterFrontendResponse
from cognit.modules._cognitconfig import CognitConfig
from cognit.modules._faas_parser import FaasParser
from cognit.modules._logger import CognitLogger
from requests.auth import HTTPBasicAuth
from typing import Callable
import requests as req
import pydantic
import hashlib
import json


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
            config: CognitConfig object containing a valid Cognit user and psd
        """
        self.config = config
        self.endpoint = self.config.cognit_frontend_engine_endpoint
        self.logger = CognitLogger()
        self._has_connection = False
        self.parser = FaasParser()
        self.app_req_id = None
        self.token = None
        
        # Storage
        self.offloaded_funs_hash_map = {}  # This is a dictionary that will store the hash of the function and the cognit_fc_id
        self.ec_fe_list = [] # TODO: List containing the endpoints of the Edge Cluster Frontend Engines
    
    def init(self, initial_reqs: Scheduling) -> bool:
        """
        Authenticates using loaded credentials to get a JWT token
        Upload initial app requirements to the Cognit FE
        Args:
            initial_reqs: 'Scheduling' object containing the requirements of the app
        Returns:
            True if response.status_code is the expected (200)
            False otherwise
        """

        if not isinstance(initial_reqs, Scheduling):
            self.logger.error("Reqs must be of type Scheduling")
            return False
        
        if self.token is None:
            self.set_has_connection(False)
            return False
        
        if not self._check_geolocation_valid(initial_reqs):
            self.logger.error("Scheduling model error: GEOLOCATION is compulsory if MAX_LATENCY is defined.")
            return False
        
        uri = f'{self.endpoint}/v1/app_requirements'
        header = self.get_header(self.token)

        response = req.post(uri, headers=header, data=initial_reqs.json(exclude_unset=True))

        try:
            self.app_req_id = response.json()
        except:
            return False
        
        if not self.app_req_id:
            self.logger.error("Application ID was not assigned. Check for errors")
            return False
        
        if response.status_code != 200:
            self._inspect_response(response)
            
        self.set_has_connection(response.status_code < 400)
        return response.status_code == 200  
    
    def _get_edge_cluster_address(self) -> str | None: # TODO, doesn't work because of CFEngine (Dann1)
        """
        Interacts with the Cognit Frontend Engine to get a list of valid 
        Edge Cluster Frontend Engine addresses. 
        For now, the most optimal ECFE will be the first element of the list.
        
        Args:
            None
        Returns:
            None if the response is not valid (length of the list <= 0)
            String with the endpoint of the ECFE otherwise
        """
        uri = f'{self.endpoint}/v1/app_requirements/{self.app_req_id}/ec_fe'
        headers = {"token": self.token}
        response = req.get(uri, headers=headers)
        self.set_has_connection(response.status_code < 400)
        if response.status_code >= 300:
            self.logger.warning(f"App req update returned {response.status_code}")
            self._inspect_response(response, "_app_req_update.warning")
            return None
        
        try:
            data = response.json()
            if not isinstance(data, list):
                self.logger.error(f"ECFE list is not a list, it is of class: {data.__class__}")
                return None
            if len(data) <= 0:
                self.logger.error("ECFE list is empty")
                return None
            parsed_data = pydantic.parse_obj_as(EdgeClusterFrontendResponse, data[0])
            return parsed_data.TEMPLATE['EDGE_CLUSTER_FRONTEND'] ## TESTBED integration
            # return "http://0.0.0.0:1339" ## only for testing in local
        except Exception as e:
            self.logger.error(f"Error in get_ECFE response handling: {e}")
            return None
    
    def _authenticate(self) -> str:
        """
        Authenticate against Cognit FE to get a valid JWT Token
        
        Args:
            user: Valid username of Cognit
            password: Password of the username
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
            self.logger.critical("Token creation failed, token is None")
            self.set_has_connection(False)
            return None
    
    def _app_req_update(self, new_reqs:Scheduling) -> bool:
        """
        Update the application requirements using the application ID.
        Args: 
            new_reqs: The new requirements to update
        Returns:
            True: The request was succesfull (status code == 200)
            False: Otherwise 
        """
        if not isinstance(new_reqs, Scheduling):
            self.logger.error("Reqs must be of type Scheduling")
            return False
        
        if not self._check_geolocation_valid(new_reqs):
            self.logger.error("Scheduling model error: GEOLOCATION is compulsory if MAX_LATENCY is defined.")
            return False
        
        uri = f'{self.endpoint}/v1/app_requirements/{self.app_req_id}'
        headers = {"token": self.token}
        response = req.put(uri, headers=headers, data=new_reqs.json(exclude_unset=True))
        if response.status_code >= 300:
            self.logger.warning(f"App req update returned {response.status_code}")
            self._inspect_response(response, "_app_req_update.warning")
        
        self.set_has_connection(response.status_code < 400)
        
        return response.status_code == 200 
        
    def _app_req_read(self) -> Scheduling | None:
        """
        Reads the app requirements using the application ID
        
        Args:
            None
        Returns:
            A dictionary containing the requested data of the app requirements
        """
        uri = f'{self.endpoint}/v1/app_requirements/{self.app_req_id}'
        headers = {"token": self.token}
        response = req.get(uri, headers=headers)
        
        # TODO: Check response.status_code < 300, else return None
        # if response.status_code >= 300:
        #     return None
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
        Deletes the app requirements 
        Args:
            self: As app reqs are stored as class attribute
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
    
    
    def _check_geolocation_valid(self, reqs: Scheduling) -> bool:
        """
        Checks if the geolocation is valid for the given requirements

        Args:
            reqs: Scheduling object containing the requirements of the app
        """
        try:
            if reqs.MAX_LATENCY in [None, 0]:  # If MAX_LATENCY is not defined, no need to check GEOLOCATION
                return True
            
            # If MAX_LATENCY is defined, GEOLOCATION becomes compulsory 
            return isinstance(reqs.GEOLOCATION, str) and reqs.GEOLOCATION != ""
            
        except Exception as e:
            self.logger.error(f"Error validating data: {e}")
            return False
        
    def is_function_uploaded(self, func_hash: str) -> bool:
        """
        Checks if the function is already uploaded

        Args:
            func_hash: Hash of the function
        """
        return func_hash in self.offloaded_funs_hash_map.keys()
    
    def get_header(self, token: str) -> dict:
        """
        Returns the header for the requests
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
        