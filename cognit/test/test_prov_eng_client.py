import pytest
from pytest_mock import MockerFixture

from cognit.models._prov_engine_client import *
from cognit.models._serverless_runtime_client import *
from cognit.modules._cognitconfig import CognitConfig
from cognit.modules._prov_engine_client import ProvEngineClient

TEST_RESPONSE_PENDING = {
    "SERVERLESS_RUNTIME": {
        "NAME": "faas",
        "ID": 1,
        "SERVICE_ID": 1,
        "FAAS": {
            "CPU": 1,
            "MEMORY": 1,
            "DISK_SIZE": 1,
            "FLAVOUR": "flavour",
            "ENDPOINT": "endpoint",
            "STATE": "PENDING",
            "VM_ID": "vm_id",
        },
        "DAAS": {
            "CPU": 1,
            "MEMORY": 1,
            "DISK_SIZE": 1,
            "FLAVOUR": "flavour",
            "ENDPOINT": "",
            "STATE": "",
            "VM_ID": "vm_id",
        },
        "SCHEDULING": {"POLICY": "policy", "REQUIREMENTS": "requirements"},
        "DEVICE_INFO": {
            "LATENCY_TO_PE": 1,
            "GEOGRAPHIC_LOCATION": "geographic_location",
        }
    }
}

TEST_SR_ENDPOINT = "http://myserverlessruntime-1234"

TEST_RESPONSE_RUNNING = {
    "SERVERLESS_RUNTIME": {
        "NAME": "faas",
        "ID": 1,
        "SERVICE_ID": 1,
        "FAAS": {
            "CPU": 1,
            "MEMORY": 1,
            "DISK_SIZE": 1,
            "FLAVOUR": "flavour",
            "ENDPOINT": TEST_SR_ENDPOINT,
            "STATE": "RUNNING",
            "VM_ID": "vm_id",
        },
        "DAAS": {
            "CPU": 1,
            "MEMORY": 1,
            "DISK_SIZE": 1,
            "FLAVOUR": "flavour",
            "ENDPOINT": "",
            "STATE": "running",
            "VM_ID": "vm_id",
        },
        "SCHEDULING": {"POLICY": "policy", "REQUIREMENTS": "requirements"},
        "DEVICE_INFO": {
            "LATENCY_TO_PE": 1,
            "GEOGRAPHIC_LOCATION": "geographic_location",
        }
    }
}


@pytest.fixture
def test_cognit_config() -> CognitConfig:
    config = CognitConfig("./cognit/test/config/cognit.yml")
    return config


@pytest.fixture
def prov_eng_cli(test_cognit_config: CognitConfig) -> ProvEngineClient:
    prov_eng_cli = ProvEngineClient(config=test_cognit_config)
    return prov_eng_cli


@pytest.fixture
def test_serverless_runtime() -> ServerlessRuntime:
    sr_data = ServerlessRuntimeData(
        NAME="MyServerlessRuntime",
        ID=1,
        FLAVOUR="Flavor 1",
        FAAS=FaaSConfig(CPU=2, MEMORY=2048, DISK_SIZE=500, FLAVOUR="FaaS Flavor"),
        DAAS=DaaSConfig(CPU=4, MEMORY=4096, DISK_SIZE=1000, FLAVOUR="DaaS Flavor"),
        POLICY="energy",
        REQUIREMENTS="energy_renewal",
    )
    return ServerlessRuntime(SERVERLESS_RUNTIME=sr_data)


def test_prov_engine_cli_create(
    prov_eng_cli: ProvEngineClient,
    test_serverless_runtime: ServerlessRuntime,
    mocker: MockerFixture,
):
    # Patch request post to return status_CODE 200 and a body with serverless runtime details
    mock_resp = mocker.Mock()
    mock_resp.json.return_value = TEST_RESPONSE_PENDING
    mock_resp.status_code = 201
    mocker.patch("requests.post", return_value=mock_resp)

    response = prov_eng_cli.create(serverless_runtime=test_serverless_runtime)
    assert response != None
    assert response.SERVERLESS_RUNTIME.FAAS.STATE == FaaSState.PENDING


def test_prov_engine_cli_retrieve(
    prov_eng_cli: ProvEngineClient, mocker: MockerFixture
):
    # Patch request get to return status_CODE 200 and a body with success: True
    mock_resp = mocker.Mock()
    mock_resp.json.return_value = TEST_RESPONSE_RUNNING
    mock_resp.status_code = 200
    mocker.patch("requests.get", return_value=mock_resp)
    response = prov_eng_cli.retrieve(1)
    assert response != None
    assert response.SERVERLESS_RUNTIME.FAAS.STATE == FaaSState.RUNNING
    assert response.SERVERLESS_RUNTIME.FAAS.ENDPOINT == TEST_SR_ENDPOINT


def test_prov_engine_cli_delete(prov_eng_cli: ProvEngineClient, mocker: MockerFixture):
    # Patch request delete to return status_CODE 204
    mock_resp = mocker.Mock()
    mock_resp.status_code = 204
    mocker.patch("requests.delete", return_value=mock_resp)
    response = prov_eng_cli.delete(1)
    assert response == True
