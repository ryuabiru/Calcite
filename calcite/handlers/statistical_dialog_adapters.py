from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import QMessageBox

from ..dialogs.anova_dialog import AnovaDialog
from ..dialogs.contingency_dialog import ContingencyDialog
from ..dialogs.correlation_dialog import CorrelationDialog
from ..dialogs.kruskal_dialog import KruskalDialog
from ..dialogs.mannwhitney_dialog import MannWhitneyDialog
from ..dialogs.paired_ttest_dialog import PairedTTestDialog
from ..dialogs.regression_dialog import RegressionDialog
from ..dialogs.ttest_dialog import TTestDialog
from ..dialogs.wilcoxon_dialog import WilcoxonDialog


@dataclass(frozen=True)
class GroupPairSelection:
    group1: dict
    group2: dict


@dataclass(frozen=True)
class PairedColumnsSelection:
    col1: str
    col2: str


@dataclass(frozen=True)
class CorrelationSelection:
    col1: str
    col2: str


@dataclass(frozen=True)
class ContingencySelection:
    rows_col: str
    cols_col: str


@dataclass(frozen=True)
class RegressionSelection:
    x_col: str
    y_col: str
    model: str


def choose_group_pair(parent, dialog_class, x_values, hue_values, group_col, hue_col):
    dialog = dialog_class(x_values=x_values, hue_values=hue_values, x_name=group_col, hue_name=hue_col, parent=parent)
    if not dialog.exec():
        return None
    settings = dialog.get_settings()
    if not settings:
        return None
    group1 = settings["group1"]
    group2 = settings["group2"]
    if group1 == group2:
        QMessageBox.warning(parent, "Warning", "Please select two different groups.")
        return None
    return GroupPairSelection(group1=group1, group2=group2)


def choose_group_list(parent, dialog_class, x_values, hue_values, group_col, hue_col, minimum_size, warning_text):
    dialog = dialog_class(x_values, hue_values, group_col, hue_col, parent)
    if not dialog.exec():
        return None
    selected_groups = dialog.get_settings()
    if not selected_groups or len(selected_groups) < minimum_size:
        QMessageBox.warning(parent, "Warning", warning_text)
        return None
    return selected_groups


def choose_paired_columns(parent, dialog_class, columns):
    dialog = dialog_class(columns, parent)
    if not dialog.exec():
        return None
    settings = dialog.get_settings()
    col1, col2 = settings["col1"], settings["col2"]
    if not col1 or not col2 or col1 == col2:
        QMessageBox.warning(parent, "Warning", "Please select two different columns.")
        return None
    return PairedColumnsSelection(col1=col1, col2=col2)


def choose_correlation_columns(parent, columns):
    dialog = CorrelationDialog(columns, parent)
    if not dialog.exec():
        return None
    settings = dialog.get_settings()
    col1, col2 = settings["col1"], settings["col2"]
    if not col1 or not col2 or col1 == col2:
        QMessageBox.warning(parent, "Warning", "Please select two different columns.")
        return None
    return CorrelationSelection(col1=col1, col2=col2)


def choose_contingency_columns(parent, columns):
    dialog = ContingencyDialog(columns, parent)
    if not dialog.exec():
        return None
    settings = dialog.get_settings()
    rows_col, cols_col = settings["rows_col"], settings["cols_col"]
    if not rows_col or not cols_col or rows_col == cols_col:
        return None
    return ContingencySelection(rows_col=rows_col, cols_col=cols_col)


def choose_regression_settings(parent, columns):
    dialog = RegressionDialog(columns, parent)
    if not dialog.exec():
        return None
    settings = dialog.get_settings()
    x_col, y_col, model = settings["x_col"], settings["y_col"], settings["model"]
    if not x_col or not y_col:
        QMessageBox.warning(parent, "Warning", "Please select both X and Y columns.")
        return None
    return RegressionSelection(x_col=x_col, y_col=y_col, model=model)
