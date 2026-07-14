"""Загрузчик локализации SPARTA 2035."""

from __future__ import annotations
from pathlib import Path
import json


def load_localization(file_path: str | Path) -> dict[str, str]:
    """Загрузить файл локализации.

    Поддерживает два формата:
    1. JSON-объект вида {"key": "value"}
    2. Текстовый файл с ключ=значение (как в SPARTA 2035)
    """
    p = Path(file_path)
    if not p.is_file():
        return {}

    # Сначала пробуем JSON
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if isinstance(value, str):
                    result[str(key)] = value
            if result:
                return result
    except Exception:
        pass

    # Пробуем парсить как ключ=значение
    result = {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith(";") or line.startswith("#") or line.startswith("//"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and value:
                        # Если ключ повторяется - пропускаем (первый приоритет)
                        if key not in result:
                            result[key] = value
    except Exception:
        pass

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
