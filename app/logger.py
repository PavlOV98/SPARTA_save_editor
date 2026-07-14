"""Логирование для SPARTA Save Editor."""

import logging
import sys
from pathlib import Path

_LOG_DIR = Path.home() / ".sparta_save_editor"
_LOG_FILE = _LOG_DIR / "editor.log"


def setup_logging():
    """Настроить логирование в файл и консоль."""
    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("SPARTA")
    logger.setLevel(logging.DEBUG)

    # Формат
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    # Файловый вывод
    file_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8", mode="w")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Консольный вывод
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str = "SPARTA") -> logging.Logger:
    """Получить логгер."""
    return logging.getLogger(name)
