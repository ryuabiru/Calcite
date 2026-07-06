from __future__ import annotations

from PySide6.QtWidgets import QMessageBox
from scipy.stats import ttest_rel, wilcoxon

from ..application import format_paired_test_result
from ..dialogs.paired_ttest_dialog import PairedTTestDialog
from ..dialogs.wilcoxon_dialog import WilcoxonDialog
from .statistical_base import StatisticalHandlerBase
from .statistical_dialog_adapters import choose_paired_columns


class StatisticalPairedHandler(StatisticalHandlerBase):
    def perform_paired_t_test(self):
        if not self._ensure_model_loaded():
            return
        df = self.main.model._data
        selection = choose_paired_columns(self.main, PairedTTestDialog, df.columns)
        if selection is None:
            return
        col1, col2 = selection.col1, selection.col2
        try:
            data1 = df[col1].dropna()
            data2 = df[col2].dropna()
            min_len = min(len(data1), len(data2))
            if min_len < 2:
                QMessageBox.warning(self.main, "Warning", "Not enough paired data to perform the test.")
                return

            t_stat, p_value = ttest_rel(data1[:min_len], data2[:min_len])
            self.state.add_paired_annotation({"box_pair": (col1, col2), "p_value": p_value})
            result_text = format_paired_test_result(
                title="Paired t-test results:",
                col1=col1,
                col2=col2,
                statistic_label="t-statistic",
                statistic_value=t_stat,
                p_value=p_value,
                col1_mean=data1.mean(),
                col2_mean=data2.mean(),
            )
            self._show_results(result_text, update_graph=True)
        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to perform paired t-test: {e}")

    def perform_wilcoxon_test(self):
        if not self._ensure_model_loaded():
            return
        df = self.main.model._data
        selection = choose_paired_columns(self.main, WilcoxonDialog, df.columns)
        if selection is None:
            return
        col1, col2 = selection.col1, selection.col2
        try:
            data1 = df[col1].dropna()
            data2 = df[col2].dropna()
            min_len = min(len(data1), len(data2))
            if min_len < 2:
                QMessageBox.warning(self.main, "Warning", "Not enough paired data to perform the test.")
                return

            diff = data1[:min_len] - data2[:min_len]
            nonzero_diff_indices = diff[diff != 0].index
            if len(nonzero_diff_indices) < 1:
                QMessageBox.warning(self.main, "Warning", "No non-zero differences found between the two columns.")
                return

            stat, p_value = wilcoxon(data1.loc[nonzero_diff_indices], data2.loc[nonzero_diff_indices])
            self.state.add_paired_annotation({"box_pair": (col1, col2), "p_value": p_value})
            result_text = format_paired_test_result(
                title="Wilcoxon Signed-rank test results:",
                col1=col1,
                col2=col2,
                statistic_label="W-statistic",
                statistic_value=stat,
                p_value=p_value,
                note=f"(n={len(nonzero_diff_indices)} pairs with non-zero difference)",
            )
            self._show_results(result_text, update_graph=True)
        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to perform Wilcoxon test: {e}")
