"""Logging configuration with Loguru"""

import logging

from flask import Flask
from loguru import logger


class InterceptHandler(logging.Handler):
    def emit(self, record):
        """
        Forward a standard logging.LogRecord to Loguru, preserving level and exception information.
        
        This handler converts the incoming LogRecord into a Loguru log call using a fixed call depth and forwards the record's message, level number, and exception info so the original context and traceback are retained.
        
        Parameters:
            record (logging.LogRecord): The logging record to be emitted and forwarded to Loguru.
        """
        logger_opt = logger.opt(depth=6, exception=record.exc_info)
        logger_opt.log(record.levelno, record.getMessage())


def setup_logging(app: Flask):
    """
    Configure a Flask application's logger to route standard library logging through Loguru.
    
    Parameters:
        app (Flask): The Flask application whose `app.logger` will receive an InterceptHandler that forwards log records to Loguru.
    """
    app.logger.addHandler(InterceptHandler())