"""Главное окно редактора сохранений SPARTA 2035."""

import json
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QFileDialog, QMessageBox, QStatusBar,
    QVBoxLayout, QWidget, QTabWidget, QPushButton, QHBoxLayout,
    QLabel, QLineEdit, QFormLayout, QGroupBox, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox,
    QDoubleSpinBox, QCheckBox, QComboBox, QSplitter, QTextEdit,
    QMenuBar, QToolBar, QApplication,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QIcon

from app.tab_file import FileTab
from app.tab_global import GlobalTab
from app.tab_characters import CharactersTab
from app.tab_warehouse import WarehouseTab


class MainWindow(QMainWindow):
    """Главное окно приложения."""

    def __init__(self):
        super().__init__()

        self.current_file: Path | None = None
        self.json_data: dict | None = None

        self._setup_ui()
        self._setup_menu()

    def _setup_ui(self):
        self.setWindowTitle("SPARTA Save Editor")
        self.resize(1280, 860)

        # Центральный виджет
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Панель инструментов (открыть/сохранить)
        self._setup_toolbar()

        # Табы
        self.tabs = QTabWidget()

        self.tab_file = FileTab()
        self.tab_global = GlobalTab()
        self.tab_characters = CharactersTab()
        self.tab_warehouse = WarehouseTab()

        self.tabs.addTab(self.tab_file, "📁 Выбор файла")
        self.tabs.addTab(self.tab_global, "🌍 Глобальные параметры")
        self.tabs.addTab(self.tab_characters, "👤 Редактор персонажей")
        self.tabs.addTab(self.tab_warehouse, "📦 Склад")

        layout.addWidget(self.tabs)

        # Статус-бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов")

        # Подключаем сигналы от вкладок
        self.tab_file.file_opened.connect(self._on_file_opened)

    def _setup_toolbar(self):
        toolbar = QToolBar("Основные")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        open_action = QAction("📂 Открыть", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_file)
        toolbar.addAction(open_action)

        save_action = QAction("💾 Сохранить", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_file)
        toolbar.addAction(save_action)

        save_as_action = QAction("💾 Сохранить как...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self._save_as)
        toolbar.addAction(save_as_action)

    def _setup_menu(self):
        menubar = self.menuBar()
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

    # ---- Загрузка / сохранение ----

    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Открыть файл сохранения", "",
            "Сохранения (*.sav);;JSON (*.json);;Все файлы (*)",
        )
        if not path:
            return
        self._load_file(Path(path))

    def _load_file(self, path: Path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.json_data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл:\n{e}")
            return

        if not isinstance(self.json_data, dict):
            QMessageBox.critical(self, "Ошибка", "Файл должен содержать JSON-объект (dict).")
            return

        self.current_file = path
        self.status_bar.showMessage(f"Открыт: {path.name}")

        # Обновляем все вкладки
        self.tab_file.set_data(self.json_data)
        self.tab_global.set_data(self.json_data)
        self.tab_characters.set_data(self.json_data)
        self.tab_warehouse.set_data(self.json_data)

        self.tabs.setCurrentIndex(0)

    def _save_file(self):
        if self.current_file is None:
            self._save_as()
            return

        # Собираем данные из вкладок
        self._collect_data()
        self._write_file(self.current_file)

    def _save_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить как", "",
            "Сохранения (*.sav);;JSON (*.json);;Все файлы (*)",
        )
        if not path:
            return

        self._collect_data()
        self.current_file = Path(path)
        self._write_file(self.current_file)

    def _collect_data(self):
        """Собрать данные из всех вкладок обратно в json_data."""
        if self.json_data is None:
            return
        self.tab_global.collect(self.json_data)
        self.tab_characters.collect(self.json_data)
        self.tab_warehouse.collect(self.json_data)

    def _write_file(self, path: Path):
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.json_data, f, ensure_ascii=False, indent=2)
            self.status_bar.showMessage(f"Сохранено: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить:\n{e}")

    def _on_file_opened(self, path: Path):
        """Обработчик из вкладки 'Выбор файла'."""
        self._load_file(path)
