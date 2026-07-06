from __future__ import annotations

import traceback

from PySide6.QtWidgets import QMessageBox
from scipy.stats import mannwhitneyu, shapiro, ttest_ind

from calcite.services.statistics_service import run_anova, run_kruskal

from ..application import (
    RunShapiroAnalysisUseCase,
    format_binary_test_result,
    format_shapiro_result,
)
from ..dialogs.anova_dialog import AnovaDialog
from ..dialogs.kruskal_dialog import KruskalDialog
from ..dialogs.mannwhitney_dialog import MannWhitneyDialog
from ..dialogs.ttest_dialog import TTestDialog
from .statistical_dialog_adapters import choose_group_list, choose_group_pair
from .statistical_base import StatisticalHandlerBase


class StatisticalGroupHandler(StatisticalHandlerBase):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.run_shapiro_analysis_use_case = RunShapiroAnalysisUseCase()

    def perform_t_test(self):
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
        selection = choose_group_pair(self.main, TTestDialog, x_values, hue_values, group_col, hue_col)
        if selection is None:
            return
        g1_cond = selection.group1
        g2_cond = selection.group2

        try:
            g1_name, g2_name = self._build_effective_group_names(g1_cond, g2_cond, hue_col)
            if facet_col and facet_col in df.columns:
                for category in df[facet_col].dropna().unique():
                    subset_df = df[df[facet_col] == category].reset_index(drop=True)
                    effective_groups, _ = self._get_interaction_group_col(subset_df, group_col, hue_col)
                    group1_values = subset_df.loc[effective_groups == g1_name, value_col].dropna()
                    group2_values = subset_df.loc[effective_groups == g2_name, value_col].dropna()
                    if group1_values.empty or group2_values.empty:
                        continue
                    _, p_value = ttest_ind(group1_values, group2_values, nan_policy="omit")
                    self._store_group_test_annotation(
                        value_col, group_col, hue_col, facet_col, category, (g1_name, g2_name), p_value
                    )
            else:
                effective_groups, _ = self._get_interaction_group_col(df, group_col, hue_col)
                group1_values = df.loc[effective_groups == g1_name, value_col].dropna()
                group2_values = df.loc[effective_groups == g2_name, value_col].dropna()
                if group1_values.empty or group2_values.empty:
                    QMessageBox.warning(self.main, "Warning", "One or both selected groups have no data.")
                    return

                t_stat, p_value = ttest_ind(group1_values, group2_values, nan_policy="omit")
                self._store_group_test_annotation(value_col, group_col, hue_col, None, None, (g1_name, g2_name), p_value)
                result_text = format_binary_test_result(
                    title="Independent t-test results (on current graph):",
                    value_col=value_col,
                    group_1_label=self._build_group_display_name(group_col, g1_cond, hue_col),
                    group_1_n=len(group1_values),
                    group_2_label=self._build_group_display_name(group_col, g2_cond, hue_col),
                    group_2_n=len(group2_values),
                    statistic_label="t-statistic",
                    statistic_value=t_stat,
                    p_value=p_value,
                    group_1_mean=group1_values.mean(),
                    group_2_mean=group2_values.mean(),
                )
                self._show_results(result_text)

            self.main.graph_manager.update_graph()
        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to perform t-test: {e}")
            traceback.print_exc()

    def perform_mannwhitney_test(self):
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
        selection = choose_group_pair(self.main, MannWhitneyDialog, x_values, hue_values, group_col, hue_col)
        if selection is None:
            return
        g1_cond = selection.group1
        g2_cond = selection.group2

        try:
            g1_name, g2_name = self._build_effective_group_names(g1_cond, g2_cond, hue_col)
            if facet_col and facet_col in df.columns:
                for category in df[facet_col].dropna().unique():
                    subset_df = df[df[facet_col] == category].reset_index(drop=True)
                    effective_groups, _ = self._get_interaction_group_col(subset_df, group_col, hue_col)
                    group1_values = subset_df.loc[effective_groups == g1_name, value_col].dropna()
                    group2_values = subset_df.loc[effective_groups == g2_name, value_col].dropna()
                    if len(group1_values) < 1 or len(group2_values) < 1:
                        continue
                    _, p_value = mannwhitneyu(group1_values, group2_values)
                    self._store_group_test_annotation(
                        value_col, group_col, hue_col, facet_col, category, (g1_name, g2_name), p_value
                    )
            else:
                effective_groups, _ = self._get_interaction_group_col(df, group_col, hue_col)
                group1_values = df.loc[effective_groups == g1_name, value_col].dropna()
                group2_values = df.loc[effective_groups == g2_name, value_col].dropna()
                if group1_values.empty or group2_values.empty:
                    QMessageBox.warning(self.main, "Warning", "One or both selected groups have no data.")
                    return

                u_stat, p_value = mannwhitneyu(group1_values, group2_values)
                self._store_group_test_annotation(value_col, group_col, hue_col, None, None, (g1_name, g2_name), p_value)
                result_text = format_binary_test_result(
                    title="Mann-Whitney U test results:",
                    value_col=value_col,
                    group_1_label=self._build_group_display_name(group_col, g1_cond, hue_col),
                    group_1_n=len(group1_values),
                    group_2_label=self._build_group_display_name(group_col, g2_cond, hue_col),
                    group_2_n=len(group2_values),
                    statistic_label="U-statistic",
                    statistic_value=u_stat,
                    p_value=p_value,
                )
                self._show_results(result_text)

            self.main.graph_manager.update_graph()
        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to perform Mann-Whitney U test: {e}")
            traceback.print_exc()

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

    def perform_kruskal_test(self):
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
            selected_groups = choose_group_list(
                self.main,
                KruskalDialog,
                x_values,
                hue_values,
                group_col,
                hue_col,
                minimum_size=2,
                warning_text="Please select at least 2 groups.",
            )
            if selected_groups is None:
                return

            result = run_kruskal(
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

            self._show_results_or_clear(result.summary_lines, "Kruskal-Wallis Test Results")
            self.main.graph_manager.update_graph()
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self.main, "Error", f"An unexpected error occurred in Kruskal-Wallis test:\n\n{e}")

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
