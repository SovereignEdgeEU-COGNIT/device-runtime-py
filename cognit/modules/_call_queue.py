from cognit.modules._logger import CognitLogger
from cognit.models._device_runtime import Call
from threading import Lock

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

"""
Class to manage the FIFO queue of functions to be executed. 
"""
class CallQueue(metaclass=Singleton):

    def __init__(self, size_limit: int = 5):
        self.queue = []
        self.mutex = Lock()
        self.size_limit = size_limit
        self.cognit_logger = CognitLogger()

    def add_call(self, call: Call) -> bool:

        # Lock the queue
        self.mutex.acquire()

        # Check if the queue is full
        if len(self.queue) >= self.size_limit:
            self.cognit_logger.error("CallQueue is full. Call will be discarded")
            return False
        
        # Add the call to the end of the queue
        self.queue.append(call)

        # Release the lock
        self.mutex.release()
        return True

    def get_call(self) -> Call:

        # Lock the queue
        self.mutex.acquire()

        # Check if the queue is empty
        if len(self.queue) == 0:
            self.cognit_logger.error("CallQueue is empty")
            self.mutex.release()
            return None
        
        # Remove the first element from the queue
        call = self.queue.pop(0)

        # Release the lock
        self.mutex.release()
        return call

    def __len__(self):
        return len(self.queue)