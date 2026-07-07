from __future__ import annotations

from dataclasses import dataclass
import warnings

from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from ..dialogs.pivot_dialog import PivotDialog
from ..dialogs.restructure_dialog import RestructureDialog

warnings.warn(
    "calcite.handlers.action_dialog_adapters is legacy Python UI scaffolding kept for parity checks.",
    DeprecationWarning,
    stacklevel=2,
)


@dataclass(frozen=True)
class FileSelection:
    path: str


def choose_open_csv_file(parent):
    file_path, _ = QFileDialog.getOpenFileName(parent, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)")
    return FileSelection(file_path) if file_path else None


def choose_save_csv_file(parent):
    file_path, _ = QFileDialog.getSaveFileName(parent, "Save CSV File", "", "CSV Files (*.csv);;All Files (*)")
    return FileSelection(file_path) if file_path else None


def choose_save_results_file(parent):
    file_path, _ = QFileDialog.getSaveFileName(
        parent,
        "Export Analysis Results",
        "",
        "Text Files (*.txt);;Markdown Files (*.md);;All Files (*)",
    )
    return FileSelection(file_path) if file_path else None


def choose_open_project_file(parent):
    file_path, _ = QFileDialog.getOpenFileName(parent, "Open Calcite Project", "", "Calcite Project Files (*.calcite)")
    return FileSelection(file_path) if file_path else None


def choose_save_project_file(parent):
    file_path, _ = QFileDialog.getSaveFileName(parent, "Save Calcite Project", "", "Calcite Project Files (*.calcite)")
    return FileSelection(file_path) if file_path else None


def get_clipboard_text():
    return QApplication.clipboard().text()


def choose_restructure_settings(parent, columns):
    dialog = RestructureDialog(columns, parent)
    if not dialog.exec():
        return None
    settings = dialog.get_settings()
    if not settings["id_vars"] or not settings["value_vars"]:
        QMessageBox.warning(parent, "Warning", "Please select both Identifier and Value columns.")
        return None
    return settings


def choose_pivot_settings(parent, columns):
    dialog = PivotDialog(columns, parent)
    if not dialog.exec():
        return None
    settings = dialog.get_settings()
    if not all(settings.values()):
        QMessageBox.warning(parent, "Warning", "Please select all three columns.")
        return None
    return settings
