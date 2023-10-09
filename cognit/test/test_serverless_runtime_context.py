import pytest
from pytest_mock import MockerFixture

from cognit.models._prov_engine_client import *
from cognit.models._serverless_runtime_client import *
from cognit.serverless_runtime_context import *

TEST_SR_ENDPOINT = "http://myserverlessruntime-1234"


@pytest.fixture
def test_requested_sr_ctx(mocker: MockerFixture):
    """
    _summary_: Fixture that returns a ServerlessRuntimeContext object already requested with id 42
    """
    f = FaaSConfig(STATE=FaaSState.PENDING)
    sr_data = ServerlessRuntimeData(ID=42, NAME="MyServerlessRuntime", FAAS=f)
    sr = ServerlessRuntime(SERVERLESS_RUNTIME=sr_data)

    mocker.patch(
        "cognit.modules._prov_engine_client.ProvEngineClient.create",
        return_value=sr,
    )

    # Create a serverless runtime with an energy scheduling policy of 50%
    sr_conf = ServerlessRuntimeConfig()
    sr_conf.name = "MyServerlessRuntime"
    sr_conf.scheduling_policies = [EnergySchedulingPolicy(50)]
    my_cognit_runtime = ServerlessRuntimeContext(
        config_path="./config/cognit.yml"
    )

    ret = my_cognit_runtime.create(sr_conf)

    return my_cognit_runtime


@pytest.fixture
def test_ready_sr_ctx(mocker: MockerFixture):
    """
    _summary_: Fixture that returns a ServerlessRuntimeContext object already requested with id 42
    """

    # The first time we request the SR, must be pending
    f = FaaSConfig(STATE=FaaSState.PENDING, ENDPOINT=TEST_SR_ENDPOINT)
    sr_data = ServerlessRuntimeData(ID=42, NAME="MyServerlessRuntime", FAAS=f)
    sr = ServerlessRuntime(SERVERLESS_RUNTIME=sr_data)

    mocker.patch(
        "cognit.modules._prov_engine_client.ProvEngineClient.create",
        return_value=sr,
    )

    # Create a serverless runtime with an energy scheduling policy of 50%
    sr_conf = ServerlessRuntimeConfig()
    sr_conf.name = "MyServerlessRuntime"
    sr_conf.scheduling_policies = [EnergySchedulingPolicy(50)]
    my_cognit_runtime = ServerlessRuntimeContext(
        config_path="./config/cognit.yml"
    )

    ret = my_cognit_runtime.create(sr_conf)

    # After a call to status, the SR must be running
    # We mock the retrieve method to return a running SR
    sr.SERVERLESS_RUNTIME.FAAS.STATE = FaaSState.RUNNING

    mocker.patch(
        "cognit.modules._prov_engine_client.ProvEngineClient.retrieve",
        return_value=sr,
    )

    assert my_cognit_runtime.status == FaaSState.RUNNING

    return my_cognit_runtime


def test_sr_ctx_create(mocker: MockerFixture):
    # Validate serverless runtime context creation by mocking the provisioning engine client.

    # Return a pending SR
    f = FaaSConfig(STATE=FaaSState.PENDING)
    sr_data = ServerlessRuntimeData(ID=42, NAME="MyServerlessRuntime", FAAS=f)
    sr = ServerlessRuntime(sr_data)

    mocker.patch(
        "cognit.modules._prov_engine_client.ProvEngineClient.create",
        return_value=sr,
    )

    # Create a serverless runtime with an energy scheduling policy of 50%
    sr_conf = ServerlessRuntimeConfig()
    sr_conf.name = "MyServerlessRuntime"
    sr_conf.scheduling_policies = [EnergySchedulingPolicy(50)]
    my_cognit_runtime = ServerlessRuntimeContext(
        config_path="./config/cognit.yml"
    )

    ret = my_cognit_runtime.create(sr_conf)
    assert ret == StatusCode.SUCCESS


