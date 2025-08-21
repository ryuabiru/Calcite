# tabs/data_tab.py

from PySide6.QtWidgets import QWidget, QFormLayout, QLabel, QComboBox
from PySide6.QtCore import Signal

class DataTab(QWidget):
    """データ選択タブのUIとロジック"""
    subgroupColumnChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QFormLayout(self)
        
        self.y_axis_combo = QComboBox()
        self.x_axis_combo = QComboBox()
        self.subgroup_combo = QComboBox()
        
        self.subgroup_combo.currentTextChanged.connect(self.subgroupColumnChanged.emit)

        layout.addRow(QLabel("Y-Axis (Value):"), self.y_axis_combo)
        layout.addRow(QLabel("X-Axis (Group):"), self.x_axis_combo)
        layout.addRow(QLabel("Sub-group (Color):"), self.subgroup_combo)

    def set_columns(self, columns):
        """コンボボックスにデータフレームの列名を設定する"""
        current_y = self.y_axis_combo.currentText()
        current_x = self.x_axis_combo.currentText()
        current_sub = self.subgroup_combo.currentText()

        self.y_axis_combo.clear()
        self.x_axis_combo.clear()
        self.subgroup_combo.clear()
        
        self.y_axis_combo.addItem("") 
        self.x_axis_combo.addItem("")
        self.subgroup_combo.addItem("")
        
        self.y_axis_combo.addItems(columns)
        self.x_axis_combo.addItems(columns)
        self.subgroup_combo.addItems(columns)

        self.y_axis_combo.setCurrentText(current_y)
        self.x_axis_combo.setCurrentText(current_x)
        self.subgroup_combo.setCurrentText(current_sub)

    def get_properties(self):
        """このタブの設定値を取得する"""
        return {
            'y_col': self.y_axis_combo.currentText(),
            'x_col': self.x_axis_combo.currentText(),
            'subgroup_col': self.subgroup_combo.currentText()
        }