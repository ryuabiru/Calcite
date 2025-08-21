# tabs/axes_tab.py

from PySide6.QtWidgets import QWidget, QFormLayout, QLabel, QLineEdit, QHBoxLayout, QCheckBox
from PySide6.QtGui import QDoubleValidator

class AxesTab(QWidget):
    """軸設定タブのUIとロジック"""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QFormLayout(self)
        validator = QDoubleValidator()
        
        self.xmin_edit = QLineEdit(); self.xmin_edit.setValidator(validator)
        self.xmax_edit = QLineEdit(); self.xmax_edit.setValidator(validator)
        self.ymin_edit = QLineEdit(); self.ymin_edit.setValidator(validator)
        self.ymax_edit = QLineEdit(); self.ymax_edit.setValidator(validator)
        
        x_range_layout = QHBoxLayout()
        x_range_layout.addWidget(self.xmin_edit); x_range_layout.addWidget(QLabel("to")); x_range_layout.addWidget(self.xmax_edit)
        y_range_layout = QHBoxLayout()
        y_range_layout.addWidget(self.ymin_edit); y_range_layout.addWidget(QLabel("to")); y_range_layout.addWidget(self.ymax_edit)
        
        layout.addRow(QLabel("X-Axis Range:"), x_range_layout)
        layout.addRow(QLabel("Y-Axis Range:"), y_range_layout)
        layout.addRow(QLabel("---"))
        
        self.grid_check = QCheckBox("Show Grid")
        layout.addRow(self.grid_check)
        layout.addRow(QLabel("---"))
        
        self.x_log_scale_check = QCheckBox("Logarithmic Scale")
        self.y_log_scale_check = QCheckBox("Logarithmic Scale")
        
        layout.addRow(QLabel("X-Axis Scale:"), self.x_log_scale_check)
        layout.addRow(QLabel("Y-Axis Scale:"), self.y_log_scale_check)

    def get_properties(self):
        """このタブの設定値を取得する"""
        return {
            'xmin': self.xmin_edit.text(),
            'xmax': self.xmax_edit.text(),
            'ymin': self.ymin_edit.text(),
            'ymax': self.ymax_edit.text(),
            'show_grid': self.grid_check.isChecked(),
            'x_log_scale': self.x_log_scale_check.isChecked(),
            'y_log_scale': self.y_log_scale_check.isChecked(),
        }