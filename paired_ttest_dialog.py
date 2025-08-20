# paired_ttest_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QComboBox, QDialogButtonBox
)

class PairedTTestDialog(QDialog):
    """
    対応のあるt検定のための設定を行うダイアログ。
    比較する2つの列（例：ビフォー/アフター）を選択させる。
    """
    def __init__(self, columns, parent=None):
        """
        ダイアログのUIを初期化する。
        """
        super().__init__(parent)
        self.setWindowTitle("Paired t-test")

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # --- ウィジェットの作成 ---
        self.column1_combo = QComboBox()
        self.column2_combo = QComboBox()
        
        self.column1_combo.addItems(columns)
        self.column2_combo.addItems(columns)
        
        # OK/Cancelボタン
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        # --- レイアウトの組み立て ---
        form_layout.addRow(QLabel("Column 1 (e.g., Before):"), self.column1_combo)
        form_layout.addRow(QLabel("Column 2 (e.g., After):"), self.column2_combo)
        
        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)

        # --- シグナルの接続 ---
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def get_settings(self):
        """
        ユーザーがダイアログで設定した内容を取得する。
        """
        return {
            "col1": self.column1_combo.currentText(),
            "col2": self.column2_combo.currentText(),
        }