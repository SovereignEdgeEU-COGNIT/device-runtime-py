import json
import pydantic
import requests as req
from requests.auth import HTTPBasicAuth
from typing import Callable, Optional, Union, List
import hashlib

from cognit.models._cognit_frontend_client import Scheduling, UploadFunctionDaaS, FunctionLanguage, EdgeClusterFrontendResponse
from cognit.modules._cognitconfig import CognitConfig
from cognit.modules._logger import CognitLogger
from cognit.modules._faas_parser import FaasParser
from cognit.models._edge_cluster_frontend_client import Execution

cognit_logger = CognitLogger()

SR_RESOURCE_ENDPOINT = "serverless-runtimes"

REQ_TIMEOUT = 60

def filter_empty_values(data):
    if isinstance(data, dict):
        return {key: filter_empty_values(value) for key,\
                value in data.items() if value is not None}
    else:
        return data
    


class CognitFrontendClient:
    # ec_fe_list = List[EdgeClusterFrontend] 
    ec_fe_list = List[str]
    
    def __init__(
        self,
        config: CognitConfig  
    ):
        """
        Initializes app_req_id to None (it is updated when the user calls init())
        Initializes token to None (it is updated when the user calls init())
        
        Args:
            config: CognitConfig object containing a valid Cognit user and psd
        """
        self.config = config
        self.endpoint = self.config.cognit_frontend_engine_endpoint
        # else:
        #     self.endpoint = "http://{0}:{1}".format(
        #         self.config.cognit_frontend_engine_endpoint, self.config.cognit_frontend_engine_port
        #     )
        self.latency_endp = self.config.cognit_frontend_engine_endpoint
        self.latency_to_cfe = 0.0
        
        self.token = None
        self.app_req_id = None
        self.offloaded_funs_hash_map = {} # {ḱey: hash(funcN)], value: cognit_fc_id_INTEGER}
        self.ec_fe_list = [] # TODO: List containing the endpoints of the Edge Cluster Frontend Engines
        self._has_connection = False

    def get_has_connection(self):
        '''
        Right now it does not implement any logic, but by using @property,
        additional logic can be implemented in the getter method
        '''
        return self._has_connection
    
    def set_has_connection(self, new_value: bool):
        self._has_connection = new_value
        
    
    def set_token(self, token):
        self.token = token
    
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
            cognit_logger.error("Reqs must be of type Scheduling")
            return False
        
        # self.token = self._authenticate() ## commented due to token duplication
        # cognit_logger.warning(f"\n\n[CFCl] ---- {self.token}\n\n")

        if self.token is None:
            self.set_has_connection(False)
            return False
        
        if not self._check_geolocation_valid(initial_reqs):
            cognit_logger.error("Scheduling model error: GEOLOCATION is compulsory if MAX_LATENCY is defined.")
            return False
        
        uri = f'{self.endpoint}/v1/app_requirements'
        headers = {"token": self.token}
        response = req.post(uri, headers=headers, data=initial_reqs.json(exclude_unset=True))
        try:
            self.app_req_id = response.json()
        except:
            return False
        
        if not self.app_req_id:
            cognit_logger.error("Application ID was not assigned. Check for errors")
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
            cognit_logger.warning(f"App req update returned {response.status_code}")
            self._inspect_response(response, "_app_req_update.warning")
            return None
        
        try:
            data = response.json()
            if not isinstance(data, list):
                cognit_logger.error(f"ECFE list is not a list, it is of class: {data.__class__}")
                return None
            if len(data) <= 0:
                cognit_logger.error("ECFE list is empty")
                return None
            parsed_data = pydantic.parse_obj_as(EdgeClusterFrontendResponse, data[0])
            return parsed_data.TEMPLATE['EDGE_CLUSTER_FRONTEND'][:-1] ## TESTBED integration
            # return "http://0.0.0.0:1339" ## only for testing in local
        except Exception as e:
            cognit_logger.error(f"Error in get_ECFE response handling: {e}")
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
        cognit_logger.debug(f"Requesting token for {self.config._cognit_frontend_engine_usr}")

        uri = f'{self.endpoint}/v1/authenticate'
        response = req.post(url=uri, auth=HTTPBasicAuth(self.config._cognit_frontend_engine_usr, self.config.cognit_frontend_engine_cfe_pwd))
        if response.status_code not in [200, 201]:
            cognit_logger.critical(f"Token creation failed with status code: {response.status_code}")
            self._inspect_response(response, "_authenticate.error")
            return None
        self.token = response.json()
        # cognit_logger.warning(f"\n\n[Auth] ---- {self.token}\n\n")
        if self.token:
            self.set_has_connection(True)
        # cognit_logger.warning(self.token)
        return self.token
    
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
            cognit_logger.error("Reqs must be of type Scheduling")
            return False
        
        if not self._check_geolocation_valid(new_reqs):
            cognit_logger.error("Scheduling model error: GEOLOCATION is compulsory if MAX_LATENCY is defined.")
            return False
        
        uri = f'{self.endpoint}/v1/app_requirements/{self.app_req_id}'
        headers = {"token": self.token}
        response = req.put(uri, headers=headers, data=new_reqs.json(exclude_unset=True))
        if response.status_code >= 300:
            cognit_logger.warning(f"App req update returned {response.status_code}")
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
            cognit_logger.error(f"Read response code was not expected one with status_code: {response.status_code}")
            self._inspect_response(response, "_app_req_read.error")
            return None
        
        self.set_has_connection(response.status_code < 400)
        try:
            response = pydantic.parse_obj_as(Scheduling, response.json())
        except pydantic.ValidationError as e:
            cognit_logger.error(e)
        
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
        cognit_logger.debug(f"Deleting application requirements {self.app_req_id}")

        uri = f'{self.endpoint}/v1/app_requirements/{self.app_req_id}'
        headers = {"token": self.token}

        response = req.delete(uri, headers=headers)
        if response.status_code >= 300:
            cognit_logger.warning(f"App req delete returned {response.status_code} with body: {response.json()}")
        
        self.set_has_connection(response.status_code < 400)
        return response.status_code == 204
    
    
    def _serialize_and_upload_fc_to_daas_gw(self, func: Callable):
        # TODO:
        parser = FaasParser()
        serialized_fc = parser.serialize(func)
        func_hash = hashlib.sha256(func.__code__.co_code).hexdigest()
        if self.is_function_uploaded(func_hash): # TODO
            cognit_logger.debug("Function already in local HASH map")
            return self.app_req_id, self.offloaded_funs_hash_map[func_hash]
        fc = UploadFunctionDaaS(
            LANG=FunctionLanguage.PY,
            FC=serialized_fc,
            FC_HASH=func_hash
        )

        cognit_fc_id = self._upload_fc(fc)
        if cognit_fc_id:
            self.offloaded_funs_hash_map[func_hash] = cognit_fc_id
            return self.app_req_id, cognit_fc_id
        return None, None
    
    def is_function_uploaded(self, func_hash: str) -> bool:
        return func_hash in self.offloaded_funs_hash_map.keys()
    
    
    def _upload_fc(self, fc: UploadFunctionDaaS) -> int:
        """
        Uploads the function to the Daas Gateway
        TODO: Save the returned func_id. One CognitFrontendClient can have 0-N func_ids
        """
        cognit_logger.debug(f"Uploading function {fc}")

        uri = f'{self.endpoint}/v1/daas/upload'
        headers = {"token": self.token}

        response = req.post(uri, headers=headers, data=fc.json())
        if response.status_code != 200:
            self._inspect_response(response)
            return False
        
        func_id = response.json()
        return func_id
    
    def _inspect_response(self, response: req.Response, requestFun: str = ""):
        """
        Prints response of a request. For debugging purpouses only 
        """
        cognit_logger.error(f"[{requestFun}] Response Code: {response.status_code}")
        if response.status_code != 204:
            try:
                cognit_logger.error(f"[{requestFun}] Response Body: {response.json()}")
            except json.JSONDecodeError:
                cognit_logger.error(f"[{requestFun}] Response Text: {response.text}")
    
    
    def _check_geolocation_valid(self, reqs: Scheduling) -> bool:
        try:
            if reqs.MAX_LATENCY in [None, 0]:  # If MAX_LATENCY is not defined, no need to check GEOLOCATION
                return True
            
            # If MAX_LATENCY is defined, GEOLOCATION becomes compulsory 
            return isinstance(reqs.GEOLOCATION, str) and reqs.GEOLOCATION != ""
            
        except Exception as e:
            cognit_logger.error(f"Error validating data: {e}")
            return False
        