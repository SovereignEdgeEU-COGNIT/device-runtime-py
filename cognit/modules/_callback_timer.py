import threading

class CallbackTimer:

    def __init__(self, interval, callback):
        """
        Initializes a timer that calls a callback function at regular intervals.

        Args:
            interval (float): The interval in seconds between each callback execution.
            callback (Callable): The function to be called at each interval.
        """
        
        self.interval = interval
        self.callback = callback
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._execute)

    def _execute(self):
        """
        Executes the callback function at regular intervals.
        """

        while not self._stop_event.wait(self.interval):
            self.callback()

    def start(self):
        """
        Starts the timer.
        """

        self._thread.start()

    def stop(self):
        """
        Stops the timer.
        """

        self._stop_event.set()
        self._thread.join()
