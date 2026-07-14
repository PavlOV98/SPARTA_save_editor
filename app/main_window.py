"""Главное окно редактора сохранений SPARTA 2035."""

from __future__ import annotations
import json
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QFileDialog, QMessageBox, QStatusBar,
    QVBoxLayout, QWidget, QTabWidget,
    QMenuBar, QToolBar, QApplication,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction

from app.tab_file import FileTab
from app.tab_global import GlobalTab
from app.tab_characters import CharactersTab
from app.tab_warehouse import WarehouseTab
from app.tab_equipment import EquipmentTab
from app.tab_weapons import WeaponsTab


class MainWindow(QMainWindow):
    """Главное окно приложения."""

    def __init__(self):
        super().__init__()

        self.current_file: Path | None = None
        self.json_data: dict | None = None
        self.localization: dict[str, str] = {}

        self._setup_ui()
        self._setup_menu()

    def _setup_ui(self):
        self.setWindowTitle("SPARTA Save Editor")
        self.resize(1280, 860)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self._setup_toolbar()

        self.tabs = QTabWidget()

        self.tab_file = FileTab()
        self.tab_global = GlobalTab()
        self.tab_characters = CharactersTab()
        self.tab_warehouse = WarehouseTab()
        self.tab_equipment = EquipmentTab()
        self.tab_weapons = WeaponsTab()

        # Подключаем сигналы ДО авто-загрузки
        self.tab_file.file_opened.connect(self._on_file_opened)
        self.tab_file.localization_loaded.connect(self._on_localization_loaded)

        self.tabs.addTab(self.tab_file, "[FOLDER]  Выбор файла")
        self.tabs.addTab(self.tab_global, "[GLOB]  Глобальные параметры")
        self.tabs.addTab(self.tab_characters, "[CHAR]  Редактор персонажей")
        self.tabs.addTab(self.tab_warehouse, "[BOX]  Склад")
        self.tabs.addTab(self.tab_equipment, "[GEAR]  Оборудование")
        self.tabs.addTab(self.tab_weapons, "[GUN]  Оружие")

        layout.addWidget(self.tabs)

        # Статус-бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов")

        # Авто-загрузка локализации после подключения сигналов
        self.tab_file.auto_load_localization()

        # Авто-загрузка оборудования и оружия из папки игры
        self.tab_equipment.auto_load()
        self.tab_weapons.auto_load()

        # Начальное состояние: вкладки заблокированы (кроме 0)
        self._set_tabs_enabled(False)

    def _set_tabs_enabled(self, enabled: bool):
        """Включить/выключить вкладки 1-3 (глобал, персонажи, склад)."""
        for i in [1, 2, 3]:  # глобальные, персонажи, склад
            self.tabs.setTabEnabled(i, enabled)

    def _setup_toolbar(self):
        toolbar = QToolBar("Основные")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        open_action = QAction("Открыть", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_file)
        toolbar.addAction(open_action)

        save_action = QAction("Сохранить", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_file)
        toolbar.addAction(save_action)

        save_as_action = QAction("Сохранить как...", self)
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

    def _on_localization_loaded(self, loc: dict[str, str]):
        self.localization = loc
        # Передаём локализацию в Equipment и Weapons
        self.tab_equipment.set_localization(loc)
        self.tab_weapons.set_localization(loc)
        self.status_bar.showMessage(f"Локализация: {len(loc)} строк", 3000)

    def _open_file(self):
        from PyQt6.QtCore import QSettings
        settings = QSettings("SPARTA Tools", "SPARTA Save Editor")
        default_dir = settings.value("saves_folder", "")
        path, _ = QFileDialog.getOpenFileName(
            self, "Открыть файл сохранения", default_dir,
            "Сохранения (*.mdb);;JSON (*.json);;Все файлы (*)",
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

        self.tab_file.set_data(self.json_data)
        self.tab_global.set_data(self.json_data)
        self.tab_characters.set_data(self.json_data)
        self.tab_warehouse.set_data(self.json_data)

        # Разблокируем вкладки
        self._set_tabs_enabled(True)
        self.tabs.setCurrentIndex(0)

    def _save_file(self):
        if self.current_file is None:
            self._save_as()
            return
        self._collect_data()
        self._write_file(self.current_file)

    def _save_as(self):
        from PyQt6.QtCore import QSettings
        settings = QSettings("SPARTA Tools", "SPARTA Save Editor")
        default_dir = settings.value("saves_folder", "")
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить как", default_dir,
            "Сохранения (*.mdb);;JSON (*.json);;Все файлы (*)",
        )
        if not path:
            return
        self._collect_data()
        self.current_file = Path(path)
        self._write_file(self.current_file)

    def _collect_data(self):
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
        self._load_file(path)
