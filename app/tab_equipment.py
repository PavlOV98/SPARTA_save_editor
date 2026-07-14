"""Вкладка редактирования ItemModuleConfig.json (предметы/оборудование)."""

from __future__ import annotations
import json
import re
import os
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QPushButton,
    QScrollArea, QSplitter, QListWidget, QListWidgetItem,
    QMessageBox, QTabWidget, QTextEdit, QComboBox, QCheckBox,
    QGroupBox, QGridLayout,
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QFrame

from app.field_config import ITEM_SECONDARY_FIELDS


def is_enemy_item(key: str) -> bool:
    """Определяет, относится ли предмет к врагам."""
    if key.startswith("Enemy"):
        return True
    if key.startswith("SuicideBelt"):
        return True
    if key.startswith("Timebomb"):
        return True
    if key.startswith("HunterDrone"):
        return True
    if key.startswith("Armor_Shield"):
        return True
    if key.startswith("MachineArmor"):
        return True
    enemy_suffixes = ("_Wolves", "_Orphans", "_G9", "_DRONE_PC", "_FRONT_PC")
    for suffix in enemy_suffixes:
        if key.endswith(suffix):
            return True
    if key == "FireGrenade_FRONT":
        return True
    return False


def find_base_key(key: str, all_keys: set) -> str | None:
    """Найти базовый (оригинальный) предмет для дубля с припиской P/PT/_loot.

    Например: ArmorPlatePT1 -> ArmorPlateT1, FragGrenadeP -> FragGrenade.
    Если базовый ключ не найден - возвращает None (не дубль).
    """
    # _loot -> база
    if key.endswith("_loot"):
        base = key[:-5]
        if base in all_keys:
            return base

    # PT + число -> T + число  (SpartaArmorPT1 -> SpartaArmorT1)
    # PT на конце -> без PT   (ScanGrenadePT -> ScanGrenade)
    m = re.match(r'^(.*)PT(\d*)$', key)
    if m:
        prefix = m.group(1)
        num = m.group(2)
        # T + число
        base = prefix + 'T' + num
        if base in all_keys:
            return base
        # просто число (ScanGrenadePT -> ScanGrenade нет T-варианта)
        if prefix in all_keys:
            return prefix
        # число без T (MinePT2 -> Mine2? нет, но MineT2 есть - уже проверили)
        if num:
            base2 = prefix + num
            if base2 in all_keys:
                return base2

    # P на конце (FragGrenadeP -> FragGrenade)
    if key.endswith('P') and not key.endswith('PT'):
        base = key[:-1]
        if base in all_keys:
            return base

    # _PT1 -> _T1 (MobileTurret_PT1 -> MobileTurret_T1)
    m = re.match(r'^(.*)_PT(\d*)$', key)
    if m:
        prefix = m.group(1)
        num = m.group(2)
        base = prefix + '_T' + num
        if base in all_keys:
            return base

    return None


def get_duplicates(base_key: str, all_keys: set) -> list[str]:
    """Найти все дубли (с PT/P/_loot) для базового ключа."""
    dupes = []
    for k in all_keys:
        if k == base_key:
            continue
        if find_base_key(k, all_keys) == base_key:
            dupes.append(k)
    # Также проверяем, может сам base_key быть найден как чей-то дубль?
    # Нет, мы ищем дубли именно для base_key
    return dupes


