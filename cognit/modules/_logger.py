import inspect
import logging
import os

LOGGER_NAME = "cognit-logger"

class CognitLogger:

    def __init__(self, verbose=True):
        
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(LOGGER_NAME)
        self.logger.propagate = False
        self.verbose = verbose

        if not self.logger.hasHandlers():

            # Add stream handler
            stream_handler = self.get_stream_handler()
            self.logger.addHandler(stream_handler)

            # Add file handler
            file_handler = self.get_file_handler()
            self.logger.addHandler(file_handler)

    def get_stream_handler(self):

        # Set level
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.DEBUG)
        
        # Set log format
        formatter = logging.Formatter("[%(asctime)5s] [%(levelname)-s] %(message)s")
        stream_handler.setFormatter(formatter)
            
        return stream_handler

    def get_file_handler(self):

        # Set level
        file_handler = logging.FileHandler('/var/log/device_runtime.log')
        file_handler.setLevel(logging.DEBUG)

        # Set log format
        formatter = logging.Formatter("[%(asctime)5s] [%(levelname)-s] %(message)s")
        file_handler.setFormatter(formatter)

        return file_handler
    
    def set_level(self, level: int):
        self.logger.setLevel(level)
    
    def _log(self, level: int, message):

        if self.verbose:

            frame = inspect.stack()[2]
            filename = os.path.basename(frame.filename)
            line = frame.lineno
            self.logger.log(level, f"[{filename}::{line}] {message}")
        else:
            self.logger.log(level, message)

    def debug(self, message):
        self._log(logging.DEBUG, message)
        return

    def info(self, message):
        self._log(logging.INFO, message)

    def warning(self, message):
        self._log(logging.WARNING, message)

    def error(self, message):
        self._log(logging.ERROR, message)

    def critical(self, message):
        self._log(logging.CRITICAL, message)
