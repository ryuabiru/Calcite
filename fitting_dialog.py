# fitting_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QComboBox, QDialogButtonBox
)

class FittingDialog(QDialog):
    """
    非線形回帰分析のための設定を行うダイアログ。
    X軸・Y軸の列と、使用するフィッティングモデルを選択させる。
    """
    def __init__(self, columns, parent=None):
        """
        ダイアログのUIを初期化する。

        Args:
            columns (list): DataFrameのカラム名のリスト。
            parent (QWidget, optional): 親ウィジェット。
        """
        super().__init__(parent)
        self.setWindowTitle("Non-linear Regression")

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # --- ウィジェットの作成 ---
        self.x_column_combo = QComboBox()
        self.y_column_combo = QComboBox()
        self.model_combo = QComboBox()

        # ドロップダウンリストにカラム名を設定
        self.x_column_combo.addItems(columns)
        self.y_column_combo.addItems(columns)
        
        # フィッティングモデルの選択肢を追加（現在はシグモイド曲線のみ）
        self.model_combo.addItem("Sigmoidal (4PL)", "4pl")

        # OK/Cancelボタン
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        # --- レイアウトの組み立て ---
        form_layout.addRow(QLabel("X-Axis Column (Concentration):"), self.x_column_combo)
        form_layout.addRow(QLabel("Y-Axis Column (Response):"), self.y_column_combo)
        form_layout.addRow(QLabel("Fitting Model:"), self.model_combo)
        
        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)

        # --- シグナルの接続 ---
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def get_settings(self) -> dict:
        """
        ユーザーがダイアログで設定した内容を取得する。

        Returns:
            dict: X軸の列名、Y軸の列名、選択されたモデルの内部名を含む辞書。
        """
        return {
            "x_col": self.x_column_combo.currentText(),
            "y_col": self.y_column_combo.currentText(),
            "model": self.model_combo.currentData(),
        }