"""Вкладка редактирования CharacterMetaStatuses.json (строения/бустеры)."""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QSpinBox, QPushButton,
    QScrollArea, QSplitter, QListWidget, QListWidgetItem,
    QMessageBox, QTabWidget,
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QFont


class BuildingsTab(QWidget):
    """Вкладка для редактирования CharacterMetaStatuses.json."""

    def __init__(self):
        super().__init__()
        self.json_data: dict | None = None
        self.file_path: str | None = None
        self._widgets: dict[str, QWidget] = {}

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Верхняя панель: загрузка файла
        top_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Путь к CharacterMetaStatuses.json")
        self.path_edit.setReadOnly(True)
        top_layout.addWidget(self.path_edit, 1)

        btn_load = QPushButton("📂 Загрузить")
        btn_load.clicked.connect(self._load_file)
        top_layout.addWidget(btn_load)

        btn_auto = QPushButton("🔍 Из папки игры")
        btn_auto.clicked.connect(self._auto_find)
        top_layout.addWidget(btn_auto)

        layout.addLayout(top_layout)

        # Прокручиваемая область с полями
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.form_layout = QVBoxLayout(scroll_widget)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # Кнопка сохранения
        btn_save = QPushButton("💾 Сохранить в файл")
        btn_save.clicked.connect(self._save_to_file)
        layout.addWidget(btn_save)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888;")
        layout.addWidget(self.status_label)

    def auto_load(self):
        """Авто-загрузка из папки игры."""
        settings = QSettings("SPARTA Tools", "SPARTA Save Editor")
        game_folder = settings.value("game_folder", "")
        if not game_folder:
            return
        candidates = [
            Path(game_folder) / "Sparta_Data" / "StreamingAssets" / "Configs" / "CharacterMetaStatuses.json",
            Path(game_folder) / "Configs" / "CharacterMetaStatuses.json",
        ]
        for c in candidates:
            if c.exists():
                self._load_file(str(c))
                return

    def _load_file(self, path: Optional[str] = None):
        if not path:
            from PyQt6.QtWidgets import QFileDialog
            path, _ = QFileDialog.getOpenFileName(
                self, "Открыть CharacterMetaStatuses.json", "",
                "JSON (*.json);;Все файлы (*)",
            )
            if not path:
                return

        try:
            with open(path, "r", encoding="utf-8") as f:
                self.json_data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить:\n{e}")
            return

        if not isinstance(self.json_data, dict):
            QMessageBox.critical(self, "Ошибка", "Файл должен содержать JSON-объект.")
            return

        self.file_path = path
        self.path_edit.setText(path)
        self._build_fields()
        self.status_label.setText(f"✅ Загружено: {path}")

    def _auto_find(self):
        settings = QSettings("SPARTA Tools", "SPARTA Save Editor")
        game_folder = settings.value("game_folder", "")
        if not game_folder:
            QMessageBox.information(self, "Папка не указана",
                                    "Сначала укажите папку с игрой.")
            return
        candidates = [
            Path(game_folder) / "Sparta_Data" / "StreamingAssets" / "Configs" / "CharacterMetaStatuses.json",
            Path(game_folder) / "Configs" / "CharacterMetaStatuses.json",
            Path(game_folder) / "CharacterMetaStatuses.json",
        ]
        for c in candidates:
            if c.exists():
                self._load_file(str(c))
                return
        QMessageBox.warning(self, "Не найден",
                            f"CharacterMetaStatuses.json не найден.")

    def _build_fields(self):
        """Построить поля формы."""
        self._clear_layout(self.form_layout)
        self._widgets.clear()

        if self.json_data is None:
            return

        data = self.json_data

        # === Boosters ===
        boosters = data.get("boosters")
        if isinstance(boosters, dict):
            group = QGroupBox("🏪 Бустеры (строения)")
            form = QFormLayout(group)

            # Hospital.boosterPercent
            hospital = boosters.get("Hospital", {})
            if isinstance(hospital, dict) and "boosterPercent" in hospital:
                w = QSpinBox()
                w.setRange(0, 1000)
                w.setValue(int(hospital["boosterPercent"]))
                form.addRow("📈 Больница (boosterPercent):", w)
                self._widgets["boosters.Hospital.boosterPercent"] = w

            # Saloon.boosterPercent
            saloon = boosters.get("Saloon", {})
            if isinstance(saloon, dict) and "boosterPercent" in saloon:
                w = QSpinBox()
                w.setRange(0, 1000)
                w.setValue(int(saloon["boosterPercent"]))
                form.addRow("📈 Салон (boosterPercent):", w)
                self._widgets["boosters.Saloon.boosterPercent"] = w

            # SlotMachine.cost
            slot = boosters.get("SlotMachine", {})
            if isinstance(slot, dict) and "cost" in slot:
                w = QSpinBox()
                w.setRange(0, 999999999)
                w.setValue(int(slot["cost"]))
                form.addRow("🎰 Автомат (cost):", w)
                self._widgets["boosters.SlotMachine.cost"] = w

            if form.rowCount() > 0:
                self.form_layout.addWidget(group)

        # === Statuses ===
        statuses = data.get("statuses")
        if isinstance(statuses, dict):
            group = QGroupBox("📋 Статусы")
            status_layout = QVBoxLayout(group)

            # Ищем Training и другие статусы
            for status_key in ["Training", "Relax", "Treatment", "Injury"]:
                status_data = statuses.get(status_key)
                if not isinstance(status_data, dict):
                    continue

                status_group = QGroupBox(f"  {status_key}")
                form = QFormLayout(status_group)

                # minDays
                if "minDays" in status_data:
                    w = QSpinBox()
                    w.setRange(0, 999)
                    w.setValue(int(status_data["minDays"]))
                    form.addRow("Мин. дней:", w)
                    self._widgets[f"statuses.{status_key}.minDays"] = w

                # maxDays
                if "maxDays" in status_data:
                    w = QSpinBox()
                    w.setRange(0, 999)
                    w.setValue(int(status_data["maxDays"]))
                    form.addRow("Макс. дней:", w)
                    self._widgets[f"statuses.{status_key}.maxDays"] = w

                # rewardOnCompleteSettings.exp
                reward = status_data.get("rewardOnCompleteSettings")
                if isinstance(reward, dict) and "exp" in reward:
                    w = QSpinBox()
                    w.setRange(0, 999999)
                    w.setValue(int(reward["exp"]))
                    form.addRow("Опыт за завершение:", w)
                    self._widgets[f"statuses.{status_key}.reward.exp"] = w

                if form.rowCount() > 0:
                    status_layout.addWidget(status_group)

            self.form_layout.addWidget(group)

        self.form_layout.addStretch()

    def _save_to_file(self):
        if not self.file_path:
            QMessageBox.warning(self, "Файл не загружен",
                                "Сначала загрузите CharacterMetaStatuses.json.")
            return

        # Применяем значения из виджетов
        for key, widget in self._widgets.items():
            parts = key.split(".")
            if parts[0] == "boosters" and len(parts) >= 3:
                booster_name = parts[1]
                field = parts[2]
                booster = self.json_data.setdefault("boosters", {}).setdefault(booster_name, {})
                booster[field] = widget.value() if isinstance(widget, QSpinBox) else widget.text()

            elif parts[0] == "statuses" and len(parts) >= 3:
                status_name = parts[1]
                field = parts[2]
                status_data = self.json_data.setdefault("statuses", {}).setdefault(status_name, {})
                if field == "minDays":
                    status_data["minDays"] = widget.value()
                elif field == "maxDays":
                    status_data["maxDays"] = widget.value()
                elif field == "reward" and parts[3] == "exp":
                    reward = status_data.setdefault("rewardOnCompleteSettings", {})
                    reward["exp"] = widget.value()

        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.json_data, f, ensure_ascii=False, indent=2)
            self.status_label.setText(f"✅ Сохранено: {self.file_path}")
            QMessageBox.information(self, "Сохранено", f"Файл сохранён:\n{self.file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить:\n{e}")

    @staticmethod
    def _clear_layout(layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
