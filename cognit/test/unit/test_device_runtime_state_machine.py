from cognit.models._edge_cluster_frontend_client import ExecResponse, ExecReturnCode
from cognit.modules._edge_cluster_frontend_client import EdgeClusterFrontendClient
from cognit.modules._device_runtime_state_machine import DeviceRuntimeStateMachine
from cognit.models._cognit_frontend_client import Scheduling
from cognit.modules._sync_result_queue import SyncResultQueue
from cognit.modules._cognitconfig import CognitConfig
from cognit.modules._call_queue import CallQueue
from cognit.models._device_runtime import *

from statemachine.exceptions import TransitionNotAllowed
from pytest_mock import MockerFixture
import pytest

COGNIT_CONFIG_PATH = "cognit/test/config/cognit_v2.yml"

# Execution requirements, dependencies and policies
REQS_INIT = {
    "FLAVOUR": "EnergyV2",
    "GEOLOCATION": {
        "latitude": 43.05,
        "longitude": -2.53
    }
}

REQS_NEW = {
    "FLAVOUR": "NatureV2",
    "MAX_FUNCTION_EXECUTION_TIME": 3.0,
    "MAX_LATENCY": 45,
    "MIN_ENERGY_RENEWABLE_USAGE": 75,
    "GEOLOCATION": {
        "latitude": 43.05,
        "longitude": -2.53
    }
}

@pytest.fixture   
def initial_requirements() -> Scheduling:
    init_req = Scheduling(**REQS_INIT)
    return init_req

@pytest.fixture   
def new_requirements() -> Scheduling:
    new_req = Scheduling(**REQS_NEW)
    return new_req

@pytest.fixture
def init_state_machine(mocker) -> DeviceRuntimeStateMachine:

    # Init parameters
    cognit_config = CognitConfig(COGNIT_CONFIG_PATH)
    requirements = Scheduling(**REQS_INIT)
    sync_result_queue = SyncResultQueue()  
    call_queue = CallQueue()

    # Mock methods that are executed in INIT state
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient._authenticate", return_value="mocked_token")

    sm = DeviceRuntimeStateMachine(cognit_config, requirements, call_queue, sync_result_queue)

    return sm

@pytest.fixture
def ready_state_machine(mocker) -> DeviceRuntimeStateMachine:

    # Init parameters
    cognit_config = CognitConfig(COGNIT_CONFIG_PATH)
    requirements = Scheduling(**REQS_INIT)
    sync_result_queue = SyncResultQueue()  
    call_queue = CallQueue()

    # Mock methods that are executed in INIT state
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient._get_edge_cluster_address", return_value="http://mocked-address.com")
    mocker.patch("cognit.modules._edge_cluster_frontend_client.EdgeClusterFrontendClient.get_has_connection", return_value=True)
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient._authenticate", return_value="mocked_token")
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient.get_has_connection", return_value=True)
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient.init", return_value=True)

    # Init SMHandler
    sm = DeviceRuntimeStateMachine(cognit_config, requirements, call_queue, sync_result_queue)

    # Transition to READY state
    sm.success_auth()  
    sm.requirements_up()  
    sm.address_obtained() 
    return sm

# Checks initial state is init and attributes are correctly initialized
def test_init_state(init_state_machine: DeviceRuntimeStateMachine):

    # Assertions
    assert init_state_machine.current_state == init_state_machine.init
    assert init_state_machine.get_address_counter == 0
    assert init_state_machine.requirements is not None
    assert init_state_machine.token == "mocked_token"
    assert init_state_machine.up_req_counter == 0
    assert init_state_machine.cfc is not None
    assert init_state_machine.ecf is None

# Check init has transition corectly to the send_init_request state
def test_init_to_send_init_request(mocker: MockerFixture, init_state_machine: DeviceRuntimeStateMachine):

    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient.init", return_value=True)

    # Transition to SEND_INIT_REQUEST
    init_state_machine.success_auth()

    # Assertions
    assert init_state_machine.current_state == init_state_machine.send_init_request
    assert init_state_machine.requirements_uploaded is True
    assert init_state_machine.token == "mocked_token"
    assert init_state_machine.up_req_counter == 1

