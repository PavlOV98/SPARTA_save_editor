"""Вкладка склада (storedEquipment как словарь)."""

import json

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QPushButton,
    QScrollArea, QSplitter, QListWidget, QListWidgetItem,
    QMessageBox, QTextEdit, QTabWidget, QComboBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class WarehouseTab(QWidget):
    """Вкладка склада — storedEquipment как словарь с выводом содержимого."""

    def __init__(self):
        super().__init__()
        self.json_data: dict | None = None
        self.equipment_dict: dict[str, dict] = {}  # ключ -> предмет
        self._current_key: str | None = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        label = QLabel("Склад оборудования (storedEquipment)")
        label.setStyleSheet("font-weight: bold; font-size: 13px; padding: 2px;")
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

        self.count_label = QLabel("Всего: 0")
        left_layout.addWidget(self.count_label)

        splitter.addWidget(left_widget)

        # Правая панель: редактор предмета
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.item_name_label = QLabel("Предмет не выбран")
        self.item_name_label.setStyleSheet("font-size: 13px; font-weight: bold; padding: 4px;")
        right_layout.addWidget(self.item_name_label)

        self.tabs = QTabWidget()

        # Вкладка "Основное"
        self.tab_main = QWidget()
        main_layout = QVBoxLayout(self.tab_main)
        scroll_main = QScrollArea()
        scroll_main.setWidgetResizable(True)
        scroll_w = QWidget()
        self.main_form = QFormLayout(scroll_w)
        self._main_widgets: dict[str, QWidget] = {}
        scroll_main.setWidget(scroll_w)
        main_layout.addWidget(scroll_main)
        self.tabs.addTab(self.tab_main, "Поля предмета")

        # Вкладка "Сырые данные"
        self.tab_raw = QWidget()
        raw_layout = QVBoxLayout(self.tab_raw)
        self.raw_text = QTextEdit()
        self.raw_text.setFont(QFont("Consolas", 9))
        raw_layout.addWidget(QLabel("Все данные (JSON):"))
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
        splitter.setSizes([280, 700])

        layout.addWidget(splitter)

    # ---- Поля предмета (авто-определение) ----
    # Исключаем поля, которые не показываем как отдельные поля
    SKIP_KEYS = set()

    def set_data(self, data: dict):
        """Загрузить данные склада. storedEquipment — словарь."""
        self.json_data = data

        eq = data.get("storedEquipment")
        if isinstance(eq, dict):
            self.equipment_dict = eq
        else:
            self.equipment_dict = {}

        self._populate_list()

    def _populate_list(self):
        """Заполнить список предметов."""
        self.item_list.blockSignals(True)
        self.item_list.clear()

        if not self.equipment_dict:
            self.item_list.addItem("⚠ storedEquipment не найден или пуст")
            self.count_label.setText("Всего: 0")
            self.item_list.blockSignals(False)
            return

        for key, item in self.equipment_dict.items():
            if not isinstance(item, dict):
                continue
            # Пытаемся получить читаемое имя
            name = item.get("name", item.get("id", key))
            level = item.get("level", "")
            rarity = item.get("rarity", "")
            display = str(name)
            if rarity:
                display = f"[{rarity}] {display}"
            if level:
                display += f" (+{level})"
            self.item_list.addItem(f"📦 {display}  [{key}]")

        self.count_label.setText(f"Всего: {len(self.equipment_dict)}")
        self.item_list.blockSignals(False)

        if self.item_list.count() > 0:
            self.item_list.setCurrentRow(0)

    def _on_item_selected(self, row: int):
        """Выбор предмета."""
        if row < 0:
            return
        keys = list(self.equipment_dict.keys())
        if row >= len(keys):
            return

        self._current_key = keys[row]
        item_data = self.equipment_dict[self._current_key]

        if not isinstance(item_data, dict):
            return

        name = item_data.get("name", item_data.get("id", self._current_key))
        self.item_name_label.setText(f"📦 {name}  [{self._current_key}]")

        self._build_fields(item_data)
        self.raw_text.setText(json.dumps(item_data, ensure_ascii=False, indent=2))

    def _build_fields(self, item_data: dict):
        """Автоматически построить поля по ключам словаря."""
        self._clear_form(self.main_form)
        self._main_widgets.clear()

        for key, value in item_data.items():
            display_name = key  # Используем сам ключ как название

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
                w.setDecimals(2)
                w.setValue(value)
            elif isinstance(value, str):
                w = QLineEdit(value)
            elif value is None:
                w = QLineEdit("null")
            elif isinstance(value, (dict, list)):
                # Сложные типы показываем как текст
                w = QLineEdit(json.dumps(value, ensure_ascii=False))
            else:
                w = QLineEdit(str(value))

            self.main_form.addRow(f"{display_name}:", w)
            self._main_widgets[key] = w

    def _apply_current(self):
        """Применить изменения."""
        if not self._current_key or self._current_key not in self.equipment_dict:
            return

        item_data = self.equipment_dict[self._current_key]

        for key, widget in self._main_widgets.items():
            if isinstance(widget, QSpinBox):
                item_data[key] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                item_data[key] = widget.value()
            elif isinstance(widget, QComboBox):
                item_data[key] = widget.currentText() == "true"
            else:
                text = widget.text()
                # Пробуем восстановить dict/list из строки
                if text and text[0] in ('{', '['):
                    try:
                        item_data[key] = json.loads(text)
                    except json.JSONDecodeError:
                        item_data[key] = text
                else:
                    item_data[key] = text if text != "null" else None

        # Из сырых данных
        try:
            raw = self.raw_text.toPlainText().strip()
            if raw:
                parsed = json.loads(raw)
                self.equipment_dict[self._current_key] = parsed
        except json.JSONDecodeError:
            pass

        self._populate_list()
        QMessageBox.information(self, "Применено",
                                "Изменения предмета сохранены.\n"
                                "Не забудьте сохранить файл (Ctrl+S).")

    def _reset_current(self):
        if self._current_key:
            keys = list(self.equipment_dict.keys())
            if self._current_key in keys:
                self._on_item_selected(keys.index(self._current_key))

    def collect(self, data: dict):
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
