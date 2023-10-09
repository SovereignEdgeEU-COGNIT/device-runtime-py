import pytest
from pytest_mock import MockerFixture

from cognit.models._prov_engine_client import *
from cognit.models._serverless_runtime_client import *
from cognit.modules._cognitconfig import CognitConfig
from cognit.modules._prov_engine_client import ProvEngineClient
from cognit.serverless_runtime_context import (
    EnergySchedulingPolicy,
    ServerlessRuntimeConfig,
    ServerlessRuntimeContext,
)

from cognit.modules._logger import CognitLogger
cognit_logger = CognitLogger()

TEST_RESPONSE_PENDING = {
    "NAME": "faas",
    "ID": 1,
    "SERVICE_ID": 1,
    "FAAS": {
        "CPU": 1,
        "MEMORY": 1,
        "DISK_SIZE": 1,
        "FLAVOUR": "flavour",
        "ENDPOINT": "endpoint",
        "STATE": "pending",
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
    },
}

TEST_SR_ENDPOINT = "http://myserverlessruntime-1234"

TEST_RESPONSE_RUNNING = {
    "NAME": "faas",
    "ID": 1,
    "SERVICE_ID": 1,
    "FAAS": {
        "CPU": 1,
        "MEMORY": 1,
        "DISK_SIZE": 1,
        "FLAVOUR": "flavour",
        "ENDPOINT": TEST_SR_ENDPOINT,
        "STATE": "running",
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
    },
}


@pytest.fixture
def test_cognit_config() -> CognitConfig:
    config = CognitConfig("./config/cognit.yml")
    return config


@pytest.fixture
def sr_context(test_cognit_config: CognitConfig) -> ServerlessRuntimeContext:
    my_cognit = ServerlessRuntimeContext(config_path="./config/cognit.yml")
    return my_cognit

def test_prov_engine_create(
    sr_context: ServerlessRuntimeContext,
):
    # Configure the serverless runtime requeriments
    sr_conf = ServerlessRuntimeConfig()
    sr_conf.name = "Example Serverless Runtime"
    sr_conf.scheduling_policies = [EnergySchedulingPolicy(50)]

    ret = None
    try:
        ret = sr_context.create(sr_conf)
    except Exception as e:
        cognit_logger.error(f'Error: {e}')
        
    assert ret != None

