from cognit.modules._cognit_frontend_client import CognitFrontendClient
from cognit.models._cognit_frontend_client import Scheduling
from cognit.modules._cognitconfig import CognitConfig

from pytest_mock import MockerFixture
import hashlib
import pytest

COGNIT_CONFIG_PATH = "cognit/test/config/cognit_v2.yml"
BAD_COGNIT_CONFIG_PATH = "cognit/test/config/cognit_v2_wrong_user.yml"

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
        "body": 3333
    },
    "req_delete": {
        "status_code": 204,
    },
    "ecf_address": {
        "status_code": 204,
        "body": [{"ID": 1, "NAME": "cluster001", "HOSTS": [1,2,3], "DATASTORES": [1,2,3], "VNETS": [1,2,3], "TEMPLATE": {"EDGE_CLUSTER_FRONTEND": ["address1", "address2", "address3", "address4"]}}]
    },
    "fun_upload": {
        "status_code": 200,
        "body": 4079  # Function ID
    },
    "latency_address": {
        "result": {"address1": 20, "address2": 10, "address3": 30, "address4": 40}
    }
}

TEST_REQS_INIT = {
      "FLAVOUR": "EnergyV2",
      "GEOLOCATION": "IKERLAN ARRASATE/MONDRAGON 20500"
}