# Check transition to get_ecf_address from send_init is correct
def test_send_init_request_to_get_ecf_address(mocker: MockerFixture, init_state_machine: DeviceRuntimeStateMachine):
    # Mock CFC methods
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient.init", return_value=True)
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient._get_edge_cluster_address", return_value="http://mocked-address.com")
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient.get_has_connection", return_value=True)

    # Mock ECF methods and constructor
    mock_ecf_instance = mocker.Mock()
    mock_ecf_instance.get_has_connection.return_value = True
    mocker.patch("cognit.modules._edge_cluster_frontend_client.EdgeClusterFrontendClient", return_value=mock_ecf_instance)

    # Simulate state transition
    init_state_machine.success_auth()
    init_state_machine.requirements_up()

    # Assertions
    assert init_state_machine.current_state == init_state_machine.get_ecf_address
    assert init_state_machine.ecc_address == "http://mocked-address.com"
    assert init_state_machine.get_address_counter == 1
    assert isinstance(init_state_machine.ecf, EdgeClusterFrontendClient)
    assert init_state_machine.ecf.address == "http://mocked-address.com"


# Check transition to ready from get_ecf_address is correct
def test_get_ecf_address_to_ready(mocker: MockerFixture, init_state_machine: DeviceRuntimeStateMachine):

    # Mock CFC
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient.init", return_value=True)
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient._get_edge_cluster_address", return_value="http://mocked-address.com")
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient.get_has_connection", return_value=True)

    # Mock ECF methods and constructor
    mock_ecf_instance = mocker.Mock()
    mock_ecf_instance.get_has_connection.return_value = True
    mocker.patch("cognit.modules._edge_cluster_frontend_client.EdgeClusterFrontendClient", return_value=mock_ecf_instance)

    # Realize necessary transitions to reach to ready
    init_state_machine.success_auth()
    init_state_machine.requirements_up()
    init_state_machine.address_obtained()

    # Assertions
    assert init_state_machine.current_state == init_state_machine.ready
    assert init_state_machine.ecc_address == "http://mocked-address.com"
    assert init_state_machine.get_address_counter == 0
    assert isinstance(init_state_machine.ecf, EdgeClusterFrontendClient)
    assert init_state_machine.ecf.address == "http://mocked-address.com"


def test_execute_function_offloading_sync(mocker: MockerFixture, ready_state_machine: DeviceRuntimeStateMachine):

    call_object = Call(function=sum, fc_lang=FunctionLanguage.PY, callback=None, mode=ExecutionMode.SYNC, params=[2, 3])

    # Mock CFC method to return a task ID
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient.upload_function_to_daas", return_value="func_id")
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient.get_app_requirements_id", return_value="app_req_id")
    mocker.patch("cognit.modules._call_queue.CallQueue.get_call", return_value=call_object)

    # Mock the ECF client and its method (mocked object)
    mock_ecf = mocker.create_autospec(EdgeClusterFrontendClient)
   
    # Create an actual ExecResponse object to return from the mock
    mock_resp = ExecResponse(
        ret_code = ExecReturnCode.SUCCESS, 
        res = 6,
        err = None
    )

    # Set the mock to return the actual ExecResponse when the function is called
    mock_ecf.execute_function.return_value = mock_resp
    # Assign the mocked ECF client to the state machine
    ready_state_machine.ecf = mock_ecf

    # Call the function you're testing
    ready_state_machine.on_enter_ready()

    # Assertions
    assert ready_state_machine.sync_results_queue.get_sync_result() == mock_resp
    assert ready_state_machine.current_state == ready_state_machine.ready

def test_update_requirements_no_change(
        mocker: MockerFixture, 
        ready_state_machine: DeviceRuntimeStateMachine, 
        initial_requirements: Scheduling
    ):

    # Mock the logger
    mock_logger = ready_state_machine.logger
    mock_logger.error = mocker.Mock()

    # Test function
    have_changed = ready_state_machine.change_requirements(initial_requirements)

    # Assertions
    assert ready_state_machine.current_state.id == ready_state_machine.ready.id
    assert have_changed is False
    mock_logger.error.assert_called_with("New requirements are the same as the current ones")


