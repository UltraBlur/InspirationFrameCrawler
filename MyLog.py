# MyLog.py

import logging
import os
from datetime import datetime

class MyLog:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)  # Set the logging level to DEBUG

        # Create a directory for logs if it doesn't exist
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Formatting the log messages
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # File handler - log messages are saved to a file
        log_filename = datetime.now().strftime(f"{log_dir}/%Y-%m-%d_%H-%M-%S.log")
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Stream handler - log messages are also printed to console
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)  # Set level to INFO for console output
        stream_handler.setFormatter(formatter)
        self.logger.addHandler(stream_handler)

    def get_logger(self):
        return self.logger