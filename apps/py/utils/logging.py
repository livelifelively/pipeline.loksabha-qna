import logging
from typing import Optional

from colorlog import ColoredFormatter

from apps.py.utils.run_context import RunContext


def setup_logger(name: str = None, run_context: Optional[RunContext] = None) -> logging.Logger:
    """Configure colored logging for the application."""

    formatter = ColoredFormatter(
        "%(log_color)s[%(asctime)s][%(run_id)s] - %(name)s - %(levelname)s - %(message)s",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(name or __name__)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    if run_context:
        logger = logging.LoggerAdapter(
            logger,
            {
                "run_id": run_context.run_id[:8],  # Use first 8 chars of UUID
                "sansad": run_context.sansad,
                "session": run_context.session,
            },
        )

    return logger
