# paired_plot_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QComboBox, QDialogButtonBox
)

class PairedPlotDialog(QDialog):
    """
    ペアード散布図を描画するための設定を行うダイアログ。
    比較したい2つのカラム（例: Before, After）を選択させる。
    """
    def __init__(self, columns, parent=None):
        """
        ダイアログのUIを初期化する。

        Args:
            columns (list): DataFrameのカラム名のリスト。
            parent (QWidget, optional): 親ウィジェット。
        """
        super().__init__(parent)
        self.setWindowTitle("Paired Scatter Plot")

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # --- ウィジェットの作成 ---
        self.col1_combo = QComboBox()
        self.col2_combo = QComboBox()
        
        # ドロップダウンリストにカラム名を設定
        self.col1_combo.addItems(columns)
        self.col2_combo.addItems(columns)
        
        # OK/Cancelボタン
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        # --- レイアウトの組み立て ---
        form_layout.addRow(QLabel("Column 1 (e.g., Before):"), self.col1_combo)
        form_layout.addRow(QLabel("Column 2 (e.g., After):"), self.col2_combo)
        
        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)

        # --- シグナルの接続 ---
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def get_settings(self) -> dict:
        """
        ユーザーがダイアログで設定した内容を取得する。

        Returns:
            dict: 選択された2つのカラム名を含む辞書。
        """
        return {
            "col1": self.col1_combo.currentText(),
            "col2": self.col2_combo.currentText(),
        }