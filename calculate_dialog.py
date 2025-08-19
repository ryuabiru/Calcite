# calculate_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QLineEdit, 
    QPushButton, QDialogButtonBox, QListWidget
)
from PySide6.QtCore import Qt

class CalculateDialog(QDialog):
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Calculate New Column")
        self.setMinimumWidth(400)

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # --- Widgets ---
        self.new_column_name_input = QLineEdit()
        self.formula_input = QLineEdit()
        self.columns_list = QListWidget()
        self.columns_list.addItems(columns)
        
        # OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        # --- Assemble Layout ---
        form_layout.addRow(QLabel("New Column Name:"), self.new_column_name_input)
        form_layout.addRow(QLabel("Formula (e.g., \"Value\" * 100):"), self.formula_input)
        
        main_layout.addLayout(form_layout)
        main_layout.addWidget(QLabel("Available Columns (double-click to insert):"))
        main_layout.addWidget(self.columns_list)
        main_layout.addWidget(button_box)

        # --- Connect Signals ---
        self.columns_list.itemDoubleClicked.connect(self.insert_column_name)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def insert_column_name(self, item):
        # カーソル位置にカラム名を挿入する
        current_text = self.formula_input.text()
        cursor_pos = self.formula_input.cursorPosition()
        # カラム名にスペースが含まれる可能性を考慮し、バッククォートで囲む
        col_name = f"`{item.text()}`"
        new_text = current_text[:cursor_pos] + col_name + current_text[cursor_pos:]
        self.formula_input.setText(new_text)
        self.formula_input.setFocus()
        self.formula_input.setCursorPosition(cursor_pos + len(col_name))

    def get_settings(self):
        return {
            "new_column_name": self.new_column_name_input.text(),
            "formula": self.formula_input.text(),
        }