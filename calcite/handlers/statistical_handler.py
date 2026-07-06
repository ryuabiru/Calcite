from __future__ import annotations

from .statistical_association_handler import StatisticalAssociationHandler
from .statistical_group_handler import StatisticalGroupHandler
from .statistical_paired_handler import StatisticalPairedHandler


class StatisticalHandler:
    def __init__(self, main_window):
        self.group_handler = StatisticalGroupHandler(main_window)
        self.paired_handler = StatisticalPairedHandler(main_window)
        self.association_handler = StatisticalAssociationHandler(main_window)

    def perform_t_test(self):
        self.group_handler.perform_t_test()

    def perform_mannwhitney_test(self):
        self.group_handler.perform_mannwhitney_test()

    def perform_one_way_anova(self):
        self.group_handler.perform_one_way_anova()

    def perform_kruskal_test(self):
        self.group_handler.perform_kruskal_test()

    def perform_shapiro_test(self):
        self.group_handler.perform_shapiro_test()

    def perform_paired_t_test(self):
        self.paired_handler.perform_paired_t_test()

    def perform_wilcoxon_test(self):
        self.paired_handler.perform_wilcoxon_test()

    def perform_chi_squared_test(self):
        self.association_handler.perform_chi_squared_test()

    def perform_two_proportion_test(self):
        self.association_handler.perform_two_proportion_test()

    def perform_pearson_correlation(self):
        self.association_handler.perform_pearson_correlation()

    def perform_spearman_correlation(self):
        self.association_handler.perform_spearman_correlation()

    def perform_regression(self):
        self.association_handler.perform_regression()
