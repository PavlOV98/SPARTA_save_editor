"""Загрузчик локализации SPARTA 2035."""

from __future__ import annotations
from pathlib import Path
import re


def load_localization(folder_path: str | Path) -> dict[str, str]:
    """Загрузить файл локализации из папки Localizations.

    Формат: текстовый файл с ключами и значениями, разделёнными знаком '='.
    Файлы: Russian (основной), English (запасной).
    Возвращает словарь ключ->значение.
    """
    folder = Path(folder_path)
    if not folder.is_dir():
        return {}

    result = {}

    # Приоритет: Russian, English, любые другие
    candidates = []
    for f in sorted(folder.iterdir()):
        if f.is_file() and not f.name.startswith('.'):
            candidates.append(f)

    # Сортируем так, чтобы Russian и English были первыми
    def sort_key(p: Path):
        name = p.name.lower()
        if name == 'russian':
            return 0
        elif name == 'english':
            return 1
        else:
            return 2

    for f in sorted(candidates, key=sort_key):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line or line.startswith(";") or line.startswith("#") or line.startswith("//"):
                        continue
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()
                        if key and value and key not in result:
                            result[key] = value
        except Exception:
            continue

        # Если уже загрузили достаточно — можно прерваться
        if len(result) > 1000:
            break

    return result


def get_item_name(localization: dict[str, str], item_name_key: str | None) -> str:
    """Получить название предмета из локализации по ключу itemName.
    
    Ключ itemName выглядит как "item/name/SpartaArmorT1".
    В локализации строка: "item/name/SpartaArmorT1=Броня Спарты"
    """
    if not item_name_key or not localization:
        return ""
    return localization.get(item_name_key, "")


def get_item_description(localization: dict[str, str], item_desc_key: str | None) -> str:
    """Получить описание предмета."""
    if not item_desc_key or not localization:
        return ""
    return localization.get(item_desc_key, "")
