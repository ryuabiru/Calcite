# anova_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QComboBox, QDialogButtonBox
)

class AnovaDialog(QDialog):
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("One-way ANOVA")

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # --- Widgets ---
        self.value_column_combo = QComboBox()
        self.group_column_combo = QComboBox()
        
        self.value_column_combo.addItems(columns)
        self.group_column_combo.addItems(columns)
        
        # OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        # --- Assemble Layout ---
        form_layout.addRow(QLabel("Value Column (Dependent Variable):"), self.value_column_combo)
        form_layout.addRow(QLabel("Group Column (Independent Variable):"), self.group_column_combo)
        
        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)

        # --- Connect Signals ---
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def get_settings(self):
        return {
            "value_col": self.value_column_combo.currentText(),
            "group_col": self.group_column_combo.currentText(),
        }