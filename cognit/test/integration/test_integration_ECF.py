import pytest

from cognit.models._edge_cluster_frontend_client import ExecutionMode, ExecReturnCode
from cognit.modules._edge_cluster_frontend_client import EdgeClusterFrontendClient
from cognit.modules._device_runtime_state_machine import DeviceRuntimeStateMachine
from cognit.models._cognit_frontend_client import Scheduling  
from cognit.modules._faas_parser import FaasParser

TEST_REQS = {
      "FLAVOUR": "Energy",
      "MAX_FUNCTION_EXECUTION_TIME": 2.0,
      "MAX_LATENCY": 25,
      "MIN_ENERGY_RENEWABLE_USAGE": 85,
      "GEOLOCATION": "IKERLAN ARRASATE/MONDRAGON 20500"
}

@pytest.fixture   
def requirements() -> Scheduling:
    req = Scheduling(**TEST_REQS)
    return req

@pytest.fixture   
def execution_mode() -> ExecutionMode:
    exec_mode = ExecutionMode.SYNC
    return exec_mode

@pytest.fixture
def ready_state_machine(requirements: Scheduling) -> DeviceRuntimeStateMachine:
    # Init SM
    sm = DeviceRuntimeStateMachine("cognit/test/config/cognit_v2.yml")
    # Initial requirements for the state machine
    sm.requirements = requirements
    # Transition to READY state
    sm.success_auth()  
    sm.requirements_up()  
    sm.address_obtained() 
    return sm

@pytest.fixture   
def ecf_client() -> EdgeClusterFrontendClient:
    test_address = "the_address"
    test_token = "the_token"
    ecf = EdgeClusterFrontendClient(test_token, test_address)
    return ecf

@pytest.fixture   
def execution_mode() -> ExecutionMode:
    exec_mode = ExecutionMode.SYNC
    return exec_mode

@pytest.fixture
def test_func() -> callable:
    def multiply(a: int, b: int):
        return a * b
    return multiply


def test_execute_sync_function(
        ready_state_machine: DeviceRuntimeStateMachine,
        execution_mode: ExecutionMode,
        test_func: callable
    ):
    parser = FaasParser()
    params = (2, 3)
    # Offload function that is going to be executed
    app_req_id, func_id = ready_state_machine.cfc._serialize_and_upload_fc_to_daas_gw(test_func)
    # Function to be checked
    response = ready_state_machine.ecf.execute_function(func_id, app_req_id, execution_mode, params)
    # Assertions
    assert response.err == None
    assert parser.deserialize(response.res) == 6
    assert response.ret_code == ExecReturnCode.SUCCESS
    assert ready_state_machine.ecf.get_has_connection() == True
    assert ready_state_machine.cfc.get_has_connection() == True
    assert ready_state_machine.current_state.id == "ready"
    