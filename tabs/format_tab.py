# tabs/format_tab.py

from PySide6.QtWidgets import (
    QWidget, QFormLayout, QLabel, QComboBox, QPushButton, QColorDialog,
    QScrollArea, QCheckBox, QSpinBox, QDoubleSpinBox, QVBoxLayout, QGroupBox
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
        
        # ▼▼▼ ここからレイアウト構造を大きく変更 ▼▼▼
        # 全体をまとめる垂直レイアウト
        main_layout = QVBoxLayout(main_widget)

        # --- 1. スタイル設定グループ ---
        style_group = QGroupBox("Graph Style")
        style_layout = QFormLayout(style_group)
        
        self.spines_check = QCheckBox("Remove Top/Right Axis Lines")
        self.spines_check.setChecked(True)
        style_layout.addRow(self.spines_check)
        
        self.scatter_overlay_check = QCheckBox("Show individual points (on Bar/Box/Violin)")
        style_layout.addRow(QLabel("Overlays:"), self.scatter_overlay_check)
        
        main_layout.addWidget(style_group)
        
        # --- 2. グラフ要素グループ ---
        elements_group = QGroupBox("Graph Elements")
        elements_layout = QFormLayout(elements_group)

        # マーカー設定
        elements_layout.addRow(QLabel("<b>Markers (Scatter/Overlays)</b>"))
        self.marker_combo = QComboBox()
        markers = {'Circle': 'o', 'Square': 's', 'Triangle': '^', 'Diamond': 'D', 'None': 'None'}
        for name, style in markers.items():
            self.marker_combo.addItem(name, style)
        elements_layout.addRow(QLabel("Style:"), self.marker_combo)
        
        self.marker_edgecolor_button = QPushButton("Select Color")
        self.marker_edgecolor_button.setStyleSheet(f"background-color: {self.current_marker_edgecolor};")
        elements_layout.addRow(QLabel("Edge Color:"), self.marker_edgecolor_button)

        self.marker_edgewidth_spin = QDoubleSpinBox()
        self.marker_edgewidth_spin.setRange(0, 10); self.marker_edgewidth_spin.setSingleStep(0.5); self.marker_edgewidth_spin.setValue(1.0)
        elements_layout.addRow(QLabel("Edge Width:"), self.marker_edgewidth_spin)
        
        # 棒グラフ設定
        elements_layout.addRow(QLabel("<b>Bar Chart</b>"))
        self.bar_edgecolor_button = QPushButton("Select Color")
        self.bar_edgecolor_button.setStyleSheet(f"background-color: {self.current_bar_edgecolor};")
        elements_layout.addRow(QLabel("Edge Color:"), self.bar_edgecolor_button)

        self.bar_edgewidth_spin = QDoubleSpinBox()
        self.bar_edgewidth_spin.setRange(0, 10); self.bar_edgewidth_spin.setSingleStep(0.5); self.bar_edgewidth_spin.setValue(1.0)
        elements_layout.addRow(QLabel("Edge Width:"), self.bar_edgewidth_spin)

        self.capsize_spin = QSpinBox()
        self.capsize_spin.setRange(0, 20); self.capsize_spin.setValue(4)
        elements_layout.addRow(QLabel("Error Bar Cap Size:"), self.capsize_spin)

        # 線設定
        elements_layout.addRow(QLabel("<b>Line (Regression/Point Plot)</b>"))
        self.linestyle_combo = QComboBox()
        linestyles = {'Solid': '-', 'Dashed': '--', 'Dotted': ':', 'Dash-Dot': '-.'}
        for name, style in linestyles.items():
            self.linestyle_combo.addItem(name, style)
        elements_layout.addRow(QLabel("Style:"), self.linestyle_combo)

        self.linewidth_spin = QDoubleSpinBox()
        self.linewidth_spin.setRange(0.5, 10.0); self.linewidth_spin.setSingleStep(0.5); self.linewidth_spin.setValue(1.5)
        elements_layout.addRow(QLabel("Width:"), self.linewidth_spin)
        
        main_layout.addWidget(elements_group)

        # --- 3. カラー設定グループ ---
        color_group = QGroupBox("Color")
        color_layout = QFormLayout(color_group)
        
        self.single_color_button = QPushButton("Select Color")
        color_layout.addRow(QLabel("Single Color:"), self.single_color_button)
        
        color_layout.addRow(QLabel("<b>Sub-group Colors</b>"))
        self.subgroup_color_layout = QFormLayout() # ここは変更なし
        color_layout.addRow(self.subgroup_color_layout)
        
        main_layout.addWidget(color_group)
        main_layout.addStretch() # スペーサーを追加してUIを上によせる
        # ▲▲▲ ここまで ▲▲▲

        outer_layout = QVBoxLayout(self)
        outer_layout.addWidget(scroll_area)
        
        self.connect_signals()

    def connect_signals(self):
        self.spines_check.stateChanged.connect(self.propertiesChanged.emit)
        self.scatter_overlay_check.stateChanged.connect(self.propertiesChanged.emit)
        # 凡例関連のシグナルは削除
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
            # 凡例関連のプロパティは削除
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