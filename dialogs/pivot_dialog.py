# pivot_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QComboBox, QDialogButtonBox
)

class PivotDialog(QDialog):
    """
    データフレームをロング形式からワイド形式に再構築するための
    パラメータを取得するダイアログウィンドウ。
    """
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("データ形式の再構築 (Long to Wide)")
        self.setMinimumSize(400, 200)

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # --- ウィジェットの作成 ---
        self.id_vars_combo = QComboBox()
        self.var_name_combo = QComboBox()
        self.value_name_combo = QComboBox()
        
        # ドロップダウンリストにカラム名を設定
        self.id_vars_combo.addItems(columns)
        self.var_name_combo.addItems(columns)
        self.value_name_combo.addItems(columns)
        
        # OK/Cancelボタン
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        # --- レイアウトの組み立て ---
        form_layout.addRow(QLabel("識別子列 (ID):"), self.id_vars_combo)
        form_layout.addRow(QLabel("変数名を持つ列:"), self.var_name_combo)
        form_layout.addRow(QLabel("値を持つ列:"), self.value_name_combo)
        
        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)

        # --- シグナルの接続 ---
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def get_settings(self) -> dict:
        """
        ユーザーがダイアログで設定した内容を取得する。

        Returns:
            dict: 選択されたID、変数、値の列名を含む辞書。
        """
        return {
            "id_vars": self.id_vars_combo.currentText(),
            "var_name": self.var_name_combo.currentText(),
            "value_name": self.value_name_combo.currentText(),
        }