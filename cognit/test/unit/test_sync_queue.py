from cognit.modules._sync_result_queue import SyncResultQueue
from cognit.models._device_runtime import ExecResponse, ExecReturnCode

import pytest

@pytest.fixture
def sync_result_queue() -> SyncResultQueue:
    return SyncResultQueue()

def test_sync_result_queue(sync_result_queue: SyncResultQueue):

    # Add a result to the queue
    result = ExecResponse(ret_code=ExecReturnCode.SUCCESS, res="2", err=None)
    added = sync_result_queue.add_sync_result(result)
    assert added == True

    # Get the result from the queue
    assert sync_result_queue.get_sync_result() == result

def test_sync_result_queue_multiple_add(sync_result_queue: SyncResultQueue):

    # Add multiple results to the queue
    result1 = ExecResponse(ret_code=ExecReturnCode.SUCCESS, res="2", err=None)
    result2 = ExecResponse(ret_code=ExecReturnCode.SUCCESS, res="3", err=None)
    result3 = ExecResponse(ret_code=ExecReturnCode.SUCCESS, res="4", err=None)
    assert sync_result_queue.add_sync_result(result1) == True
    assert sync_result_queue.add_sync_result(result2) == False
    assert sync_result_queue.add_sync_result(result3) == False

    # Get the results from the queue
    assert sync_result_queue.get_sync_result() == result1