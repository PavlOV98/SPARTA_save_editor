"""Вкладка склада (storedEquipment как словарь ключ->количество)."""

from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QSpinBox, QPushButton,
    QScrollArea, QSplitter, QListWidget, QListWidgetItem,
    QMessageBox, QTabWidget, QTextEdit,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class WarehouseTab(QWidget):
    """Вкладка склада — storedEquipment: {ключ: количество}."""

    def __init__(self):
        super().__init__()
        self.json_data: dict | None = None
        self.equipment_dict: dict[str, int] = {}
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

        self.count_label = QLabel("Всего: 0 | Уникальных: 0")
        left_layout.addWidget(self.count_label)

        splitter.addWidget(left_widget)

        # Правая панель: редактор
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.item_name_label = QLabel("Предмет не выбран")
        self.item_name_label.setStyleSheet("font-size: 13px; font-weight: bold; padding: 4px;")
        right_layout.addWidget(self.item_name_label)

        # Форма редактирования
        form_widget = QWidget()
        form = QFormLayout(form_widget)

        self.key_edit = QLineEdit()
        self.key_edit.setReadOnly(True)
        form.addRow("ID предмета:", self.key_edit)

        self.count_spin = QSpinBox()
        self.count_spin.setRange(0, 999999999)
        form.addRow("Количество:", self.count_spin)

        right_layout.addWidget(form_widget)
        right_layout.addStretch()

        # Кнопки
        btn_layout = QHBoxLayout()
        btn_apply = QPushButton("✅ Применить")
        btn_apply.clicked.connect(self._apply_current)
        btn_layout.addWidget(btn_apply)

        btn_reset = QPushButton("↩ Сбросить")
        btn_reset.clicked.connect(self._reset_current)
        btn_layout.addWidget(btn_reset)

        btn_delete = QPushButton("🗑 Удалить")
        btn_delete.clicked.connect(self._delete_item)
        btn_layout.addWidget(btn_delete)

        right_layout.addLayout(btn_layout)

        splitter.addWidget(right_widget)
        splitter.setSizes([300, 400])

        layout.addWidget(splitter)

        # Нижняя панель: информация
        info_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Поиск предмета...")
        self.search_edit.textChanged.connect(self._filter_list)
        info_layout.addWidget(self.search_edit)

        self.total_items_label = QLabel("")
        self.total_items_label.setStyleSheet("color: #555;")
        info_layout.addWidget(self.total_items_label)

        layout.addLayout(info_layout)

    def set_data(self, data: dict):
        """Загрузить данные склада."""
        self.json_data = data

        eq = data.get("storedEquipment")
        if isinstance(eq, dict):
            self.equipment_dict = eq
        else:
            self.equipment_dict = {}

        self._populate_list()
        self._update_total()

    def _populate_list(self, filter_text: str = ""):
        """Заполнить список предметов с фильтром."""
        self.item_list.blockSignals(True)
        self.item_list.clear()

        if not self.equipment_dict:
            self.item_list.addItem("⚠ storedEquipment не найден или пуст")
            self.item_list.blockSignals(False)
            return

        total_count = 0
        shown = 0

        for key in sorted(self.equipment_dict.keys()):
            count = self.equipment_dict[key]
            total_count += count

            if filter_text and filter_text.lower() not in key.lower():
                continue

            display = f"{key}  ×{count}"
            self.item_list.addItem(f"📦 {display}")
            shown += 1

        if filter_text and shown == 0:
            self.item_list.addItem(f"⚠ Ничего не найдено по запросу '{filter_text}'")

        self.count_label.setText(
            f"Показано: {shown} | Всего: {len(self.equipment_dict)} предметов"
        )
        self._cached_total = total_count

        self.item_list.blockSignals(False)

        if self.item_list.count() > 0 and self._current_key is None:
            self.item_list.setCurrentRow(0)

    def _filter_list(self, text: str):
        """Фильтровать список."""
        self._populate_list(text)

    def _update_total(self):
        """Обновить общую информацию."""
        if not self.equipment_dict:
            self.total_items_label.setText("")
            return

        total_count = sum(self.equipment_dict.values())
        total_items = len(self.equipment_dict)
        self.total_items_label.setText(
            f"Всего единиц: {total_count} | Уникальных предметов: {total_items}"
        )

    def _on_item_selected(self, row: int):
        """Выбор предмета."""
        if row < 0:
            return

        # Определяем ключ по тексту элемента
        item = self.item_list.item(row)
        if not item:
            return
        text = item.text()

        # Извлекаем ключ (формат: "📦 ключ  ×N")
        if "📦 " not in text:
            return
        after_icon = text[2:]  # убираем "📦 "
        # ключ до "  ×"
        if "  ×" in after_icon:
            key = after_icon.split("  ×")[0]
        else:
            key = after_icon

        if key not in self.equipment_dict:
            return

        self._current_key = key
        self.key_edit.setText(key)
        self.count_spin.setValue(self.equipment_dict[key])
        self.item_name_label.setText(f"📦 {key}")

    def _apply_current(self):
        """Применить изменения."""
        if not self._current_key or self._current_key not in self.equipment_dict:
            return

        self.equipment_dict[self._current_key] = self.count_spin.value()
        self._populate_list(self.search_edit.text())
        self._update_total()
        self.status_message(f"✅ {self._current_key} = {self.count_spin.value()}")

    def _reset_current(self):
        """Сбросить."""
        if self._current_key and self._current_key in self.equipment_dict:
            self.count_spin.setValue(self.equipment_dict[self._current_key])

    def _delete_item(self):
        """Удалить предмет из склада."""
        if not self._current_key or self._current_key not in self.equipment_dict:
            return

        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить предмет '{self._current_key}' из склада?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            del self.equipment_dict[self._current_key]
            self._current_key = None
            self.key_edit.clear()
            self.count_spin.setValue(0)
            self.item_name_label.setText("Предмет не выбран")
            self._populate_list(self.search_edit.text())
            self._update_total()
            self.status_message(f"🗑 Предмет удалён")

    def status_message(self, msg: str):
        """Показать сообщение в статусе (через родительское окно)."""
        # Ищем родительское окно со статус-баром
        parent = self.window()
        if hasattr(parent, 'statusBar'):
            parent.statusBar().showMessage(msg, 3000)

    def collect(self, data: dict):
        """Сохраняем данные — None, т.к. работаем по references."""
        pass
