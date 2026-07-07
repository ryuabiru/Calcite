from __future__ import annotations

import warnings

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QApplication, QLineEdit

warnings.warn(
    "calcite.main_window_table_interaction is legacy Python UI scaffolding kept for parity checks.",
    DeprecationWarning,
    stacklevel=2,
)


class MainWindowTableInteraction:
    def __init__(self, window):
        self.window = window
        self.header_editor = None

    def edit_header(self, logical_index):
        if self.header_editor:
            self.header_editor.close()
        header = self.window.table_view.horizontalHeader()
        model = self.window.table_view.model()
        self.header_editor = QLineEdit(parent=header)
        self.header_editor.setText(model.headerData(logical_index, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole))
        self.header_editor.setGeometry(
            header.sectionViewportPosition(logical_index), 0, header.sectionSize(logical_index), header.height()
        )
        self.header_editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_editor.editingFinished.connect(lambda: self.finish_header_edit(logical_index))
        self.header_editor.show()
        self.header_editor.setFocus()

    def finish_header_edit(self, logical_index):
        if not self.header_editor:
            return
        new_text = self.header_editor.text()
        model = self.window.table_view.model()
        model.setHeaderData(logical_index, Qt.Orientation.Horizontal, new_text, Qt.ItemDataRole.EditRole)
        self.window.table_controller.sync_columns(model, self.window.data_widget)
        self.header_editor.close()
        self.header_editor = None

    def handle_event_filter(self, source, event):
        if event.type() != QEvent.Type.KeyPress or source is not self.window.table_view:
            return False

        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            current_index = self.window.table_view.currentIndex()
            if current_index.isValid():
                next_index = current_index.model().index(current_index.row() + 1, current_index.column())
                if next_index.isValid():
                    self.window.table_view.setCurrentIndex(next_index)
                    return True

        if event.matches(QKeySequence.StandardKey.Copy):
            self.copy_selection()
            return True

        if event.matches(QKeySequence.StandardKey.Paste):
            self.paste_selection()
            return True

        return False

    def fill_down(self):
        selection_model = self.window.table_view.selectionModel()
        selected_indexes = selection_model.selectedIndexes() if selection_model is not None else []
        self.window.table_controller.fill_down(self.window.model, selected_indexes)

    def copy_selection(self):
        selection_model = self.window.table_view.selectionModel()
        selected_indexes = selection_model.selectedIndexes() if selection_model is not None else []
        if not selected_indexes:
            return
        QApplication.clipboard().setText(self.window.table_controller.build_selection_clipboard_text(selected_indexes))

    def paste_selection(self):
        clipboard_text = QApplication.clipboard().text()
        if not clipboard_text:
            return
        start_index = self.window.table_view.currentIndex()
        if not start_index.isValid():
            return
        self.window.table_controller.paste_into_model(self.window.model, start_index, clipboard_text)

    def on_subgroup_column_changed(self, column_name):
        self.window.table_controller.sync_subgroup_colors(self.window.model, column_name, self.window.properties_widget)

    def insert_row(self):
        self.window.table_controller.insert_row(self.window.model, self.window.table_view.currentIndex())
        self.window.table_controller.sync_columns(self.window.model, self.window.data_widget)

    def remove_row(self):
        selection_model = self.window.table_view.selectionModel()
        selected_rows = [index.row() for index in selection_model.selectedRows()] if selection_model is not None else []
        self.window.table_controller.remove_rows(self.window.model, selected_rows)

    def insert_col(self, left=False):
        self.window.table_controller.insert_column(self.window.model, self.window.table_view.currentIndex(), left)
        self.window.table_controller.sync_columns(self.window.model, self.window.data_widget)

    def remove_col(self):
        selection_model = self.window.table_view.selectionModel()
        selected_cols = [index.column() for index in selection_model.selectedColumns()] if selection_model is not None else []
        self.window.table_controller.remove_columns(self.window.model, selected_cols)
        self.window.table_controller.sync_columns(self.window.model, self.window.data_widget)
