from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from ..dialogs.advanced_filter_dialog import AdvancedFilterDialog
from ..dialogs.calculate_dialog import CalculateDialog
from ..dialogs.pivot_dialog import PivotDialog
from ..dialogs.restructure_dialog import RestructureDialog


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


def choose_calculate_settings(parent, columns):
    dialog = CalculateDialog(columns, parent)
    if not dialog.exec():
        return None
    settings = dialog.get_settings()
    if not settings["new_column_name"] or not settings["formula"]:
        QMessageBox.warning(parent, "Warning", "Please enter both a new column name and a formula.")
        return None
    return settings


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


def choose_filter_settings(parent, dataframe):
    dialog = AdvancedFilterDialog(dataframe, parent)
    if not dialog.exec():
        return None
    settings = dialog.get_settings()
    if not settings:
        QMessageBox.warning(parent, "Warning", "One or more filter conditions are incomplete or invalid.")
        return None
    return settings