def test_sr_ctx_status(
    mocker: MockerFixture, test_requested_sr_ctx: ServerlessRuntimeContext
):
    # First should reutrn pending status
    f = FaaSConfig(STATE=FaaSState.PENDING)
    pending_sr_data = ServerlessRuntimeData(ID=42, NAME="MyServerlessRuntime", FAAS=f)
    pending_sr = ServerlessRuntime(SERVERLESS_RUNTIME=pending_sr_data)

    mocker.patch(
        "cognit.modules._prov_engine_client.ProvEngineClient.retrieve",
        return_value=pending_sr,
    )

    assert test_requested_sr_ctx.status == FaaSState.PENDING

    #  The second time should return RUNNING  status and a valid endpoint
    f = FaaSConfig(
        STATE=FaaSState.RUNNING,
        ENDPOINT=TEST_SR_ENDPOINT,
    )
    running_sr_data = ServerlessRuntimeData(ID=42, NAME="MyServerlessRuntime", FAAS=f)
    running_sr = ServerlessRuntime(SERVERLESS_RUNTIME=running_sr_data)

    mocker.patch(
        "cognit.modules._prov_engine_client.ProvEngineClient.retrieve",
        return_value=running_sr,
    )

    assert test_requested_sr_ctx.status == FaaSState.RUNNING


def test_sr_ctx_status_no_init():
    my_cognit_runtime = ServerlessRuntimeContext(
        config_path="./config/cognit.yml"
    )
    assert my_cognit_runtime.status == None


def dummy_func(a, b, c):
    return a * b * c


def test_sr_ctx_call_sync(
    test_ready_sr_ctx: ServerlessRuntimeContext, mocker: MockerFixture
):
    # Mock the response of a sync function offloading
    mock_resp = mocker.Mock()
    mock_resp.json.return_value = {
        "res": "gAWVDAAAAAAAAAAoSwBLAUsCSwN0lC4=",
        "code": 201,
    }

    mock_resp.status_code = 200
    mocker.patch("requests.post", return_value=mock_resp)

    status = test_ready_sr_ctx.call_sync(dummy_func, 2, 3, 4)
#    assert status == ExecResponse()
    assert status.res == (0, 1, 2, 3)


def test_sr_ctx_call_async(
    test_ready_sr_ctx: ServerlessRuntimeContext, mocker: MockerFixture
):
    # Mock the response of an async function offloading
    mock_running_src = mocker.Mock()
    mock_running_src.json.return_value = {
        "faas_uuid": "123e4567-e89b-12d3-a456-426614174000",
        "code": 201,
    }
    mock_running_src.status_code = 200

    nash_equilibrium = lambda payoff_A_C, payoff_A_D, payoff_B_C, payoff_B_D: (
        (payoff_B_D - payoff_A_D) / (payoff_A_C + payoff_B_D - payoff_A_D - payoff_B_C),
        (payoff_B_C - payoff_A_C) / (payoff_A_C + payoff_B_D - payoff_A_D - payoff_B_C),
    )

    # Example usage of nash equilibrium mock function with
    # Prisoner's Dilemma payoffs
    payoff_A_C = 3  # Payoff for player A cooperating and player B defecting
    payoff_A_D = 0  # Payoff for player A defecting and player B defecting
    payoff_B_C = 5  # Payoff for player B cooperating and player A defecting
    payoff_B_D = 1  # Payoff for player B defecting and player A cooperating
    test_params = [payoff_A_C, payoff_A_D, payoff_B_C, payoff_B_D]

    mocker.patch("requests.post", return_value=mock_running_src)
    status = test_ready_sr_ctx.call_async(
        nash_equilibrium, payoff_A_C, payoff_A_D, payoff_B_C, payoff_B_D
    )
    assert status.status == AsyncExecStatus.WORKING


def test_sr_ctx_wait(
    test_ready_sr_ctx: ServerlessRuntimeContext, mocker: MockerFixture
):
    # Mock example of a querying to a function that is still working
    mock_src_wait = mocker.Mock()
    mock_src_wait.json.return_value = {"state": "WORKING", "code": 200}
    mock_src_wait.status_code = 200

    uuid = AsyncExecId(faas_task_uuid="12345-67890-12345")
    mocker.patch("requests.get", return_value=mock_src_wait)
    status = test_ready_sr_ctx.wait(uuid, 3)
    assert status != None
    assert status.status == AsyncExecStatus.WORKING


def test_sr_ctx_delete(
    test_ready_sr_ctx: ServerlessRuntimeContext, mocker: MockerFixture
):
    # Mock example of a Cognit context deletion
    mock_src_delete = mocker.Mock()
    mock_src_delete.json.return_value = {}
    mock_src_delete.status_code = 200

    mocker.patch("requests.delete", return_value=mock_src_delete)
    test_ready_sr_ctx.delete()

    # TODO: How to test that an SR is deleted within an unitary test
    # with no interaction with PE
    assert test_ready_sr_ctx != None


# TODO: For M15.
def test_sr_ctx__copy():
    pass
