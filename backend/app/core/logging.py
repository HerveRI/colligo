from __future__ import annotations

import logging
import sys
from logging.config import dictConfig

_FORMAT = "%(asctime)s %(levelname)-8s %(name)s | %(message)s"


def setup_logging(level: str = "INFO") -> None:
    # Need to swap the formatter for JSON output later
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"console": {"format": _FORMAT, "datefmt": "%H:%M:%S"}},
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "console",
                    "stream": sys.stdout,
                }
            },
            "root": {"handlers": ["console"], "level": level.upper()},
            "loggers": {
                "uvicorn.access": {"level": "WARNING", "propagate": True},
                "https": {"level": "WARNING", "propagate": True},
            },
        }
    )
    logging.captureWarnings(True)
