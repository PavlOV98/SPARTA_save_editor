"""Вкладка глобальных параметров сохранения SPARTA 2035."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QPushButton,
    QScrollArea, QGridLayout, QMessageBox,
)
from PyQt6.QtCore import Qt


class GlobalTab(QWidget):
    """Вкладка для редактирования глобальных параметров сохранения."""

    def __init__(self):
        super().__init__()
        self._widgets: dict[str, QLineEdit | QSpinBox] = {}
        self.json_data: dict | None = None
        self._paths: dict[str, list[str]] = {}  # ключ -> путь в JSON

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Пояснение
        label = QLabel(
            "Ниже перечислены глобальные параметры, которые часто встречаются "
            "в сохранениях SPARTA 2035.\n"
            "Если параметр не найден в вашем файле, он будет пропущен."
        )
        label.setWordWrap(True)
        label.setStyleSheet("color: #666; padding: 4px;")
        layout.addWidget(label)

        # Прокручиваемая область
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        scroll_widget = QWidget()
        self.grid_layout = QGridLayout(scroll_widget)
        self.grid_layout.setVerticalSpacing(6)
        self.grid_layout.setHorizontalSpacing(12)

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # Кнопка "Применить все" — но данные сохраняются при сохранении файла
        self.btn_apply = QPushButton("🔄 Применить изменения (сохранятся при Ctrl+S)")
        self.btn_apply.setEnabled(False)
        self.btn_apply.clicked.connect(self._apply_all)
        layout.addWidget(self.btn_apply)

    # ---- Набор полей ----

    PARAM_DEFINITIONS = [
        # (имя для отображения, ключ в JSON, путь, тип, подсказка)
        # Путь может быть ["раздел", "подраздел", "поле"]
        ("Криптокоины", "crypto", ["crypto"], "int", "Игровая валюта"),
        ("Разведданные", "recon", ["recon"], "int", "Очки разведки"),
        ("Текущая миссия", "mission", ["mission"], "str", "ID текущей миссии"),
        ("Название локации", "location", ["location"], "str", "Текущая локация"),
    ]

    # Параметры, которые могут быть в разных местах — ищем по ключам
    EXTRA_KEYS_TO_FIND = [
        ("Очки действий (ОД)", "action_points", "int"),
        ("Здоровье базы", "base_health", "int"),
        ("Макс. здоровье базы", "base_max_health", "int"),
        ("День", "day", "int"),
        ("Час", "hour", "int"),
        ("Версия сохранения", "save_version", "str"),
        ("Время игры (сек)", "play_time", "int"),
    ]

    def set_data(self, data: dict):
        """Заполнить поля из JSON-данных."""
        self.json_data = data
        self._build_fields(data)

    def _build_fields(self, data: dict):
        """Построить поля на основе данных."""
        # Очищаем старые поля
        self._clear_layout(self.grid_layout)
        self._widgets.clear()
        self._paths.clear()

        row = 0

        # 1. Определённые параметры
        for display_name, key, path, ptype, hint in self.PARAM_DEFINITIONS:
            value = self._get_value_by_path(data, path)
            if value is not None:
                self._add_field(row, display_name, key, value, ptype, hint, path)
                row += 1

        # 2. Ищем дополнительные параметры по ключам
        for display_name, key, ptype in self.EXTRA_KEYS_TO_FIND:
            found = self._find_key_in_dict(data, key)
            if found is not None:
                val, path = found
                self._add_field(row, display_name, key, val, ptype, "", path)
                row += 1

        # Если ничего не найдено
        if row == 0:
            info = QLabel("⚠ Глобальные параметры не найдены. "
                          "Проверьте структуру файла на вкладке 'Выбор файла'.")
            info.setStyleSheet("color: orange; padding: 8px;")
            self.grid_layout.addWidget(info, 0, 0, 1, 2)

        self.btn_apply.setEnabled(row > 0)

    def _add_field(self, row: int, display_name: str, key: str,
                   value, ptype: str, hint: str, path: list[str]):
        """Добавить поле в сетку."""
        label = QLabel(f"{display_name}:")
        label.setToolTip(hint)

        if ptype == "int":
            widget = QSpinBox()
            widget.setRange(-999999999, 999999999)
            try:
                widget.setValue(int(value))
            except (ValueError, TypeError):
                widget.setValue(0)
        elif ptype == "float":
            widget = QDoubleSpinBox()
            widget.setRange(-999999999, 999999999)
            widget.setDecimals(2)
            try:
                widget.setValue(float(value))
            except (ValueError, TypeError):
                widget.setValue(0.0)
        else:  # str
            widget = QLineEdit(str(value) if value is not None else "")

        self.grid_layout.addWidget(label, row, 0)
        self.grid_layout.addWidget(widget, row, 1)

        self._widgets[key] = widget
        self._paths[key] = path

    def _apply_all(self):
        """Применить все значения (визуальное подтверждение)."""
        if self.json_data is None:
            return
        QMessageBox.information(
            self, "Применено",
            "Изменения будут сохранены при нажатии Ctrl+S (Файл → Сохранить)."
        )

    def collect(self, data: dict):
        """Собрать данные из полей обратно в JSON."""
        if data is None:
            return

        for key, widget in self._widgets.items():
            path = self._paths.get(key)
            if not path:
                continue

            # Получаем значение из виджета
            if isinstance(widget, QSpinBox):
                value = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                value = widget.value()
            else:
                value = widget.text()

            # Устанавливаем по пути
            self._set_value_by_path(data, path, value)

    # ---- Утилиты для работы с JSON-путями ----

    @staticmethod
    def _get_value_by_path(data: dict, path: list[str]):
        """Получить значение из вложенного словаря по пути."""
        current = data
        for part in path:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    @staticmethod
    def _set_value_by_path(data: dict, path: list[str], value):
        """Установить значение по пути."""
        current = data
        for i, part in enumerate(path):
            if i == len(path) - 1:
                current[part] = value
            elif isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return

    @staticmethod
    def _find_key_in_dict(data: dict, target_key: str, max_depth: int = 5):
        """Рекурсивно ищет ключ в словаре, возвращает (значение, путь)."""
        def _search(d, path, depth=0):
            if depth > max_depth:
                return None
            if isinstance(d, dict):
                for k, v in d.items():
                    if k.lower() == target_key.lower():
                        return (v, path + [k])
                    result = _search(v, path + [k], depth + 1)
                    if result:
                        return result
            elif isinstance(d, list):
                for i, v in enumerate(d):
                    result = _search(v, path + [str(i)], depth + 1)
                    if result:
                        return result
            return None

        return _search(data, [])

    @staticmethod
    def _clear_layout(layout):
        """Удалить все виджеты из layout."""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
