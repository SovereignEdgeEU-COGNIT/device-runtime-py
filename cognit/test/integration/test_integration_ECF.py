from cognit.models._edge_cluster_frontend_client import ExecutionMode, ExecReturnCode
from cognit.modules._edge_cluster_frontend_client import EdgeClusterFrontendClient
from cognit.modules._device_runtime_state_machine import DeviceRuntimeStateMachine
from cognit.modules._sync_result_queue import SyncResultQueue
from cognit.models._cognit_frontend_client import Scheduling  
from cognit.modules._cognitconfig import CognitConfig
from cognit.modules._call_queue import CallQueue

import pytest

COGNIT_CONFIG_PATH = "cognit/test/config/cognit_v2.yml"

TEST_REQS = {
      "FLAVOUR": "EnergyV2",
      "GEOLOCATION": "IKERLAN ARRASATE/MONDRAGON 20500"
}

@pytest.fixture
def test_func() -> callable:
    def multiply(a: int, b: int):
        return a * b
    return multiply

@pytest.fixture
def dummy_callback() -> callable:
    def callback(response):
        global callback_executed
        global response_received
        response_received = response
        callback_executed = True
    return callback

@pytest.fixture
def ready_state_machine() -> DeviceRuntimeStateMachine:

    # Init parameters
    cognit_config = CognitConfig(COGNIT_CONFIG_PATH)
    requirements = Scheduling(**TEST_REQS)  
    call_queue = CallQueue()
    sync_result_queue = SyncResultQueue()

    # Init SMHandler
    sm = DeviceRuntimeStateMachine(cognit_config, requirements, call_queue, sync_result_queue)

    # Transition to READY state
    sm.success_auth()  
    sm.requirements_up()  
    sm.address_obtained() 
    return sm

def test_execute_function_if_async(
        dummy_callback: callable,
        ready_state_machine: DeviceRuntimeStateMachine,
    ):
    
    callback_executed = False

    # Initialize ECF Client
    function_id = ready_state_machine.cfc.upload_function_to_daas(test_func)
    app_req_id = ready_state_machine.cfc.get_app_requirements_id()

    response = ready_state_machine.ecf.execute_function(function_id, app_req_id, ExecutionMode.ASYNC, dummy_callback, (2, 3))

    # Assertions
    assert response == None
    assert response_received.res == "3"
    assert response_received.ret_code == ExecReturnCode.SUCCESS
    assert ready_state_machine.ecf._has_connection == True
    assert callback_executed == True


def test_execute_function_if_sync(
        ready_state_machine: DeviceRuntimeStateMachine,
        test_func: callable
    ):

    callback_executed = False

    # Initialize ECF Client
    function_id = ready_state_machine.cfc.upload_function_to_daas(test_func)
    app_req_id = ready_state_machine.cfc.get_app_requirements_id()

    response = ready_state_machine.ecf.execute_function(function_id, app_req_id, ExecutionMode.SYNC, None, (2, 3))

    # Assertions
    assert response.res == "3"
    assert response.ret_code == ExecReturnCode.SUCCESS
    assert ready_state_machine.ecf._has_connection == True
    assert callback_executed == False
    