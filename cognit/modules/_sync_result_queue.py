from cognit.models._device_runtime import ExecResponse
from cognit.modules._logger import CognitLogger
from threading import Lock, Condition
import time

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class SyncResultQueue(metaclass=Singleton):

    def __init__(self):
        self.result = None
        self.mutex = Lock()
        self.cognit_logger = CognitLogger()
        self.condition = Condition(self.mutex)  # Use condition variable

    def add_sync_result(self, result: ExecResponse) -> bool:
        """
        Add a result to the queue

        Args:
            result (ExecResponse): Result to be added to the queue
        """
        with self.condition:  # Acquire lock for thread safety
            if self.result is not None:
                self.cognit_logger.error("SyncResultsQueue is full. Result will be discarded")
                return False
            self.result = result
            self.condition.notify()  # Notify any waiting thread that the result is available
        return True

    def get_sync_result(self) -> ExecResponse:
        """
        Get a result from the queue

        Returns:
            ExecResponse: Result from the queue
        """
        with self.condition:  # Acquire lock for thread safety
            while self.result is None:
                # Wait until there is a result available
                self.condition.wait()  # Efficiently wait for a result
            result = self.result
            self.result = None  # Reset the result
        return result

