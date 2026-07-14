"""Виджет дерева JSON для редактирования сохранений SPARTA 2035."""

import json
from typing import Any

from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt6.QtCore import Qt


class JsonTreeWidget(QTreeWidget):
    """Древовидное представление JSON-данных с возможностью редактирования."""

    # Роли для хранения данных в QTreeWidgetItem
    RoleKey = Qt.ItemDataRole.UserRole + 1         # ключ (строка)
    RoleValue = Qt.ItemDataRole.UserRole + 2       # значение
    RoleIsContainer = Qt.ItemDataRole.UserRole + 3  # True если dict/list
    RoleContainerType = Qt.ItemDataRole.UserRole + 4  # 'dict' или 'list'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabels(["Поле", "Значение"])
        self.setColumnCount(2)
        self.setAlternatingRowColors(True)
        self.setAnimated(True)
        self.setColumnWidth(0, 350)

    def load_json(self, data: Any):
        """Загрузить JSON-данные в дерево."""
        self.clear()
        root = self.invisibleRootItem()

        if isinstance(data, dict):
            item = self._build_item("(root)", data, "dict")
            root.addChild(item)
        elif isinstance(data, list):
            item = self._build_item("(root)", data, "list")
            root.addChild(item)
        else:
            item = QTreeWidgetItem(["(root)", str(data)])
            item.setData(0, self.RoleKey, "(root)")
            item.setData(0, self.RoleValue, data)
            item.setData(0, self.RoleIsContainer, False)
            root.addChild(item)

        self.expandAll()

    def to_dict(self) -> Any:
        """Собрать JSON обратно из дерева."""
        root = self.invisibleRootItem()
        if root.childCount() == 0:
            return None
        root_item = root.child(0)
        return self._item_to_value(root_item)

    # ---- Внутренние методы ----

    def _build_item(self, key: str, value: Any, container_type: str = "dict") -> QTreeWidgetItem:
        """Рекурсивно строит QTreeWidgetItem из JSON-значения."""

        if isinstance(value, dict):
            display = f"{key}:" if key != "(root)" else "(root)"
            item = QTreeWidgetItem([display, f"{{{len(value)} полей}}"])
            item.setData(0, self.RoleKey, key)
            item.setData(0, self.RoleValue, value)
            item.setData(0, self.RoleIsContainer, True)
            item.setData(0, self.RoleContainerType, "dict")
            item.setChildIndicatorPolicy(
                QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator
            )

            for k, v in value.items():
                if isinstance(v, (dict, list)):
                    child = self._build_item(str(k), v)
                else:
                    child = QTreeWidgetItem([str(k), self._format_value(v)])
                    child.setData(0, self.RoleKey, str(k))
                    child.setData(0, self.RoleValue, v)
                    child.setData(0, self.RoleIsContainer, False)
                item.addChild(child)

        elif isinstance(value, list):
            display = f"{key}:" if key != "(root)" else "(root)"
            item = QTreeWidgetItem([display, f"[{len(value)} элементов]"])
            item.setData(0, self.RoleKey, key)
            item.setData(0, self.RoleValue, value)
            item.setData(0, self.RoleIsContainer, True)
            item.setData(0, self.RoleContainerType, "list")
            item.setChildIndicatorPolicy(
                QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator
            )

            for i, v in enumerate(value):
                if isinstance(v, (dict, list)):
                    child = self._build_item(f"[{i}]", v)
                else:
                    child = QTreeWidgetItem([f"[{i}]", self._format_value(v)])
                    child.setData(0, self.RoleKey, f"[{i}]")
                    child.setData(0, self.RoleValue, v)
                    child.setData(0, self.RoleIsContainer, False)
                item.addChild(child)

        return item

    def _item_to_value(self, item: QTreeWidgetItem) -> Any:
        """Рекурсивно собирает значение из дерева."""
        is_container = item.data(0, self.RoleIsContainer)

        if not is_container:
            return item.data(0, self.RoleValue)

        container_type = item.data(0, self.RoleContainerType)

        if container_type == "dict":
            result = {}
            for i in range(item.childCount()):
                child = item.child(i)
                key = child.data(0, self.RoleKey)
                result[key] = self._item_to_value(child)
            return result

        elif container_type == "list":
            result = []
            for i in range(item.childCount()):
                child = item.child(i)
                result.append(self._item_to_value(child))
            return result

        return item.data(0, self.RoleValue)

    @staticmethod
    def _format_value(value: Any) -> str:
        """Форматирует значение для отображения."""
        if value is None:
            return "null"
        if isinstance(value, bool):
            return str(value).lower()
        if isinstance(value, str):
            if len(value) > 100:
                return value[:100] + "..."
            return value
        return str(value)

    def contextMenuEvent(self, event):
        """Обработчик контекстного меню."""
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction

        item = self.itemAt(event.pos())
        if item is None:
            return

        menu = QMenu(self)

        expand = QAction("Развернуть всё", self)
        expand.triggered.connect(lambda: self.expandAll())
        menu.addAction(expand)

        collapse = QAction("Свернуть всё", self)
        collapse.triggered.connect(lambda: self.collapseAll())
        menu.addAction(collapse)

        menu.exec(event.globalPos())
