import pytest
from pytest_mock import MockerFixture
from cognit.modules._cognitconfig import CognitConfig
from cognit.modules._cognit_frontend_client import CognitFrontendClient  
from cognit.models._cognit_frontend_client import Scheduling  

COGNIT_CONF_PATH = __file__.split("cognit/")[0] + "cognit/test/config/cognit_v2.yml"

TEST_CFE_RESPONSES = {
    "authenticate": {
        "status_code": 201,
        "body": "JWT_token"
    },
    "req_init_upload": {
        "status_code": 200,
        "body": 4123  # App req id
    },
    "req_read_ok": {
        "status_code": 200,
        "body": {
            "FLAVOUR": "smart_city"
        }
    },
    "req_read_error": {
        "status_code": 404,
        "body": {"detail": "[one.document.info] Error getting document [4123]."}
    },
    "req_update": {
        "status_code": 200,
        "body": None
    },
    "req_delete": {
        "status_code": 204,
    },
    "fun_upload": {
        "status_code": 200,
        "body": 4079  # Function ID
    }
}

REQS_INIT = {
      "FLAVOUR": "NatureV2"
}

REQS_NEW = {
      "FLAVOUR": "NatureV2",
      "MAX_FUNCTION_EXECUTION_TIME": 2.0,
      "MAX_LATENCY": 25,
      "MIN_ENERGY_RENEWABLE_USAGE": 85,
      "GEOLOCATION": "IKERLAN ARRASATE/MONDRAGON 20500"
}

REQS_WRONG = { # Wrong because "GEOLOCATION" is not defined when "MAX_LATENCY" is
      "FLAVOUR": "NatureV2",
      "MAX_FUNCTION_EXECUTION_TIME": 2.0,
      "MAX_LATENCY": 25,
      "MIN_ENERGY_RENEWABLE_USAGE": 85,
}

# Fixture for CognitConfig mock
@pytest.fixture
def test_cognit_config() -> CognitConfig:
    return CognitConfig(COGNIT_CONF_PATH)

# Fixture for CognitFrontendClient using mock config
@pytest.fixture
def cognit_client(test_cognit_config):
    return CognitFrontendClient(test_cognit_config)

# Mock the post request for authentication
@pytest.fixture
def mock_authenticate_request(mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = TEST_CFE_RESPONSES["authenticate"]["status_code"]
    mock_response.json.return_value = TEST_CFE_RESPONSES["authenticate"]["body"]
    mocker.patch("requests.post", return_value=mock_response)

# Test _authenticate method
def test_authenticate(cognit_client, mock_authenticate_request):
    token = cognit_client._authenticate()
    assert token == TEST_CFE_RESPONSES["authenticate"]["body"]

# Mock the request to initialize app requirements
@pytest.fixture
def mock_init_request(mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = TEST_CFE_RESPONSES["req_init_upload"]["status_code"]
    mock_response.json.return_value = TEST_CFE_RESPONSES["req_init_upload"]["body"]
    mocker.patch("requests.post", return_value=mock_response)

# Test init method
def test_init(cognit_client, mock_init_request):
    initial_reqs = Scheduling(**REQS_INIT)
    cognit_client.set_token("test_token")
    cognit_client.init(initial_reqs)
    assert cognit_client.app_req_id == TEST_CFE_RESPONSES["req_init_upload"]["body"] 

# Mock the request for reading app requirements
@pytest.fixture
def mock_read_request(mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = TEST_CFE_RESPONSES["req_read_ok"]["status_code"]
    mock_response.json.return_value = TEST_CFE_RESPONSES["req_read_ok"]["body"]
    mocker.patch("requests.get", return_value=mock_response)

# Test _app_req_read method
def test_app_req_read(cognit_client, mock_read_request):
    response = cognit_client._app_req_read()
    assert response == Scheduling(**TEST_CFE_RESPONSES["req_read_ok"]["body"])

# Mock the request for updating app requirements
@pytest.fixture
def mock_update_request(mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = TEST_CFE_RESPONSES["req_update"]["status_code"]
    mock_response.json.return_value = TEST_CFE_RESPONSES["req_update"]["body"]
    mocker.patch("requests.put", return_value=mock_response)

# Test _app_req_update method
def test_app_req_update(cognit_client, mock_update_request):
    new_reqs = Scheduling(**REQS_NEW)
    success = cognit_client._app_req_update(new_reqs)
    assert success is True
    
# Test _app_req_update method with wrong requirements
def test_app_req_update_failure(cognit_client, mock_update_request):
    wrong_reqs = Scheduling(**REQS_WRONG)
    success = cognit_client._app_req_update(wrong_reqs)
    assert success is False

# Mock the request for deleting app requirements
@pytest.fixture
def mock_delete_request(mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = TEST_CFE_RESPONSES["req_delete"]["status_code"]
    mocker.patch("requests.delete", return_value=mock_response)

# Test _app_req_delete method
def test_app_req_delete(cognit_client, mock_delete_request):
    success = cognit_client._app_req_delete()
    assert success is True

# Test _app_req_delete with failed deletion
def test_app_req_delete_failure(cognit_client, mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 404
    mock_response.json.return_value = {"detail": "Not found"}
    mocker.patch("requests.delete", return_value=mock_response)

    success = cognit_client._app_req_delete()
    assert success is False

# Mock the request for uploading a function
@pytest.fixture
def mock_upload_fc_request(mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = TEST_CFE_RESPONSES["fun_upload"]["status_code"]
    mock_response.json.return_value = TEST_CFE_RESPONSES["fun_upload"]["body"]
    mocker.patch("requests.post", return_value=mock_response)

def test_fc_upload(cognit_client, mock_upload_fc_request):
    def dummy():
        print("Test")
        
    _, cognit_fc_id = cognit_client._serialize_and_upload_fc_to_daas_gw(dummy)
    assert cognit_fc_id is not None
