# tabs/axes_tab.py
from PySide6.QtWidgets import (
    QWidget, QFormLayout, QLabel, QLineEdit, 
    QHBoxLayout, QCheckBox, QScrollArea, QVBoxLayout, QGroupBox
)
from PySide6.QtGui import QDoubleValidator

from .format_tab import NoScrollComboBox, NoScrollDoubleSpinBox

class AxesTab(QWidget):
    """軸設定タブのUIとロジック"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        main_widget = QWidget()
        scroll_area.setWidget(main_widget)

        main_layout = QVBoxLayout(main_widget)
        
        # --- 軸範囲グループ ---
        range_group = QGroupBox("Axis Range")
        range_layout = QFormLayout(range_group)
        
        validator = QDoubleValidator()
        
        self.xmin_edit = QLineEdit(); self.xmin_edit.setValidator(validator)
        self.xmax_edit = QLineEdit(); self.xmax_edit.setValidator(validator)
        self.ymin_edit = QLineEdit(); self.ymin_edit.setValidator(validator)
        self.ymax_edit = QLineEdit(); self.ymax_edit.setValidator(validator)
        
        x_range_layout = QHBoxLayout()
        x_range_layout.addWidget(self.xmin_edit); x_range_layout.addWidget(QLabel("to")); x_range_layout.addWidget(self.xmax_edit)
        y_range_layout = QHBoxLayout()
        y_range_layout.addWidget(self.ymin_edit); y_range_layout.addWidget(QLabel("to")); y_range_layout.addWidget(self.ymax_edit)
        
        range_layout.addRow(QLabel("X-Axis Range:"), x_range_layout)
        range_layout.addRow(QLabel("Y-Axis Range:"), y_range_layout)
        main_layout.addWidget(range_group)

        # --- スケールとグリッドグループ ---
        scale_grid_group = QGroupBox("Scale & Grid")
        scale_grid_layout = QFormLayout(scale_grid_group)
        
        self.grid_check = QCheckBox("Show Grid")
        scale_grid_layout.addRow(self.grid_check)
        
        self.x_log_scale_check = QCheckBox("Logarithmic Scale")
        self.y_log_scale_check = QCheckBox("Logarithmic Scale")
        
        scale_grid_layout.addRow(QLabel("X-Axis Scale:"), self.x_log_scale_check)
        scale_grid_layout.addRow(QLabel("Y-Axis Scale:"), self.y_log_scale_check)
        main_layout.addWidget(scale_grid_group)

        # --- 軸と目盛りのスタイルグループ ---
        style_group = QGroupBox("Axis & Tick Style")
        style_layout = QFormLayout(style_group)

        self.axis_linewidth_spin = NoScrollDoubleSpinBox()
        self.axis_linewidth_spin.setRange(0.5, 5.0); self.axis_linewidth_spin.setSingleStep(0.1); self.axis_linewidth_spin.setValue(1.0)
        style_layout.addRow(QLabel("Axis Line Width:"), self.axis_linewidth_spin)

        self.tick_length_spin = NoScrollDoubleSpinBox()
        self.tick_length_spin.setRange(0, 20); self.tick_length_spin.setSingleStep(0.5); self.tick_length_spin.setValue(4.0)
        style_layout.addRow(QLabel("Tick Length:"), self.tick_length_spin)

        self.tick_direction_combo = NoScrollComboBox()
        self.tick_direction_combo.addItem("Out", "out")
        self.tick_direction_combo.addItem("In", "in")
        self.tick_direction_combo.addItem("In & Out", "inout")
        style_layout.addRow(QLabel("Tick Direction:"), self.tick_direction_combo)

        main_layout.addWidget(style_group)

        main_layout.addStretch() # スペーサー

        outer_layout = QVBoxLayout(self)
        outer_layout.addWidget(scroll_area)

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
            'axis_linewidth': self.axis_linewidth_spin.value(),
            'tick_length': self.tick_length_spin.value(),
            'tick_direction': self.tick_direction_combo.currentData(),
        }