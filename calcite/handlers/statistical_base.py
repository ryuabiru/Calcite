from __future__ import annotations
import warnings

from PySide6.QtWidgets import QMessageBox

from calcite.models import AnalysisRequest
from calcite.services.statistics_service import (
    UNIQUE_SEPARATOR,
    build_effective_groups,
    format_annotation_pair,
    prepare_analysis_dataframe,
)

warnings.warn(
    "calcite.handlers.statistical_base is part of the legacy Python UI and will be retired after the Rust migration.",
    DeprecationWarning,
    stacklevel=2,
)


class StatisticalHandlerBase:
    _UNIQUE_SEPARATOR = UNIQUE_SEPARATOR

    def __init__(self, main_window):
        self.main = main_window
        self.state = main_window.app_state

    def _ensure_model_loaded(self) -> bool:
        if hasattr(self.main, "model") and self.main.model is not None:
            return True
        QMessageBox.warning(self.main, "Data Not Found", "Please import data before performing an analysis.")
        return False

    def _get_analysis_context(self):
        df = self.main.model._data.copy()
        request = AnalysisRequest.from_settings(self.main.data_widget.get_current_settings())
        return prepare_analysis_dataframe(df, request)

    def _warn_if_missing_axes(self, value_col, group_col):
        if value_col and group_col:
            return False
        QMessageBox.warning(self.main, "Warning", "Please select Y-Axis and X-Axis in the 'Data' tab first.")
        return True

    def _get_interaction_group_col(self, df, x_col, hue_col):
        return build_effective_groups(df, x_col, hue_col)

    def _format_pair_for_annotation(self, pair, hue_col):
        return format_annotation_pair(pair, hue_col)

    def _get_group_dialog_values(self, df, group_col, hue_col):
        x_values = [str(v) for v in df[group_col].dropna().unique()]
        hue_values = [str(v) for v in df[hue_col].dropna().unique()] if hue_col and hue_col in df.columns else []
        return x_values, hue_values

    def _build_effective_group_names(self, group1_condition, group2_condition, hue_col):
        if hue_col:
            return (
                f"{group1_condition['x']}{self._UNIQUE_SEPARATOR}{group1_condition['hue']}",
                f"{group2_condition['x']}{self._UNIQUE_SEPARATOR}{group2_condition['hue']}",
            )
        return group1_condition["x"], group2_condition["x"]

    def _build_group_display_name(self, group_col, condition, hue_col):
        return f"{group_col}={condition['x']}" + (
            f", {hue_col}={condition['hue']}" if hue_col and condition.get("hue") else ""
        )

    def _build_statistical_annotation(self, value_col, group_col, hue_col, facet_col, facet_value, box_pair, p_value):
        return {
            "value_col": value_col,
            "group_col": group_col,
            "hue_col": hue_col,
            "facet_col": facet_col,
            "facet_value": facet_value,
            "box_pair": box_pair,
            "p_value": p_value,
        }

    def _store_group_test_annotation(self, value_col, group_col, hue_col, facet_col, facet_value, pair, p_value):
        formatted_pair = self._format_pair_for_annotation(pair, hue_col)
        annotation = self._build_statistical_annotation(
            value_col=value_col,
            group_col=group_col,
            hue_col=hue_col,
            facet_col=facet_col,
            facet_value=facet_value,
            box_pair=formatted_pair,
            p_value=p_value,
        )
        self.state.add_statistical_annotation(annotation)

    def _show_results(self, text: str, update_graph: bool = False):
        self.main.results_widget.set_results_text(text)
        if update_graph:
            self.main.graph_manager.update_graph()

    def _show_results_or_clear(self, lines: list[str], title: str):
        if lines:
            self.main.results_widget.set_results_text(f"{title}\n======================\n\n" + "\n".join(lines))
        else:
            self.main.results_widget.clear_results()
