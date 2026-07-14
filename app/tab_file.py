"""Вкладка выбора файла с сохранением настроек путей."""

from __future__ import annotations
import json
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QMessageBox,
)
from PyQt6.QtCore import pyqtSignal, QSettings

from app.localization import load_localization


class FileTab(QWidget):
    """Вкладка для выбора папок и открытия файла сохранения."""

    file_opened = pyqtSignal(Path)
    localization_loaded = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.json_data: dict | None = None
        self.localization: dict[str, str] = {}
        self.settings = QSettings("SPARTA Tools", "SPARTA Save Editor")
        self.saves_folder: str = self.settings.value("saves_folder", "")
        self.game_folder: str = self.settings.value("game_folder", "")
        self.locale_file: str = self.settings.value("locale_file", "")

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Настройте пути к папкам:"))

        row1 = QHBoxLayout()
        btn_saves = QPushButton("📁 Папка с сохранениями")
        btn_saves.setMinimumHeight(34)
        btn_saves.clicked.connect(self._select_saves_folder)
        row1.addWidget(btn_saves)
        self.label_saves = QLabel(self.saves_folder if self.saves_folder else "Не указана")
        self.label_saves.setStyleSheet("color: #888; font-size: 11px;")
        row1.addWidget(self.label_saves, 1)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        btn_game = QPushButton("🎮 Папка с игрой")
        btn_game.setMinimumHeight(34)
        btn_game.clicked.connect(self._select_game_folder)
        row2.addWidget(btn_game)
        self.label_game = QLabel(self.game_folder if self.game_folder else "Не указана")
        self.label_game.setStyleSheet("color: #888; font-size: 11px;")
        row2.addWidget(self.label_game, 1)
        layout.addLayout(row2)

        # Строка 3: файл локализации
        row3 = QHBoxLayout()
        btn_locale = QPushButton("🌐 Файл локализации")
        btn_locale.setMinimumHeight(34)
        btn_locale.clicked.connect(self._select_locale_file)
        row3.addWidget(btn_locale)
        self.label_locale = QLabel(self.locale_file if self.locale_file else "Не выбран")
        self.label_locale.setStyleSheet("color: #888; font-size: 11px;")
        row3.addWidget(self.label_locale, 1)
        layout.addLayout(row3)

        layout.addSpacing(12)

        row4 = QHBoxLayout()
        self.btn_open = QPushButton("📂 Открыть файл сохранения")
        self.btn_open.setMinimumHeight(38)
        self.btn_open.clicked.connect(self._open_file)
        row4.addWidget(self.btn_open)
        self.label_path = QLabel("Файл не выбран")
        self.label_path.setStyleSheet("color: #888; font-size: 12px;")
        row4.addWidget(self.label_path, 1)
        layout.addLayout(row4)

        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #555; padding: 6px;")
        layout.addWidget(self.info_label)

        layout.addStretch()

    def get_localization(self) -> dict[str, str]:
        return self.localization

    def _select_saves_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Выберите папку с сохранениями", self.saves_folder or "")
        if not folder:
            return
        self.saves_folder = folder
        self.settings.setValue("saves_folder", folder)
        self.label_saves.setText(folder)
        self._auto_open_mdb(folder)

    def _select_game_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Выберите папку с игрой", self.game_folder or "")
        if not folder:
            return
        self.game_folder = folder
        self.settings.setValue("game_folder", folder)
        self.label_game.setText(folder)

    def _select_locale_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите файл локализации", "",
            "Все файлы (*)",
        )
        if not path:
            return
        self.locale_file = path
        self.settings.setValue("locale_file", path)
        self.label_locale.setText(path)
        self._load_localization(path)

    def _load_localization(self, file_path: str):
        self.localization = load_localization(file_path)
        count = len(self.localization)
        self.info_label.setText(
            f"✅ Загружено строк локализации: {count}"
        )
        self.localization_loaded.emit(self.localization)

    def _auto_open_mdb(self, folder: str):
        p = Path(folder)
        mdb_files = sorted(p.glob("*.mdb"))
        if not mdb_files:
            QMessageBox.information(self, "Файлы не найдены",
                                    f"В папке '{folder}' не найдено .mdb файлов.")
            return
        if len(mdb_files) == 1:
            self._load_mdb(mdb_files[0])
        else:
            items = "\n".join(f.name for f in mdb_files)
            msg = QMessageBox(self)
            msg.setWindowTitle("Выберите файл")
            msg.setText(f"Найдено несколько .mdb файлов:\n\n{items}")
            msg.setInformativeText("Нажмите Да — открыть первый, Нет — выбрать вручную.")
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
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.json_data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл:\n{e}")
            return
        if not isinstance(self.json_data, dict):
            QMessageBox.critical(self, "Ошибка", "Файл должен содержать JSON-объект.")
            return

        self.label_path.setText(path.name)
        size = path.stat().st_size
        size_str = f"{size} Б" if size < 1024 else f"{size / 1024:.1f} КБ"
        self.info_label.setText(
            f"Файл: {path.name} | Размер: {size_str} | Разделов: {len(self.json_data)}"
        )
        self.file_opened.emit(path)

    def _open_file(self):
        default_dir = self.saves_folder if self.saves_folder else ""
        path, _ = QFileDialog.getOpenFileName(
            self, "Открыть файл сохранения", default_dir,
            "Сохранения (*.mdb);;JSON (*.json);;Все файлы (*)",
        )
        if not path:
            return
        self._load_mdb(Path(path))

    def set_data(self, data: dict):
        self.json_data = data
        self.info_label.setText(f"Файл загружен | Разделов: {len(data)}")
