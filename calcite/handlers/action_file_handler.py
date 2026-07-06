from __future__ import annotations

import os
import traceback

from PySide6.QtWidgets import QMessageBox

from ..application import OpenCsvUseCase, OpenProjectUseCase, PasteClipboardUseCase, SaveProjectUseCase
from .action_base import ActionHandlerBase
from .action_dialog_adapters import (
    choose_open_csv_file,
    choose_open_project_file,
    choose_save_project_file,
    get_clipboard_text,
)


class ActionFileHandler(ActionHandlerBase):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.open_project_use_case = OpenProjectUseCase()
        self.open_csv_use_case = OpenCsvUseCase()
        self.paste_clipboard_use_case = PasteClipboardUseCase()
        self.save_project_use_case = SaveProjectUseCase()

    def open_csv_file(self):
        selection = choose_open_csv_file(self.main)
        if selection is None:
            return
        try:
            df = self.open_csv_use_case.execute(selection.path)
            self.main.load_dataframe(df)
        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Error opening file: {e}")

    def paste_from_clipboard(self):
        try:
            text = get_clipboard_text()
            if not text:
                return
            df = self.paste_clipboard_use_case.execute(text)
            self.main.load_dataframe(df)
        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to paste from clipboard: {e}")

    def save_project(self):
        if not hasattr(self.main, "model") or self.main.model is None:
            QMessageBox.warning(self.main, "Warning", "No data to save.")
            return
        selection = choose_save_project_file(self.main)
        if selection is None:
            return
        try:
            self.save_project_use_case.execute(selection.path, self.main.get_project_state())
            QMessageBox.information(self.main, "Success", f"Project saved to:\n{selection.path}")
            self.main.statusBar().showMessage(f"Project saved: {os.path.basename(selection.path)}")
        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to save project: {e}")
            traceback.print_exc()

    def open_project(self):
        selection = choose_open_project_file(self.main)
        if selection is None:
            return
        try:
            state = self.open_project_use_case.execute(selection.path)
            self.main.apply_project_state(state)
            self.main.statusBar().showMessage(f"Project opened: {os.path.basename(selection.path)}")
        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to open project: {e}")
            traceback.print_exc()
