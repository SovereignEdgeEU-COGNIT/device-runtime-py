from cognit.models._edge_cluster_frontend_client import ExecReturnCode
from cognit.models._cognit_frontend_client import Scheduling 
from cognit.modules._faas_parser import FaasParser
from cognit.device_runtime import DeviceRuntime

import pytest
import time 

COGNIT_CONFIG_PATH = "cognit/test/config/cognit_v2.yml"

# Execution requirements, dependencies and policies
REQS_INIT = {
      "FLAVOUR": "EnergyV2",
      "GEOLOCATION": "IKERLAN ARRASATE/MONDRAGON 20500"
}

REQS_NEW = {
      "FLAVOUR": "NatureV2",
      "MAX_FUNCTION_EXECUTION_TIME": 3.0,
      "MAX_LATENCY": 45,
      "MIN_ENERGY_RENEWABLE_USAGE": 75,
      "GEOLOCATION": "IKERLAN ARRASATE/MONDRAGON 20500"
}

@pytest.fixture   
def test_func() -> callable:
    def multiply(a: int, b: int):
        return a * b
    return multiply

# Test init() is executed correctly
def test_device_runtime_init():

    # Instantiate DeviceRuntime
    device_runtime = DeviceRuntime(COGNIT_CONFIG_PATH)

    # Initialize device runtime
    has_init = device_runtime.init(REQS_INIT)

    # Assertions
    assert has_init is True
    assert device_runtime.sm_handler is not None
    assert device_runtime.sm_thread is not None

    # Stop
    has_stop = device_runtime.stop()

    # Assertions
    assert has_stop is True
    assert device_runtime.sm_handler is None
    assert device_runtime.sm_thread is None

# Test init() is executed two times
def test_device_runtime_init_two_times():

    # Instantiate DeviceRuntime
    device_runtime = DeviceRuntime(COGNIT_CONFIG_PATH)

    # Initialize device runtime
    has_init = device_runtime.init(REQS_INIT)
    has_init2 = device_runtime.init(REQS_INIT)

    # Assertions
    assert has_init is True
    assert has_init2 is False
    assert device_runtime.sm_handler is not None
    assert device_runtime.sm_thread is not None

    # Stop
    has_stop = device_runtime.stop()

    # Assertions
    assert has_stop is True
    assert device_runtime.sm_handler is None
    assert device_runtime.sm_thread is None 

# Test stop()
def test_device_runtime_stop():

    # Instantiate DeviceRuntime
    device_runtime = DeviceRuntime(COGNIT_CONFIG_PATH)

    # Initialize device runtime
    has_init = device_runtime.init(REQS_INIT)

    assert has_init is True
    assert device_runtime.sm_handler is not None
    assert device_runtime.sm_thread is not None

    has_stop = device_runtime.stop()

    # Assertions
    
    assert has_stop is True
    assert device_runtime.sm_handler is None
    assert device_runtime.sm_thread is None

# Test user is able to update its requirements
def test_device_runtime_update_requirements():

    device_runtime = DeviceRuntime(COGNIT_CONFIG_PATH)

    # Initialize device runtime
    has_init = device_runtime.init(REQS_INIT)

    assert has_init is True
    assert device_runtime.sm_handler is not None
    assert device_runtime.sm_thread is not None

    has_update = device_runtime.update_requirements(REQS_NEW)

    # Assertions
    assert has_update is True
    assert device_runtime.sm_handler is not None
    assert device_runtime.sm_thread is not None
    assert device_runtime.current_reqs == REQS_NEW

    # Stop Device Runtime
    has_stop = device_runtime.stop()

    # Assertions
    assert has_stop is True

# Test user is not able to update its requirements if the Device Runtime is not running
def test_device_runtime_update_requirements_not_running():

    device_runtime = DeviceRuntime(COGNIT_CONFIG_PATH)

    has_update = device_runtime.update_requirements(REQS_NEW)

    # Assertions
    assert has_update is False
    assert device_runtime.current_reqs is None

# Global variables
callback_executed = False
response_received = None

@pytest.fixture
def dummy_callback():
    global callback_executed, response_received
    def callback(response):
        global callback_executed, response_received
        response_received = response
        callback_executed = True
    return callback

# Test user call_async()
def test_device_runtime_call_async(test_func: callable, dummy_callback: callable):
    global callback_executed, response_received

    device_runtime = DeviceRuntime(COGNIT_CONFIG_PATH)

    # Initialize device runtime
    has_init = device_runtime.init(REQS_INIT)

    assert has_init is True
    assert device_runtime.sm_handler is not None
    assert device_runtime.sm_thread is not None

    # Offload and execute a function
    was_called = device_runtime.call_async(test_func, dummy_callback, 2, 3)

    time.sleep(10)

    # Assertions
    assert was_called is True
    assert callback_executed is True
    assert response_received.res == 6
    assert response_received.ret_code == ExecReturnCode.SUCCESS

    # Stop Device Runtime
    has_stop = device_runtime.stop()

    # Assertions
    assert has_stop is True
    assert has_stop is True

# Test user call_sync()
def test_device_runtime_call_sync(test_func: callable):

    device_runtime = DeviceRuntime(COGNIT_CONFIG_PATH)

    # Initialize device runtime
    has_init = device_runtime.init(REQS_INIT)

    assert has_init is True
    assert device_runtime.sm_handler is not None
    assert device_runtime.sm_thread is not None

    # Offload and execute a function
    result = device_runtime.call_sync(test_func, 2, 3)

    # Assertions
    assert result.res == 6
    assert result.ret_code == ExecReturnCode.SUCCESS

    # Stop Device Runtime
    has_stop = device_runtime.stop()

    # Assertions
    assert has_stop is True