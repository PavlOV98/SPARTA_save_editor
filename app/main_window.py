"""Главное окно редактора сохранений SPARTA 2035."""

import json
import os
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow,
    QFileDialog,
    QMessageBox,
    QMenuBar,
    QStatusBar,
    QVBoxLayout,
    QWidget,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QLineEdit,
    QLabel,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
)

from app.json_editor import JsonTreeWidget


class MainWindow(QMainWindow):
    """Главное окно приложения."""

    def __init__(self):
        super().__init__()

        self.current_file: Path | None = None
        self.json_data: dict | list | None = None

        self._setup_ui()
        self._setup_menu()

    def _setup_ui(self):
        self.setWindowTitle("SPARTA Save Editor")
        self.resize(1200, 800)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Основной сплиттер: дерево JSON + панель редактирования
        splitter = QSplitter()

        # Дерево JSON
        self.tree = JsonTreeWidget()
        splitter.addWidget(self.tree)

        # Панель редактирования
        editor_panel = QWidget()
        editor_layout = QVBoxLayout(editor_panel)

        editor_layout.addWidget(QLabel("Редактирование:"))

        self.key_label = QLabel("Ключ:")
        editor_layout.addWidget(self.key_label)

        self.value_edit = QLineEdit()
        self.value_edit.setPlaceholderText("Значение...")
        editor_layout.addWidget(self.value_edit)

        btn_layout = QHBoxLayout()
        apply_btn = QPushButton("Применить")
        apply_btn.clicked.connect(self._apply_edit)
        btn_layout.addWidget(apply_btn)

        add_btn = QPushButton("Добавить поле")
        add_btn.clicked.connect(self._add_field)
        btn_layout.addWidget(add_btn)

        remove_btn = QPushButton("Удалить поле")
        remove_btn.clicked.connect(self._remove_field)
        btn_layout.addWidget(remove_btn)

        editor_layout.addLayout(btn_layout)
        editor_layout.addStretch()

        splitter.addWidget(editor_panel)
        splitter.setSizes([700, 500])

        layout.addWidget(splitter)

        # Статус-бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов")

        # Подключение сигнала выбора в дереве
        self.tree.itemClicked.connect(self._on_item_selected)

    def _setup_menu(self):
        menubar = self.menuBar()

        # Файл
        file_menu = menubar.addMenu("Файл")

        open_action = file_menu.addAction("Открыть...")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_file)

        save_action = file_menu.addAction("Сохранить")
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_file)

        save_as_action = file_menu.addAction("Сохранить как...")
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self._save_as)

        file_menu.addSeparator()

        exit_action = file_menu.addAction("Выход")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)

    # ---- Обработчики ----

    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Открыть файл сохранения", "", "JSON (*.json);;Все файлы (*)",
        )
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                self.json_data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл:\n{e}")
            return

        self.current_file = Path(path)
        self.tree.load_json(self.json_data)
        self.status_bar.showMessage(f"Открыт: {path}")

    def _save_file(self):
        if self.current_file is None:
            self._save_as()
            return

        self._write_file(self.current_file)

    def _save_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить как", "", "JSON (*.json);;Все файлы (*)",
        )
        if not path:
            return
        self.current_file = Path(path)
        self._write_file(self.current_file)

    def _write_file(self, path: Path):
        try:
            self.json_data = self.tree.to_dict()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.json_data, f, ensure_ascii=False, indent=2)
            self.status_bar.showMessage(f"Сохранено: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить:\n{e}")

    def _on_item_selected(self, item: QTreeWidgetItem, _column: int):
        """При выборе элемента показываем ключ и значение в панели редактора."""
        key = item.data(0, JsonTreeWidget.RoleKey)
        value = item.data(0, JsonTreeWidget.RoleValue)
        is_container = item.data(0, JsonTreeWidget.RoleIsContainer)

        if is_container:
            self.key_label.setText(f"Ключ: {key}")
            self.value_edit.setEnabled(False)
            self.value_edit.setText("(объект / массив — редактируется в дереве)")
        else:
            self.key_label.setText(f"Ключ: {key}")
            self.value_edit.setEnabled(True)
            self.value_edit.setText(str(value) if value is not None else "")

    def _apply_edit(self):
        """Применить отредактированное значение."""
        item = self.tree.currentItem()
        if item is None:
            return

        is_container = item.data(0, JsonTreeWidget.RoleIsContainer)
        if is_container:
            return

        new_value = self.value_edit.text()
        key = item.data(0, JsonTreeWidget.RoleKey)
        old_value = item.data(0, JsonTreeWidget.RoleValue)

        # Пробуем преобразовать тип
        converted = self._convert_value(new_value, old_value)
        item.setData(0, JsonTreeWidget.RoleValue, converted)

        # Обновляем отображение
        item.setText(0, f"{key}: {converted}")
        self.status_bar.showMessage(f"Поле '{key}' = {converted}")

    def _add_field(self):
        """Добавить новое поле (заглушка)."""
        QMessageBox.information(
            self, "Добавление поля",
            "Выберите родительский объект в дереве, затем нажмите Добавить."
        )

    def _remove_field(self):
        """Удалить выбранное поле."""
        item = self.tree.currentItem()
        if item is None:
            return

        parent = item.parent()
        if parent is None:
            QMessageBox.warning(self, "Ошибка", "Нельзя удалить корневой элемент.")
            return

        key = item.data(0, JsonTreeWidget.RoleKey)
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить поле '{key}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            parent.removeChild(item)

    @staticmethod
    def _convert_value(text: str, original):
        """Пытается привести строку к типу исходного значения."""
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
        # строка или None
        return text
