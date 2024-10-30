from cognit.models._edge_cluster_frontend_client import ExecResponse, ExecReturnCode
from cognit.modules._edge_cluster_frontend_client import EdgeClusterFrontendClient
from cognit.modules._device_runtime_state_machine import DeviceRuntimeStateMachine
from cognit.models._cognit_frontend_client import *

from pytest_mock import MockerFixture
import pytest

TEST_REQS_INIT = {
      "FLAVOUR": "SmartCity",
      "MAX_LATENCY": 0
}

TEST_REQS_NEW = {
      "FLAVOUR": "Energy",
      "MAX_FUNCTION_EXECUTION_TIME": 2.0,
      "MAX_LATENCY": 25,
      "MIN_ENERGY_RENEWABLE_USAGE": 85,
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
def init_state_machine(mocker) -> DeviceRuntimeStateMachine:
    # Mock methods that are executed in INIT state
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient._authenticate", return_value="mocked_token")
    sm = DeviceRuntimeStateMachine("cognit/test/config/cognit_v2.yml")
    return sm

@pytest.fixture
def ready_state_machine(mocker, initial_requirements: Scheduling) -> DeviceRuntimeStateMachine:
    # Mock CFC
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient._authenticate", return_value="mocked_token")
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient.init", return_value=True)
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient._get_edge_cluster_address", return_value="mocked_ecf_address")
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient.get_has_connection", return_value=True)
    # Mock ECF
    mocker.patch("cognit.modules._edge_cluster_frontend_client.EdgeClusterFrontendClient.get_has_connection", return_value=True)
    # Init SM
    sm = DeviceRuntimeStateMachine("cognit/test/config/cognit_v2.yml")
    # Initial requirements for the state machine
    sm.requirements = initial_requirements
    # Transition to READY state
    sm.success_auth()  
    sm.requirements_up()  
    sm.address_obtained() 
    return sm

# Checks initial state is init and attributes are correctly initialized
def test_init_state(init_state_machine: DeviceRuntimeStateMachine):
    # Assertions
    assert init_state_machine.current_state == init_state_machine.init
    assert init_state_machine.cfc is not None
    assert init_state_machine.ecf is None
    assert init_state_machine.token == "mocked_token"
    assert init_state_machine.requirements is None
    assert init_state_machine.up_req_counter == 0
    assert init_state_machine.get_address_counter == 0

# Check init has transition corectly to the send_init_request state
def test_init_to_send_init_request(mocker: MockerFixture, init_state_machine: DeviceRuntimeStateMachine): 
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient.init", return_value=True)
    # Transition to SEND_INIT
    init_state_machine.success_auth()
    # Assertions
    assert init_state_machine.current_state == init_state_machine.send_init_request
    assert init_state_machine.token == "mocked_token"

# Check send_init_request enters correctly
def test_on_enter_send_init_request(mocker: MockerFixture, init_state_machine: DeviceRuntimeStateMachine):
    # Mock CognitFrontendClient init method
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient.init", return_value=True)
    # Transition to SEND_INIT_REQUEST
    init_state_machine.on_enter_send_init_request()
    # Assertions
    assert init_state_machine.requirements_uploaded is True
    assert init_state_machine.up_req_counter == 1

# Check transition to get_ecf_address from send_init is correct
def test_send_init_request_to_get_ecf_address(mocker: MockerFixture, init_state_machine: DeviceRuntimeStateMachine):
    # Mock CFC
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient.init", return_value=True)
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient._get_edge_cluster_address", return_value="mocked_ecf_address")
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient.get_has_connection", return_value=True)
    # Mock ECF
    mocker.patch("cognit.modules._edge_cluster_frontend_client.EdgeClusterFrontendClient.get_has_connection", return_value=True)
    # Transition to INIT to GET_ECF_ADDRESS
    init_state_machine.success_auth()
    init_state_machine.requirements_up()
    # Assertions
    assert init_state_machine.current_state == init_state_machine.get_ecf_address
    assert init_state_machine.ecc_address == "mocked_ecf_address"
    assert init_state_machine.ecf is not None
    assert init_state_machine.get_address_counter == 1

# Check get_ecf_address state enters correctly
def test_on_enter_get_ecf_address(mocker: MockerFixture, init_state_machine: DeviceRuntimeStateMachine):
    # Mock CFC and ECF methods
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient._get_edge_cluster_address", return_value="mocked_ecf_address")
    mocker.patch("cognit.modules._edge_cluster_frontend_client.EdgeClusterFrontendClient.get_has_connection", return_value=True)
    # Test function
    init_state_machine.on_enter_get_ecf_address()
    # Assertions
    assert init_state_machine.ecf is not None
    assert init_state_machine.get_address_counter == 1
    assert init_state_machine.ecc_address == "mocked_ecf_address"

# Check transition to ready from get_ecf_address is correct
def test_get_ecf_address_to_ready(mocker: MockerFixture, init_state_machine: DeviceRuntimeStateMachine):
    # Mock CFC
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient.init", return_value=True)
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient._get_edge_cluster_address", return_value="mocked_ecf_address")
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient.get_has_connection", return_value=True)
    # Mock ECF
    mocker.patch("cognit.modules._edge_cluster_frontend_client.EdgeClusterFrontendClient.get_has_connection", return_value=True)
    # Realize necessary transitions to reach to ready
    init_state_machine.success_auth()
    init_state_machine.requirements_up()
    init_state_machine.address_obtained()
    # Assertions
    assert init_state_machine.current_state == init_state_machine.ready

def test_execute_function_offloading(mocker: MockerFixture, init_state_machine: DeviceRuntimeStateMachine):
    # Mock CFC method to return a task ID
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient._serialize_and_upload_fc_to_daas_gw", return_value=["func_id", "app_req_id"])
    # Mock the ECF client and its method (mocked object)
    mock_ecf = mocker.create_autospec(EdgeClusterFrontendClient)
    # Create an actual ExecResponse object to return from the mock
    mock_resp = ExecResponse(
        ret_code = ExecReturnCode.SUCCESS, 
        res = "mocked_result",
        err = None
    )
    # Set the mock to return the actual ExecResponse when the function is called
    mock_ecf.execute_function.return_value = mock_resp
    # Assign the mocked ECF client to the state machine
    init_state_machine.ecf = mock_ecf
    # Call the function you're testing
    result = init_state_machine._execute_function_offloading(lambda x: x + 1, 2)
    # Assertions
    assert result is not None
    assert result.err is None
    assert result.res == "mocked_result"
    # Verify that the correct methods were called
    mock_ecf.execute_function.assert_called_once_with("app_req_id", "func_id", "sync", (2,))

# Tests for offload_function

# Test offload_function if the state machine is in not READY state
def test_offload_function_success_in_ready(mocker: MockerFixture, ready_state_machine: DeviceRuntimeStateMachine):
    # Mock SM method
    mock_execute_function = mocker.patch.object(DeviceRuntimeStateMachine, "_execute_function_offloading", return_value="mocked_result")
    # Execute test function
    test_func = lambda x: x + 1
    result = ready_state_machine.offload_function(test_func, 2)
    # Assertions
    mock_execute_function.assert_called_once_with(test_func, 2)
    assert result == "mocked_result"

# Test offload_function if the state machine is not in READY state
def test_offload_function_when_not_ready(mocker: MockerFixture, init_state_machine: DeviceRuntimeStateMachine):
    mock_execute_function = mocker.patch.object(DeviceRuntimeStateMachine, "_execute_function_offloading", return_value="mocked_result")
    # Mock CFC
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient.init", return_value=True)
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient._get_edge_cluster_address", return_value="mocked_ecf_address")
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient.get_has_connection", return_value=True)
    # Mock ECF
    mocker.patch("cognit.modules._edge_cluster_frontend_client.EdgeClusterFrontendClient.get_has_connection", return_value=True)
    # Execute test function
    test_func = lambda x: x + 1
    result = init_state_machine.offload_function(test_func, 2)
    # It should end in ready state and giving "mocked_result"
    assert init_state_machine.ecc_address == "mocked_ecf_address"
    assert init_state_machine.token == "mocked_token"
    assert init_state_machine.current_state == init_state_machine.ready
    mock_execute_function.assert_called_once_with(test_func, 2)
    assert result == "mocked_result"
    
# Test if result was not given
def test_offload_function_no_result(mocker: MockerFixture, ready_state_machine: DeviceRuntimeStateMachine):
    # Mock cfc method
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient._get_edge_cluster_address", return_value="mocked_ecf_address")
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient._serialize_and_upload_fc_to_daas_gw", return_value=["func_id", "app_req_id"])
    # Mock ECF method
    mock_resp = mocker.Mock()
    mock_resp = ExecResponse(
        ret_code = ExecReturnCode.SUCCESS, 
        res = None,
        err = None
    )
    mocker.patch("cognit.modules._edge_cluster_frontend_client.EdgeClusterFrontendClient.execute_function", return_value=mock_resp)
    # Test function
    test_func = lambda x: x + 1
    result = ready_state_machine.offload_function(test_func, 2)
    # Assertions
    assert result.res is None

# Tests for update_requirements()

def test_update_requirements_no_change(
        mocker: MockerFixture, 
        ready_state_machine: DeviceRuntimeStateMachine, 
        initial_requirements: Scheduling
    ):
    # Mock init method when SM passes to SEND_INIT_REQ to update requirements
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient.init", return_value=True)
    # Mock the logger
    mock_logger = ready_state_machine.logger
    mock_logger.info = mocker.Mock()
    # Test function
    ready_state_machine.update_requirements(initial_requirements)
    # Assertions
    assert ready_state_machine.current_state.id == ready_state_machine.ready.id
    mock_logger.info.assert_called_with("Requirements have not changed. Clients are not restarted.")

def test_update_requirements_with_change_in_ready_state(
        mocker: MockerFixture, 
        ready_state_machine: DeviceRuntimeStateMachine, 
        new_requirements: Scheduling
    ):
    # Mock init method when SM passes to SEND_INIT_REQ to update requirements
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient.init", return_value=True)
    # Mock the logger
    mock_logger = ready_state_machine.logger
    mock_logger.info = mocker.Mock()
    # Test function
    ready_state_machine.update_requirements(new_requirements)
    # Assertions
    assert ready_state_machine.current_state.id == "get_ecf_address"
    assert ready_state_machine.requirements == new_requirements
    mock_logger.info.assert_called_with("Requirements successfully uploaded! Entering GET_ECF_ADDRESS state...")

def test_update_requirements_with_change_in_get_ecf_address_state(
        mocker: MockerFixture, 
        init_state_machine: DeviceRuntimeStateMachine, 
        initial_requirements: Scheduling,
        new_requirements: Scheduling
    ):
    # Mock CFC methods
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient.init", return_value=True)
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient._get_edge_cluster_address", return_value="mocked_ecf_address")
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient.get_has_connection", return_value=True)
    # Mock ECF methods
    mocker.patch("cognit.modules._edge_cluster_frontend_client.EdgeClusterFrontendClient.get_has_connection", return_value=True)
    # Move state machine to get_ecf_address
    init_state_machine.requirements = initial_requirements
    init_state_machine.success_auth()  
    init_state_machine.requirements_up()  
    # Verify the state is get_ecf_address
    assert init_state_machine.current_state.id == 'get_ecf_address'
    # Test function
    init_state_machine.update_requirements(new_requirements)
    # Assertions
    assert init_state_machine.current_state.id == 'get_ecf_address'
    assert init_state_machine.requirements == new_requirements

def test_update_requirements_token_invalid_in_ready_state(
        mocker: MockerFixture, 
        ready_state_machine: DeviceRuntimeStateMachine, 
        new_requirements: Scheduling
    ):
    # Change is_token_valid to false
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient.get_has_connection", return_value=False)
    # Mock the logger
    mock_logger = ready_state_machine.logger
    mock_logger.error = mocker.Mock()
    # Test function
    ready_state_machine.update_requirements(new_requirements)
    # Assertions
    assert ready_state_machine.current_state.id == ready_state_machine.init.id
    assert ready_state_machine.requirements == None
    mock_logger.error.assert_called_with("Frontend client is not connected: requirements could not be uploaded.")

def test_update_requirements_in_init_state(
        mocker: MockerFixture, 
        init_state_machine: DeviceRuntimeStateMachine, 
        new_requirements: Scheduling
    ):
    # Mock CFC
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient.init", return_value=True)
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient.get_has_connection", return_value=True)
    # Test function
    init_state_machine.update_requirements(new_requirements)
    # Assertions
    assert init_state_machine.current_state == init_state_machine.get_ecf_address
    assert init_state_machine.requirements == new_requirements

def test_update_requirements_limit_reached(
        mocker: MockerFixture, 
        init_state_machine: DeviceRuntimeStateMachine, 
        new_requirements: Scheduling
    ):
    # Mock CFC
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient.init", return_value=False)
    mocker.patch("cognit.modules._cognit_frontend_client.CognitFrontendClient.get_has_connection", return_value=True)
    # Mock the logger
    mock_logger = init_state_machine.logger
    mock_logger.error = mocker.Mock()
    # Test function
    init_state_machine.update_requirements(new_requirements)
    # Assertions
    assert init_state_machine.current_state == init_state_machine.init
    assert init_state_machine.requirements is None
    # Now check if the logger was called with the correct message
    mock_logger.error.assert_called_with(
        "Number of attempts reached: unable to upload requirements. State machine is now in init state."
    )
