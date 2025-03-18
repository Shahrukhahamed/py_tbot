import logging
import sys
from logging.handlers import RotatingFileHandler

class BotLogger:
    def __init__(self):
        self.logger = logging.getLogger('CryptoBot')
        self.logger.setLevel(logging.INFO)
        
        # Define log format
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File Handler with rotation
        file_handler = RotatingFileHandler('bot.log', maxBytes=10 * 1024 * 1024, backupCount=5)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def log(self, level: str, message: str):
        """Log message at specified level"""
        if hasattr(self.logger, level):
            getattr(self.logger, level)(message)
        else:
            self.logger.warning(f"Invalid log level '{level}' provided. Logging as WARNING.")
            self.logger.warning(message)

# Instantiate the logger
logger = BotLogger()