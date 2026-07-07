from __future__ import annotations

import warnings

from PySide6.QtWidgets import QMessageBox

from ..application import (
    CreateChildWindowUseCase,
    PivotDataUseCase,
    RestructureDataUseCase,
)
from .action_base import ActionHandlerBase
from .action_dialog_adapters import choose_pivot_settings, choose_restructure_settings

warnings.warn(
    "calcite.handlers.action_data_handler is legacy Python UI scaffolding kept for parity checks.",
    DeprecationWarning,
    stacklevel=2,
)


class ActionDataHandler(ActionHandlerBase):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.create_child_window_use_case = CreateChildWindowUseCase()
        self.restructure_data_use_case = RestructureDataUseCase()
        self.pivot_data_use_case = PivotDataUseCase()

    def show_restructure_dialog(self):
        if not hasattr(self.main, "model"):
            QMessageBox.warning(self.main, "Warning", "Please load data first.")
            return
        settings = choose_restructure_settings(self.main, self.main.model._data.columns)
        if settings is None:
            return
        self.restructure_data(settings)

    def restructure_data(self, settings):
        try:
            new_df = self.restructure_data_use_case.execute(self.main.model._data, settings)
            self.create_child_window_use_case.execute(self.main, new_df, "Restructured")
        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to restructure data: {e}")

    def show_pivot_dialog(self):
        if not hasattr(self.main, "model"):
            QMessageBox.warning(self.main, "Warning", "Please load data first.")
            return
        settings = choose_pivot_settings(self.main, self.main.model._data.columns)
        if settings is None:
            return
        self.pivot_data(settings)

    def pivot_data(self, settings):
        try:
            new_df = self.pivot_data_use_case.execute(self.main.model._data, settings)
            self.create_child_window_use_case.execute(self.main, new_df, "Pivoted")
        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to pivot data: {e}")
