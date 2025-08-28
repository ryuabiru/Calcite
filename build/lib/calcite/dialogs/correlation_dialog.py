# dialogs/correlation_dialog.py (新規作成)

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QComboBox, QDialogButtonBox
)

class CorrelationDialog(QDialog):
    """
    相関分析のために、2つの変数（列）を選択させるダイアログ。
    """
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Correlation Analysis")

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.column1_combo = QComboBox()
        self.column2_combo = QComboBox()
        
        self.column1_combo.addItems(columns)
        self.column2_combo.addItems(columns)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        form_layout.addRow(QLabel("Variable 1:"), self.column1_combo)
        form_layout.addRow(QLabel("Variable 2:"), self.column2_combo)
        
        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def get_settings(self):
        """
        ユーザーが選択した2つの列名を返す。
        """
        return {
            "col1": self.column1_combo.currentText(),
            "col2": self.column2_combo.currentText(),
        }