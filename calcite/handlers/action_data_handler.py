from __future__ import annotations

import traceback

from PySide6.QtWidgets import QMessageBox

from ..application import (
    ApplyAdvancedFilterUseCase,
    CreateChildWindowUseCase,
    PivotDataUseCase,
    RestructureDataUseCase,
)
from .action_base import ActionHandlerBase
from .action_dialog_adapters import (
    choose_calculate_settings,
    choose_filter_settings,
    choose_pivot_settings,
    choose_restructure_settings,
)


class ActionDataHandler(ActionHandlerBase):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.create_child_window_use_case = CreateChildWindowUseCase()
        self.restructure_data_use_case = RestructureDataUseCase()
        self.pivot_data_use_case = PivotDataUseCase()
        self.apply_advanced_filter_use_case = ApplyAdvancedFilterUseCase()

    def show_calculate_dialog(self):
        if not hasattr(self.main, "model"):
            QMessageBox.warning(self.main, "Warning", "Please load data first.")
            return
        settings = choose_calculate_settings(self.main, self.main.model._data.columns)
        if settings is None:
            return
        self.calculate_new_column(settings)

    def calculate_new_column(self, settings):
        try:
            df = self.main.model._data
            self.main.history.begin_change(df)
            df[settings["new_column_name"]] = df.eval(settings["formula"], engine="python")
            self.main.model.refresh_model()
            self.main.data_widget.set_columns(df.columns)
            self.main.history.end_change(df)
        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to calculate column: {e}")

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

    def show_advanced_filter_dialog(self):
        if not hasattr(self.main, "model") or self.main.model is None:
            QMessageBox.warning(self.main, "Warning", "Please load data first.")
            return
        settings = choose_filter_settings(self.main, self.main.model._data)
        if settings is None:
            return
        self.apply_advanced_filter(settings)

    def apply_advanced_filter(self, settings):
        try:
            result = self.apply_advanced_filter_use_case.execute(self.main.model._data.copy(), settings)
            if result.dataframe.empty:
                QMessageBox.information(self.main, "Info", "The filter returned no data.")
                return
            self.create_child_window_use_case.execute(self.main, result.dataframe, "Filtered")
        except Exception as e:
            attempted_query = ""
            try:
                attempted_query = self.apply_advanced_filter_use_case.execute(
                    self.main.model._data.copy(), settings
                ).query
            except Exception:
                pass
            QMessageBox.critical(self.main, "Error", f"Failed to apply filter: {e}\n\nAttempted Query: {attempted_query}")
            traceback.print_exc()
