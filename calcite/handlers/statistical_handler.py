from __future__ import annotations

import warnings

from .statistical_group_handler import StatisticalGroupHandler


class StatisticalHandler:
    def __init__(self, main_window):
        warnings.warn(
            "calcite.handlers.statistical_* is legacy Python analysis scaffolding kept for parity checks.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.group_handler = StatisticalGroupHandler(main_window)

    def perform_one_way_anova(self):
        self.group_handler.perform_one_way_anova()

    def perform_shapiro_test(self):
        self.group_handler.perform_shapiro_test()