class EquipmentTab(QWidget):
    """Вкладка для редактирования ItemModuleConfig.json."""

    def __init__(self):
        super().__init__()
        self.json_data: dict | None = None
        self.file_path: str | None = None
        self.equipment_dict: dict[str, dict] = {}
        self._localization: dict[str, str] = {}

        self._setup_ui()

    def auto_load(self):
        """Авто-загрузка из папки игры, если путь сохранён."""
        settings = QSettings("SPARTA Tools", "SPARTA Save Editor")
        game_folder = settings.value("game_folder", "")
        if not game_folder:
            return
        candidates = [
            Path(game_folder) / "Sparta_Data" / "StreamingAssets" / "Configs" / "Modules" / "ItemModuleConfig.json",
            Path(game_folder) / "Configs" / "Modules" / "ItemModuleConfig.json",
            Path(game_folder) / "ItemModuleConfig.json",
        ]
        for c in candidates:
            if c.exists():
                self._load_file(str(c))
                return

    def set_localization(self, loc: dict[str, str]):
        self._localization = loc
        self.sparta_tab.set_localization(loc)
        self.enemy_tab.set_localization(loc)

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        top_layout = QHBoxLayout()

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText(
            "Путь к ItemModuleConfig.json (или выберите папку с игрой)"
        )
        self.path_edit.setReadOnly(True)
        top_layout.addWidget(self.path_edit, 1)

        btn_load = QPushButton("[OPEN]  Загрузить")
        btn_load.clicked.connect(self._load_file)
        top_layout.addWidget(btn_load)

        btn_auto = QPushButton("[SEARCH]  Из папки игры")
        btn_auto.clicked.connect(self._auto_find)
        top_layout.addWidget(btn_auto)

        layout.addLayout(top_layout)

        self.tabs = QTabWidget()
        self.sparta_tab = _FactionSubTab("Спарта", is_sparta=True)
        self.enemy_tab = _FactionSubTab("Враги", is_sparta=False)

        self.tabs.addTab(self.sparta_tab, "[SHIELD]  Спарта")
        self.tabs.addTab(self.enemy_tab, "[SKULL]  Враги")

        layout.addWidget(self.tabs)

        btn_layout = QHBoxLayout()
        btn_save = QPushButton("[SAVE]  Сохранить в файл")
        btn_save.clicked.connect(self._save_to_file)
        btn_layout.addWidget(btn_save)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888;")
        btn_layout.addWidget(self.status_label, 1)

        layout.addLayout(btn_layout)

    def _load_file(self, path: Optional[str] = None):
        if not path:
            from PyQt6.QtWidgets import QFileDialog
            path, _ = QFileDialog.getOpenFileName(
                self, "Открыть ItemModuleConfig.json", "",
                "JSON (*.json);;Все файлы (*)",
            )
            if not path:
                return

        try:
            with open(path, "r", encoding="utf-8") as f:
                self.equipment_dict = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить:\n{e}")
            return

        if not isinstance(self.equipment_dict, dict):
            QMessageBox.critical(self, "Ошибка", "Файл должен содержать JSON-объект.")
            return

        self.file_path = path
        self.path_edit.setText(path)

        all_keys = set(self.equipment_dict.keys())
        sparta_items = {}
        enemy_items = {}
        for key, value in self.equipment_dict.items():
            if is_enemy_item(key):
                enemy_items[key] = value
            else:
                sparta_items[key] = value

        self.sparta_tab.set_data(sparta_items, all_keys)
        self.enemy_tab.set_data(enemy_items, all_keys)

        self.status_label.setText(
            f"[OK]  Загружено: {len(self.equipment_dict)} предметов "
            f"(Спарта: {len(sparta_items)}, Враги: {len(enemy_items)})"
        )

    def _auto_find(self):
        settings = QSettings("SPARTA Tools", "SPARTA Save Editor")
        game_folder = settings.value("game_folder", "")
        if not game_folder:
            QMessageBox.information(
                self, "Папка не указана",
                "Сначала укажите папку с игрой на вкладке «Выбор файла»."
            )
            return

        candidates = [
            Path(game_folder) / "Sparta_Data" / "StreamingAssets" / "Configs" / "Modules" / "ItemModuleConfig.json",
            Path(game_folder) / "Configs" / "Modules" / "ItemModuleConfig.json",
            Path(game_folder) / "ItemModuleConfig.json",
        ]

        for c in candidates:
            if c.exists():
                self._load_file(str(c))
                return

        QMessageBox.warning(
            self, "Не найден",
            f"ItemModuleConfig.json не найден в папке игры:\n{game_folder}"
        )

    def _save_to_file(self):
        if not self.file_path:
            QMessageBox.warning(self, "Файл не загружен",
                                "Сначала загрузите ItemModuleConfig.json.")
            return

        sparta_data = self.sparta_tab.collect()
        enemy_data = self.enemy_tab.collect()

        merged = {}
        merged.update(sparta_data)
        merged.update(enemy_data)

        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(merged, f, ensure_ascii=False, indent=2)
            self.status_label.setText(f"[OK]  Сохранено: {self.file_path}")
            QMessageBox.information(self, "Сохранено",
                                    f"Файл сохранён:\n{self.file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить:\n{e}")


