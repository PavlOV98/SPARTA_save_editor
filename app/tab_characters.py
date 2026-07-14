"""Вкладка редактора персонажей SPARTA 2035."""

import json
from typing import Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QPushButton,
    QScrollArea, QGridLayout, QSplitter, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QTabWidget, QTextEdit, QCheckBox, QComboBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class CharactersTab(QWidget):
    """Вкладка для редактирования персонажей (бойцов) отряда."""

    def __init__(self):
        super().__init__()
        self.json_data: dict | None = None
        self.characters_data: list[dict] = []
        self._current_char_index: int = -1

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Пояснение
        label = QLabel(
            "Редактирование персонажей отряда. "
            "Выберите персонажа слева и редактируйте его параметры справа."
        )
        label.setWordWrap(True)
        label.setStyleSheet("color: #666; padding: 4px;")
        layout.addWidget(label)

        # Основной сплиттер
        splitter = QSplitter()

        # Левая панель: список персонажей
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_layout.addWidget(QLabel("Персонажи отряда:"))

        self.char_list = QListWidget()
        self.char_list.currentRowChanged.connect(self._on_char_selected)
        left_layout.addWidget(self.char_list)

        splitter.addWidget(left_widget)

        # Правая панель: редактор персонажа
        right_widget = QWidget()
        self.right_layout = QVBoxLayout(right_widget)
        self.right_layout.setContentsMargins(0, 0, 0, 0)

        self.right_layout.addWidget(QLabel("Параметры персонажа:"))

        # Под-табы для разных категорий параметров
        self.char_tabs = QTabWidget()

        # --- Вкладка "Основное" ---
        self.tab_main = QWidget()
        main_layout = QVBoxLayout(self.tab_main)
        self.main_form = QFormLayout()
        self._main_widgets: dict[str, QWidget] = {}
        main_layout.addLayout(self.main_form)
        main_layout.addStretch()
        self.char_tabs.addTab(self.tab_main, "Основное")

        # --- Вкладка "Характеристики" ---
        self.tab_stats = QWidget()
        stats_layout = QVBoxLayout(self.tab_stats)
        self.stats_form = QFormLayout()
        self._stats_widgets: dict[str, QWidget] = {}
        stats_layout.addLayout(self.stats_form)
        stats_layout.addStretch()
        self.char_tabs.addTab(self.tab_stats, "Характеристики")

        # --- Вкладка "Способности" ---
        self.tab_abilities = QWidget()
        abilities_layout = QVBoxLayout(self.tab_abilities)
        self.abilities_text = QTextEdit()
        self.abilities_text.setPlaceholderText("JSON списка способностей...")
        self.abilities_text.setFont(QFont("Consolas", 9))
        abilities_layout.addWidget(QLabel("Способности (редактируйте JSON):"))
        abilities_layout.addWidget(self.abilities_text)
        self.char_tabs.addTab(self.tab_abilities, "Способности")

        # --- Вкладка "Инвентарь" ---
        self.tab_inventory = QWidget()
        inventory_layout = QVBoxLayout(self.tab_inventory)
        self.inventory_text = QTextEdit()
        self.inventory_text.setPlaceholderText("JSON инвентаря...")
        self.inventory_text.setFont(QFont("Consolas", 9))
        inventory_layout.addWidget(QLabel("Инвентарь (редактируйте JSON):"))
        inventory_layout.addWidget(self.inventory_text)
        self.char_tabs.addTab(self.tab_inventory, "Инвентарь")

        # --- Вкладка "Сырые данные" ---
        self.tab_raw = QWidget()
        raw_layout = QVBoxLayout(self.tab_raw)
        self.raw_text = QTextEdit()
        self.raw_text.setPlaceholderText("Полные сырые JSON-данные персонажа...")
        self.raw_text.setFont(QFont("Consolas", 9))
        raw_layout.addWidget(QLabel("Все данные персонажа (сырой JSON):"))
        raw_layout.addWidget(self.raw_text)
        self.char_tabs.addTab(self.tab_raw, "Сырые данные")

        self.right_layout.addWidget(self.char_tabs)

        # Кнопка "Применить изменения"
        btn_layout = QHBoxLayout()
        btn_apply = QPushButton("✅ Применить изменения к персонажу")
        btn_apply.clicked.connect(self._apply_current)
        btn_layout.addWidget(btn_apply)

        btn_reset = QPushButton("↩ Сбросить")
        btn_reset.clicked.connect(self._reset_current)
        btn_layout.addWidget(btn_reset)

        self.right_layout.addLayout(btn_layout)

        splitter.addWidget(right_widget)
        splitter.setSizes([250, 700])

        layout.addWidget(splitter)

    # ---- Инициализация полей ----

    MAIN_FIELDS = [
        ("Имя", "name", "str"),
        ("ID", "id", "str"),
        ("Уровень", "level", "int"),
        ("Опыт", "exp", "int"),
        ("Здоровье (HP)", "hp", "int"),
        ("Макс. здоровье (MaxHP)", "max_hp", "int"),
        ("ОД (Action Points)", "ap", "int"),
        ("Макс. ОД", "max_ap", "int"),
        ("Броня", "armor", "int"),
        ("Инициатива", "initiative", "int"),
        ("Класс", "class_name", "str"),
        ("Роль", "role", "str"),
        ("Портрет", "portrait", "str"),
    ]

    STATS_FIELDS = [
        ("Сила", "strength", "int"),
        ("Ловкость", "dexterity", "int"),
        ("Выносливость", "endurance", "int"),
        ("Интеллект", "intelligence", "int"),
        ("Восприятие", "perception", "int"),
        ("Удача", "luck", "int"),
        ("Меткость", "accuracy", "int"),
        ("Уклонение", "dodge", "int"),
    ]

    def _build_main_fields(self, char_data: dict):
        """Построить поля основной информации."""
        self._clear_form(self.main_form)
        self._main_widgets.clear()

        for display_name, key, ptype in self.MAIN_FIELDS:
            value = self._find_value(char_data, key)
            widget = self._create_field(ptype, value)
            self.main_form.addRow(f"{display_name}:", widget)
            self._main_widgets[key] = widget

    def _build_stats_fields(self, char_data: dict):
        """Построить поля характеристик."""
        self._clear_form(self.stats_form)
        self._stats_widgets.clear()

        for display_name, key, ptype in self.STATS_FIELDS:
            value = self._find_value(char_data, key)
            widget = self._create_field(ptype, value)
            self.stats_form.addRow(f"{display_name}:", widget)
            self._stats_widgets[key] = widget

    def _create_field(self, ptype: str, value):
        """Создать виджет поля."""
        if ptype == "int":
            w = QSpinBox()
            w.setRange(-999999999, 999999999)
            try:
                w.setValue(int(value) if value is not None else 0)
            except (ValueError, TypeError):
                w.setValue(0)
            return w
        elif ptype == "float":
            w = QDoubleSpinBox()
            w.setRange(-999999999, 999999999)
            w.setDecimals(2)
            try:
                w.setValue(float(value) if value is not None else 0.0)
            except (ValueError, TypeError):
                w.setValue(0.0)
            return w
        else:
            w = QLineEdit(str(value) if value is not None else "")
            return w

    @staticmethod
    def _find_value(data: dict, key: str, depth: int = 0, max_depth: int = 3):
        """Ищет ключ в словаре на небольшой глубине."""
        if depth > max_depth:
            return None
        if isinstance(data, dict):
            if key in data:
                return data[key]
            for v in data.values():
                result = CharactersTab._find_value(v, key, depth + 1, max_depth)
                if result is not None:
                    return result
        elif isinstance(data, list):
            for item in data:
                result = CharactersTab._find_value(item, key, depth + 1, max_depth)
                if result is not None:
                    return result
        return None

    # ---- Основные методы ----

    def set_data(self, data: dict):
        """Загрузить данные персонажей из JSON."""
        self.json_data = data
        self._find_characters(data)
        self._populate_list()

    def _find_characters(self, data: dict):
        """Найти список персонажей в JSON."""
        self.characters_data = []

        # Ищем массив персонажей по типичным ключам
        possible_keys = [
            "characters", "squad", "team", "units", "heroes",
            "fighters", "soldiers", "members", "party",
        ]

        for key in possible_keys:
            if key in data and isinstance(data[key], list):
                items = data[key]
                # Проверяем, что элементы похожи на персонажей (содержат имя/здоровье и т.п.)
                if items and isinstance(items[0], dict):
                    self.characters_data = items
                    return

        # Рекурсивный поиск
        self._find_list_recursive(data)

    def _find_list_recursive(self, data):
        """Рекурсивно ищет списки словарей, похожие на персонажей."""
        if self.characters_data:
            return

        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, list) and len(value) > 0:
                    # Проверяем первый элемент
                    if isinstance(value[0], dict):
                        # Проверяем, похож ли на персонажа (есть name или hp)
                        sample = value[0]
                        if any(k in sample for k in ["name", "hp", "level", "class"]):
                            self.characters_data = value
                            return
                if isinstance(value, (dict, list)):
                    self._find_list_recursive(value)
        elif isinstance(data, list):
            for item in data:
                self._find_list_recursive(item)

    def _populate_list(self):
        """Заполнить список персонажей."""
        self.char_list.blockSignals(True)
        self.char_list.clear()

        if not self.characters_data:
            self.char_list.addItem("⚠ Персонажи не найдены")
            self.char_list.blockSignals(False)
            return

        for i, char in enumerate(self.characters_data):
            name = char.get("name", char.get("Name", char.get("id", f"Персонаж {i+1}")))
            level = char.get("level", char.get("Level", ""))
            if level:
                display = f"{name} (Lvl {level})"
            else:
                display = str(name)
            item = QListWidgetItem(f"👤 {display}")
            item.setData(Qt.ItemDataRole.UserRole, i)
            self.char_list.addItem(item)

        self.char_list.blockSignals(False)

        if self.char_list.count() > 0:
            self.char_list.setCurrentRow(0)

    def _on_char_selected(self, row: int):
        """Обработчик выбора персонажа."""
        if row < 0 or row >= len(self.characters_data):
            return

        self._current_char_index = row
        char_data = self.characters_data[row]

        # Строим поля
        self._build_main_fields(char_data)
        self._build_stats_fields(char_data)

        # Способности
        abilities = self._find_value(char_data, "abilities") or \
                     self._find_value(char_data, "skills") or \
                     self._find_value(char_data, "perks") or []
        self.abilities_text.setText(
            json.dumps(abilities, ensure_ascii=False, indent=2)
            if abilities else "[]"
        )

        # Инвентарь
        inventory = self._find_value(char_data, "inventory") or \
                     self._find_value(char_data, "items") or \
                     self._find_value(char_data, "equipment") or []
        self.inventory_text.setText(
            json.dumps(inventory, ensure_ascii=False, indent=2)
            if inventory else "[]"
        )

        # Сырые данные
        self.raw_text.setText(
            json.dumps(char_data, ensure_ascii=False, indent=2)
        )

    def _apply_current(self):
        """Применить изменения текущего персонажа."""
        if self._current_char_index < 0 or not self.characters_data:
            return

        char_data = self.characters_data[self._current_char_index]

        # Применяем основные поля
        for key, widget in self._main_widgets.items():
            if isinstance(widget, QSpinBox):
                value = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                value = widget.value()
            else:
                value = widget.text()
            # Устанавливаем на верхнем уровне или ищем
            if key in char_data:
                char_data[key] = value
            else:
                # Пробуем найти и установить
                self._set_nested_value(char_data, key, value)

        # Применяем характеристики
        for key, widget in self._stats_widgets.items():
            value = widget.value() if isinstance(widget, (QSpinBox, QDoubleSpinBox)) else widget.text()
            if key in char_data:
                char_data[key] = value
            else:
                self._set_nested_value(char_data, key, value)

        # Применяем способности
        try:
            abilities_text = self.abilities_text.toPlainText().strip()
            if abilities_text:
                abilities = json.loads(abilities_text)
                # Ищем куда сохранить
                for k in ["abilities", "skills", "perks"]:
                    if k in char_data:
                        char_data[k] = abilities
                        break
        except json.JSONDecodeError:
            pass

        # Применяем инвентарь
        try:
            inv_text = self.inventory_text.toPlainText().strip()
            if inv_text:
                inventory = json.loads(inv_text)
                for k in ["inventory", "items", "equipment"]:
                    if k in char_data:
                        char_data[k] = inventory
                        break
        except json.JSONDecodeError:
            pass

        # Обновляем список
        self._populate_list()
        QMessageBox.information(self, "Применено",
                                f"Изменения персонажа применены.\n"
                                f"Не забудьте сохранить файл (Ctrl+S).")

    def _reset_current(self):
        """Сбросить изменения текущего персонажа."""
        if self._current_char_index >= 0 and self.characters_data:
            self._on_char_selected(self._current_char_index)

    @staticmethod
    def _set_nested_value(data: dict, key: str, value, depth=0, max_depth=3):
        """Установить значение в словаре по ключу (рекурсивно)."""
        if depth > max_depth:
            return False
        if isinstance(data, dict):
            if key in data:
                data[key] = value
                return True
            for k, v in data.items():
                if CharactersTab._set_nested_value(v, key, value, depth + 1, max_depth):
                    return True
        elif isinstance(data, list):
            for item in data:
                if CharactersTab._set_nested_value(item, key, value, depth + 1, max_depth):
                    return True
        return False

    def collect(self, data: dict):
        """Собрать данные обратно — ничего не делаем, т.к. работаем напрямую с references."""
        pass

    @staticmethod
    def _clear_form(form_layout):
        """Очистить form layout."""
        while form_layout.count():
            item = form_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
