from __future__ import annotations

import traceback
import warnings
from pathlib import Path

from PySide6.QtWidgets import QMessageBox

from .action_base import ActionHandlerBase

warnings.warn(
    "calcite.handlers.action_misc_handler is legacy Python UI scaffolding kept for parity checks.",
    DeprecationWarning,
    stacklevel=2,
)


class ActionMiscHandler(ActionHandlerBase):
    def save_table_as_csv(self):
        from .action_dialog_adapters import choose_save_csv_file

        if not hasattr(self.main, "model") or self.main.model is None:
            QMessageBox.warning(self.main, "Warning", "No data to save.")
            return
        selection = choose_save_csv_file(self.main)
        if selection is None:
            return
        try:
            self.main.model._data.to_csv(selection.path, index=False)
            QMessageBox.information(self.main, "Success", f"Table successfully saved to:\n{selection.path}")
        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to save table: {e}")

    def export_analysis_results(self):
        from .action_dialog_adapters import choose_save_results_file

        text = self.main.results_widget.get_results_text()
        if not text.strip():
            QMessageBox.warning(self.main, "Warning", "No analysis results to export.")
            return

        selection = choose_save_results_file(self.main)
        if selection is None:
            return

        try:
            with open(selection.path, "w", encoding="utf-8") as f:
                f.write(text)
            QMessageBox.information(self.main, "Success", f"Analysis results exported to:\n{selection.path}")
        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to export analysis results: {e}")

    def show_migration_notes(self):
        try:
            notes_path = Path(__file__).resolve().parents[2] / "PYTHON_RETIREMENT.md"
            if notes_path.exists():
                QMessageBox.information(
                    self.main,
                    "Python Retirement",
                    "Python GUI is now a legacy reference implementation.\n\n"
                    f"Checklist: {notes_path}",
                )
            else:
                QMessageBox.information(
                    self.main,
                    "Python Retirement",
                    "Python GUI is now a legacy reference implementation.\n\n"
                    "See PYTHON_RETIREMENT.md for the retirement checklist.",
                )
        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Could not display migration notes: {e}")
            traceback.print_exc()
