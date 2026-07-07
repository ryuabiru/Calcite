from __future__ import annotations

import warnings

from PySide6.QtCore import QSettings

warnings.warn(
    "calcite.main_window_persistence is legacy Python UI scaffolding kept for parity checks.",
    DeprecationWarning,
    stacklevel=2,
)


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
