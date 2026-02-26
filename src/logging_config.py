"""Logging configuration: level from NBA_DEBUG env var (1 = DEBUG) or WARNING."""
import logging
import os

LOG_LEVEL = logging.DEBUG if os.environ.get("NBA_DEBUG") else logging.WARNING


def setup_logging():
    """Configure the app root logger. Call at the start of run()."""
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(levelname)s [%(name)s] %(message)s",
    )


def get_logger(name):
    """Return a logger with the module name."""
    return logging.getLogger(name)
