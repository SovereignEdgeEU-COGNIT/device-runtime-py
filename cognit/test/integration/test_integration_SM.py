from cognit.modules._device_runtime_state_machine import DeviceRuntimeStateMachine
from cognit.models._edge_cluster_frontend_client import ExecReturnCode
from cognit.models._cognit_frontend_client import *
from cognit.modules._faas_parser import FaasParser

import pytest

TEST_REQS_INIT = {
      "FLAVOUR": "NatureV2",
      "MAX_FUNCTION_EXECUTION_TIME": 2.0,
      "MAX_LATENCY": 25,
      "MIN_ENERGY_RENEWABLE_USAGE": 85,
      "GEOLOCATION": "IKERLAN ARRASATE/MONDRAGON 20500"
}

TEST_REQS_NEW = {
      "FLAVOUR": "NatureV2",
      "MAX_FUNCTION_EXECUTION_TIME": 3.0,
      "MAX_LATENCY": 45,
      "MIN_ENERGY_RENEWABLE_USAGE": 75,
      "GEOLOCATION": "IKERLAN ARRASATE/MONDRAGON 20500"
}

# Wrong: "GEOLOCATION" has to be defined when "MAX_LATENCY" is not null
TEST_REQS_WRONG = { 
      "FLAVOUR": "NatureV2",
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
def bad_requirements() -> Scheduling:
    bad_req = Scheduling(**TEST_REQS_WRONG)
    return bad_req

@pytest.fixture
def init_state_machine() -> DeviceRuntimeStateMachine:
    # Mock methods that are executed in INIT state
    sm = DeviceRuntimeStateMachine("cognit/test/config/cognit_v2.yml")
    return sm

# Test authentication is achieved
def test_cognit_frontend_authentication():
    # When initialize the SM, init state is executed
    sm = DeviceRuntimeStateMachine("cognit/test/config/cognit_v2.yml")
    # Assertions
    assert sm.current_state.id == "init"
    assert sm.is_token_empty() is False

# Test authentication could not be managed
def test_cognit_frontend_wrong_authentication():
    # Initialize SM with wrong credentials
    sm = DeviceRuntimeStateMachine("cognit/test/config/cognit_v2_wrong_user.yml")
    # Assertions
    assert sm.current_state.id == "init"
    assert sm.is_token_empty() is True
    
# Test upload requirements for the first time
def test_upload_requirements(
        init_state_machine: DeviceRuntimeStateMachine, 
        initial_requirements: Scheduling
    ):
    # Execute test function
    init_state_machine.update_requirements(initial_requirements)  
    # Assertions
    assert init_state_machine.requirements_uploaded is True
    assert init_state_machine.cfc.get_has_connection() is True
    assert init_state_machine.requirements_changed is False
    assert init_state_machine.current_state.id == "get_ecf_address"
    assert init_state_machine.requirements == initial_requirements

# Test upload requirements but failed
def test_failed_upload_requirements(
        init_state_machine: DeviceRuntimeStateMachine, 
        bad_requirements: Scheduling
    ):
    init_state_machine.success_auth()
    # Execute test function
    init_state_machine.update_requirements(bad_requirements)  
    # Assertions
    assert init_state_machine.requirements_uploaded is False
    assert init_state_machine.current_state.id == "init"
    assert init_state_machine.requirements == None

# Test upload requirements for the first time
def test_change_requirements(
        init_state_machine: DeviceRuntimeStateMachine, 
        initial_requirements: Scheduling,
        new_requirements: Scheduling
    ):
    # Execute test function
    init_state_machine.update_requirements(initial_requirements)  
    init_state_machine.update_requirements(new_requirements)  
    # Assertions
    assert init_state_machine.requirements_uploaded is True
    assert init_state_machine.cfc.get_has_connection() is True
    assert init_state_machine.requirements_changed is False
    assert init_state_machine.current_state.id == "get_ecf_address"
    assert init_state_machine.requirements == new_requirements

@pytest.fixture   
def test_func() -> callable:
    def subs(a: int, b: int):
        return a - b
    return subs

# Test offload function. CHECK FLAVOUR
def test_offload_function(
        init_state_machine: DeviceRuntimeStateMachine,
        initial_requirements: Scheduling,
        test_func: callable
    ):
    parser = FaasParser()
    # Upload requirements
    init_state_machine.update_requirements(initial_requirements)
    # Offload function
    # test_func = lambda x: x + 1
    result = init_state_machine.offload_function(test_func, 5, 2)
    # Assertions
    assert init_state_machine.cfc.get_has_connection() is True
    assert init_state_machine.ecf.get_has_connection() is True
    assert init_state_machine.is_token_empty() is False
    assert init_state_machine.requirements_changed is False
    assert init_state_machine.current_state.id == "ready"
    assert result.ret_code == ExecReturnCode.SUCCESS
    assert parser.deserialize(result.res) == 3
    assert result.err == None