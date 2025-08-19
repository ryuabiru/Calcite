# restructure_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QLineEdit, 
    QPushButton, QDialogButtonBox, QAbstractItemView
)

class RestructureDialog(QDialog):
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Restructure Data (Wide to Long)")
        self.setMinimumSize(600, 400)

        # --- Layouts ---
        main_layout = QVBoxLayout(self)
        columns_layout = QHBoxLayout()
        
        # --- Widgets ---
        self.all_columns_list = QListWidget()
        self.all_columns_list.addItems(columns)
        self.all_columns_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self.id_vars_list = QListWidget()
        self.id_vars_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self.value_vars_list = QListWidget()
        self.value_vars_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        # Buttons to move items between lists
        add_id_button = QPushButton(">>\nAdd ID")
        remove_id_button = QPushButton("<<\nRemove ID")
        add_value_button = QPushButton(">>\nAdd Value")
        remove_value_button = QPushButton("<<\nRemove Value")

        # New column name inputs
        self.var_name_input = QLineEdit("Replicate")
        self.value_name_input = QLineEdit("Value")

        # OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        # --- Assemble Layout ---
        # Left side (all columns)
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("All Columns:"))
        left_panel.addWidget(self.all_columns_list)
        
        # Middle (buttons for ID vars)
        id_buttons_panel = QVBoxLayout()
        id_buttons_panel.addStretch()
        id_buttons_panel.addWidget(add_id_button)
        id_buttons_panel.addWidget(remove_id_button)
        id_buttons_panel.addStretch()

        # Right side (ID and Value vars)
        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("Identifier Columns (won't be changed):"))
        right_panel.addWidget(self.id_vars_list)

        value_buttons_panel = QVBoxLayout()
        value_buttons_panel.addStretch()
        value_buttons_panel.addWidget(add_value_button)
        value_buttons_panel.addWidget(remove_value_button)
        value_buttons_panel.addStretch()
        
        right_panel.addWidget(QLabel("Value Columns (will be gathered):"))
        right_panel.addWidget(self.value_vars_list)
        
        columns_layout.addLayout(left_panel)
        columns_layout.addLayout(id_buttons_panel)
        columns_layout.addLayout(right_panel)
        columns_layout.insertLayout(2, value_buttons_panel) # Insert value buttons

        main_layout.addLayout(columns_layout)
        main_layout.addWidget(QLabel("New column name for variables:"))
        main_layout.addWidget(self.var_name_input)
        main_layout.addWidget(QLabel("New column name for values:"))
        main_layout.addWidget(self.value_name_input)
        main_layout.addWidget(button_box)

        # --- Connect Signals ---
        add_id_button.clicked.connect(lambda: self.move_items(self.all_columns_list, self.id_vars_list))
        remove_id_button.clicked.connect(lambda: self.move_items(self.id_vars_list, self.all_columns_list))
        add_value_button.clicked.connect(lambda: self.move_items(self.all_columns_list, self.value_vars_list))
        remove_value_button.clicked.connect(lambda: self.move_items(self.value_vars_list, self.all_columns_list))
        
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def move_items(self, source_list, dest_list):
        for item in source_list.selectedItems():
            dest_list.addItem(source_list.takeItem(source_list.row(item)))

    def get_settings(self):
        id_vars = [self.id_vars_list.item(i).text() for i in range(self.id_vars_list.count())]
        value_vars = [self.value_vars_list.item(i).text() for i in range(self.value_vars_list.count())]
        return {
            "id_vars": id_vars,
            "value_vars": value_vars,
            "var_name": self.var_name_input.text(),
            "value_name": self.value_name_input.text(),
        }