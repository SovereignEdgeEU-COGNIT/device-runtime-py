import threading

class CallbackTimer:

    def __init__(self, interval, callback):
        """
        Initializes a timer that calls a callback function at regular intervals.

        :param interval: Time in seconds between each callback invocation.
        :param callback: Function to be called at each interval.
        """
        self.interval = interval
        self.callback = callback
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._execute)

    def _execute(self):
        while not self._stop_event.wait(self.interval):
            self.callback()

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread.join()
