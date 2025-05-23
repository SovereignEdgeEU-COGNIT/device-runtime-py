from cognit.models._edge_cluster_frontend_client import ExecResponse, ExecutionMode, ExecReturnCode
from cognit.modules._edge_cluster_frontend_client import EdgeClusterFrontendClient

from pytest_mock import MockerFixture
import pytest

global callback_executed, response_received

@pytest.fixture
def dummy_callback() -> callable:
    def callback(response):
        global callback_executed
        global response_received
        response_received = response
        callback_executed = True
    return callback

def test_client_success_initialization():
    test_address = "the_address"
    test_token = "the_token"

    # Initialize ECF Client
    ecf = EdgeClusterFrontendClient(test_token, test_address)

    # Assertions
    assert ecf.token == "the_token"
    assert ecf.address == "the_address"
    assert ecf._has_connection == True
    
def test_client_bad_initialization():
    test_address = None
    test_token = "the_token"

    # Initialize ECF Client
    ecf = EdgeClusterFrontendClient(test_token, test_address)

    # Assertions
    assert ecf.token == "the_token"
    assert ecf.address == None
    assert ecf._has_connection == False

def test_execute_function_if_async(
        mocker: MockerFixture,
        dummy_callback: callable
    ):

    global callback_executed, response_received
    test_address = "the_address"
    test_token = "the_token"

    mocker.patch("cognit.modules._faas_parser.FaasParser.deserialize", return_value=6)

    # Initialize ECF Client
    ecf = EdgeClusterFrontendClient(test_token, test_address)

    assert ecf.address == "the_address"
    assert ecf._has_connection == True
    assert ecf.token == "the_token"
    
    # Mocked result from post method
    mock_resp = mocker.Mock()
    mock_resp.json.return_value = ExecResponse(
        ret_code = ExecReturnCode.SUCCESS, 
        res = "serialized_res",
        err = None
    )

    # Mock post method
    mocker.patch("requests.post", return_value=mock_resp)

    # Test function
    function_id = "123"
    app_req_id = 123

    response = ecf.execute_function(
        func_id=function_id, 
        app_req_id=app_req_id, 
        exec_mode=ExecutionMode.ASYNC, 
        callback=dummy_callback, 
        params_tuple=[2, 3]
    )

    # Assertions
    assert response == None
    assert callback_executed == True
    assert response_received.res == 6
    assert response_received.ret_code == ExecReturnCode.SUCCESS
   
def test_execute_function_if_sync(
        mocker: MockerFixture,
    ):

    global callback_executed

    mocker.patch("cognit.modules._faas_parser.FaasParser.deserialize", return_value=6)

    test_address = "the_address"
    callback_executed = False
    test_token = "the_token"

    # Initialize ECF Client
    ecf = EdgeClusterFrontendClient(test_token, test_address)

    assert ecf.address == "the_address"
    assert ecf._has_connection == True
    assert ecf.token == "the_token"
    
    # Mocked result from post method
    mock_resp = mocker.Mock()
    mock_resp.json.return_value = ExecResponse(
        ret_code = ExecReturnCode.SUCCESS, 
        res = "serialized_res",
        err = None
    )

    # Mock post method
    mocker.patch("requests.post", return_value=mock_resp)

    # Test function
    function_id = "123"
    app_req_id = 123
    response = ecf.execute_function(
        func_id=function_id, 
        app_req_id=app_req_id, 
        exec_mode=ExecutionMode.SYNC, 
        callback=callback_executed, 
        params_tuple=[2, 3]
    )

    # Assertions
    
    assert response.ret_code == ExecReturnCode.SUCCESS
    assert callback_executed == False
    assert response.res == 6