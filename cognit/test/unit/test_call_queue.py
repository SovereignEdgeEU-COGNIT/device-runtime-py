from cognit.models._device_runtime import Call, ExecutionMode, FunctionLanguage
from cognit.modules._call_queue import CallQueue

import pytest

@pytest.fixture
def call_queue(5) -> CallQueue:
    return CallQueue()

def sum(a: int, b: int):
    return a + b

def dummy_callback(response):
    print("Callback called")

def test_call_queue(call_queue: CallQueue):

    # Add a call to the queue
    call = Call(
        function=sum,
        fc_lang=FunctionLanguage.PY,
        callback=dummy_callback,
        mode=ExecutionMode.SYNC,
        params=[2, 2]
    )

    added = call_queue.add_call(call)
    assert added == True

    # Get the call from the queue
    assert call_queue.get_call() == call

def test_call_queue_empty(call_queue: CallQueue):

    # Get the call from the queue
    assert call_queue.get_call() == None

def test_call_queue_multiple_calls(call_queue: CallQueue):

    # Add multiple calls to the queue
    call1 = Call(function=sum, fc_lang=FunctionLanguage.PY, callback=dummy_callback, mode=ExecutionMode.SYNC, params=[2, 2])
    call2 = Call(function=sum, fc_lang=FunctionLanguage.PY, callback=dummy_callback, mode=ExecutionMode.SYNC, params=[3, 3])    
    call3 = Call(function=sum, fc_lang=FunctionLanguage.PY, callback=dummy_callback, mode=ExecutionMode.SYNC, params=[4, 4])
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
    call1 = Call(function=sum, fc_lang=FunctionLanguage.PY, callback=dummy_callback, mode=ExecutionMode.SYNC, params=[2, 2])
    call2 = Call(function=sum, fc_lang=FunctionLanguage.PY, callback=dummy_callback, mode=ExecutionMode.SYNC, params=[3, 3])
    call3 = Call(function=sum, fc_lang=FunctionLanguage.PY, callback=dummy_callback, mode=ExecutionMode.SYNC, params=[4, 4])
    call4 = Call(function=sum, fc_lang=FunctionLanguage.PY, callback=dummy_callback, mode=ExecutionMode.SYNC, params=[5, 5])
    call5 = Call(function=sum, fc_lang=FunctionLanguage.PY, callback=dummy_callback, mode=ExecutionMode.SYNC, params=[6, 6])
    call6 = Call(function=sum, fc_lang=FunctionLanguage.PY, callback=dummy_callback, mode=ExecutionMode.SYNC, params=[7, 7])
    
    assert call_queue.add_call(call1) == True
    assert call_queue.add_call(call2) == True
    assert call_queue.add_call(call3) == True
    assert call_queue.add_call(call4) == True
    assert call_queue.add_call(call5) == True
    assert call_queue.add_call(call6) == False

    # Get the calls from the queue
    assert call_queue.get_call() == call1
    assert call_queue.get_call() == call2
    assert call_queue.get_call() == call3
    assert call_queue.get_call() == call4
    assert call_queue.get_call() == call5
    assert call_queue.get_call() == None