TEST_REQS_INIT_MAX_LATENCY = {
      "FLAVOUR": "EnergyV2",
      "GEOLOCATION": "IKERLAN ARRASATE/MONDRAGON 20500",
      "MAX_LATENCY": 25
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
    return CognitConfig()

@pytest.fixture
def bad_cognit_config() -> CognitConfig:
    return CognitConfig(BAD_COGNIT_CONFIG_PATH)

@pytest.fixture
def cognit_client(cognit_config: CognitConfig, mocker: MockerFixture) -> CognitFrontendClient:

    cfc = CognitFrontendClient(cognit_config)

    mock_response = mocker.Mock()
    mock_response.status_code = TEST_CFE_RESPONSES["authenticate"]["status_code"]
    mock_response.json.return_value = TEST_CFE_RESPONSES["authenticate"]["body"]

    mocker.patch("requests.post", return_value=mock_response)

    cfc._authenticate()

    mock_response = mocker.Mock()
    mock_response.status_code = TEST_CFE_RESPONSES["req_init_upload"]["status_code"]
    mock_response.json.return_value = TEST_CFE_RESPONSES["req_init_upload"]["body"]

    mocker.patch("requests.post", return_value=mock_response)

    cfc.init(Scheduling(**TEST_REQS_INIT))

    return cfc

@pytest.fixture
def cognit_client_max_latency(cognit_config: CognitConfig, mocker: MockerFixture) -> CognitFrontendClient:

    cfc = CognitFrontendClient(cognit_config)

    mock_response = mocker.Mock()
    mock_response.status_code = TEST_CFE_RESPONSES["authenticate"]["status_code"]
    mock_response.json.return_value = TEST_CFE_RESPONSES["authenticate"]["body"]

    mocker.patch("requests.post", return_value=mock_response)

    cfc._authenticate()

    mock_response = mocker.Mock()
    mock_response.status_code = TEST_CFE_RESPONSES["req_init_upload"]["status_code"]
    mock_response.json.return_value = TEST_CFE_RESPONSES["req_init_upload"]["body"]

    mocker.patch("requests.post", return_value=mock_response)

    cfc.init(Scheduling(**TEST_REQS_INIT_MAX_LATENCY))

    return cfc

# Test _authenticate method
def test_authenticate(cognit_config: CognitConfig, mocker: MockerFixture):

    cfc = CognitFrontendClient(cognit_config)
    
    assert cfc._has_connection is False
    assert cfc.endpoint is not None
    assert cfc.app_req_id is None
    assert cfc.token is None

    mock_response = mocker.Mock()
    mock_response.status_code = TEST_CFE_RESPONSES["authenticate"]["status_code"]
    mock_response.json.return_value = TEST_CFE_RESPONSES["authenticate"]["body"]

    mocker.patch("requests.post", return_value=mock_response)

    token = cfc._authenticate()

    assert cfc.get_has_connection() is True
    assert token is "JWT_token"

# Test init method
def test_init_cfc(cognit_config: CognitConfig, mocker: MockerFixture):

    cfc = CognitFrontendClient(cognit_config)
    
    assert cfc._has_connection is False
    assert cfc.endpoint is not None
    assert cfc.app_req_id is None
    assert cfc.token is None

    mock_response = mocker.Mock()
    mock_response.status_code = TEST_CFE_RESPONSES["authenticate"]["status_code"]
    mock_response.json.return_value = TEST_CFE_RESPONSES["authenticate"]["body"]

    mocker.patch("requests.post", return_value=mock_response)

    token = cfc._authenticate()

    assert cfc.get_has_connection() is True
    assert token is "JWT_token"

    mock_response = mocker.Mock()
    mock_response.status_code = TEST_CFE_RESPONSES["req_init_upload"]["status_code"]
    mock_response.json.return_value = TEST_CFE_RESPONSES["req_init_upload"]["body"]

    mocker.patch("requests.post", return_value=mock_response)

    has_initialized = cfc.init(Scheduling(**TEST_REQS_INIT))

    assert cfc.get_has_connection() is True
    assert has_initialized is True
    assert cfc.is_max_latency_activated is False
    assert cfc.app_req_id is 4123

def test_get_edge_cluster_address_no_max_latency(cognit_client: CognitFrontendClient, mocker: MockerFixture):

    mock_response = mocker.Mock()
    mock_response.status_code = TEST_CFE_RESPONSES["ecf_address"]["status_code"]
    mock_response.json.return_value = TEST_CFE_RESPONSES["ecf_address"]["body"]

    mocker.patch("requests.get", return_value=mock_response)

    address = cognit_client._get_edge_cluster_address()

    assert address == "address1"
    assert cognit_client.get_has_connection() is True

def test_get_edge_cluster_address_with_max_latency(cognit_client_max_latency: CognitFrontendClient, mocker: MockerFixture):

    mock_response = mocker.Mock()
    mock_response.status_code = TEST_CFE_RESPONSES["ecf_address"]["status_code"]
    mock_response.json.return_value = TEST_CFE_RESPONSES["ecf_address"]["body"]

    mocker.patch("requests.get", return_value=mock_response)

    mocker.patch("cognit.modules._latency_calculator.LatencyCalculator.get_latency_for_clusters", return_value=TEST_CFE_RESPONSES["latency_address"]["result"])

    address = cognit_client_max_latency._get_edge_cluster_address()

    assert address == "address2"
    assert cognit_client_max_latency.get_has_connection() is True

def test_upload_function_to_daas(cognit_client: CognitFrontendClient, mocker: MockerFixture, test_func: callable):

    mock_response = mocker.Mock()
    mock_response.status_code = TEST_CFE_RESPONSES["fun_upload"]["status_code"]
    mock_response.json.return_value = TEST_CFE_RESPONSES["fun_upload"]["body"]

    mocker.patch("requests.post", return_value=mock_response)

    function_id = cognit_client.upload_function_to_daas(test_func)

    hash_func = hashlib.sha256(test_func.__code__.co_code).hexdigest()

    assert cognit_client.offloaded_funs_hash_map.get(hash_func) == function_id
    assert cognit_client.get_has_connection() is True
    assert function_id == 4079

def test_app_req_update(cognit_client: CognitFrontendClient, mocker: MockerFixture):

    mock_response = mocker.Mock()
    mock_response.status_code = TEST_CFE_RESPONSES["req_update"]["status_code"]
    mock_response.json.return_value = TEST_CFE_RESPONSES["req_update"]["body"]

    mocker.patch("requests.put", return_value=mock_response)

    is_updated = cognit_client.init(Scheduling(**REQS_NEW))

    assert is_updated is True
    assert cognit_client.get_has_connection() is True

def test_app_req_read(cognit_client: CognitFrontendClient, mocker: MockerFixture):

    mock_response = mocker.Mock()
    mock_response.status_code = TEST_CFE_RESPONSES["req_read_ok"]["status_code"]
    mock_response.json.return_value = TEST_CFE_RESPONSES["req_read_ok"]["body"]

    mocker.patch("requests.get", return_value=mock_response)

    result = cognit_client._app_req_read()

    assert result == Scheduling(**TEST_CFE_RESPONSES["req_read_ok"]["body"])

def test_app_req_delete(cognit_client: CognitFrontendClient, mocker: MockerFixture):

    mock_response = mocker.Mock()
    mock_response.status_code = TEST_CFE_RESPONSES["req_delete"]["status_code"]

    mocker.patch("requests.delete", return_value=mock_response)

    is_deleted = cognit_client._app_req_delete()

    assert is_deleted is True

# Test _app_req_delete with failed deletion
def test_app_req_delete_failure(cognit_client, mocker):

    mock_response = mocker.Mock()
    mock_response.status_code = 404
    mock_response.json.return_value = {"detail": "Not found"}

    mocker.patch("requests.delete", return_value=mock_response)

    is_deleted = cognit_client._app_req_delete()

    assert is_deleted is False