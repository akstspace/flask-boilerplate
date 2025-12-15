"""Logging configuration with Loguru"""

import logging

from flask import Flask
from loguru import logger


class InterceptHandler(logging.Handler):
    def emit(self, record):
        """
        Forward a standard logging.LogRecord to the Loguru logger while preserving exception information.
        
        Parameters:
            record (logging.LogRecord): The logging record to forward to Loguru; its level, message,
                and exception information (if any) are preserved as part of the forwarded log.
        """
        logger_opt = logger.opt(depth=6, exception=record.exc_info)
        logger_opt.log(record.levelno, record.getMessage())


def setup_logging(app: Flask):
    # Avoid adding multiple InterceptHandler instances if create_app is called multiple times
    """
    Configure the Flask application's logger to route records through Loguru by adding an InterceptHandler if one is not already present.
    
    Parameters:
        app (Flask): The Flask application whose logger will be configured.
    """
    if not any(isinstance(h, InterceptHandler) for h in app.logger.handlers):
        app.logger.addHandler(InterceptHandler())