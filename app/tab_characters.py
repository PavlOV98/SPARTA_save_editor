"""Вкладка редактора персонажей SPARTA 2035."""

from __future__ import annotations
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QPushButton,
    QScrollArea, QGridLayout, QSplitter, QListWidget, QListWidgetItem,
    QMessageBox, QTabWidget, QTextEdit, QCheckBox, QComboBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class CharactersTab(QWidget):
    """Вкладка для редактирования персонажей."""

    def __init__(self):
        super().__init__()
        self.json_data: dict | None = None
        self.characters_dict: dict[str, dict] = {}  # key -> вся запись персонажа
        self._current_key: str | None = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        label = QLabel("Редактор персонажей")
        label.setStyleSheet("font-weight: bold; font-size: 13px; padding: 2px;")
        layout.addWidget(label)

        splitter = QSplitter()

        # Левая панель: список персонажей
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel("Персонажи:"))

        self.char_list = QListWidget()
        self.char_list.currentRowChanged.connect(self._on_char_selected)
        left_layout.addWidget(self.char_list)

        self.count_label = QLabel("Всего: 0")
        left_layout.addWidget(self.count_label)

        splitter.addWidget(left_widget)

        # Правая панель
        right_widget = QWidget()
        self.right_layout = QVBoxLayout(right_widget)
        self.right_layout.setContentsMargins(0, 0, 0, 0)

        self.name_label = QLabel("Персонаж не выбран")
        self.name_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 4px;")
        self.right_layout.addWidget(self.name_label)

        self.tabs = QTabWidget()

        # === Вкладка "Основное" (data) ===
        self.tab_main = QWidget()
        main_layout = QVBoxLayout(self.tab_main)
        scroll_main = QScrollArea()
        scroll_main.setWidgetResizable(True)
        scroll_main_widget = QWidget()
        self.main_form = QFormLayout(scroll_main_widget)
        self._main_widgets: dict[str, QWidget] = {}
        scroll_main.setWidget(scroll_main_widget)
        main_layout.addWidget(scroll_main)
        self.tabs.addTab(self.tab_main, "Основное")

        # === Вкладка "Характеристики" (property) ===
        self.tab_props = QWidget()
        props_layout = QVBoxLayout(self.tab_props)
        scroll_props = QScrollArea()
        scroll_props.setWidgetResizable(True)
        scroll_props_widget = QWidget()
        self.props_form = QFormLayout(scroll_props_widget)
        self._props_widgets: dict[str, QWidget] = {}
        scroll_props.setWidget(scroll_props_widget)
        props_layout.addWidget(scroll_props)
        self.tabs.addTab(self.tab_props, "Характеристики (property)")

        # === Вкладка "Слоты экипировки" (inventorySlots) ===
        self.tab_slots = QWidget()
        slots_layout = QVBoxLayout(self.tab_slots)
        scroll_slots = QScrollArea()
        scroll_slots.setWidgetResizable(True)
        scroll_slots_widget = QWidget()
        self.slots_form = QFormLayout(scroll_slots_widget)
        self._slots_widgets: dict[str, QWidget] = {}
        scroll_slots.setWidget(scroll_slots_widget)
        slots_layout.addWidget(scroll_slots)
        self.tabs.addTab(self.tab_slots, "Экипировка")

        # === Вкладка "Способности" (characterAbilities) ===
        self.tab_abilities = QWidget()
        abilities_layout = QVBoxLayout(self.tab_abilities)
        self.abilities_text = QTextEdit()
        self.abilities_text.setPlaceholderText("JSON способностей...")
        self.abilities_text.setFont(QFont("Consolas", 9))
        abilities_layout.addWidget(QLabel("Способности (JSON):"))
        abilities_layout.addWidget(self.abilities_text)
        self.tabs.addTab(self.tab_abilities, "Способности")

        # === Вкладка "Статистика" (statistics) ===
        self.tab_stats = QWidget()
        stats_layout = QVBoxLayout(self.tab_stats)
        scroll_stats = QScrollArea()
        scroll_stats.setWidgetResizable(True)
        scroll_stats_widget = QWidget()
        self.stats_form = QFormLayout(scroll_stats_widget)
        self._stats_widgets: dict[str, QWidget] = {}
        scroll_stats.setWidget(scroll_stats_widget)
        stats_layout.addWidget(scroll_stats)
        self.tabs.addTab(self.tab_stats, "Статистика")

        # === Вкладка "Сырые данные" ===
        self.tab_raw = QWidget()
        raw_layout = QVBoxLayout(self.tab_raw)
        self.raw_text = QTextEdit()
        self.raw_text.setFont(QFont("Consolas", 9))
        raw_layout.addWidget(QLabel("Все данные персонажа (JSON):"))
        raw_layout.addWidget(self.raw_text)
        self.tabs.addTab(self.tab_raw, "Сырые данные")

        self.right_layout.addWidget(self.tabs)

        # Кнопки
        btn_layout = QHBoxLayout()
        btn_apply = QPushButton("✅ Применить")
        btn_apply.clicked.connect(self._apply_current)
        btn_layout.addWidget(btn_apply)

        btn_reset = QPushButton("↩ Сбросить")
        btn_reset.clicked.connect(self._reset_current)
        btn_layout.addWidget(btn_reset)

        self.right_layout.addLayout(btn_layout)

        splitter.addWidget(right_widget)
        splitter.setSizes([250, 700])

        layout.addWidget(splitter)

    # ---- Поля для вкладок ----

    MAIN_FIELDS = [
        ("Уровень", "level", "int"),
        ("Опыт", "exp", "int"),
        ("Макс. опыт", "maxExp", "int"),
        ("Класс", "characterClass", "str"),
        ("Пол", "genderType", "str"),
        ("Дней до прибытия", "arriveTimeDays", "int"),
        ("Цена за месяц", "pricePerMonth", "int"),
        ("Цена найма", "price", "int"),
        ("Цена продажи", "sellPrice", "int"),
        ("Травма", "injury", "int"),
        ("Бесплатный боец", "uniqueCharacter", "bool"),
        ("Дрон", "isDrone", "bool"),
        ("Укрытие", "canTakeCover", "bool"),
    ]

    PROPERTY_FIELDS = [
        ("Здоровье (HP)", "DefaultHitPoints", "int"),
        ("Защита (Protection)", "BaseProtectionValue", "int"),
        ("Мобильность", "Mobility", "int"),
        ("Меткость", "Accuracy", "int"),
        ("Крит. шанс", "CriticalDamageChance", "int"),
        ("Обзор", "FieldOfView", "int"),
        ("Обнаружение", "FieldOfDetection", "int"),
        ("Ходов до смерти", "IncapacitationTurnBeforeDie", "int"),
        ("Рукопашный бой", "MeleeFactor", "int"),
        ("Тип движения", "MovementType", "int"),
    ]

    SLOTS_FIELDS = [
        ("Основное оружие", "MainWeapon"),
        ("Спец. слот", "SpecialSlot"),
        ("Броня", "Armor"),
        ("Снаряжение 1", "EquipmentSlot1"),
        ("Снаряжение 2", "EquipmentSlot2"),
    ]

    STATS_FIELDS = [
        ("Дата найма", "hired", "str"),
        ("Убито врагов", "killed", "int"),
        ("Завершено миссий", "finishedMissions", "int"),
    ]

    def set_data(self, data: dict):
        """Загрузить данные персонажей."""
        self.json_data = data

        chars = data.get("characters")
        if isinstance(chars, dict):
            self.characters_dict = chars
        else:
            self.characters_dict = {}

        self._populate_list()

    def _populate_list(self):
        """Заполнить список персонажей."""
        self.char_list.blockSignals(True)
        self.char_list.clear()

        if not self.characters_dict:
            self.char_list.addItem("⚠ Персонажи не найдены")
            self.count_label.setText("Всего: 0")
            self.char_list.blockSignals(False)
            return

        for key, char_data in self.characters_dict.items():
            if not isinstance(char_data, dict):
                continue
            d = char_data.get("data", char_data)
            name = d.get("metaInfoIdent", key)
            level = d.get("level", "")
            if level:
                display = f"{name} (Lvl {level})"
            else:
                display = str(name)
            self.char_list.addItem(f"👤 {display}")

        self.count_label.setText(f"Всего: {len(self.characters_dict)}")
        self.char_list.blockSignals(False)

        if self.char_list.count() > 0:
            self.char_list.setCurrentRow(0)

    def _on_char_selected(self, row: int):
        """Выбор персонажа."""
        if row < 0:
            return
        keys = list(self.characters_dict.keys())
        if row >= len(keys):
            return

        self._current_key = keys[row]
        full_entry = self.characters_dict[self._current_key]
        data = full_entry.get("data", full_entry)

        ident = full_entry.get("ident", self._current_key)
        self.name_label.setText(f"👤 {ident}")

        # Заполняем вкладки
        self._fill_main(data)
        self._fill_property(data)
        self._fill_slots(data)
        self._fill_stats(data)

        # Способности
        abilities = data.get("characterAbilities", {})
        self.abilities_text.setText(
            json.dumps(abilities, ensure_ascii=False, indent=2)
        )

        # Сырые данные
        self.raw_text.setText(
            json.dumps(full_entry, ensure_ascii=False, indent=2)
        )

    def _fill_main(self, data: dict):
        """Заполнить поля основной информации."""
        self._clear_form(self.main_form)
        self._main_widgets.clear()

        for display_name, key, ptype in self.MAIN_FIELDS:
            if key not in data:
                continue
            value = data[key]
            w = self._make_field(ptype, value)
            self.main_form.addRow(f"{display_name}:", w)
            self._main_widgets[key] = w

    def _fill_property(self, data: dict):
        """Заполнить характеристики (property)."""
        self._clear_form(self.props_form)
        self._props_widgets.clear()

        prop = data.get("property")
        if not isinstance(prop, dict):
            self.props_form.addRow(QLabel("⚠ property не найдено"))
            return

        for display_name, key, ptype in self.PROPERTY_FIELDS:
            if key not in prop:
                continue
            value = prop[key]
            w = self._make_field(ptype, value)
            self.props_form.addRow(f"{display_name}:", w)
            self._props_widgets[key] = w

    def _fill_slots(self, data: dict):
        """Заполнить слоты экипировки."""
        self._clear_form(self.slots_form)
        self._slots_widgets.clear()

        slots = data.get("inventorySlots")
        if not isinstance(slots, dict):
            self.slots_form.addRow(QLabel("⚠ inventorySlots не найдено"))
            return

        for display_name, key in self.SLOTS_FIELDS:
            if key not in slots:
                continue
            value = slots.get(key, "")
            w = QLineEdit(str(value))
            self.slots_form.addRow(f"{display_name}:", w)
            self._slots_widgets[key] = w

    def _fill_stats(self, data: dict):
        """Заполнить статистику."""
        self._clear_form(self.stats_form)
        self._stats_widgets.clear()

        stats = data.get("statistics")
        if not isinstance(stats, dict):
            self.stats_form.addRow(QLabel("⚠ statistics не найдено"))
            return

        for display_name, key, ptype in self.STATS_FIELDS:
            if key not in stats:
                continue
            value = stats[key]
            w = self._make_field(ptype, value)
            self.stats_form.addRow(f"{display_name}:", w)
            self._stats_widgets[key] = w

    def _make_field(self, ptype: str, value):
        """Создать поле по типу."""
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
        elif ptype == "bool":
            w = QComboBox()
            w.addItems(["false", "true"])
            w.setCurrentText(str(value).lower())
            return w
        else:
            w = QLineEdit(str(value) if value is not None else "")
            return w

    def _apply_current(self):
        """Применить изменения текущего персонажа."""
        if not self._current_key or self._current_key not in self.characters_dict:
            return

        full_entry = self.characters_dict[self._current_key]
        data = full_entry.get("data", full_entry)

        # Основные поля
        for key, w in self._main_widgets.items():
            if isinstance(w, QSpinBox):
                data[key] = w.value()
            elif isinstance(w, QDoubleSpinBox):
                data[key] = w.value()
            elif isinstance(w, QComboBox):
                data[key] = w.currentText() == "true"
            else:
                data[key] = w.text()

        # Характеристики (property)
        prop = data.get("property")
        if isinstance(prop, dict):
            for key, w in self._props_widgets.items():
                if isinstance(w, QSpinBox):
                    prop[key] = w.value()
                elif isinstance(w, QDoubleSpinBox):
                    prop[key] = w.value()
                elif isinstance(w, QComboBox):
                    prop[key] = w.currentText() == "true"
                else:
                    prop[key] = w.text()

        # Слоты экипировки
        slots = data.get("inventorySlots")
        if isinstance(slots, dict):
            for key, w in self._slots_widgets.items():
                slots[key] = w.text()

        # Статистика
        stats = data.get("statistics")
        if isinstance(stats, dict):
            for key, w in self._stats_widgets.items():
                if isinstance(w, QSpinBox):
                    stats[key] = w.value()
                elif isinstance(w, QDoubleSpinBox):
                    stats[key] = w.value()
                else:
                    stats[key] = w.text()

        # Способности (из текстового поля)
        try:
            abil_text = self.abilities_text.toPlainText().strip()
            if abil_text:
                data["characterAbilities"] = json.loads(abil_text)
        except json.JSONDecodeError:
            pass

        # Сырые данные
        try:
            raw = self.raw_text.toPlainText().strip()
            if raw:
                parsed = json.loads(raw)
                self.characters_dict[self._current_key] = parsed
        except json.JSONDecodeError:
            pass

        self._populate_list()
        QMessageBox.information(
            self, "Применено",
            "Изменения персонажа сохранены.\nНе забудьте сохранить файл (Ctrl+S)."
        )

    def _reset_current(self):
        """Сбросить."""
        if self._current_key:
            keys = list(self.characters_dict.keys())
            if self._current_key in keys:
                self._on_char_selected(keys.index(self._current_key))

    def collect(self, data: dict):
        """Ничего не делаем — работаем по references."""
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
