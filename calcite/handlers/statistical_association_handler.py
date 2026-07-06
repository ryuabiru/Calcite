from __future__ import annotations

import traceback
import pandas as pd

from PySide6.QtWidgets import QMessageBox

from ..application import (
    RunChiSquaredAnalysisUseCase,
    RunPearsonCorrelationUseCase,
    RunRegressionAnalysisUseCase,
    RunSpearmanCorrelationUseCase,
    RunTwoProportionAnalysisUseCase,
    format_chi_squared_result,
    format_pearson_correlation_result,
    format_regression_summary,
    format_spearman_correlation_result,
    format_two_proportion_result,
)
from .statistical_base import StatisticalHandlerBase
from .statistical_dialog_adapters import (
    choose_contingency_columns,
    choose_correlation_columns,
    choose_regression_settings,
)


class StatisticalAssociationHandler(StatisticalHandlerBase):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.run_chi_squared_analysis_use_case = RunChiSquaredAnalysisUseCase()
        self.run_pearson_correlation_use_case = RunPearsonCorrelationUseCase()
        self.run_regression_analysis_use_case = RunRegressionAnalysisUseCase()
        self.run_spearman_correlation_use_case = RunSpearmanCorrelationUseCase()
        self.run_two_proportion_analysis_use_case = RunTwoProportionAnalysisUseCase()

    def perform_chi_squared_test(self):
        if not self._ensure_model_loaded():
            return

        df = self.main.model._data
        selection = choose_contingency_columns(self.main, df.columns)
        if selection is None:
            return
        rows_col, cols_col = selection.rows_col, selection.cols_col

        try:
            result = self.run_chi_squared_analysis_use_case.execute(df, rows_col, cols_col)
            self.state.chi_squared_highlight = {
                "rows_col": rows_col,
                "cols_col": cols_col,
                "standardized_residuals": result.standardized_residuals.round(6).to_dict(),
                "p_value": result.p_value,
            }
            self._show_results(format_chi_squared_result(result, rows_col, cols_col), update_graph=True)
        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to perform Chi-squared test: {e}")

    def perform_two_proportion_test(self):
        if not self._ensure_model_loaded():
            return

        df = self.main.model._data
        selection = choose_contingency_columns(self.main, df.columns)
        if selection is None:
            return
        rows_col, cols_col = selection.rows_col, selection.cols_col

        try:
            result = self.run_two_proportion_analysis_use_case.execute(df, rows_col, cols_col)
            self.state.two_proportion_highlight = {
                "rows_col": rows_col,
                "cols_col": cols_col,
                "group1_label": result.group1_label,
                "group2_label": result.group2_label,
                "success_label": result.success_label,
                "difference_in_proportions": result.difference_in_proportions,
                "ci_low_difference": result.ci_low_difference,
                "ci_high_difference": result.ci_high_difference,
                "p_value": result.p_value,
            }
            self._show_results(format_two_proportion_result(result, rows_col, cols_col), update_graph=True)
        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to perform 2-proportion z-test: {e}")

    def perform_spearman_correlation(self):
        if not self._ensure_model_loaded():
            return

        df = self.main.model._data
        selection = choose_correlation_columns(self.main, df.columns)
        if selection is None:
            return
        col1, col2 = selection.col1, selection.col2

        try:
            data1 = df[col1].dropna()
            data2 = df[col2].dropna()
            common_indices = data1.index.intersection(data2.index)
            if len(common_indices) < 3:
                QMessageBox.warning(self.main, "Warning", "Not enough paired data to perform the test.")
                return
            result = self.run_spearman_correlation_use_case.execute(df, col1, col2)
            self._show_results(format_spearman_correlation_result(result, col1, col2))
        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to perform Spearman's correlation: {e}")
            traceback.print_exc()

    def perform_pearson_correlation(self):
        if not self._ensure_model_loaded():
            return

        df = self.main.model._data
        selection = choose_correlation_columns(self.main, df.columns)
        if selection is None:
            return
        col1, col2 = selection.col1, selection.col2

        try:
            data1 = pd.to_numeric(df[col1], errors="coerce").dropna()
            data2 = pd.to_numeric(df[col2], errors="coerce").dropna()
            common_indices = data1.index.intersection(data2.index)
            if len(common_indices) < 3:
                QMessageBox.warning(self.main, "Warning", "Not enough paired numeric data to perform the test.")
                return
            result = self.run_pearson_correlation_use_case.execute(df, col1, col2)
            self._show_results(format_pearson_correlation_result(result, col1, col2))
        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to perform Pearson correlation: {e}")
            traceback.print_exc()

    def perform_regression(self):
        if not self._ensure_model_loaded():
            return

        df = self.main.model._data
        selection = choose_regression_settings(self.main, df.columns)
        if selection is None:
            return
        x_col, y_col, model = selection.x_col, selection.y_col, selection.model

        subgroup_col = self.main.data_widget.get_current_settings().get("subgroup_col")
        if subgroup_col == x_col:
            subgroup_col = None

        try:
            result = self.run_regression_analysis_use_case.execute(
                dataframe=df,
                x_col=x_col,
                y_col=y_col,
                model=model,
                subgroup_col=subgroup_col,
            )
            self.state.regression_line_params = result.regression_line_params
            self.state.fit_params = result.fit_params
            self.main.graph_manager.update_graph()
            self._show_results(format_regression_summary(model, result.summary_lines))
        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to perform regression: {e}\n\n{traceback.format_exc()}")
