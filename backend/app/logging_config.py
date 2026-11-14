"""Logging setup. The application uses the standard `logging` module only (never print)."""

import logging.config


def configure_logging(level: str = "INFO") -> None:
    """
    Configure root logging with a single console handler.

    Args:
        level: Minimum log level name (DEBUG, INFO, WARNING, ERROR).
    """
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {"format": "%(asctime)s %(levelname)s [%(name)s] %(message)s"},
            },
            "handlers": {
                "console": {"class": "logging.StreamHandler", "formatter": "default"},
            },
            "root": {"level": level, "handlers": ["console"]},
        }
    )
