from cognit.modules._cognit_frontend_client import CognitFrontendClient
from cognit.models._cognit_frontend_client import Scheduling
from cognit.modules._cognitconfig import CognitConfig

import hashlib
import pytest

"""
To run this test, a locally running Cognit Frontend Engine is needed
Instructions of how to make CFE run found on: https://github.com/SovereignEdgeEU-COGNIT/cognit-frontend
"""

COGNIT_CONFIG_PATH = "cognit/test/config/cognit_v2.yml"
BAD_COGNIT_CONFIG_PATH = "cognit/test/config/cognit_v2_wrong_user.yml"

TEST_REQS_INIT = {
      "FLAVOUR": "EnergyV2",
      "GEOLOCATION": "IKERLAN ARRASATE/MONDRAGON 20500"
}

REQS_NEW = {
    "FLAVOUR": "EnergyV2",
    "GEOLOCATION": "IKERLAN BILBAO 48007"
}

# Wrong because "GEOLOCATION" is not defined when "MAX_LATENCY" is defined  
TEST_REQS_WRONG = { 
      "FLAVOUR": "Energy",
      "MAX_FUNCTION_EXECUTION_TIME": 2.0,
      "MAX_LATENCY": 25,
      "MIN_ENERGY_RENEWABLE_USAGE": 85,
}

@pytest.fixture
def test_func() -> callable:
    def sum(a: int, b: int):
        return a + b
    return sum

@pytest.fixture
def cognit_config() -> CognitConfig:
    return CognitConfig(COGNIT_CONFIG_PATH)

@pytest.fixture
def bad_cognit_config() -> CognitConfig:
    return CognitConfig(BAD_COGNIT_CONFIG_PATH)

def test_cognit_frontend_authenticate(cognit_config: CognitConfig):

    # Instantiate CFC
    cfc = CognitFrontendClient(cognit_config)

    # Authenticate
    token = cfc._authenticate()

    # Check if the CFE is reachable
    assert cfc.get_has_connection() is True
    assert token is not None

def test_cognit_frontend_bad_authenticate(bad_cognit_config: CognitConfig):

    # Instantiate CFC
    cfc = CognitFrontendClient(bad_cognit_config)

    # Authenticate
    token = cfc._authenticate()

    # Check if the CFE is reachable
    assert cfc.get_has_connection() is False
    assert token is None

def test_cognit_frontend_init(cognit_config: CognitConfig):
    
    # Instantiate CFC
    cfc = CognitFrontendClient(cognit_config)

    # Authenticate
    token = cfc._authenticate()

    # Check if the CFE is reachable
    assert cfc.get_has_connection() is True
    assert token is not None

    # Requirements
    reqs = Scheduling(**TEST_REQS_INIT)
    has_initiated = cfc.init(reqs)

    # Check CFC uploaded the requirements correctly
    assert has_initiated is True
    assert cfc.app_req_id is not None
    assert cfc.get_has_connection() is True

def test_cognit_frontend_bad_init(cognit_config: CognitConfig):
    
    # Instantiate CFC
    cfc = CognitFrontendClient(cognit_config)

    # Authenticate
    token = cfc._authenticate()

    # Check if the CFE is reachable
    assert cfc.get_has_connection() is True
    assert token is not None

    # Requirements
    reqs = Scheduling(**TEST_REQS_WRONG)
    has_initiated = cfc.init(reqs)

    # Check CFC uploaded the requirements correctly
    assert has_initiated is False
    assert cfc.app_req_id is None
    assert cfc.get_has_connection() is True
    
def test_cognit_frontend_get_ecf_address(cognit_config: CognitConfig):
    
    # Instantiate CFC
    cfc = CognitFrontendClient(cognit_config)

    # Authenticate
    token = cfc._authenticate()

    # Check if the CFE is reachable
    assert cfc.get_has_connection() is True
    assert token is not None

    # Requirements
    reqs = Scheduling(**TEST_REQS_INIT)
    has_initiated = cfc.init(reqs)

    # Check CFC uploaded the requirements correctly
    assert has_initiated is True
    assert cfc.app_req_id is not None
    assert cfc.get_has_connection() is True

    # Get ECF address
    ecf_address = cfc._get_edge_cluster_address()

    # Check if the ECF address is not None
    assert ecf_address is not None

def test_cognit_frontend_upload_function_to_daas(cognit_config: CognitConfig, test_func: callable):

    # Instantiate CFC
    cfc = CognitFrontendClient(cognit_config)

    # Authenticate
    token = cfc._authenticate()

    # Check if the CFE is reachable
    assert cfc.get_has_connection() is True
    assert token is not None

    # Requirements
    reqs = Scheduling(**TEST_REQS_INIT)
    has_initiated = cfc.init(reqs)

    # Check CFC uploaded the requirements correctly
    assert has_initiated is True
    assert cfc.app_req_id is not None
    assert cfc.get_has_connection() is True

    # Upload function
    function_id = cfc.upload_function_to_daas(test_func)
    function_hash = hashlib.sha256(test_func.__code__.co_code).hexdigest()

    # Check if the function was uploaded correctly
    assert function_id is not None
    assert cfc.offloaded_funs_hash_map.get(function_hash) is function_id 

def test_check_function_reuploading(cognit_config: CognitConfig, test_func: callable):

    # Instantiate CFC
    cfc = CognitFrontendClient(cognit_config)

    # Authenticate
    token = cfc._authenticate()

    # Check if the CFE is reachable
    assert cfc.get_has_connection() is True
    assert token is not None

    initial_reqs =  Scheduling(**TEST_REQS_INIT)
    new_reqs = Scheduling(**REQS_NEW)

    # Requirements
    has_initiated = cfc.init(initial_reqs)

    # Check CFC uploaded the requirements correctly
    assert has_initiated is True
    assert cfc.app_req_id is not None
    assert cfc.get_has_connection() is True

    # Get ECF address
    ecf_address = cfc._get_edge_cluster_address()

    # Check if the ECF address is not None
    assert ecf_address is not None
    
    # Requirements
    has_initiated = cfc.init(new_reqs)

    # Check CFC uploaded the requirements correctly
    assert has_initiated is True
    assert cfc.app_req_id is not None
    assert cfc.get_has_connection() is True

    # Get ECF address
    ecf_address = cfc._get_edge_cluster_address()

    # Check if the ECF address is not None
    assert ecf_address is not None