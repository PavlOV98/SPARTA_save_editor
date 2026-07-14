"""Вкладка файла с деревом JSON (сворачиваемое) и редактированием."""

from __future__ import annotations
import json

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QTextEdit, QTreeWidget, QTreeWidgetItem,
    QTabWidget, QLineEdit, QSpinBox, QComboBox, QFormLayout,
    QSplitter, QScrollArea,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


# Роли для хранения данных в QTreeWidgetItem
ROLE_KEY = Qt.ItemDataRole.UserRole + 1
ROLE_VALUE = Qt.ItemDataRole.UserRole + 2
ROLE_IS_CONTAINER = Qt.ItemDataRole.UserRole + 3
ROLE_CONTAINER_TYPE = Qt.ItemDataRole.UserRole + 4  # 'dict' или 'list'
ROLE_PARENT_PATH = Qt.ItemDataRole.UserRole + 5


class JsonTree(QTreeWidget):
    """Дерево для отображения JSON с возможностью сворачивания."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabels(["Ключ", "Значение"])
        self.setColumnCount(2)
        self.setAlternatingRowColors(True)
        self.setAnimated(True)
        self.setColumnWidth(0, 350)
        self.setExpandsOnDoubleClick(True)

    def load_json(self, data: dict):
        self.clear()
        root = self.invisibleRootItem()

        for key, value in data.items():
            item = self._build_item(key, value)
            root.addChild(item)

        self.expandAll()

    def _build_item(self, key: str, value) -> QTreeWidgetItem:
        if isinstance(value, dict):
            item = QTreeWidgetItem([str(key), f"{{{len(value)} полей}}"])
            item.setData(0, ROLE_KEY, key)
            item.setData(0, ROLE_VALUE, value)
            item.setData(0, ROLE_IS_CONTAINER, True)
            item.setData(0, ROLE_CONTAINER_TYPE, "dict")
            item.setChildIndicatorPolicy(
                QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator
            )
            for k, v in value.items():
                child = self._build_item(k, v)
                item.addChild(child)

        elif isinstance(value, list):
            item = QTreeWidgetItem([str(key), f"[{len(value)} элементов]"])
            item.setData(0, ROLE_KEY, key)
            item.setData(0, ROLE_VALUE, value)
            item.setData(0, ROLE_IS_CONTAINER, True)
            item.setData(0, ROLE_CONTAINER_TYPE, "list")
            item.setChildIndicatorPolicy(
                QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator
            )
            for i, v in enumerate(value):
                child = self._build_item(f"[{i}]", v)
                item.addChild(child)

        else:
            display = self._format_value(value)
            item = QTreeWidgetItem([str(key), display])
            item.setData(0, ROLE_KEY, key)
            item.setData(0, ROLE_VALUE, value)
            item.setData(0, ROLE_IS_CONTAINER, False)

        return item

    def to_dict(self) -> dict:
        """Собрать JSON обратно из дерева."""
        root = self.invisibleRootItem()
        result = {}
        for i in range(root.childCount()):
            child = root.child(i)
            key = child.data(0, ROLE_KEY)
            result[key] = self._item_to_value(child)
        return result

    def _item_to_value(self, item: QTreeWidgetItem):
        is_container = item.data(0, ROLE_IS_CONTAINER)
        if not is_container:
            return item.data(0, ROLE_VALUE)

        container_type = item.data(0, ROLE_CONTAINER_TYPE)
        if container_type == "dict":
            result = {}
            for i in range(item.childCount()):
                child = item.child(i)
                key = child.data(0, ROLE_KEY) or str(i)
                result[key] = self._item_to_value(child)
            return result
        elif container_type == "list":
            result = []
            for i in range(item.childCount()):
                child = item.child(i)
                result.append(self._item_to_value(child))
            return result
        return item.data(0, ROLE_VALUE)

    @staticmethod
    def _format_value(value) -> str:
        if value is None:
            return "null"
        if isinstance(value, bool):
            return str(value).lower()
        if isinstance(value, str):
            if len(value) > 120:
                return value[:120] + "..."
            return value
        return str(value)


class RawFileTab(QWidget):
    """Вкладка для просмотра и редактирования всего файла сохранения целиком."""

    def __init__(self):
        super().__init__()
        self.json_data: dict | None = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Верхняя панель
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Файл сохранения — сворачиваемое дерево JSON"))
        top_layout.addStretch()

        # Кнопки развернуть/свернуть всё
        btn_expand = QPushButton("▶ Развернуть всё")
        btn_expand.clicked.connect(lambda: self.tree.expandAll())
        top_layout.addWidget(btn_expand)

        btn_collapse = QPushButton("◀ Свернуть всё")
        btn_collapse.clicked.connect(lambda: self.tree.collapseAll())
        top_layout.addWidget(btn_collapse)

        layout.addLayout(top_layout)

        # Основной сплиттер: дерево + панель редактирования
        splitter = QSplitter()

        # Дерево JSON
        self.tree = JsonTree()
        self.tree.itemClicked.connect(self._on_item_clicked)
        splitter.addWidget(self.tree)

        # Правая панель: редактирование
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        right_layout.addWidget(QLabel("Редактирование:"))

        self.edit_key_label = QLabel("Ключ: —")
        right_layout.addWidget(self.edit_key_label)

        self.edit_value = QLineEdit()
        self.edit_value.setPlaceholderText("Значение...")
        self.edit_value.returnPressed.connect(self._apply_edit)
        right_layout.addWidget(self.edit_value)

        btn_apply_edit = QPushButton("✅ Применить значение")
        btn_apply_edit.clicked.connect(self._apply_edit)
        right_layout.addWidget(btn_apply_edit)

        btn_remove = QPushButton("🗑 Удалить поле")
        btn_remove.clicked.connect(self._remove_field)
        right_layout.addWidget(btn_remove)

        right_layout.addStretch()

        splitter.addWidget(right_widget)
        splitter.setSizes([700, 400])

        layout.addWidget(splitter)

        # Нижняя панель: кнопки и статус
        btn_layout = QHBoxLayout()

        btn_save_memory = QPushButton("💾 Сохранить в память (из дерева)")
        btn_save_memory.clicked.connect(self._save_tree_to_memory)
        btn_layout.addWidget(btn_save_memory)

        btn_refresh = QPushButton("🔄 Обновить дерево из памяти")
        btn_refresh.clicked.connect(self._refresh)
        btn_layout.addWidget(btn_refresh)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888;")
        btn_layout.addWidget(self.status_label, 1)

        layout.addLayout(btn_layout)

    # ---- Загрузка данных ----

    def set_data(self, data: dict):
        self.json_data = data
        self._refresh()

    def _refresh(self):
        """Обновить дерево из json_data."""
        if self.json_data is None:
            self.tree.clear()
            self.status_label.setText("Нет данных")
            return

        self.tree.load_json(self.json_data)
        size_str = self._format_size(len(json.dumps(self.json_data, ensure_ascii=False)))
        self.status_label.setText(
            f"Размер: {size_str} | Разделов: {len(self.json_data)}"
        )

    # ---- Редактирование ----

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Клик по элементу дерева."""
        is_container = item.data(0, ROLE_IS_CONTAINER)
        key = item.data(0, ROLE_KEY)
        value = item.data(0, ROLE_VALUE)

        self.edit_key_label.setText(f"Ключ: {key}")

        if is_container:
            self.edit_value.setEnabled(False)
            self.edit_value.setText(f"(контейнер — {len(item.childCount())} элементов)")
        else:
            self.edit_value.setEnabled(True)
            if value is None:
                self.edit_value.setText("null")
            elif isinstance(value, bool):
                self.edit_value.setText("true" if value else "false")
            else:
                self.edit_value.setText(str(value))

    def _apply_edit(self):
        """Применить отредактированное значение."""
        item = self.tree.currentItem()
        if item is None:
            return

        is_container = item.data(0, ROLE_IS_CONTAINER)
        if is_container:
            return

        text = self.edit_value.text().strip()
        old_value = item.data(0, ROLE_VALUE)
        key = item.data(0, ROLE_KEY)

        # Пробуем преобразовать к исходному типу
        new_value = self._convert_value(text, old_value)
        item.setData(0, ROLE_VALUE, new_value)
        item.setText(1, self.tree._format_value(new_value))

        self.status_label.setText(f"✅ Поле '{key}' = {new_value}")

    def _remove_field(self):
        """Удалить выбранное поле."""
        item = self.tree.currentItem()
        if item is None:
            return

        parent = item.parent()
        if parent is None:
            QMessageBox.warning(self, "Ошибка", "Нельзя удалить корневой элемент.")
            return

        key = item.data(0, ROLE_KEY)
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить поле '{key}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            parent.removeChild(item)
            self.status_label.setText(f"🗑 Поле '{key}' удалено")

    def _save_tree_to_memory(self):
        """Сохранить изменения из дерева в json_data."""
        if self.json_data is None:
            return

        try:
            parsed = self.tree.to_dict()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось собрать данные из дерева:\n{e}")
            return

        self.json_data.clear()
        self.json_data.update(parsed)

        size_str = self._format_size(len(json.dumps(self.json_data, ensure_ascii=False)))
        self.status_label.setText(
            f"✅ Сохранено в память | Размер: {size_str} | Разделов: {len(parsed)}"
        )
        QMessageBox.information(
            self, "Применено",
            "Данные из дерева сохранены в память.\n"
            "Не забудьте сохранить файл (Ctrl+S)."
        )

    # ---- Утилиты ----

    @staticmethod
    def _convert_value(text: str, original):
        if isinstance(original, bool):
            return text.lower() in ("true", "1", "да", "yes")
        if isinstance(original, int):
            try:
                return int(text)
            except ValueError:
                return text
        if isinstance(original, float):
            try:
                return float(text)
            except ValueError:
                return text
        if original is None and text.lower() == "null":
            return None
        return text

    @staticmethod
    def _format_size(size: int) -> str:
        if size < 1024:
            return f"{size} Б"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} КБ"
        else:
            return f"{size / 1024 / 1024:.1f} МБ"

    def collect(self, data: dict):
        pass
