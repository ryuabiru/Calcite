# dialogs/wilcoxon_dialog.py (新規作成)

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QComboBox, QDialogButtonBox
)

class WilcoxonDialog(QDialog):
    """
    ウィルコクソンの符号順位検定のためのダイアログ。
    PairedTTestDialogをベースに作成。
    """
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        # ウィンドウのタイトルを変更
        self.setWindowTitle("Wilcoxon Signed-rank Test")

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.column1_combo = QComboBox()
        self.column2_combo = QComboBox()
        
        self.column1_combo.addItems(columns)
        self.column2_combo.addItems(columns)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        form_layout.addRow(QLabel("Column 1 (e.g., Before):"), self.column1_combo)
        form_layout.addRow(QLabel("Column 2 (e.g., After):"), self.column2_combo)
        
        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def get_settings(self):
        """
        ユーザーがダイアログで設定した内容を取得する（PairedTTestDialogと共通）。
        """
        return {
            "col1": self.column1_combo.currentText(),
            "col2": self.column2_combo.currentText(),
        }