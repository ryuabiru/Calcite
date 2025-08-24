# tabs/format_tab.py

from PySide6.QtWidgets import (
    QWidget, QFormLayout, QLabel, QComboBox, QPushButton, QColorDialog,
    QScrollArea, QCheckBox, QSpinBox, QDoubleSpinBox, QVBoxLayout, QLineEdit
)
from PySide6.QtCore import Signal
from functools import partial
import seaborn as sns

class FormatTab(QWidget):
    """フォーマット設定タブのUIとロジック"""
    propertiesChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_color = None
        self.current_marker_edgecolor = 'black'
        self.current_bar_edgecolor = 'black'
        self.subgroup_colors = {}
        self.subgroup_widgets = {}

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        main_widget = QWidget()
        scroll_area.setWidget(main_widget)
        
        layout = QFormLayout(main_widget)
        
        layout.addRow(QLabel("<b>Graph Style Settings</b>"))
        self.spines_check = QCheckBox("Remove Top/Right Axis Lines")
        self.spines_check.setChecked(True)
        layout.addRow(self.spines_check)
        layout.addRow(QLabel("---"))

        layout.addRow(QLabel("<b>Overlays</b>"))
        self.scatter_overlay_check = QCheckBox("Show individual points (on Bar/Box/Violin)")
        layout.addRow(self.scatter_overlay_check)

        layout.addRow(QLabel("---"))
        
        layout.addRow(QLabel("<b>Legend</b>"))
        self.legend_pos_combo = QComboBox()
        positions = {
            "Automatic (Upper Right)": "best", # デフォルトの挙動をこちらで制御
            "Upper Right": "upper right",
            "Upper Left": "upper left",
            "Lower Right": "lower right",
            "Lower Left": "lower left",
        }
        for name, key in positions.items():
            self.legend_pos_combo.addItem(name, key)
        self.legend_title_edit = QLineEdit()

        layout.addRow(QLabel("Position:"), self.legend_pos_combo)
        layout.addRow(QLabel("Title:"), self.legend_title_edit)
        layout.addRow(QLabel("---"))

        # ... (以降のコードは変更なし) ...
        layout.addRow(QLabel("<b>Marker Settings (for Scatter/Overlays)</b>"))
        self.marker_combo = QComboBox()
        markers = {'Circle': 'o', 'Square': 's', 'Triangle': '^', 'Diamond': 'D', 'None': 'None'}
        for name, style in markers.items():
            self.marker_combo.addItem(name, style)
        layout.addRow(QLabel("Marker Style:"), self.marker_combo)
        
        self.marker_edgecolor_button = QPushButton("Select Color")
        self.marker_edgecolor_button.setStyleSheet(f"background-color: {self.current_marker_edgecolor};")
        layout.addRow(QLabel("Marker Edge Color:"), self.marker_edgecolor_button)

        self.marker_edgewidth_spin = QDoubleSpinBox()
        self.marker_edgewidth_spin.setRange(0, 10); self.marker_edgewidth_spin.setSingleStep(0.5); self.marker_edgewidth_spin.setValue(1.0)
        layout.addRow(QLabel("Marker Edge Width:"), self.marker_edgewidth_spin)
        layout.addRow(QLabel("---"))
        
        layout.addRow(QLabel("<b>Bar Chart Settings</b>"))
        self.bar_edgecolor_button = QPushButton("Select Color")
        self.bar_edgecolor_button.setStyleSheet(f"background-color: {self.current_bar_edgecolor};")
        layout.addRow(QLabel("Bar Edge Color:"), self.bar_edgecolor_button)

        self.bar_edgewidth_spin = QDoubleSpinBox()
        self.bar_edgewidth_spin.setRange(0, 10); self.bar_edgewidth_spin.setSingleStep(0.5); self.bar_edgewidth_spin.setValue(1.0)
        layout.addRow(QLabel("Bar Edge Width:"), self.bar_edgewidth_spin)

        self.capsize_spin = QSpinBox()
        self.capsize_spin.setRange(0, 20); self.capsize_spin.setValue(4)
        layout.addRow(QLabel("Error Bar Cap Size:"), self.capsize_spin)
        layout.addRow(QLabel("---"))

        layout.addRow(QLabel("<b>Regression Line Settings</b>"))
        self.linestyle_combo = QComboBox()
        linestyles = {'Solid': '-', 'Dashed': '--', 'Dotted': ':', 'Dash-Dot': '-.'}
        for name, style in linestyles.items():
            self.linestyle_combo.addItem(name, style)
        layout.addRow(QLabel("Line Style:"), self.linestyle_combo)

        self.linewidth_spin = QDoubleSpinBox()
        self.linewidth_spin.setRange(0.5, 10.0); self.linewidth_spin.setSingleStep(0.5); self.linewidth_spin.setValue(1.5)
        layout.addRow(QLabel("Line Width:"), self.linewidth_spin)
        layout.addRow(QLabel("---"))

        layout.addRow(QLabel("<b>Color Settings</b>"))
        self.single_color_button = QPushButton("Select Color")
        layout.addRow(QLabel("Graph Color (Single):"), self.single_color_button)
        self.subgroup_color_layout = QFormLayout()
        layout.addRow(QLabel("Graph Color (Sub-group):"))
        layout.addRow(self.subgroup_color_layout)

        outer_layout = QVBoxLayout(self)
        outer_layout.addWidget(scroll_area)
        
        self.connect_signals()

    def connect_signals(self):
        self.spines_check.stateChanged.connect(self.propertiesChanged.emit)
        self.scatter_overlay_check.stateChanged.connect(self.propertiesChanged.emit)
        self.legend_pos_combo.currentIndexChanged.connect(self.propertiesChanged.emit)
        self.legend_title_edit.editingFinished.connect(self.propertiesChanged.emit)
        self.marker_combo.currentIndexChanged.connect(self.propertiesChanged.emit)
        self.linestyle_combo.currentIndexChanged.connect(self.propertiesChanged.emit)
        self.marker_edgewidth_spin.valueChanged.connect(self.propertiesChanged.emit)
        self.bar_edgewidth_spin.valueChanged.connect(self.propertiesChanged.emit)
        self.capsize_spin.valueChanged.connect(self.propertiesChanged.emit)
        self.linewidth_spin.valueChanged.connect(self.propertiesChanged.emit)
        self.single_color_button.clicked.connect(self.open_single_color_dialog)
        self.marker_edgecolor_button.clicked.connect(self.open_marker_edgecolor_dialog)
        self.bar_edgecolor_button.clicked.connect(self.open_bar_edgecolor_dialog)

    def get_properties(self):
        return {
            'hide_top_right_spines': self.spines_check.isChecked(),
            'scatter_overlay': self.scatter_overlay_check.isChecked(),
            'legend_position': self.legend_pos_combo.currentData(),
            'legend_title': self.legend_title_edit.text(),
            'marker_style': self.marker_combo.currentData(),
            'marker_edgecolor': self.current_marker_edgecolor,
            'marker_edgewidth': self.marker_edgewidth_spin.value(),
            'bar_edgecolor': self.current_bar_edgecolor,
            'bar_edgewidth': self.bar_edgewidth_spin.value(),
            'capsize': self.capsize_spin.value(),
            'linestyle': self.linestyle_combo.currentData(),
            'linewidth': self.linewidth_spin.value(),
            'single_color': self.current_color,
            'subgroup_colors': self.subgroup_colors,
        }

    def open_single_color_dialog(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.current_color = color.name()
            self.single_color_button.setStyleSheet(f"background-color: {self.current_color};")
            self.propertiesChanged.emit()
            
    def open_marker_edgecolor_dialog(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.current_marker_edgecolor = color.name()
            self.marker_edgecolor_button.setStyleSheet(f"background-color: {self.current_marker_edgecolor};")
            self.propertiesChanged.emit()

    def open_bar_edgecolor_dialog(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.current_bar_edgecolor = color.name()
            self.bar_edgecolor_button.setStyleSheet(f"background-color: {self.current_bar_edgecolor};")
            self.propertiesChanged.emit()

    def open_subgroup_color_dialog(self, category):
        color = QColorDialog.getColor()
        if color.isValid():
            color_name = color.name()
            self.subgroup_colors[category] = color_name
            if category in self.subgroup_widgets:
                self.subgroup_widgets[category].setStyleSheet(f"background-color: {color_name};")
            self.propertiesChanged.emit()

    def update_subgroup_color_ui(self, categories):
        while self.subgroup_color_layout.count():
            item = self.subgroup_color_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.subgroup_widgets.clear()
        
        if categories:
            default_colors = sns.color_palette(n_colors=len(categories))
            hex_colors = [f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}" for r, g, b in default_colors]
        else:
            hex_colors = []

        for i, category in enumerate(categories):
            str_category = str(category)
            if str_category not in self.subgroup_colors:
                self.subgroup_colors[str_category] = hex_colors[i]
        
        current_categories_str = {str(c) for c in categories}
        for key in list(self.subgroup_colors.keys()):
            if key not in current_categories_str:
                del self.subgroup_colors[key]

        for category in categories:
            str_category = str(category)
            button = QPushButton("Select Color")
            if str_category in self.subgroup_colors:
                button.setStyleSheet(f"background-color: {self.subgroup_colors[str_category]};")
            
            button.clicked.connect(partial(self.open_subgroup_color_dialog, str_category))
            self.subgroup_color_layout.addRow(QLabel(f"{str_category}:"), button)
            self.subgroup_widgets[str_category] = button