import pytest
from pytest_mock import MockerFixture

from cognit.models._prov_engine_client import *
from cognit.models._serverless_runtime_client import *
from cognit.modules._faas_parser import FaasParser
from cognit.modules._serverless_runtime_client import *

TEST_RESPONSE_FAAS_EXEC_SYNC = ExecResponse()


def sum(a: int, b: int):
    return a + b


@pytest.fixture
def serialized_fc() -> ExecSyncParams:
    parser = FaasParser()
    serialized_fc = parser.serialize(sum)
    mock_hash = "000-000-000"
    serialized_fc_hash = parser.serialize(mock_hash)
    serialized_params = []
    serialized_params.append(parser.serialize(2))
    serialized_params.append(parser.serialize(2))

    fc = ExecSyncParams(fc=serialized_fc, fc_hash=serialized_fc_hash, lang="PY", params=serialized_params)

    return fc


@pytest.fixture
def test_src() -> ServerlessRuntimeClient:
    srvl_rt_cli = ServerlessRuntimeClient("http://myserverlessruntime-1234")
    return srvl_rt_cli


def test_src_faas_exec_sync(
    test_src: ServerlessRuntimeClient,
    mocker: MockerFixture,
    serialized_fc: ExecSyncParams,
):
    # Patch request post to return status_CODE 200 and a body
    # with Faas execution StatusCode
    mock_resp = mocker.Mock()
    mock_resp.json.return_value = ExecResponse()
    mock_resp.status_code = 200
    mocker.patch("requests.post", return_value=mock_resp)
    r = test_src.faas_execute_sync(serialized_fc)
    assert r != None
    assert r.ret_code == ExecReturnCode.SUCCESS


def test_src_faas_exec_async(
    test_src: ServerlessRuntimeClient,
    mocker: MockerFixture,
    serialized_fc: ExecSyncParams,
):
    # Patch request post to return status_CODE 200 and a body
    # with AsyncExeecId corresponding to the FaaS ID that
    # is executing the function.
    mock_resp = mocker.Mock()
    mock_resp.json.return_value = AsyncExecResponse(
        status=AsyncExecStatus.WORKING, exec_id=AsyncExecId(faas_task_uuid="0")
    )
    mock_resp.status_code = 200
    mocker.patch("requests.post", return_value=mock_resp)
    r = test_src.faas_execute_async(serialized_fc)
    assert r != None
    assert r.status == AsyncExecStatus.WORKING
    assert r.exec_id == AsyncExecId(faas_task_uuid="0")


def test_src_wait(test_src: ServerlessRuntimeClient, mocker: MockerFixture):
    mock_src_wait = mocker.Mock()
    mock_src_wait.json.return_value = {
        "success": True,
        "exec_id": 1,
        "status": AsyncExecStatus("WORKING"),
    }
    mock_src_wait.status_code = 200
    mocker.patch("requests.get", return_value=mock_src_wait)
    r = test_src.wait("12345")
    print("WAIT status: {}".format(r))
    assert r != None
    assert r.status == AsyncExecStatus("READY")
    assert type(r.exec_id) == AsyncExecId
    assert type(r.res) == ExecResponse
    # assert r.res.ret_code == ExecReturnCode.ERROR
    assert type(r.res.ret_code) == ExecReturnCode
    # assert r.exec_id.faas_task_uuid == "0"
