from cognit.modules._logger import CognitLogger
from cognit.models._device_runtime import Call
from threading import Lock

"""
Class to manage the FIFO queue of functions to be executed. 
"""
class CallQueue:

    def __init__(self, size_limit: int = 50):

        self.queue = []
        self.mutex = Lock()
        self.size_limit = size_limit
        self.cognit_logger = CognitLogger()

    def add_call(self, call: Call) -> bool:
        """
        Adds a call to the queue.

        Args:
            call (Call): Call object to be added to the queue

        Returns:
            bool: True if the call was added successfully, False otherwise
        """

        # Lock the queue
        self.mutex.acquire()

        # Check if the queue is full
        if len(self.queue) >= self.size_limit:
            self.cognit_logger.error("CallQueue is full. Call will be discarded")
            self.mutex.release()
            return False
        
        # Add the call to the end of the queue
        self.queue.append(call)

        # Release the lock
        self.mutex.release()
        return True

    def get_call(self) -> Call:
        """
        Removes and returns the first call from the queue.
        
        Returns:
            Call: Call object removed from the queue. If the queue is empty, returns None.
        """

        # Lock the queue
        self.mutex.acquire()

        # Check if the queue is empty
        if len(self.queue) == 0:
            
            self.cognit_logger.debug("CallQueue is empty")
            self.mutex.release()
            return None
        
        # Remove the first element from the queue
        call = self.queue.pop(0)

        # Release the lock
        self.mutex.release()
        return call

    def __len__(self):
        """
        Returns the number of calls in the queue.

        Returns:
            int: Number of calls in the queue
        """
        
        return len(self.queue)