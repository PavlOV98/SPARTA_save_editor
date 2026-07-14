"""Загрузчик локализации SPARTA 2035."""

from __future__ import annotations
from pathlib import Path
import json


def load_localization(file_path: str | Path) -> dict[str, str]:
    """Загрузить файл локализации (JSON-словарь ключ->значение).

    Файл без расширения, содержимое — JSON-объект вида {"key": "value"}.
    """
    p = Path(file_path)
    if not p.is_file():
        return {}

    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}

    if not isinstance(data, dict):
        return {}

    result = {}
    for key, value in data.items():
        if isinstance(value, str):
            result[str(key)] = value

    return result


def get_item_name(localization: dict[str, str], item_name_key: str | None) -> str:
    """Получить название предмета из локализации по ключу itemName."""
    if not item_name_key or not localization:
        return ""
    return localization.get(item_name_key, "")


def get_item_description(localization: dict[str, str], item_desc_key: str | None) -> str:
    """Получить описание предмета."""
    if not item_desc_key or not localization:
        return ""
    return localization.get(item_desc_key, "")
