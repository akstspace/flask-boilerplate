"""Logging configuration with Loguru"""

import logging

from flask import Flask
from loguru import logger


class InterceptHandler(logging.Handler):
    def emit(self, record):
        logger_opt = logger.opt(depth=6, exception=record.exc_info)
        logger_opt.log(record.levelno, record.getMessage())


def setup_logging(app: Flask):
    # Avoid adding multiple InterceptHandler instances if create_app is called multiple times
    if not any(isinstance(h, InterceptHandler) for h in app.logger.handlers):
        app.logger.addHandler(InterceptHandler())