def test_update_requirements_with_change_in_ready_state(
        mocker: MockerFixture, 
        ready_state_machine: DeviceRuntimeStateMachine, 
        new_requirements: Scheduling
    ):

    # Mock the logger
    mock_logger = ready_state_machine.logger
    mock_logger.debug = mocker.Mock()

    # Test function
    have_changed = ready_state_machine.change_requirements(new_requirements)

    assert ready_state_machine.new_requirements == new_requirements
    assert ready_state_machine.requirements_changed is True
    assert ready_state_machine.current_state.id == "ready"
    assert have_changed is True

    ready_state_machine.ready_update_requirements()

    # Assertions
    assert ready_state_machine.current_state.id == "send_init_request"
    
    mock_logger.debug.assert_called_with("Uploading requirements: " + str(new_requirements))
    assert ready_state_machine.new_requirements == None

def test_update_requirements_with_change_in_get_ecf_address_state(
        mocker: MockerFixture, 
        init_state_machine: DeviceRuntimeStateMachine, 
        new_requirements: Scheduling
    ):

    # Mock CFC methods
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient.init", return_value=True)
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient._get_edge_cluster_address", return_value="http://mocked-address.com")
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient.get_has_connection", return_value=True)

    # Mock ECF methods
    mocker.patch("cognit.modules._edge_cluster_frontend_client.EdgeClusterFrontendClient.get_has_connection", return_value=True)

    # Mock the logger
    mock_logger = init_state_machine.logger
    mock_logger.debug = mocker.Mock()

    # Move state machine to get_ecf_address
    init_state_machine.success_auth()  
    init_state_machine.requirements_up()  

    # Test function
    have_changed = init_state_machine.change_requirements(new_requirements)

    assert init_state_machine.current_state.id == "get_ecf_address"
    assert init_state_machine.new_requirements == new_requirements
    assert init_state_machine.requirements_changed is True
    assert have_changed is True

    init_state_machine.get_address_update_requirements()

    # Assertions
    assert init_state_machine.current_state.id == "send_init_request"
    
    mock_logger.debug.assert_called_with("Uploading requirements: " + str(new_requirements))
    assert init_state_machine.new_requirements == None


def test_update_requirements_token_invalid_in_ready_state(
        mocker: MockerFixture, 
        ready_state_machine: DeviceRuntimeStateMachine, 
        new_requirements: Scheduling
    ):

    # Change is_token_valid to false
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient.get_has_connection", return_value=False)

    # Test function
    have_changed = ready_state_machine.change_requirements(new_requirements)

    assert ready_state_machine.current_state.id == "ready"
    assert ready_state_machine.new_requirements == new_requirements
    assert ready_state_machine.requirements_changed is True
    assert have_changed is True

    with pytest.raises(TransitionNotAllowed, match="Can't ready_update_requirements when in Ready"):
        ready_state_machine.ready_update_requirements()

    ready_state_machine.token_not_valid_ready()

    # Assertions
    assert ready_state_machine.current_state.id == "init"
    assert ready_state_machine.new_requirements == new_requirements
    assert ready_state_machine.requirements_changed is True

def test_address_has_changed_in_ready_state(
        ready_state_machine: DeviceRuntimeStateMachine, 
    ):

    ready_state_machine.new_ecf_address = None
    
    # Transition to ecf_address state
    ready_state_machine.result_given()

    # Assertions
    assert ready_state_machine.current_state.id == "ready"
    assert ready_state_machine.ecc_address == "http://mocked-address.com"
    assert ready_state_machine.get_address_counter == 0
    assert isinstance(ready_state_machine.ecf, EdgeClusterFrontendClient)
    assert ready_state_machine.ecf.address == "http://mocked-address.com"

    # Change the address
    ready_state_machine.new_ecf_address = "http://new-mocked-address.com"

    # Transition to ecf_address state
    ready_state_machine.ready_update_ecf_address()

    # Assertions
    assert ready_state_machine.current_state.id == "get_ecf_address"
    assert ready_state_machine.ecc_address == "http://new-mocked-address.com"
    assert ready_state_machine.get_address_counter == 1
    assert isinstance(ready_state_machine.ecf, EdgeClusterFrontendClient)
    assert ready_state_machine.ecf.address == "http://new-mocked-address.com"
    assert ready_state_machine.new_ecf_address is None