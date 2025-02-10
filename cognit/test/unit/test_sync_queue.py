from cognit.modules._sync_result_queue import SyncResultQueue
from cognit.models._device_runtime import ExecResponse, ExecReturnCode

import pytest

@pytest.fixture
def sync_result_queue() -> SyncResultQueue:
    return SyncResultQueue()

def test_sync_result_queue(sync_result_queue: SyncResultQueue):

    # Add a result to the queue
    result = ExecResponse(ExecReturnCode, "2", None)
    added = sync_result_queue.add_sync_result(result)
    assert added == True

    # Get the result from the queue
    assert sync_result_queue.get_sync_result() == result

def test_sync_result_queue_empty(sync_result_queue: SyncResultQueue):

    # Get the result from the queue
    assert sync_result_queue.get_sync_result() == None

def test_sync_result_queue_multiple_add(sync_result_queue: SyncResultQueue):

    # Add multiple results to the queue
    result1 = ExecResponse(ExecReturnCode, "2", None)
    result2 = ExecResponse(ExecReturnCode, "3", None)
    result3 = ExecResponse(ExecReturnCode, "4", None)
    assert sync_result_queue.add_sync_result(result1) == True
    assert sync_result_queue.add_sync_result(result2) == False
    assert sync_result_queue.add_sync_result(result3) == False

    # Get the results from the queue
    assert sync_result_queue.get_sync_result() == result1
    assert sync_result_queue.get_sync_result() == None

    
