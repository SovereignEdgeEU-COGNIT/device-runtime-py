import pytest

from cognit.models._edge_cluster_frontend_client import ExecReturnCode
from cognit.models._cognit_frontend_client import Scheduling 
from cognit.modules._faas_parser import FaasParser
from cognit.device_runtime import DeviceRuntime


TEST_REQS_INIT = {
      "FLAVOUR": "Energy",
      "MAX_FUNCTION_EXECUTION_TIME": 2.0,
      "MAX_LATENCY": 25,
      "MIN_ENERGY_RENEWABLE_USAGE": 85,
      "GEOLOCATION": "IKERLAN ARRASATE/MONDRAGON 20500"
}

TEST_REQS_NEW = {
      "FLAVOUR": "SmartCity",
      "MAX_FUNCTION_EXECUTION_TIME": 3.0,
      "MAX_LATENCY": 45,
      "MIN_ENERGY_RENEWABLE_USAGE": 75,
      "GEOLOCATION": "IKERLAN ARRASATE/MONDRAGON 20500"
}

# Wrong: "GEOLOCATION" has to be defined when "MAX_LATENCY" is not null
TEST_REQS_WRONG = { 
      "FLAVOUR": "Energy",
      "MAX_FUNCTION_EXECUTION_TIME": 2.0,
      "MAX_LATENCY": 25,
      "MIN_ENERGY_RENEWABLE_USAGE": 85,
}

@pytest.fixture   
def initial_requirements() -> Scheduling:
    init_req = Scheduling(**TEST_REQS_INIT)
    return init_req

@pytest.fixture   
def new_requirements() -> Scheduling:
    new_req = Scheduling(**TEST_REQS_NEW)
    return new_req

@pytest.fixture   
def test_func() -> callable:
    def multiply(a: int, b: int):
        return a * b
    return multiply

# Test init() is executed correctly
def test_device_runtime_init(initial_requirements: Scheduling):
    # Instantiate DeviceRuntime
    device_runtime = DeviceRuntime("cognit/test/config/cognit_v2.yml")
    # Initialize device runtime
    device_runtime.init(TEST_REQS_INIT)
    # Assertions
    assert device_runtime.device_runtime_sm.current_state.id == "get_ecf_address"
    assert device_runtime.device_runtime_sm.requirements == initial_requirements
    assert device_runtime.device_runtime_sm.cfc.get_has_connection() is True
    assert device_runtime.device_runtime_sm.requirements_uploaded is True
    assert device_runtime.device_runtime_sm.is_token_empty() is False

# Test if bad requirements for init() where provided
def test_device_runtime_init_bad_requirements_provided():
    # Instantiate DeviceRuntime
    device_runtime = DeviceRuntime("cognit/test/config/cognit_v2.yml")
    # Initialize device runtime
    device_runtime.init(TEST_REQS_WRONG)
    # Assertions
    assert device_runtime.device_runtime_sm.current_state.id == "init"
    assert device_runtime.device_runtime_sm.cfc.get_has_connection() is True
    assert device_runtime.device_runtime_sm.requirements_uploaded is False
    assert device_runtime.device_runtime_sm.is_token_empty() is False

# Test user is able to update its requirements
def test_device_runtime_update_requirements(new_requirements: Scheduling):
    # Instantiate DeviceRuntime
    device_runtime = DeviceRuntime("cognit/test/config/cognit_v2.yml")
    # Initialize device runtime
    device_runtime.init(TEST_REQS_INIT)
    # Update requirements
    device_runtime.init(TEST_REQS_NEW)
    # Assertions
    assert device_runtime.device_runtime_sm.current_state.id == "get_ecf_address"
    assert device_runtime.device_runtime_sm.cfc.get_has_connection() is True
    assert device_runtime.device_runtime_sm.requirements == new_requirements
    assert device_runtime.device_runtime_sm.requirements_uploaded is True
    assert device_runtime.device_runtime_sm.is_token_empty() is False

def test_device_runtime_upload_empty_requirements():
    # Instantiate DeviceRuntime
    device_runtime = DeviceRuntime("cognit/test/config/cognit_v2.yml")
    # Initialize device runtime with none req and asset if correct exception is given
    with pytest.raises(TypeError):
        device_runtime.init(None)

def test_device_runtime_call(
        initial_requirements: Scheduling,
        test_func: callable
    ):
    parser = FaasParser()
    # Instantiate DeviceRuntime
    device_runtime = DeviceRuntime("cognit/test/config/cognit_v2.yml")
    # Initialize device runtime
    device_runtime.init(TEST_REQS_INIT)
    # Offload function according with initial_requirements
    return_code, result = device_runtime.call(test_func, 2, 3)
    # Assertions
    assert device_runtime.device_runtime_sm.requirements == initial_requirements
    assert device_runtime.device_runtime_sm.cfc.get_has_connection() is True
    assert device_runtime.device_runtime_sm.ecf.get_has_connection() is True
    assert device_runtime.device_runtime_sm.requirements_uploaded is True
    assert device_runtime.device_runtime_sm.current_state.id == "ready"
    assert device_runtime.device_runtime_sm.is_token_empty() is False
    assert return_code == ExecReturnCode.SUCCESS
    assert result == 6

def test_device_runtime_call_with_new_reqs(
        new_requirements: Scheduling,
        test_func: callable
    ):
    parser = FaasParser()
    # Instantiate DeviceRuntime
    device_runtime = DeviceRuntime("cognit/test/config/cognit_v2.yml")
    # Initialize device runtime
    device_runtime.init(TEST_REQS_INIT)
    # Offload function according with initial_requirements
    return_code, result = device_runtime.call(test_func, 2, 3, new_reqs=TEST_REQS_NEW)
    # Assertions
    assert device_runtime.device_runtime_sm.requirements == new_requirements
    assert device_runtime.device_runtime_sm.cfc.get_has_connection() is True
    assert device_runtime.device_runtime_sm.ecf.get_has_connection() is True
    assert device_runtime.device_runtime_sm.requirements_uploaded is True
    assert device_runtime.device_runtime_sm.current_state.id == "ready"
    assert device_runtime.device_runtime_sm.is_token_empty() is False
    assert return_code == ExecReturnCode.SUCCESS
    assert result == 6

def test_device_runtime_call_with_bad_params(
        test_func: callable
    ):
    parser = FaasParser()
    # Instantiate DeviceRuntime
    device_runtime = DeviceRuntime("cognit/test/config/cognit_v2.yml")
    # Initialize device runtime
    device_runtime.init(TEST_REQS_INIT)
    # Offload function according with initial_requirements
    return_code, result = device_runtime.call(test_func, "hello", new_reqs=TEST_REQS_NEW)
    # Assertions
    assert device_runtime.device_runtime_sm.cfc.get_has_connection() is True
    assert device_runtime.device_runtime_sm.ecf.get_has_connection() is True
    assert device_runtime.device_runtime_sm.requirements_uploaded is True
    assert device_runtime.device_runtime_sm.current_state.id == "ready"
    assert device_runtime.device_runtime_sm.is_token_empty() is False
    assert return_code == ExecReturnCode.ERROR
    assert result == "Error executing function: test_func.<locals>.multiply() missing 1 required positional argument: 'b'"