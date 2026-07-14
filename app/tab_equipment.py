"""Вкладка редактирования ItemModuleConfig.json (предметы/оборудование)."""

import json
import os
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QPushButton,
    QScrollArea, QSplitter, QListWidget, QListWidgetItem,
    QMessageBox, QTabWidget, QTextEdit, QComboBox, QCheckBox,
    QGroupBox, QGridLayout,
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QFont


def is_enemy_item(key: str) -> bool:
    """Определяет, относится ли предмет к врагам."""
    # Прямые маркеры врагов
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
    # Суффиксы вражеских фракций
    enemy_suffixes = ("_Wolves", "_Orphans", "_G9", "_DRONE_PC", "_FRONT_PC")
    for suffix in enemy_suffixes:
        if key.endswith(suffix):
            return True
    # Специальный случай: FireGrenade_FRONT (без _T0)
    if key == "FireGrenade_FRONT":
        return True
    return False


class EquipmentTab(QWidget):
    """Вкладка для редактирования ItemModuleConfig.json."""

    def __init__(self):
        super().__init__()
        self.json_data: dict | None = None
        self.file_path: str | None = None
        self.equipment_dict: dict[str, dict] = {}

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Верхняя панель: путь и загрузка
        top_layout = QHBoxLayout()

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText(
            "Путь к ItemModuleConfig.json (или выберите папку с игрой)"
        )
        self.path_edit.setReadOnly(True)
        top_layout.addWidget(self.path_edit, 1)

        btn_load = QPushButton("📂 Загрузить")
        btn_load.clicked.connect(self._load_file)
        top_layout.addWidget(btn_load)

        btn_auto = QPushButton("🔍 Из папки игры")
        btn_auto.clicked.connect(self._auto_find)
        top_layout.addWidget(btn_auto)

        layout.addLayout(top_layout)

        # Табы: Спарта / Враги
        self.tabs = QTabWidget()
        self.sparta_tab = _FactionSubTab("Спарта")
        self.enemy_tab = _FactionSubTab("Враги")

        self.tabs.addTab(self.sparta_tab, "🛡 Спарта")
        self.tabs.addTab(self.enemy_tab, "☠ Враги")

        layout.addWidget(self.tabs)

        # Кнопки сохранения
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("💾 Сохранить в файл")
        btn_save.clicked.connect(self._save_to_file)
        btn_layout.addWidget(btn_save)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888;")
        btn_layout.addWidget(self.status_label, 1)

        layout.addLayout(btn_layout)

    def _load_file(self, path: str | None = None):
        """Загрузить файл ItemModuleConfig."""
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

        # Разделяем на Спарту и врагов
        sparta_items = {}
        enemy_items = {}
        for key, value in self.equipment_dict.items():
            if is_enemy_item(key):
                enemy_items[key] = value
            else:
                sparta_items[key] = value

        self.sparta_tab.set_data(sparta_items)
        self.enemy_tab.set_data(enemy_items)

        self.status_label.setText(
            f"✅ Загружено: {len(self.equipment_dict)} предметов "
            f"(Спарта: {len(sparta_items)}, Враги: {len(enemy_items)})"
        )

    def _auto_find(self):
        """Автоматически найти файл из папки игры (из QSettings)."""
        settings = QSettings("SPARTA Tools", "SPARTA Save Editor")
        game_folder = settings.value("game_folder", "")
        if not game_folder:
            QMessageBox.information(
                self, "Папка не указана",
                "Сначала укажите папку с игрой на вкладке «Выбор файла»."
            )
            return

        # Ищем Configs/Modules/ItemModuleConfig.json
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
        """Сохранить изменения."""
        if not self.file_path:
            QMessageBox.warning(self, "Файл не загружен",
                                "Сначала загрузите ItemModuleConfig.json.")
            return

        # Собираем данные из обеих вкладок
        sparta_data = self.sparta_tab.collect()
        enemy_data = self.enemy_tab.collect()

        merged = {}
        merged.update(sparta_data)
        merged.update(enemy_data)

        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(merged, f, ensure_ascii=False, indent=2)
            self.status_label.setText(f"✅ Сохранено: {self.file_path}")
            QMessageBox.information(self, "Сохранено",
                                    f"Файл сохранён:\n{self.file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить:\n{e}")


