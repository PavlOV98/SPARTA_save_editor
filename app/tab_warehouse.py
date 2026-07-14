"""Вкладка склада (storedEquipment)."""

import json
from typing import Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QSpinBox, QPushButton,
    QScrollArea, QGridLayout, QSplitter, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QTextEdit, QTabWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class WarehouseTab(QWidget):
    """Вкладка склада — редактирование storedEquipment."""

    def __init__(self):
        super().__init__()
        self.json_data: dict | None = None
        self._equipment_list: list[dict] = []
        self._current_idx: int = -1

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        label = QLabel(
            "Склад оборудования (storedEquipment). "
            "Выберите предмет слева и редактируйте его параметры справа."
        )
        label.setWordWrap(True)
        label.setStyleSheet("color: #666; padding: 4px;")
        layout.addWidget(label)

        splitter = QSplitter()

        # Левая панель: список предметов
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel("Предметы на складе:"))

        self.item_list = QListWidget()
        self.item_list.currentRowChanged.connect(self._on_item_selected)
        left_layout.addWidget(self.item_list)

        left_layout.addWidget(QLabel("Всего предметов: "))
        self.count_label = QLabel("0")
        left_layout.addWidget(self.count_label)

        splitter.addWidget(left_widget)

        # Правая панель: редактор предмета
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        right_layout.addWidget(QLabel("Параметры предмета:"))

        self.tabs = QTabWidget()

        # Вкладка "Основное"
        self.tab_main = QWidget()
        main_layout = QVBoxLayout(self.tab_main)
        self.main_form = QFormLayout()
        self._main_widgets: dict[str, QWidget] = {}
        main_layout.addLayout(self.main_form)
        main_layout.addStretch()
        self.tabs.addTab(self.tab_main, "Основное")

        # Вкладка "Сырые данные"
        self.tab_raw = QWidget()
        raw_layout = QVBoxLayout(self.tab_raw)
        self.raw_text = QTextEdit()
        self.raw_text.setFont(QFont("Consolas", 9))
        self.raw_text.setPlaceholderText("Полные JSON-данные предмета...")
        raw_layout.addWidget(QLabel("Все данные (сырой JSON):"))
        raw_layout.addWidget(self.raw_text)
        self.tabs.addTab(self.tab_raw, "Сырые данные")

        right_layout.addWidget(self.tabs)

        # Кнопки
        btn_layout = QHBoxLayout()
        btn_apply = QPushButton("✅ Применить")
        btn_apply.clicked.connect(self._apply_current)
        btn_layout.addWidget(btn_apply)

        btn_reset = QPushButton("↩ Сбросить")
        btn_reset.clicked.connect(self._reset_current)
        btn_layout.addWidget(btn_reset)

        right_layout.addLayout(btn_layout)

        splitter.addWidget(right_widget)
        splitter.setSizes([250, 700])

        layout.addWidget(splitter)

    # Поля, которые ищем в каждом предмете
    MAIN_FIELDS = [
        ("ID", "id", "str"),
        ("Название", "name", "str"),
        ("Тип", "type", "str"),
        ("Редкость", "rarity", "str"),
        ("Количество", "count", "int"),
        ("Уровень", "level", "int"),
        ("Слот", "slot", "str"),
        ("Подтип", "subtype", "str"),
        ("Вес", "weight", "float"),
        ("Цена", "price", "int"),
        ("Прочность", "durability", "int"),
        ("Макс. прочность", "maxDurability", "int"),
        ("Заряжено", "isEquipped", "bool"),
        ("Экипировано", "isEquipped", "bool"),
    ]

    def set_data(self, data: dict):
        """Загрузить данные склада."""
        self.json_data = data

        # Ищем storedEquipment
        eq = data.get("storedEquipment")
        if isinstance(eq, list):
            self._equipment_list = eq
        else:
            # Поиск по ключам
            self._equipment_list = self._find_equipment(data)

        self._populate_list()

    def _find_equipment(self, data: dict) -> list[dict]:
        """Ищет список оборудования в JSON."""
        candidates = ["storedEquipment", "equipment", "items", "inventory", "storage"]
        for key in candidates:
            val = data.get(key)
            if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                return val

        # Рекурсивный поиск
        def search(d, depth=0):
            if depth > 4:
                return None
            if isinstance(d, dict):
                for v in d.values():
                    if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                        return v
                    r = search(v, depth + 1)
                    if r:
                        return r
            elif isinstance(d, list):
                for item in d:
                    r = search(item, depth + 1)
                    if r:
                        return r
            return None

        result = search(data)
        return result or []

    def _populate_list(self):
        """Заполнить список предметов."""
        self.item_list.blockSignals(True)
        self.item_list.clear()

        if not self._equipment_list:
            self.item_list.addItem("⚠ Оборудование не найдено")
            self.count_label.setText("0")
            self.item_list.blockSignals(False)
            return

        for i, item in enumerate(self._equipment_list):
            name = item.get("name", item.get("id", item.get("type", f"Предмет {i+1}")))
            level = item.get("level", "")
            count = item.get("count", 1)
            if level:
                display = f"{name} (+{level}) x{count}" if count > 1 else f"{name} (+{level})"
            else:
                display = f"{name} x{count}" if count > 1 else str(name)
            self.item_list.addItem(f"📦 {display}")

        self.count_label.setText(str(len(self._equipment_list)))
        self.item_list.blockSignals(False)

        if self.item_list.count() > 0:
            self.item_list.setCurrentRow(0)

    def _on_item_selected(self, row: int):
        """Выбор предмета."""
        if row < 0 or row >= len(self._equipment_list):
            return
        self._current_idx = row
        item_data = self._equipment_list[row]
        self._build_fields(item_data)
        self.raw_text.setText(json.dumps(item_data, ensure_ascii=False, indent=2))

    def _build_fields(self, item_data: dict):
        """Построить поля редактирования."""
        self._clear_form(self.main_form)
        self._main_widgets.clear()

        for display_name, key, ptype in self.MAIN_FIELDS:
            if key not in item_data:
                continue
            value = item_data[key]

            if ptype == "int":
                w = QSpinBox()
                w.setRange(-999999999, 999999999)
                try:
                    w.setValue(int(value))
                except (ValueError, TypeError):
                    w.setValue(0)
            elif ptype == "float":
                w = QDoubleSpinBox()
                w.setRange(-999999999, 999999999)
                w.setDecimals(2)
                try:
                    w.setValue(float(value))
                except (ValueError, TypeError):
                    w.setValue(0.0)
            elif ptype == "bool":
                w = QComboBox()
                w.addItems(["false", "true"])
                w.setCurrentText(str(value).lower())
            else:
                w = QLineEdit(str(value) if value is not None else "")

            self.main_form.addRow(f"{display_name}:", w)
            self._main_widgets[key] = w

    def _apply_current(self):
        """Применить изменения текущего предмета."""
        if self._current_idx < 0 or not self._equipment_list:
            return

        item_data = self._equipment_list[self._current_idx]

        for key, widget in self._main_widgets.items():
            if isinstance(widget, QSpinBox):
                item_data[key] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                item_data[key] = widget.value()
            elif isinstance(widget, QComboBox):
                item_data[key] = widget.currentText() == "true"
            else:
                item_data[key] = widget.text()

        # Также обновляем из сырых данных
        try:
            raw = self.raw_text.toPlainText().strip()
            if raw:
                parsed = json.loads(raw)
                self._equipment_list[self._current_idx] = parsed
        except json.JSONDecodeError:
            pass

        self._populate_list()
        QMessageBox.information(self, "Применено",
                                "Изменения предмета сохранены.\n"
                                "Не забудьте сохранить файл (Ctrl+S).")

    def _reset_current(self):
        """Сбросить."""
        if self._current_idx >= 0 and self._equipment_list:
            self._on_item_selected(self._current_idx)

    def collect(self, data: dict):
        """Собрать данные — ничего не делаем, т.к. работаем по references."""
        pass

    @staticmethod
    def _clear_form(form_layout):
        while form_layout.count():
            item = form_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
