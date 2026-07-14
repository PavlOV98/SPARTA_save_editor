"""Вкладка глобальных параметров сохранения SPARTA 2035."""

from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QSpinBox, QPushButton,
    QScrollArea, QGridLayout, QMessageBox,
)
from PyQt6.QtCore import Qt


class GlobalTab(QWidget):
    """Вкладка для редактирования глобальных параметров сохранения."""

    def __init__(self):
        super().__init__()
        self.json_data: dict | None = None
        self._currency_widgets: dict[str, QSpinBox] = {}
        self._faction_widgets: dict[str, QSpinBox] = {}

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.main_layout = QVBoxLayout(scroll_widget)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

    def set_data(self, data: dict):
        """Заполнить поля из JSON-данных."""
        self.json_data = data
        self._build_fields(data)

    def _build_fields(self, data: dict):
        """Построить поля на основе данных."""
        self._clear_layout(self.main_layout)
        self._currency_widgets.clear()
        self._faction_widgets.clear()

        # === Валюта ===
        currency = data.get("currency")
        if isinstance(currency, dict):
            group = QGroupBox("💰 Валюта и ресурсы")
            form = QFormLayout(group)

            fields = [
                ("Деньги", "money"),
                ("Разведданные", "intel"),
                ("Размер команды", "crew"),
                ("Лимит персонажей", "characters"),
            ]

            for label, key in fields:
                value = currency.get(key, 0)
                if isinstance(value, (int, float)):
                    w = QSpinBox()
                    w.setRange(0, 999999999)
                    w.setValue(int(value))
                    form.addRow(f"{label}:", w)
                    self._currency_widgets[key] = w
                else:
                    w = QLineEdit(str(value))
                    form.addRow(f"{label}:", w)
                    self._currency_widgets[key] = w

            self.main_layout.addWidget(group)

        # === Фракции ===
        factions = data.get("Factions")
        if isinstance(factions, dict):
            group = QGroupBox("🤝 Отношения с фракциями")
            group_layout = QVBoxLayout(group)

            # Заголовок таблицы
            header = QHBoxLayout()
            header.addWidget(QLabel("<b>Фракция</b>"), 1)
            header.addWidget(QLabel("<b>Репутация</b>"), 0)
            group_layout.addLayout(header)

            for faction_id, faction_data in factions.items():
                if not isinstance(faction_data, dict):
                    continue

                row = QHBoxLayout()
                # Выводим factionId (читаем из поля, либо используем ключ)
                fid = faction_data.get("factionId", faction_id)
                name_label = QLabel(fid)
                name_label.setMinimumWidth(150)
                row.addWidget(name_label, 1)

                # Поле reputation
                rep = faction_data.get("reputation", 50)
                rep_spin = QSpinBox()
                rep_spin.setRange(0, 100)
                rep_spin.setValue(int(rep))
                rep_spin.setSuffix("")
                row.addWidget(rep_spin, 0)

                group_layout.addLayout(row)
                self._faction_widgets[faction_id] = rep_spin

            self.main_layout.addWidget(group)

        # Кнопка применения
        if self._currency_widgets or self._faction_widgets:
            btn = QPushButton("[SYNC]  Применить (сохранится при Ctrl+S)")
            btn.clicked.connect(self._show_info)
            self.main_layout.addWidget(btn)

        self.main_layout.addStretch()

    def _show_info(self):
        QMessageBox.information(
            self, "Готово",
            "Изменения будут сохранены при нажатии Ctrl+S (Файл -> Сохранить)."
        )

    def collect(self, data: dict):
        """Собрать данные из полей обратно в JSON."""
        if data is None:
            return

        # Валюта
        currency = data.get("currency")
        if isinstance(currency, dict):
            for key, widget in self._currency_widgets.items():
                if isinstance(widget, QSpinBox):
                    currency[key] = widget.value()
                else:
                    currency[key] = widget.text()

        # Фракции
        factions = data.get("Factions")
        if isinstance(factions, dict):
            for faction_id, widget in self._faction_widgets.items():
                if faction_id in factions and isinstance(factions[faction_id], dict):
                    factions[faction_id]["reputation"] = widget.value()

    @staticmethod
    def _clear_layout(layout):
        """Удалить все виджеты из layout."""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