class _FactionSubTab(QWidget):
    """Подвкладка для списка предметов одной фракции."""

    def __init__(self, title: str):
        super().__init__()
        self.title = title
        self.items: dict[str, dict] = {}
        self._current_key: str | None = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        splitter = QSplitter()

        # Левая панель: список
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        search_row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Поиск...")
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

        # Форма с автоподставными полями
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        form_widget = QWidget()
        self.form_layout = QFormLayout(form_widget)
        self._fields: dict[str, QWidget] = {}
        scroll.setWidget(form_widget)
        right_layout.addWidget(scroll)

        # Кнопки
        btn_layout = QHBoxLayout()
        btn_apply = QPushButton("✅ Применить")
        btn_apply.clicked.connect(self._apply)
        btn_layout.addWidget(btn_apply)

        btn_reset = QPushButton("↩ Сбросить")
        btn_reset.clicked.connect(self._reset)
        btn_layout.addWidget(btn_reset)

        right_layout.addLayout(btn_layout)

        splitter.addWidget(right_widget)
        splitter.setSizes([280, 600])

        layout.addWidget(splitter)

    def set_data(self, items: dict[str, dict]):
        """Загрузить данные."""
        self.items = items
        self._populate_list()

    def _populate_list(self, filter_text: str = ""):
        """Заполнить список."""
        self.item_list.blockSignals(True)
        self.item_list.clear()

        for key in sorted(self.items.keys()):
            if filter_text and filter_text.lower() not in key.lower():
                continue

            item = self.items[key]
            # Пытаемся показать тип/цену
            price = item.get("price", "?")
            item_type = item.get("itemCharacteristicsType",
                                  item.get("itemType", "?"))
            display = f"{key}  [{item_type}]  ({price}$)"
            self.item_list.addItem(display)

        self.count_label.setText(f"Всего: {len(self.items)}")
        self.item_list.blockSignals(False)

        if self.item_list.count() > 0 and self._current_key is None:
            self.item_list.setCurrentRow(0)

    def _filter(self, text: str):
        self._populate_list(text)

    def _on_item_selected(self, row: int):
        """Выбор предмета."""
        if row < 0:
            return
        item = self.item_list.item(row)
        if not item:
            return
        text = item.text()
        # Извлекаем ключ (до первого пробела "[")
        key = text.split("  [")[0] if "  [" in text else text.split("  (")[0]

        if key not in self.items:
            return

        self._current_key = key
        self.item_name.setText(f"📦 {key}")
        self._build_fields(self.items[key])

    def _build_fields(self, data: dict):
        """Построить поля формы на основе ключей предмета."""
        self._clear_form()
        self._fields.clear()

        for key, value in data.items():
            if isinstance(value, bool):
                w = QComboBox()
                w.addItems(["false", "true"])
                w.setCurrentText(str(value).lower())
            elif isinstance(value, int):
                w = QSpinBox()
                w.setRange(-999999999, 999999999)
                w.setValue(value)
            elif isinstance(value, float):
                w = QDoubleSpinBox()
                w.setRange(-999999999, 999999999)
                w.setDecimals(4)
                w.setValue(value)
            elif isinstance(value, str):
                w = QLineEdit(value)
            elif value is None:
                w = QLineEdit("null")
            elif isinstance(value, (dict, list)):
                w = QLineEdit(json.dumps(value, ensure_ascii=False))
            else:
                w = QLineEdit(str(value))

            self.form_layout.addRow(f"{key}:", w)
            self._fields[key] = w

    def _apply(self):
        """Применить изменения к текущему предмету."""
        if not self._current_key or self._current_key not in self.items:
            return

        data = self.items[self._current_key]
        for key, widget in self._fields.items():
            if isinstance(widget, QSpinBox):
                data[key] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                data[key] = widget.value()
            elif isinstance(widget, QComboBox):
                data[key] = widget.currentText() == "true"
            else:
                text = widget.text()
                if text and text[0] in ('{', '['):
                    try:
                        data[key] = json.loads(text)
                    except json.JSONDecodeError:
                        data[key] = text
                else:
                    data[key] = text if text != "null" else None

        self._populate_list(self.search_edit.text())
        parent = self.window()
        if hasattr(parent, 'statusBar'):
            parent.statusBar().showMessage(
                f"✅ {self._current_key} обновлён", 3000
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
