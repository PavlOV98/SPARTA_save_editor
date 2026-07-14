"""Вкладка полного JSON-редактора файла сохранения."""

import json

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QTextEdit,
)
from PyQt6.QtGui import QFont


class RawFileTab(QWidget):
    """Вкладка для просмотра и редактирования всего файла сохранения целиком."""

    def __init__(self):
        super().__init__()
        self.json_data: dict | None = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Полный JSON файла сохранения. Редактируйте и нажимайте «Применить»."))

        self.editor = QTextEdit()
        self.editor.setFont(QFont("Consolas", 10))
        self.editor.setPlaceholderText("JSON-данные файла...")
        layout.addWidget(self.editor)

        btn_layout = QHBoxLayout()

        btn_apply = QPushButton("✅ Применить (проверить и сохранить в память)")
        btn_apply.clicked.connect(self._apply)
        btn_layout.addWidget(btn_apply)

        btn_refresh = QPushButton("🔄 Обновить из памяти")
        btn_refresh.clicked.connect(self._refresh)
        btn_layout.addWidget(btn_refresh)

        btn_layout.addStretch()

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888;")
        btn_layout.addWidget(self.status_label)

        layout.addLayout(btn_layout)

    def set_data(self, data: dict):
        """Загрузить данные в редактор."""
        self.json_data = data
        self._refresh()

    def _refresh(self):
        """Обновить текст из json_data."""
        if self.json_data is None:
            self.editor.setText("")
            self.status_label.setText("Нет данных")
            return

        text = json.dumps(self.json_data, ensure_ascii=False, indent=2)
        self.editor.setText(text)
        self.status_label.setText(f"Размер: {len(text)} символов | Разделов: {len(self.json_data)}")

    def _apply(self):
        """Применить отредактированный JSON."""
        if self.json_data is None:
            return

        text = self.editor.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Ошибка", "JSON не может быть пустым.")
            return

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as e:
            QMessageBox.critical(
                self, "Ошибка JSON",
                f"Не удалось разобрать JSON:\n{e}"
            )
            return

        if not isinstance(parsed, dict):
            QMessageBox.critical(self, "Ошибка", "Корневой элемент должен быть объектом (dict).")
            return

        # Обновляем данные in-place — заменяем ключи верхнего уровня
        self.json_data.clear()
        self.json_data.update(parsed)

        self.status_label.setText(f"✅ Применено | {len(parsed)} разделов")
        QMessageBox.information(
            self, "Применено",
            "JSON проверен и сохранён в память.\n"
            "Не забудьте сохранить файл (Ctrl+S)."
        )

    def collect(self, data: dict):
        """Ничего не делаем — работаем по references."""
        pass
