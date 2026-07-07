from __future__ import annotations

import traceback
import warnings

from PySide6.QtWidgets import QMessageBox

from ..application import CreateChildWindowUseCase, CreateSubsetUseCase
from .action_base import ActionHandlerBase

warnings.warn(
    "calcite.handlers.action_table_handler is legacy Python UI scaffolding kept for parity checks.",
    DeprecationWarning,
    stacklevel=2,
)


class ActionTableHandler(ActionHandlerBase):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.create_child_window_use_case = CreateChildWindowUseCase()
        self.create_subset_use_case = CreateSubsetUseCase()

    def create_table_from_selection(self):
        if not hasattr(self.main, "model") or self.main.model is None:
            QMessageBox.warning(self.main, "Warning", "No data available.")
            return

        selection_model = self.main.table_view.selectionModel()
        selected_rows = selection_model.selectedRows() if selection_model is not None else []
        if not selected_rows:
            QMessageBox.warning(self.main, "Warning", "Please select one or more rows to create a new table.")
            return

        try:
            row_indices = sorted(list(set(index.row() for index in selected_rows)))
            new_df = self.create_subset_use_case.execute(self.main.model._data, row_indices)
            self.create_child_window_use_case.execute(self.main, new_df, "Subset")
        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to create new table from selection: {e}")
            traceback.print_exc()
