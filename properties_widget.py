# properties_widget.py

from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QComboBox, QFormLayout, QPushButton, QColorDialog, QHBoxLayout,
    QScrollArea, QCheckBox, QTabWidget, QSpinBox, QDoubleSpinBox
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor, QDoubleValidator
from functools import partial

class PropertiesWidget(QDockWidget):
    propertiesChanged = Signal()
    graphUpdateRequest = Signal()
    subgroupColumnChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__("Properties", parent)

        self.current_color = None
        self.subgroup_colors = {}
        self.subgroup_widgets = {}

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        tab_widget = QTabWidget()

        data_tab = self.create_data_tab()
        format_tab = self.create_format_tab()
        text_tab = self.create_text_tab()
        axes_tab = self.create_axes_tab()

        tab_widget.addTab(data_tab, "データ")
        tab_widget.addTab(format_tab, "フォーマット")
        tab_widget.addTab(text_tab, "テキスト")
        tab_widget.addTab(axes_tab, "軸")

        update_button = QPushButton("Update Graph")
        update_button.clicked.connect(self.graphUpdateRequest.emit)
        
        main_layout.addWidget(tab_widget)
        main_layout.addWidget(update_button)

        self.setWidget(main_widget)
        
        self.connect_signals()

    def connect_signals(self):
        """全てのUI要素の変更をpropertiesChangedシグナルに接続する"""
        # ★--- TypeErrorを解決するため、lambda式でラップ ---★
        # テキストタブ
        self.title_edit.editingFinished.connect(self.propertiesChanged.emit)
        self.xaxis_edit.editingFinished.connect(self.propertiesChanged.emit)
        self.yaxis_edit.editingFinished.connect(self.propertiesChanged.emit)
        self.title_fontsize_spin.valueChanged.connect(lambda: self.propertiesChanged.emit())
        self.xlabel_fontsize_spin.valueChanged.connect(lambda: self.propertiesChanged.emit())
        self.ylabel_fontsize_spin.valueChanged.connect(lambda: self.propertiesChanged.emit())
        self.ticks_fontsize_spin.valueChanged.connect(lambda: self.propertiesChanged.emit())
        # 軸タブ
        self.xmin_edit.editingFinished.connect(self.propertiesChanged.emit)
        self.xmax_edit.editingFinished.connect(self.propertiesChanged.emit)
        self.ymin_edit.editingFinished.connect(self.propertiesChanged.emit)
        self.ymax_edit.editingFinished.connect(self.propertiesChanged.emit)
        self.grid_check.stateChanged.connect(lambda: self.propertiesChanged.emit())
        self.x_log_scale_check.stateChanged.connect(lambda: self.propertiesChanged.emit())
        self.y_log_scale_check.stateChanged.connect(lambda: self.propertiesChanged.emit())
        # 線のスタイル
        self.linestyle_combo.currentIndexChanged.connect(lambda: self.propertiesChanged.emit())
        self.linewidth_spin.valueChanged.connect(lambda: self.propertiesChanged.emit())
        self.capsize_spin.valueChanged.connect(lambda: self.propertiesChanged.emit())


    def create_data_tab(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        self.y_axis_combo = QComboBox()
        self.x_axis_combo = QComboBox()
        self.subgroup_combo = QComboBox()
        self.subgroup_combo.currentTextChanged.connect(self.subgroupColumnChanged.emit)
        layout.addRow(QLabel("Y-Axis (Value):"), self.y_axis_combo)
        layout.addRow(QLabel("X-Axis (Group):"), self.x_axis_combo)
        layout.addRow(QLabel("Sub-group (Color):"), self.subgroup_combo)
        return widget

    def create_format_tab(self):
        widget = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(widget)
        layout = QFormLayout(widget)
        
        # マーカのシンボル
        self.scatter_overlay_check = QCheckBox()
        layout.addRow(QLabel("Overlay Individual Points:"), self.scatter_overlay_check)
        self.marker_combo = QComboBox()
        markers = {'Circle': 'o', 'Square': 's', 'Triangle': '^', 'Diamond': 'D', 'None': 'None'}
        for name, style in markers.items():
            self.marker_combo.addItem(name, style)
        layout.addRow(QLabel("Marker Style:"), self.marker_combo)
        
         # 線のスタイル
        self.linestyle_combo = QComboBox()
        linestyles = {'Solid': '-', 'Dashed': '--', 'Dotted': ':', 'Dash-Dot': '-.'}
        for name, style in linestyles.items():
            self.linestyle_combo.addItem(name, style)
        layout.addRow(QLabel("Line Style (Regression):"), self.linestyle_combo)

        # 線の太さ
        self.linewidth_spin = QDoubleSpinBox()
        self.linewidth_spin.setRange(0.5, 10.0)
        self.linewidth_spin.setSingleStep(0.5)
        self.linewidth_spin.setValue(1.5)
        layout.addRow(QLabel("Line Width (Regression):"), self.linewidth_spin)

        # エラーバーのキャップサイズ
        self.capsize_spin = QSpinBox()
        self.capsize_spin.setRange(0, 20)
        self.capsize_spin.setValue(4)
        layout.addRow(QLabel("Error Bar Cap Size:"), self.capsize_spin)
        
        # グラフの色
        self.single_color_button = QPushButton("Select Color")
        self.single_color_button.clicked.connect(self.open_single_color_dialog)
        layout.addRow(QLabel("Graph Color (Single):"), self.single_color_button)
        self.subgroup_color_layout = QFormLayout()
        layout.addRow(QLabel("Graph Color (Sub-group):"))
        layout.addRow(self.subgroup_color_layout)
        
        
        
        return scroll_area

    def create_text_tab(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        self.title_edit = QLineEdit()
        self.xaxis_edit = QLineEdit()
        self.yaxis_edit = QLineEdit()
        layout.addRow(QLabel("Title:"), self.title_edit)
        layout.addRow(QLabel("X-Axis Label:"), self.xaxis_edit)
        layout.addRow(QLabel("Y-Axis Label:"), self.yaxis_edit)
        layout.addRow(QLabel("---"))
        self.title_fontsize_spin = QSpinBox()
        self.title_fontsize_spin.setRange(6, 48); self.title_fontsize_spin.setValue(16)
        self.xlabel_fontsize_spin = QSpinBox()
        self.xlabel_fontsize_spin.setRange(6, 48); self.xlabel_fontsize_spin.setValue(12)
        self.ylabel_fontsize_spin = QSpinBox()
        self.ylabel_fontsize_spin.setRange(6, 48); self.ylabel_fontsize_spin.setValue(12)
        self.ticks_fontsize_spin = QSpinBox()
        self.ticks_fontsize_spin.setRange(6, 48); self.ticks_fontsize_spin.setValue(10)
        layout.addRow(QLabel("Title Font Size:"), self.title_fontsize_spin)
        layout.addRow(QLabel("X-Label Font Size:"), self.xlabel_fontsize_spin)
        layout.addRow(QLabel("Y-Label Font Size:"), self.ylabel_fontsize_spin)
        layout.addRow(QLabel("Ticks Font Size:"), self.ticks_fontsize_spin)
        return widget

    def create_axes_tab(self):
        widget = QWidget()
        layout = QFormLayout(widget)
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
        return widget
    
    def get_properties(self):
        """UIから現在の設定値をすべて集めて辞書として返す。"""
        # ★--- KeyErrorを解決するため、抜けていたキーを追加 ---★
        return {
            'title': self.title_edit.text(),
            'xlabel': self.xaxis_edit.text(),
            'ylabel': self.yaxis_edit.text(),
            'title_fontsize': self.title_fontsize_spin.value(),
            'xlabel_fontsize': self.xlabel_fontsize_spin.value(),
            'ylabel_fontsize': self.ylabel_fontsize_spin.value(),
            'ticks_fontsize': self.ticks_fontsize_spin.value(),
            'xmin': self.xmin_edit.text(),
            'xmax': self.xmax_edit.text(),
            'ymin': self.ymin_edit.text(),
            'ymax': self.ymax_edit.text(),
            'show_grid': self.grid_check.isChecked(),
            'x_log_scale': self.x_log_scale_check.isChecked(),
            'y_log_scale': self.y_log_scale_check.isChecked(),
            'show_grid': self.grid_check.isChecked(),
            'x_log_scale': self.x_log_scale_check.isChecked(),
            'y_log_scale': self.y_log_scale_check.isChecked(),
            'marker_style': self.marker_combo.currentData(),
            'linestyle': self.linestyle_combo.currentData(),
            'linewidth': self.linewidth_spin.value(),
            'capsize': self.capsize_spin.value(),
        }

    def open_single_color_dialog(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.current_color = color.name()
            self.single_color_button.setStyleSheet(f"background-color: {self.current_color};")
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
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.subgroup_widgets.clear()
        self.subgroup_colors.clear()
        for category in categories:
            label = QLabel(f"{category}:")
            button = QPushButton("Select Color")
            button.clicked.connect(partial(self.open_subgroup_color_dialog, category))
            self.subgroup_color_layout.addRow(label, button)
            self.subgroup_widgets[category] = button

    def set_columns(self, columns):
        self.y_axis_combo.clear()
        self.x_axis_combo.clear()
        self.subgroup_combo.clear()
        self.y_axis_combo.addItem("") 
        self.x_axis_combo.addItem("")
        self.subgroup_combo.addItem("")
        self.y_axis_combo.addItems(columns)
        self.x_axis_combo.addItems(columns)
        self.subgroup_combo.addItems(columns)