from __future__ import annotations

import warnings

from ..dialogs.anova_dialog import AnovaDialog

warnings.warn(
    "calcite.handlers.statistical_dialog_adapters is legacy Python UI scaffolding kept for parity checks.",
    DeprecationWarning,
    stacklevel=2,
)


def choose_group_list(parent, dialog_class, x_values, hue_values, group_col, hue_col, minimum_size, warning_text):
    dialog = dialog_class(x_values, hue_values, group_col, hue_col, parent)
    if not dialog.exec():
        return None
    selected_groups = dialog.get_settings()
    if not selected_groups or len(selected_groups) < minimum_size:
        return None
    return selected_groups
