# dialogs/filter_dialog.py (新規作成)

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QComboBox, QLineEdit,
    QDialogButtonBox
)
import pandas as pd

class FilterDialog(QDialog):
    """
    データフレームをフィルタリングするための条件を設定するダイアログ。
    """
    def __init__(self, df, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Filter Data")
        self.df = df

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # --- Widgets ---
        self.column_combo = QComboBox()
        self.operator_combo = QComboBox()
        self.value_input = QLineEdit()
        
        self.column_combo.addItems(df.columns)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        # --- Assemble Layout ---
        form_layout.addRow(QLabel("Column:"), self.column_combo)
        form_layout.addRow(QLabel("Condition:"), self.operator_combo)
        form_layout.addRow(QLabel("Value:"), self.value_input)
        
        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)

        # --- Connect Signals ---
        self.column_combo.currentTextChanged.connect(self.update_operators)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # --- Initialize ---
        self.update_operators(self.column_combo.currentText())

    def update_operators(self, column_name):
        """選択されたカラムのデータ型に応じて、利用可能な演算子を更新する"""
        self.operator_combo.clear()
        if not column_name or column_name not in self.df.columns:
            return

        dtype = self.df[column_name].dtype
        
        if pd.api.types.is_numeric_dtype(dtype):
            operators = {
                "equals": "==",
                "not equal": "!=",
                "greater than": ">",
                "less than": "<",
                "greater than or equal to": ">=",
                "less than or equal to": "<="
            }
        else: # String or other types
            operators = {
                "equals": "==",
                "not equal": "!=",
                "contains": "contains",
                "does not contain": "not contains",
                "starts with": "startswith",
                "ends with": "endswith"
            }
        
        for name, key in operators.items():
            self.operator_combo.addItem(name, key)

    def get_settings(self):
        """ダイアログでユーザーが入力した設定を辞書として返す"""
        column = self.column_combo.currentText()
        operator = self.operator_combo.currentData()
        value = self.value_input.text()
        
        # 数値カラムの場合は、入力値を数値に変換しようと試みる
        if pd.api.types.is_numeric_dtype(self.df[column].dtype):
            try:
                value = float(value)
            except ValueError:
                # 変換に失敗した場合はNoneを返し、エラーハンドリングを上位に任せる
                return None
        
        return {
            "column": column,
            "operator": operator,
            "value": value
        }