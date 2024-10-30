from pytest_mock import MockerFixture
import pytest

from cognit.models._edge_cluster_frontend_client import ExecResponse, ExecutionMode, ExecReturnCode
from cognit.modules._edge_cluster_frontend_client import EdgeClusterFrontendClient

@pytest.fixture   
def execution_mode() -> ExecutionMode:
    exec_mode = ExecutionMode.SYNC
    return exec_mode

def test_client_success_initialization():
    test_address = "the_address"
    test_token = "the_token"
    # Initialize ECF Client
    ecf = EdgeClusterFrontendClient(test_token, test_address)
    # Assertions
    assert ecf.token == "the_token"
    assert ecf.address == "the_address"
    assert ecf.has_connection == True
    
def test_client_bad_initialization():
    test_address = None
    test_token = "the_token"
    # Initialize ECF Client
    ecf = EdgeClusterFrontendClient(test_token, test_address)
    # Assertions
    assert ecf.token == "the_token"
    assert ecf.address == None
    assert ecf.has_connection == False

def test_execute_function(
        mocker: MockerFixture,
        execution_mode: ExecutionMode
    ):
    test_address = "the_address"
    test_token = "the_token"
    # Initialize ECF Client
    ecf = EdgeClusterFrontendClient(test_token, test_address)
    # Mocked result from post method
    mock_resp = mocker.Mock()
    mock_resp.json.return_value = ExecResponse(
        ret_code = ExecReturnCode.SUCCESS, 
        res = 3,
        err = None
    )
    # Mock post method
    mocker.patch("requests.post", return_value=mock_resp)
    # Test function
    function_id = "123"
    app_req_id = 123
    response = ecf.execute_function(function_id, app_req_id, execution_mode, (1, 2))
    # Assertions
    assert response.res == "3"
    assert response.ret_code == ExecReturnCode.SUCCESS
    assert ecf.has_connection == True
    assert ecf.token == "the_token"
    assert ecf.address == "the_address"