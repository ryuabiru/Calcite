from __future__ import annotations

import traceback

from PySide6.QtWidgets import QMessageBox
from scipy.stats import shapiro

from calcite.services.statistics_service import run_anova

from ..application import (
    RunShapiroAnalysisUseCase,
    format_shapiro_result,
)
from ..dialogs.anova_dialog import AnovaDialog
from .statistical_dialog_adapters import choose_group_list
from .statistical_base import StatisticalHandlerBase


class StatisticalGroupHandler(StatisticalHandlerBase):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.run_shapiro_analysis_use_case = RunShapiroAnalysisUseCase()

    def perform_one_way_anova(self):
        try:
            if not self._ensure_model_loaded():
                return

            df, request = self._get_analysis_context()
            value_col = request.value_col
            group_col = request.group_col
            hue_col = request.subgroup_col or None
            facet_col = request.facet_col

            if self._warn_if_missing_axes(value_col, group_col):
                return

            x_values, hue_values = self._get_group_dialog_values(df, group_col, hue_col)
            if not x_values:
                QMessageBox.warning(self.main, "Warning", "The selected X-Axis column has no data.")
                return

            selected_groups = choose_group_list(
                self.main,
                AnovaDialog,
                x_values,
                hue_values,
                group_col,
                hue_col,
                minimum_size=1,
                warning_text="Please build a list of at least 2 groups to compare.",
            )
            if selected_groups is None:
                return

            result = run_anova(
                df,
                value_col=value_col,
                group_col=group_col,
                subgroup_col=hue_col or "",
                facet_col=facet_col or "",
                selected_groups=selected_groups,
            )
            if not result.has_valid_samples:
                QMessageBox.warning(self.main, "Warning", "Not enough data for the selected groups.")
                return

            for annotation in result.annotations:
                self.state.add_statistical_annotation(annotation)

            self._show_results_or_clear(result.summary_lines, "One-way ANOVA Results")
            self.main.graph_manager.update_graph()
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self.main, "Error", f"An unexpected error occurred in ANOVA:\n\n{e}")

    def perform_shapiro_test(self):
        if not self._ensure_model_loaded():
            return

        df, request = self._get_analysis_context()
        value_col = request.value_col
        group_col = request.group_col
        hue_col = request.subgroup_col or None

        if self._warn_if_missing_axes(value_col, group_col):
            return

        try:
            effective_groups, group_name = self._get_interaction_group_col(df, group_col, hue_col)
            if not len(effective_groups.dropna().unique()):
                QMessageBox.warning(self.main, "Warning", "No groups found to test.")
                return
            result = self.run_shapiro_analysis_use_case.execute(df, value_col, effective_groups, group_name)
            self._show_results(format_shapiro_result(result))
        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to perform Shapiro-Wilk test: {e}")
            traceback.print_exc()
