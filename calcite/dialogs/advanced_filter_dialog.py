# dialogs/advanced_filter_dialog.py (新規作成)

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QComboBox, QLineEdit,
    QDialogButtonBox, QPushButton, QWidget, QScrollArea
)
import pandas as pd

class FilterConditionWidget(QWidget):
    """
    フィルター条件一行分を管理するUIウィジェット。
    """
    def __init__(self, df, parent=None):
        super().__init__(parent)
        self.df = df
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.and_or_combo = QComboBox()
        self.and_or_combo.addItems(["AND", "OR"])
        
        self.column_combo = QComboBox()
        self.column_combo.addItems(df.columns)
        
        self.operator_combo = QComboBox()
        self.value_input = QLineEdit()

        self.remove_button = QPushButton(" - ")

        layout.addWidget(self.and_or_combo)
        layout.addWidget(self.column_combo)
        layout.addWidget(self.operator_combo)
        layout.addWidget(self.value_input)
        layout.addWidget(self.remove_button)

        self.column_combo.currentTextChanged.connect(self.update_operators)
        self.update_operators(self.column_combo.currentText())
        
        self.and_or_combo.setVisible(False)


    def update_operators(self, column_name):
        
        self.operator_combo.clear()
        if not column_name or column_name not in self.df.columns: return
        dtype = self.df[column_name].dtype
        
        operators = {"equals": "==", "not equal": "!="}
        
        if pd.api.types.is_numeric_dtype(dtype):
            operators.update({
                "greater than": ">", "less than": "<",
                "greater than or equal to": ">=", "less than or equal to": "<="
            })
        else:
            operators.update({
                "contains": "contains", "does not contain": "not contains",
                "starts with": "startswith", "ends with": "endswith"
            })
        
        for name, key in operators.items():
            self.operator_combo.addItem(name, key)
            
    
    def get_condition(self):
        """この行の設定を辞書として返す"""
        return {
            "connector": self.and_or_combo.currentText().lower(),
            "column": self.column_combo.currentText(),
            "operator": self.operator_combo.currentData(),
            "value": self.value_input.text()
        }


class AdvancedFilterDialog(QDialog):
    """
    複数のフィルター条件を組み合わせるための高度なダイアログ。
    """
    def __init__(self, df, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Advanced Filter")
        self.setMinimumWidth(600)
        self.setMinimumHeight(200)
        self.df = df
        self.condition_widgets = []

        main_layout = QVBoxLayout(self)
        
        # スクロール可能なエリアを作成
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.conditions_layout = QVBoxLayout(self.scroll_content)
        scroll_area.setWidget(self.scroll_content)

        add_button = QPushButton(" + Add Condition")
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        main_layout.addWidget(scroll_area)
        main_layout.addWidget(add_button)
        main_layout.addWidget(button_box)

        add_button.clicked.connect(self.add_condition_row)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        self.add_condition_row() # 最初に一行追加しておく


    def add_condition_row(self):
        
        is_first_row = len(self.condition_widgets) == 0
        condition_widget = FilterConditionWidget(self.df)
        
        if not is_first_row:
            condition_widget.and_or_combo.setVisible(True)
            
        condition_widget.remove_button.clicked.connect(
            lambda: self.remove_condition_row(condition_widget)
        )
        
        self.conditions_layout.addWidget(condition_widget)
        self.condition_widgets.append(condition_widget)

        
    def remove_condition_row(self, widget_to_remove):
        
        if len(self.condition_widgets) > 1: # 最後の1行は消させない
            widget_to_remove.setParent(None)
            widget_to_remove.deleteLater()
            self.condition_widgets.remove(widget_to_remove)


    def get_settings(self):
        """全条件のリストを返す"""
        
        settings = []
        
        for widget in self.condition_widgets:
            condition = widget.get_condition()
            
            # 値が入力されているかチェック
            if not condition['value']:
                return None # 空の値があれば無効な設定とみなす
                
            # 数値カラムの場合は値を変換
            col_name = condition['column']
            if pd.api.types.is_numeric_dtype(self.df[col_name].dtype):
                try:
                    condition['value'] = float(condition['value'])
                except ValueError:
                    return None # 数値変換に失敗したら無効
            
            settings.append(condition)
        return settings