from __future__ import annotations

from PySide6.QtCore import QSettings


class MainWindowPersistence:
    def restore_geometry(self, window):
        settings = QSettings()
        geometry = settings.value("geometry")
        if geometry:
            window.restoreGeometry(geometry)
        else:
            window.setGeometry(100, 100, 1000, 650)

    def save_geometry(self, window):
        settings = QSettings()
        settings.setValue("geometry", window.saveGeometry())
