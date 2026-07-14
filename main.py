#!/usr/bin/env python3
"""Точка входа в SPARTA Save Editor."""

import sys
from PyQt6.QtWidgets import QApplication
from app.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SPARTA Save Editor")
    app.setOrganizationName("SPARTA Tools")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
