"""Вкладка выбора файла с сохранением настроек путей."""

import json
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QMessageBox, QListWidget, QListWidgetItem,
    QTextEdit, QSplitter, QGroupBox, QFormLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings
from PyQt6.QtGui import QFont


class FileTab(QWidget):
    """Вкладка для выбора и предпросмотра файла сохранения."""

    file_opened = pyqtSignal(Path)

    def __init__(self):
        super().__init__()
        self.json_data: dict | None = None
        self.settings = QSettings("SPARTA Tools", "SPARTA Save Editor")
        self.saves_folder: str = self.settings.value("saves_folder", "")
        self.game_folder: str = self.settings.value("game_folder", "")

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Верхняя панель: кнопки выбора папок
        top_layout = QVBoxLayout()

        # Строка 1: папка сохранений
        row1 = QHBoxLayout()
        btn_saves = QPushButton("📁 Выбор папки с сохранениями")
        btn_saves.setMinimumHeight(36)
        btn_saves.clicked.connect(self._select_saves_folder)
        row1.addWidget(btn_saves)

        self.label_saves = QLabel(self.saves_folder if self.saves_folder else "Не указана")
        self.label_saves.setStyleSheet("color: #888; font-size: 11px;")
        row1.addWidget(self.label_saves, 1)
        top_layout.addLayout(row1)

        # Строка 2: папка игры
        row2 = QHBoxLayout()
        btn_game = QPushButton("🎮 Выбор папки с игрой")
        btn_game.setMinimumHeight(36)
        btn_game.clicked.connect(self._select_game_folder)
        row2.addWidget(btn_game)

        self.label_game = QLabel(self.game_folder if self.game_folder else "Не указана")
        self.label_game.setStyleSheet("color: #888; font-size: 11px;")
        row2.addWidget(self.label_game, 1)
        top_layout.addLayout(row2)

        # Строка 3: кнопка открыть файл + инфо
        row3 = QHBoxLayout()
        self.btn_open = QPushButton("📂 Открыть файл сохранения")
        self.btn_open.setMinimumHeight(36)
        self.btn_open.clicked.connect(self._open_file)
        row3.addWidget(self.btn_open)

        row3.addStretch()

        self.label_path = QLabel("Файл не выбран")
        self.label_path.setStyleSheet("color: #888; font-size: 12px;")
        row3.addWidget(self.label_path)

        top_layout.addLayout(row3)

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

    # ---- Выбор папок ----

    def _select_saves_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Выберите папку с сохранениями",
            self.saves_folder or "",
        )
        if not folder:
            return
        self.saves_folder = folder
        self.settings.setValue("saves_folder", folder)
        self.label_saves.setText(folder)

        # Автоматически ищем .mdb файлы
        self._auto_open_mdb(folder)

    def _select_game_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Выберите папку с игрой",
            self.game_folder or "",
        )
        if not folder:
            return
        self.game_folder = folder
        self.settings.setValue("game_folder", folder)
        self.label_game.setText(folder)

    def _auto_open_mdb(self, folder: str):
        """Автоматически ищет и открывает .mdb файлы в папке."""
        p = Path(folder)
        mdb_files = sorted(p.glob("*.mdb"))
        if not mdb_files:
            QMessageBox.information(
                self, "Файлы не найдены",
                f"В папке '{folder}' не найдено .mdb файлов."
            )
            return

        if len(mdb_files) == 1:
            self._load_mdb(mdb_files[0])
        else:
            # Если несколько — показываем список для выбора
            items = "\n".join(f.name for f in mdb_files)
            msg = QMessageBox(self)
            msg.setWindowTitle("Выберите файл")
            msg.setText(f"Найдено несколько .mdb файлов:\n\n{items}\n\nНажмите Да — открыть первый, "
                        f"Нет — выбрать вручную, Отмена — отмена.")
            msg.setStandardButtons(
                QMessageBox.StandardButton.Yes |
                QMessageBox.StandardButton.No |
                QMessageBox.StandardButton.Cancel
            )
            result = msg.exec()
            if result == QMessageBox.StandardButton.Yes:
                self._load_mdb(mdb_files[0])
            elif result == QMessageBox.StandardButton.No:
                self._open_file()

    def _load_mdb(self, path: Path):
        """Загрузить .mdb файл."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.json_data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл:\n{e}")
            return

        if not isinstance(self.json_data, dict):
            QMessageBox.critical(self, "Ошибка", "Файл должен содержать JSON-объект.")
            return

        self._update_preview(path)
        self.file_opened.emit(path)

    # ---- Открытие файла ----

    def _open_file(self):
        # По умолчанию открываем в папке сохранений
        default_dir = self.saves_folder if self.saves_folder else ""
        path, _ = QFileDialog.getOpenFileName(
            self, "Открыть файл сохранения", default_dir,
            "Сохранения (*.mdb);;JSON (*.json);;Все файлы (*)",
        )
        if not path:
            return
        self._load_mdb(Path(path))

    def set_data(self, data: dict):
        """Установить данные из вне (когда файл открыт из меню)."""
        self.json_data = data

        self.sections_list.clear()
        for key in data.keys():
            item = QListWidgetItem(f"▪ {key}")
            item.setData(Qt.ItemDataRole.UserRole, key)
            self.sections_list.addItem(item)

        self.label_path.setText(self.parent_file_name() or "Файл загружен")
        self.info_label.setText(
            f"Информация о файле: {len(data)} корневых разделов"
        )

        if self.sections_list.count() > 0:
            self.sections_list.setCurrentRow(0)
            self._show_section(self.sections_list.item(0))

    def parent_file_name(self) -> str:
        return self.label_path.text() if self.label_path.text() != "Файл не выбран" else ""

    def _update_preview(self, path: Path):
        self.label_path.setText(path.name)

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
