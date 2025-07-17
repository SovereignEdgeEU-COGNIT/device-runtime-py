from cognit.modules._sync_result_queue import SyncResultQueue
from cognit.models._cognit_frontend_client import Scheduling
from cognit.modules._cognitconfig import CognitConfig
from cognit.modules._sm_handler import StateMachineHandler
from cognit.modules._call_queue import CallQueue
import pytest

COGNIT_CONFIG_PATH = "cognit/test/config/cognit_v2.yml"
BAD_COGNIT_CONFIG_PATH = "cognit/test/config/cognit_v2_wrong_user.yml"

REQS_INIT = {
    "FLAVOUR": "EnergyV2",
    "GEOLOCATION": {
        "latitude": 43.05,
        "longitude": -2.53
    }
}

REQS_NEW = {
    "FLAVOUR": "EnergyV2",
    "MAX_LATENCY": 45,  # New requirement added
    "GEOLOCATION": {
        "latitude": 33.05,
        "longitude": -55.0
    }
}

BAD_REQS = {
    "FLAVOUR": "WrongFlavour"  
}

@pytest.fixture
def sm_handler() -> StateMachineHandler:

    # Init parameters
    cognit_config = CognitConfig(COGNIT_CONFIG_PATH)
    requirements = Scheduling(**REQS_INIT)  
    call_queue = CallQueue()
    sync_result_queue = SyncResultQueue()

    # Init SMHandler
    return StateMachineHandler(cognit_config, requirements, call_queue, sync_result_queue)


@pytest.fixture
def sm_handler_bad_config() -> StateMachineHandler:

    # Init parameters
    cognit_config = CognitConfig(BAD_COGNIT_CONFIG_PATH)
    requirements = Scheduling(**REQS_INIT)  
    call_queue = CallQueue()
    sync_result_queue = SyncResultQueue()

    # Init SMHandler
    return StateMachineHandler(cognit_config, requirements, call_queue, sync_result_queue)

# INIT -> SEND_INIT_REQUEST -> GET_ECF_ADDRESS -> READY

def test_sm_handler_positive_escenario(
    sm_handler: StateMachineHandler,
):
    
    assert sm_handler.sm.current_state.id == "init"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "send_init_request"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "get_ecf_address"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "ready"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "ready"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "ready"

# INIT -> SEND_INIT_REQUEST -> GET_ECF_ADDRESS -> READY -> READY -> READY -> GET_ECF_ADDRESS

def test_sm_handler_edge_cluster_address_changed(
    sm_handler: StateMachineHandler,
):
    
    assert sm_handler.sm.current_state.id == "init"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "send_init_request"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "get_ecf_address"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "ready"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "ready"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "ready"
    sm_handler.sm.new_ecf_address = "http://new-ecf-address.com"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "get_ecf_address"

# INIT -> INIT

def test_sm_handler_bad_config(
    sm_handler_bad_config: StateMachineHandler,
):
    
    assert sm_handler_bad_config.sm.current_state.id == "init"
    sm_handler_bad_config.evaluate_conditions()
    assert sm_handler_bad_config.sm.current_state.id == "init"
    sm_handler_bad_config.evaluate_conditions()
    assert sm_handler_bad_config.sm.current_state.id == "init"

# INIT -> SEND_INIT_REQUEST -> SEND_INIT_REQUEST -> SEND_INIT_REQUEST -> INIT **

def test_sm_handler_send_init_request_bad_requirements(
    sm_handler: StateMachineHandler,
):
    
    assert sm_handler.sm.current_state.id == "init"
    sm_handler.sm.requirements = None
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "send_init_request" # First attempt
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "send_init_request" # Second attempt
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "send_init_request" # Third attempt
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "init"

# INIT -> SEND_INIT_REQUEST -> INIT 

def test_sm_handler_send_init_request_cfc_not_connected(
    sm_handler: StateMachineHandler,
):
    
    assert sm_handler.sm.current_state.id == "init"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "send_init_request"
    sm_handler.sm.cfc.set_has_connection(False)
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "init"

# INIT -> SEND_INIT_REQUEST -> SEND_INIT_REQUEST -> GET_ECF_ADDRESS -> READY

def test_sm_handler_send_init_request_update_requirements(
    sm_handler: StateMachineHandler
):
    
    assert sm_handler.sm.current_state.id == "init"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "send_init_request"
    sm_handler.change_requirements(Scheduling(**REQS_NEW))
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "send_init_request"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "get_ecf_address"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "ready"

# INIT -> SEND_INIT_REQUEST -> GET_ECF_ADDRESS -> GET_ECF_ADDRESS -> GET_ECF_ADDRESS -> INIT

def test_sm_handler_get_ecf_address_ecf_not_connected(
    sm_handler: StateMachineHandler,
):
    
    assert sm_handler.sm.current_state.id == "init"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "send_init_request"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "get_ecf_address"
    sm_handler.sm.ecf.set_has_connection(False)
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "get_ecf_address"
    sm_handler.sm.ecf.set_has_connection(False)
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "get_ecf_address"
    sm_handler.sm.ecf.set_has_connection(False)
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "init"
    
# INIT -> SEND_INIT_REQUEST -> GET_ECF_ADDRESS -> SEND_INIT_REQUEST -> GET_ECF_ADDRESS -> READY

def test_sm_handler_get_ecf_address_change_requirements(
    sm_handler: StateMachineHandler,    
):
    
    assert sm_handler.sm.current_state.id == "init"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "send_init_request"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "get_ecf_address"
    sm_handler.change_requirements(Scheduling(**REQS_NEW))
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "send_init_request"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "get_ecf_address"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "ready"

# INIT -> SEND_INIT_REQUEST -> GET_ECF_ADDRESS -> INIT

def test_sm_handler_get_ecf_address_cfc_disconnected(
    sm_handler: StateMachineHandler,
):
    
    assert sm_handler.sm.current_state.id == "init"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "send_init_request"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "get_ecf_address"
    sm_handler.sm.cfc.set_has_connection(False)
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "init"
    
# INIT -> SEND_INIT_REQUEST -> GET_ECF_ADDRESS -> READY -> SEND_INIT_REQUEST -> GET_ECF_ADDRESS -> READY

def test_sm_handler_ready_new_requirements(
    sm_handler: StateMachineHandler,
):
    
    assert sm_handler.sm.current_state.id == "init"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "send_init_request"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "get_ecf_address"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "ready"
    sm_handler.change_requirements(Scheduling(**REQS_NEW))
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "send_init_request"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "get_ecf_address"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "ready"    

# INIT -> SEND_INIT_REQUEST -> GET_ECF_ADDRESS -> READY -> INIT (ECF not connected)

def test_sm_handler_get_ecf_address_reconnect(
    sm_handler: StateMachineHandler,
):
    
    assert sm_handler.sm.current_state.id == "init"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "send_init_request"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "get_ecf_address"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "ready"
    sm_handler.sm.ecf.set_has_connection(False)
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "init"   

# INIT -> SEND_INIT_REQUEST -> GET_ECF_ADDRESS -> READY -> INIT (CFC not connected)

def test_sm_handler_get_cfc_address_reconnect(
    sm_handler: StateMachineHandler,
):
    
    assert sm_handler.sm.current_state.id == "init"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "send_init_request"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "get_ecf_address"
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "ready"
    sm_handler.sm.cfc.set_has_connection(False)
    sm_handler.evaluate_conditions()
    assert sm_handler.sm.current_state.id == "init"