class _FactionSubTab(QWidget):
    """Подвкладка для списка предметов одной фракции."""

    def __init__(self, title: str, is_sparta: bool = True):
        super().__init__()
        self.title = title
        self.is_sparta = is_sparta
        self.items: dict[str, dict] = {}
        self._all_keys: set = set()
        self._current_key: str | None = None
        self._sync_enabled: bool = True
        self._base_to_dupes: dict[str, list[str]] = {}
        self._duplicate_keys: set = set()
        self._localization: dict[str, str] = {}

        self._setup_ui()

    def set_localization(self, loc: dict[str, str]):
        self._localization = loc

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Чекбокс синхронизации (только для Спарты)
        if self.is_sparta:
            sync_row = QHBoxLayout()
            self.sync_check = QCheckBox("[SYNC]  Синхронизировать покупное и найденное")
            self.sync_check.setChecked(True)
            self.sync_check.toggled.connect(self._on_sync_toggled)
            sync_row.addWidget(self.sync_check)
            sync_row.addStretch()
            layout.addLayout(sync_row)

        splitter = QSplitter()

        # Левая панель: список
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        search_row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("[SEARCH]  Поиск...")
        self.search_edit.textChanged.connect(self._filter)
        search_row.addWidget(self.search_edit)

        self.count_label = QLabel("Всего: 0")
        search_row.addWidget(self.count_label)
        left_layout.addLayout(search_row)

        self.item_list = QListWidget()
        self.item_list.currentRowChanged.connect(self._on_item_selected)
        left_layout.addWidget(self.item_list)

        splitter.addWidget(left_widget)

        # Правая панель: редактор
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.item_name = QLabel("Выберите предмет")
        self.item_name.setStyleSheet("font-weight: bold; font-size: 13px;")
        right_layout.addWidget(self.item_name)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        form_widget = QWidget()
        self.form_layout = QFormLayout(form_widget)
        self._fields: dict[str, QWidget] = {}
        scroll.setWidget(form_widget)
        right_layout.addWidget(scroll)

        # Кнопки
        btn_layout = QHBoxLayout()
        btn_apply = QPushButton("[OK]  Применить")
        btn_apply.clicked.connect(self._apply)
        btn_layout.addWidget(btn_apply)

        btn_reset = QPushButton("↩ Сбросить")
        btn_reset.clicked.connect(self._reset)
        btn_layout.addWidget(btn_reset)

        right_layout.addLayout(btn_layout)

        splitter.addWidget(right_widget)
        splitter.setSizes([350, 550])

        layout.addWidget(splitter)

    def set_data(self, items: dict[str, dict], all_keys: set):
        """Загрузить данные."""
        self.items = items
        self._all_keys = all_keys

        # Строим карту дублей
        self._base_to_dupes = {}
        self._duplicate_keys = set()

        if self.is_sparta:
            for key in items.keys():
                base = find_base_key(key, all_keys)
                if base and base in items:
                    # Это дубль
                    self._duplicate_keys.add(key)
                    if base not in self._base_to_dupes:
                        self._base_to_dupes[base] = []
                    self._base_to_dupes[base].append(key)

        self._populate_list()

    def _on_sync_toggled(self, enabled: bool):
        """Вкл/выкл синхронизацию."""
        self._sync_enabled = enabled
        self._populate_list(self.search_edit.text())

    def _get_item_name(self, key: str, item: dict) -> str:
        """Получить локализованное название предмета."""
        name_key = item.get("itemName", "")
        if name_key and name_key in self._localization:
            return self._localization[name_key]
        return ""

    def _populate_list(self, filter_text: str = ""):
        """Заполнить список с учётом синхронизации."""
        self.item_list.blockSignals(True)
        self.item_list.clear()

        shown = 0
        for key in sorted(self.items.keys()):
            if self._sync_enabled and key in self._duplicate_keys:
                continue

            if filter_text and filter_text.lower() not in key.lower():
                continue

            item = self.items[key]
            price = item.get("price", "?")
            item_type = item.get("itemCharacteristicsType",
                                  item.get("itemType", "?"))
            # Локализованное название
            loc_name = self._get_item_name(key, item)
            if loc_name:
                display = f"{key} - {loc_name}  [{item_type}]  ({price}$)"
            else:
                display = f"{key}  [{item_type}]  ({price}$)"
            item_w = QListWidgetItem(display)
            item_w.setData(Qt.ItemDataRole.UserRole, key)
            self.item_list.addItem(item_w)
            shown += 1

        self.count_label.setText(f"Показано: {shown} / Всего: {len(self.items)}")
        self.item_list.blockSignals(False)

        if self.item_list.count() > 0 and self._current_key is None:
            self.item_list.setCurrentRow(0)

    def _filter(self, text: str):
        self._populate_list(text)

    def _on_item_selected(self, row: int):
        """Выбор предмета."""
        if row < 0:
            return
        item_w = self.item_list.item(row)
        if not item_w:
            return

        key = item_w.data(Qt.ItemDataRole.UserRole)
        if not key or key not in self.items:
            return

        self._current_key = key
        item_data = self.items[key]
        loc_name = self._get_item_name(key, item_data)
        if loc_name:
            self.item_name.setText(f"[BOX]  {key} - {loc_name}")
        else:
            self.item_name.setText(f"[BOX]  {key}")
        self._build_fields(item_data)

    SPECIAL_KEYS = {"armorSettings", "abilitiesSettings", "characterProperty", "AbilitiesSettings"}

    def _build_fields(self, data: dict):
        """Построить поля формы, разделив на секции."""
        self._clear_form()
        self._fields.clear()

        primary_keys = []
        special_keys = []
        secondary_keys = []

        for key in data.keys():
            if key in ITEM_SECONDARY_FIELDS:
                secondary_keys.append(key)
            elif key in self.SPECIAL_KEYS:
                special_keys.append(key)
            else:
                primary_keys.append(key)

        # Первая секция (основные поля)
        for key in primary_keys:
            value = data[key]
            w = self._make_widget(value)
            self.form_layout.addRow(f"{key}:", w)
            self._fields[key] = w

        # Секция специальных параметров (armorSettings, abilitiesSettings)
        if special_keys:
            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setFrameShadow(QFrame.Shadow.Sunken)
            self.form_layout.addRow(line)

            label = QLabel("Редактирование параметров")
            label.setStyleSheet("font-weight: bold; color: #666; padding: 4px 0;")
            self.form_layout.addRow(label)

            for key in special_keys:
                value = data[key]
                w = self._make_widget(value)
                self.form_layout.addRow(f"{key}:", w)
                self._fields[key] = w

        # Вторая секция (визуальные/текстовые поля)
        if secondary_keys:
            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setFrameShadow(QFrame.Shadow.Sunken)
            self.form_layout.addRow(line)

            label = QLabel("Визуальные / текстовые поля")
            label.setStyleSheet("font-weight: bold; color: #666; padding: 4px 0;")
            self.form_layout.addRow(label)

            for key in secondary_keys:
                value = data[key]
                w = self._make_widget(value)
                self.form_layout.addRow(f"{key}:", w)
                self._fields[key] = w

    def _make_widget(self, value):
        if isinstance(value, bool):
            w = QComboBox()
            w.addItems(["false", "true"])
            w.setCurrentText(str(value).lower())
            return w
        elif isinstance(value, int):
            w = QSpinBox()
            w.setRange(-999999999, 999999999)
            w.setValue(value)
            return w
        elif isinstance(value, float):
            w = QDoubleSpinBox()
            w.setRange(-999999999, 999999999)
            w.setDecimals(4)
            w.setValue(value)
            return w
        elif isinstance(value, str):
            return QLineEdit(value)
        elif value is None:
            return QLineEdit("null")
        elif isinstance(value, (dict, list)):
            return QLineEdit(json.dumps(value, ensure_ascii=False))
        else:
            return QLineEdit(str(value))

    def _sync_duplicates(self, base_key: str, field_changes: dict):
        """Синхронизировать изменения с дублями."""
        if not self._sync_enabled or base_key not in self._base_to_dupes:
            return

        for dupe_key in self._base_to_dupes[base_key]:
            if dupe_key not in self.items:
                continue
            dupe_data = self.items[dupe_key]
            for field_key, value in field_changes.items():
                if field_key in dupe_data:
                    dupe_data[field_key] = value

    def _get_field_values(self) -> dict:
        """Собрать значения из полей формы."""
        values = {}
        for key, widget in self._fields.items():
            if isinstance(widget, QSpinBox):
                values[key] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                values[key] = widget.value()
            elif isinstance(widget, QComboBox):
                values[key] = widget.currentText() == "true"
            else:
                text = widget.text()
                if text and text[0] in ('{', '['):
                    try:
                        values[key] = json.loads(text)
                    except json.JSONDecodeError:
                        values[key] = text
                else:
                    values[key] = text if text != "null" else None
        return values

    def _apply(self):
        """Применить изменения к текущему предмету."""
        if not self._current_key or self._current_key not in self.items:
            return

        data = self.items[self._current_key]
        changes = self._get_field_values()

        for key, value in changes.items():
            data[key] = value

        # Синхронизируем дубли
        if self._sync_enabled and self._current_key in self._base_to_dupes:
            self._sync_duplicates(self._current_key, changes)

        self._populate_list(self.search_edit.text())
        parent = self.window()
        if hasattr(parent, 'statusBar'):
            parent.statusBar().showMessage(
                f"[OK]  {self._current_key} обновлён", 3000
            )

    def _reset(self):
        """Сбросить."""
        if self._current_key and self._current_key in self.items:
            self._build_fields(self.items[self._current_key])

    def collect(self) -> dict:
        """Собрать все данные обратно."""
        return self.items

    def _clear_form(self):
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
