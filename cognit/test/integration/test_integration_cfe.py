from cognit.models._edge_cluster_frontend_client import ExecParams
from cognit.models._cognit_frontend_client import FunctionLanguage, Scheduling
from cognit.modules._cognit_frontend_client import CognitFrontendClient
from cognit.modules._cognitconfig import CognitConfig
from cognit.modules._faas_parser import FaasParser
from cognit.modules._logger import CognitLogger

from pytest_mock import MockerFixture
import pytest

"""
To run this test, a locally running Cognit Frontend Engine is needed
Instructions of how to make CFE run found on: https://github.com/SovereignEdgeEU-COGNIT/cognit-frontend
"""

# TODO: Right now everything is harcoded, need to create the corresponding classes
COGNIT_CONF_PATH = __file__.split("cognit/")[0] + "cognit/test/config/cognit_v2.yml"
TEST_REQS_INIT = {
      "FLAVOUR": "smart_city",
      "MAX_LATENCY": 0,
      "GEOLOCATION": "IKERLAN ARRASATE/MONDRAGON 20500"
}

TEST_REQS_NEW = {
      "FLAVOUR": "Energy",
      "MAX_FUNCTION_EXECUTION_TIME": 2.0,
      "MAX_LATENCY": 25,
      "MIN_ENERGY_RENEWABLE_USAGE": 85,
      "GEOLOCATION": "IKERLAN ARRASATE/MONDRAGON 20500"
}

TEST_REQS_WRONG = { # Wrong because "GEOLOCATION" is not defined when "MAX_LATENCY" is
      "FLAVOUR": "Energy",
      "MAX_FUNCTION_EXECUTION_TIME": 2.0,
      "MAX_LATENCY": 25,
      "MIN_ENERGY_RENEWABLE_USAGE": 85,
}
TEST_FUNC = {
    "LANG": "PY",
    "FC": "ZGVmIHNheV9oZWxsbygpOgogICAgcHJpbnQoJ2hlbGxvJykK",
    "FC_HASH": "bacaa2c80e4f7f381117ff8503bd8752"
}

cognit_logger = CognitLogger()


def sum(a: int, b: int):
    #time.sleep(20)
    cognit_logger.debug("This is a test")
    return a + b

@pytest.fixture
def serialized_fc() -> ExecParams:
    parser = FaasParser()
    serialized_fc = parser.serialize(sum)
    mock_hash = "000-000-000"
    serialized_fc_hash = parser.serialize(mock_hash)
    serialized_params = []
    serialized_params.append(parser.serialize(2))
    serialized_params.append(parser.serialize(2))

    fc = ExecParams(
        fc=serialized_fc, 
        fc_hash=serialized_fc_hash, 
        lang=FunctionLanguage.PY
        )

    return fc

def test_cognit_frontend_integration():
    initial_reqs =  Scheduling(**TEST_REQS_INIT)
    cognit = CognitFrontendClient(CognitConfig(COGNIT_CONF_PATH))
    
    assert cognit.init(initial_reqs) is True
    assert cognit.get_has_connection() is True
    
    reqs_1 = cognit._app_req_read() # status_code == 200
    assert reqs_1.__class__ == Scheduling
    assert reqs_1.json() == initial_reqs.json().replace("null", '\"None\"')
    assert cognit.get_has_connection() is True
    
    new_reqs = Scheduling(**TEST_REQS_NEW)
    assert cognit._app_req_update(new_reqs) is True  # status_code == 200
    assert cognit._app_req_update(TEST_REQS_NEW) is False  # Exception because input is not of class Scheduling
    assert cognit.get_has_connection() is True
    
    reqs_2 = cognit._app_req_read() # status_code == 200
    assert reqs_2.__class__ == Scheduling
    assert reqs_2.json() == new_reqs.json().replace("null", '\"None\"')
    assert reqs_1 != reqs_2
    assert cognit.get_has_connection() is True
    
    wrong_reqs = Scheduling(**TEST_REQS_WRONG)
    assert cognit._app_req_update(wrong_reqs) is False
    reqs_3 = cognit._app_req_read() 
    assert reqs_3 == reqs_2 # as it has given an error, reqs_3 should be the same as reqs_2
    assert cognit.get_has_connection() is True
    
    
    assert cognit._serialize_and_upload_fc_to_daas_gw(sum) != None, None
    assert cognit.get_has_connection() is True
    
    # assert len(cognit._get_ECFE()) > 0 ## Not implemented        
    
    # Cleanup & read error test
    assert cognit._app_req_delete() is True # status_code == 204
    assert cognit.get_has_connection() is True
    
    assert cognit._app_req_read() is None # status_code == 404
    
    
def test_cognit_frontend_get_ecfe_endpoint():
    # FAILS because this funcionality is not yet (22/10/2024) implemented in Dann1 CFE code
    initial_reqs =  Scheduling(**TEST_REQS_NEW)
    cognit = CognitFrontendClient(CognitConfig(COGNIT_CONF_PATH))
    
    assert cognit.init(initial_reqs) is True
    assert cognit.get_has_connection() is True
    
    cognit._serialize_and_upload_fc_to_daas_gw(sum)
    assert cognit.get_has_connection() is True
    
    # assert len(cognit._get_ECFE()) > 0
    optimal_ecfe_endpoint = cognit._get_edge_cluster_address()
    assert optimal_ecfe_endpoint is not None
    
    
def test_check_function_reuploading():
    """
    Goal: Check if a function is already uploaded it does not upload again.
    Steps:
    1. Upload function `sum`
    2. Upload function `sum `, check foor logging message
    """
    pass
    initial_reqs =  Scheduling(**TEST_REQS_NEW)
    cognit = CognitFrontendClient(CognitConfig(COGNIT_CONF_PATH))
    
    assert cognit.init(initial_reqs) is True
    assert cognit.get_has_connection() is True
    
    cognit._serialize_and_upload_fc_to_daas_gw(sum)
    assert cognit.get_has_connection() is True
    
    cognit._serialize_and_upload_fc_to_daas_gw(sum)
    assert cognit.get_has_connection() is True