"""Вкладка выбора файла."""

import json
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QMessageBox, QListWidget, QListWidgetItem,
    QGroupBox, QTextEdit, QSplitter, QFormLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class FileTab(QWidget):
    """Вкладка для выбора и предпросмотра файла сохранения."""

    file_opened = pyqtSignal(Path)

    def __init__(self):
        super().__init__()
        self.json_data: dict | None = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Верхняя панель: кнопка открыть
        top_layout = QHBoxLayout()

        self.btn_open = QPushButton("📂 Открыть файл сохранения")
        self.btn_open.setMinimumHeight(40)
        self.btn_open.clicked.connect(self._open_file)
        top_layout.addWidget(self.btn_open)

        top_layout.addStretch()

        self.label_path = QLabel("Файл не выбран")
        self.label_path.setStyleSheet("color: #888; font-size: 12px;")
        top_layout.addWidget(self.label_path)

        layout.addLayout(top_layout)

        # Основная область: предпросмотр
        splitter = QSplitter()

        # Левая панель: список секций
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_layout.addWidget(QLabel("Структура файла:"))

        self.sections_list = QListWidget()
        self.sections_list.itemClicked.connect(self._on_section_clicked)
        left_layout.addWidget(self.sections_list)

        splitter.addWidget(left_widget)

        # Правая панель: предпросмотр содержимого секции
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        right_layout.addWidget(QLabel("Содержимое секции:"))

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setFont(QFont("Consolas", 9))
        right_layout.addWidget(self.preview_text)

        splitter.addWidget(right_widget)
        splitter.setSizes([250, 600])

        layout.addWidget(splitter)

        # Нижняя панель: информация о файле
        self.info_label = QLabel("Информация о файле: —")
        self.info_label.setStyleSheet("color: #555; padding: 4px;")
        layout.addWidget(self.info_label)

    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Открыть файл сохранения", "",
            "Сохранения (*.sav);;JSON (*.json);;Все файлы (*)",
        )
        if not path:
            return
        p = Path(path)
        try:
            with open(p, "r", encoding="utf-8") as f:
                self.json_data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл:\n{e}")
            return

        if not isinstance(self.json_data, dict):
            QMessageBox.critical(self, "Ошибка", "Файл должен содержать JSON-объект.")
            return

        self._update_preview(p)
        self.file_opened.emit(p)

    def set_data(self, data: dict):
        """Установить данные из вне (когда файл открыт из меню)."""
        self.json_data = data

        # Обновляем список секций
        self.sections_list.clear()
        for key in data.keys():
            item = QListWidgetItem(f"▪ {key}")
            item.setData(Qt.ItemDataRole.UserRole, key)
            self.sections_list.addItem(item)

        # Обновляем информацию
        self.label_path.setText(self.parent_file_name() or "Файл загружен")
        self.info_label.setText(
            f"Информация о файле: {len(data)} корневых разделов"
        )

        # Показываем первую секцию
        if self.sections_list.count() > 0:
            self.sections_list.setCurrentRow(0)
            self._show_section(self.sections_list.item(0))

    def parent_file_name(self) -> str:
        """Вернуть имя файла, если известно."""
        return self.label_path.text() if self.label_path.text() != "Файл не выбран" else ""

    def _update_preview(self, path: Path):
        """Обновить предпросмотр после открытия файла."""
        self.label_path.setText(path.name)

        # Обновляем список секций
        self.sections_list.clear()
        for key in self.json_data.keys():
            item = QListWidgetItem(f"▪ {key}")
            item.setData(Qt.ItemDataRole.UserRole, key)
            self.sections_list.addItem(item)

        total_size = path.stat().st_size
        if total_size < 1024:
            size_str = f"{total_size} Б"
        elif total_size < 1024 * 1024:
            size_str = f"{total_size / 1024:.1f} КБ"
        else:
            size_str = f"{total_size / 1024 / 1024:.1f} МБ"

        self.info_label.setText(
            f"Файл: {path.name} | Размер: {size_str} | "
            f"Разделов: {len(self.json_data)}"
        )

        # Показываем первую секцию
        if self.sections_list.count() > 0:
            self.sections_list.setCurrentRow(0)
            self._show_section(self.sections_list.item(0))

    def _on_section_clicked(self, item: QListWidgetItem):
        self._show_section(item)

    def _show_section(self, item: QListWidgetItem):
        if not item or self.json_data is None:
            return

        key = item.data(Qt.ItemDataRole.UserRole)
        value = self.json_data.get(key, {})

        self.preview_text.setText(json.dumps(value, ensure_ascii=False, indent=2))
