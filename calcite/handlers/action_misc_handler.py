from __future__ import annotations

import os
import traceback

from PySide6.QtWidgets import QMessageBox

from ..application import SaveTextUseCase
from .action_base import ActionHandlerBase
from ..dialogs.license_dialog import LicenseDialog


class ActionMiscHandler(ActionHandlerBase):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.save_text_use_case = SaveTextUseCase()

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
            self.save_text_use_case.execute(selection.path, text)
            QMessageBox.information(self.main, "Success", f"Analysis results exported to:\n{selection.path}")
        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to export analysis results: {e}")

    def show_license_dialog(self):
        try:
            other_licenses = []
            base_path = os.path.dirname(os.path.abspath(__file__))
            license_dir = os.path.join(base_path, "..", "LICENSES")

            if os.path.isdir(license_dir):
                for filename in sorted(os.listdir(license_dir)):
                    if filename.endswith(".txt"):
                        lib_name = filename.replace("LICENSES_", "").replace(".txt", "")
                        with open(os.path.join(license_dir, filename), "r", encoding="utf-8") as f:
                            content = f.read()
                            other_licenses.append(
                                f"----------------------------------------\n"
                                f"{lib_name.capitalize()}\n"
                                f"----------------------------------------\n"
                                f"{content}\n"
                            )

            pyside6_license = (
                "----------------------------------------\n"
                "PySide6 (LGPL v3)\n"
                "----------------------------------------\n"
                "This application uses PySide6, which is licensed under the GNU Lesser General Public License (LGPL), version 3.\n\n"
                "Under the terms of the LGPL, you have the right to access the source code of PySide6 and to replace the library with your own modified version.\n\n"
                "You can obtain the source code for PySide6 from its official repository:\n"
                "<a href='https://code.qt.io/cgit/pyside/pyside-setup.git/'>https://code.qt.io/cgit/pyside/pyside-setup.git/</a>\n\n"
            )

            final_text_content = "\n".join(other_licenses) + pyside6_license
            final_html = final_text_content.replace("\n", "<br>")
            dialog = LicenseDialog(final_html, self.main)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Could not display licenses: {e}")
            traceback.print_exc()
