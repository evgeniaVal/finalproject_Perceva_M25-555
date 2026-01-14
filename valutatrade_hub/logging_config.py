import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

_logger: logging.Logger | None = None


def get_logger() -> logging.Logger:
    global _logger
    if _logger is None:
        log_path = Path("logs")
        log_path.mkdir(parents=True, exist_ok=True)

        _logger = logging.getLogger("valutatrade_hub")
        _logger.setLevel(logging.INFO)
        _logger.propagate = False

        if _logger.handlers:
            _logger.handlers.clear()

        handler = RotatingFileHandler(
            filename=log_path / "actions.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            fmt="%(levelname)s %(asctime)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        handler.setFormatter(formatter)

        _logger.addHandler(handler)

    return _logger
