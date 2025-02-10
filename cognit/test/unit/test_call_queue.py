from cognit.models._device_runtime import Call, ExecutionMode, FunctionLanguage
from cognit.modules._call_queue import CallQueue

import pytest

@pytest.fixture
def call_queue() -> CallQueue:
    return CallQueue()

def sum(a: int, b: int):
    return a + b

def dummy_callback(response):
    print("Callback called")

def test_call_queue(call_queue: CallQueue):

    # Add a call to the queue
    call = Call(sum, FunctionLanguage.PY, dummy_callback, ExecutionMode.SYNC, 2, 2)
    added = call_queue.add_call(call)
    assert added == True

    # Get the call from the queue
    assert call_queue.get_call() == call

def test_call_queue_empty(call_queue: CallQueue):

    # Get the call from the queue
    assert call_queue.get_call() == None

def test_call_queue_multiple_calls(call_queue: CallQueue):

    # Add multiple calls to the queue
    call1 = Call(sum, FunctionLanguage.PY, dummy_callback, ExecutionMode.SYNC, 2, 2)
    call2 = Call(sum, FunctionLanguage.PY, dummy_callback, ExecutionMode.SYNC, 3, 3)
    call3 = Call(sum, FunctionLanguage.PY, dummy_callback, ExecutionMode.SYNC, 4, 4)
    call_queue.add_call(call1)
    call_queue.add_call(call2)
    call_queue.add_call(call3)

    # Get the calls from the queue
    assert call_queue.get_call() == call1
    assert call_queue.get_call() == call2
    assert call_queue.get_call() == call3
    assert call_queue.get_call() == None

def test_call_queue_full(call_queue: CallQueue):

    # Add multiple calls to the queue
    call1 = Call(sum, FunctionLanguage.PY, dummy_callback, ExecutionMode.SYNC, 2, 2)
    call2 = Call(sum, FunctionLanguage.PY, dummy_callback, ExecutionMode.SYNC, 3, 3)
    call3 = Call(sum, FunctionLanguage.PY, dummy_callback, ExecutionMode.SYNC, 4, 4)
    call4 = Call(sum, FunctionLanguage.PY, dummy_callback, ExecutionMode.SYNC, 5, 5)
    call5 = Call(sum, FunctionLanguage.PY, dummy_callback, ExecutionMode.SYNC, 6, 6)

    
    assert call_queue.add_call(call1) == False
    assert call_queue.add_call(call2) == False
    assert call_queue.add_call(call3) == False
    assert call_queue.add_call(call4) == False
    assert call_queue.add_call(call5) == False

    # Get the calls from the queue
    assert call_queue.get_call() == call1
    assert call_queue.get_call() == call2
    assert call_queue.get_call() == call3
    assert call_queue.get_call() == call4
    assert call_queue.get_call() == call5
    assert call_queue.get_call() == None

