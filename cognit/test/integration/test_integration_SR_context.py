import logging
import os
import time

import pytest
from pytest_mock import MockerFixture

from cognit.models._prov_engine_client import FaaSConfig, FaaSState
from cognit.modules._faas_parser import FaasParser
from cognit.modules._logger import CognitLogger
from cognit.modules._serverless_runtime_client import (
    AsyncExecId,
    AsyncExecResponse,
    AsyncExecStatus,
    ExecResponse,
    ExecReturnCode,
    ExecSyncParams,
)
from cognit.serverless_runtime_context import *

cognit_logger = CognitLogger()

COGNIT_CONF_PATH = (
    os.path.dirname(os.path.abspath(__file__))
    + "/../../../cognit/test/config/cognit.yml"
)

TEST_SR_ENDPOINT = "http://172.16.105.5:8000"


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
    my_cognit_runtime = ServerlessRuntimeContext(config_path=COGNIT_CONF_PATH)

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
    my_cognit_runtime = ServerlessRuntimeContext(config_path=COGNIT_CONF_PATH)

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
    sr = ServerlessRuntime(SERVERLESS_RUNTIME=sr_data)

    mocker.patch(
        "cognit.modules._prov_engine_client.ProvEngineClient.create",
        return_value=sr,
    )

    # Create a serverless runtime with an energy scheduling policy of 50%
    sr_conf = ServerlessRuntimeConfig()
    sr_conf.name = "MyServerlessRuntime"
    sr_conf.scheduling_policies = [EnergySchedulingPolicy(50)]
    my_cognit_runtime = ServerlessRuntimeContext(config_path=COGNIT_CONF_PATH)

    ret = my_cognit_runtime.create(sr_conf)
    assert ret == StatusCode.SUCCESS


def test_sr_ctx_status(
    mocker: MockerFixture, test_requested_sr_ctx: ServerlessRuntimeContext
):
    # First should return pending status
    f = FaaSConfig(STATE=FaaSState.PENDING)
    pending_sr_data = ServerlessRuntimeData(ID=42, NAME="MyServerlessRuntime", FAAS=f)
    pending_sr = ServerlessRuntime(SERVERLESS_RUNTIME=pending_sr_data)

    mocker.patch(
        "cognit.modules._prov_engine_client.ProvEngineClient.retrieve",
        return_value=pending_sr,
    )

    assert test_requested_sr_ctx.status == FaaSState.PENDING
    # assert test_requested_sr_ctx.status == FaaSState.NOTHING

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
    my_cognit_runtime = ServerlessRuntimeContext(config_path=COGNIT_CONF_PATH)
    assert my_cognit_runtime.status == None


def dummy_func(a, b, c):
    return a * b * c


def test_sr_ctx_call_sync(
    test_ready_sr_ctx: ServerlessRuntimeContext, mocker: MockerFixture
):
    status = test_ready_sr_ctx.call_sync(dummy_func, 2, 3, 4)

    assert type(status) == ExecResponse
    assert status.ret_code == ExecReturnCode.SUCCESS
    assert status.res == 24


def test_sr_ctx_call_async(
    test_ready_sr_ctx: ServerlessRuntimeContext, mocker: MockerFixture
):
    test_params = [2, 3, 4]

    status = test_ready_sr_ctx.call_async(dummy_func, 4, 5, 3)

    assert status.status == AsyncExecStatus.WORKING


def dummy_func_(a, b, c):
    return a * b * c


def test_sr_ctx_wait(
    test_ready_sr_ctx: ServerlessRuntimeContext, mocker: MockerFixture
):
    status1 = test_ready_sr_ctx.call_async(dummy_func_, 4, 5, 3)
    status2 = test_ready_sr_ctx.wait(status1.exec_id, 3)

    assert status2 != None
    assert status2.res.res == 60
    assert status2.exec_id == status1.exec_id
    assert status2.res.err == None


def test_sr_ctx_sync_func_error(
    test_ready_sr_ctx: ServerlessRuntimeContext, mocker: MockerFixture
):
    status = test_ready_sr_ctx.call_sync("c = a * b *c", 2, 3, 4)
    assert type(status) == ExecResponse
    assert status.ret_code == ExecReturnCode.ERROR
    assert status.res == None
    assert status.err == "400"


def test_sr_ctx_sync_param_error(
    test_ready_sr_ctx: ServerlessRuntimeContext, mocker: MockerFixture
):
    status = test_ready_sr_ctx.call_sync(dummy_func, [2, 3, 4])
    assert type(status) == ExecResponse
    assert status.ret_code == ExecReturnCode.ERROR
    assert status.res == None
    assert status.err == "400"


def test_sr_ctx_sync_param_error2(
    test_ready_sr_ctx: ServerlessRuntimeContext, mocker: MockerFixture
):
    status = test_ready_sr_ctx.call_sync(dummy_func, 2, 3, 4, 5)
    assert type(status) == ExecResponse
    assert status.ret_code == ExecReturnCode.ERROR
    assert status.res == None
    assert status.err == "400"


def test_sr_ctx_async_func_format_error(
    test_ready_sr_ctx: ServerlessRuntimeContext, mocker: MockerFixture
):
    status = test_ready_sr_ctx.call_async("c = a * b *c", 4, 5, 3)
    assert status.status == AsyncExecStatus.FAILED
    assert status.exec_id == AsyncExecId(faas_task_uuid="000-000-000")


def test_sr_ctx_async_param_error(
    test_ready_sr_ctx: ServerlessRuntimeContext, mocker: MockerFixture
):
    status = test_ready_sr_ctx.call_async(dummy_func, [2, 3, 4])
    assert status.status == AsyncExecStatus.WORKING


def test_sr_ctx_wait_param_error(
    test_ready_sr_ctx: ServerlessRuntimeContext, mocker: MockerFixture
):
    status1 = test_ready_sr_ctx.call_async(dummy_func, [4, 5, 3])
    status2 = test_ready_sr_ctx.wait(status1.exec_id, 3)
    assert status2.status == AsyncExecStatus.FAILED
    assert status2.exec_id == status1.exec_id


def faulty_function(a, b, c):
    time.sleep(10)
    return a / 0


def test_sr_ctx_wait_faulty_func(
    test_ready_sr_ctx: ServerlessRuntimeContext, mocker: MockerFixture
):
    status1 = test_ready_sr_ctx.call_async(faulty_function, 4, 5, 3)
    status2 = test_ready_sr_ctx.wait(status1.exec_id, 3)
    assert status2.status == AsyncExecStatus.FAILED
    assert status2.exec_id == status1.exec_id
