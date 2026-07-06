from __future__ import annotations

from .action_data_handler import ActionDataHandler
from .action_file_handler import ActionFileHandler
from .action_misc_handler import ActionMiscHandler
from .action_table_handler import ActionTableHandler
from .statistical_handler import StatisticalHandler


class ActionHandler:
    def __init__(self, main_window):
        self.file_handler = ActionFileHandler(main_window)
        self.data_handler = ActionDataHandler(main_window)
        self.table_handler = ActionTableHandler(main_window)
        self.misc_handler = ActionMiscHandler(main_window)
        self.statistical_handler = StatisticalHandler(main_window)

    def save_table_as_csv(self):
        self.misc_handler.save_table_as_csv()

    def open_csv_file(self):
        self.file_handler.open_csv_file()

    def paste_from_clipboard(self):
        self.file_handler.paste_from_clipboard()

    def save_project(self):
        self.file_handler.save_project()

    def open_project(self):
        self.file_handler.open_project()

    def show_calculate_dialog(self):
        self.data_handler.show_calculate_dialog()

    def calculate_new_column(self, settings):
        self.data_handler.calculate_new_column(settings)

    def show_restructure_dialog(self):
        self.data_handler.show_restructure_dialog()

    def restructure_data(self, settings):
        self.data_handler.restructure_data(settings)

    def show_pivot_dialog(self):
        self.data_handler.show_pivot_dialog()

    def pivot_data(self, settings):
        self.data_handler.pivot_data(settings)

    def show_advanced_filter_dialog(self):
        self.data_handler.show_advanced_filter_dialog()

    def apply_advanced_filter(self, settings):
        self.data_handler.apply_advanced_filter(settings)

    def create_table_from_selection(self):
        self.table_handler.create_table_from_selection()

    def show_license_dialog(self):
        self.misc_handler.show_license_dialog()

    def export_analysis_results(self):
        self.misc_handler.export_analysis_results()
