from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOG_FILE_NAME = "account_manager.log"


def setup_logging(data_dir: Path, *, debug: bool = False) -> Path:
    """Configure un logger fichier dans AppData avec rotation."""

    data_dir = Path(data_dir)
    log_dir = data_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / _LOG_FILE_NAME

    root = logging.getLogger()
    level = logging.DEBUG if debug else logging.INFO
    root.setLevel(level)

    # Eviter d'ajouter plusieurs fois le meme handler lors de relances internes.
    for handler in root.handlers:
        if isinstance(handler, RotatingFileHandler):
            try:
                if Path(handler.baseFilename).resolve() == log_path.resolve():
                    handler.setLevel(level)
                    return log_path
            except Exception:
                continue

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        filename=log_path,
        maxBytes=1_048_576,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    logging.captureWarnings(True)
    logging.getLogger(__name__).info("Logging initialise: %s (level=%s)", log_path, logging.getLevelName(level))
    return log_path
