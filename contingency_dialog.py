# contingency_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QComboBox, QDialogButtonBox
)

class ContingencyDialog(QDialog):
    """
    カイ二乗検定のための設定を行うダイアログ。
    分割表の行と列に対応するカラムを選択させる。
    """
    def __init__(self, columns, parent=None):
        """
        ダイアログのUIを初期化する。

        Args:
            columns (list): DataFrameのカラム名のリスト。
            parent (QWidget, optional): 親ウィジェット。
        """
        super().__init__(parent)
        self.setWindowTitle("Chi-squared Test")

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # --- ウィジェットの作成 ---
        self.rows_column_combo = QComboBox()
        self.cols_column_combo = QComboBox()
        
        # ドロップダウンリストにカラム名を設定
        self.rows_column_combo.addItems(columns)
        self.cols_column_combo.addItems(columns)
        
        # OK/Cancelボタン
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        # --- レイアウトの組み立て ---
        form_layout.addRow(QLabel("Rows (Observed Groups):"), self.rows_column_combo)
        form_layout.addRow(QLabel("Columns (Expected Groups):"), self.cols_column_combo)
        
        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)

        # --- シグナルの接続 ---
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def get_settings(self) -> dict:
        """
        ユーザーがダイアログで設定した内容を取得する。

        Returns:
            dict: 行の列名と列の列名を含む辞書。
        """
        return {
            "rows_col": self.rows_column_combo.currentText(),
            "cols_col": self.cols_column_combo.currentText(),
        }