# properties_widget.py

from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QLabel, QLineEdit, 
    QComboBox, QFormLayout, QPushButton, QColorDialog, QHBoxLayout,
    QScrollArea, QCheckBox, QTabWidget
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor, QDoubleValidator
from functools import partial

class PropertiesWidget(QDockWidget):
    propertiesChanged = Signal(dict)
    graphUpdateRequest = Signal()
    subgroupColumnChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__("Properties", parent)

        self.current_color = None
        self.subgroup_colors = {}
        self.subgroup_widgets = {}

        # --- メインとなるウィジェットとレイアウト ---
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # --- タブウィジェットの作成 ---
        tab_widget = QTabWidget()

        # --- 各タブの中身を作成 ---
        data_tab = self.create_data_tab()
        format_tab = self.create_format_tab()
        axes_tab = self.create_axes_tab()

        # --- タブウィジェットに各タブを追加 ---
        tab_widget.addTab(data_tab, "データ")
        tab_widget.addTab(format_tab, "フォーマット")
        tab_widget.addTab(axes_tab, "軸")

        # --- 更新ボタン ---
        update_button = QPushButton("Update Graph")
        update_button.clicked.connect(self.graphUpdateRequest.emit)
        
        # --- 全体をレイアウトに追加 ---
        main_layout.addWidget(tab_widget)
        main_layout.addWidget(update_button)

        self.setWidget(main_widget)

    def create_data_tab(self):
        """データマッピング用UIを持つタブを作成する"""
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
        """グラフのスタイリング用UIを持つタブを作成する"""
        widget = QWidget()
        # スクロール可能にする
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(widget)
        layout = QFormLayout(widget)

        self.scatter_overlay_check = QCheckBox()
        layout.addRow(QLabel("Overlay Individual Points:"), self.scatter_overlay_check)
        
        self.marker_combo = QComboBox()
        markers = {'Circle': 'o', 'Square': 's', 'Triangle': '^', 'Diamond': 'D', 'None': 'None'}
        for name, style in markers.items():
            self.marker_combo.addItem(name, style)
        layout.addRow(QLabel("Marker Style:"), self.marker_combo)
        
        self.single_color_button = QPushButton("Select Color")
        self.single_color_button.clicked.connect(self.open_single_color_dialog)
        layout.addRow(QLabel("Graph Color (Single):"), self.single_color_button)
        
        self.subgroup_color_layout = QFormLayout()
        layout.addRow(QLabel("Graph Color (Sub-group):"))
        layout.addRow(self.subgroup_color_layout)

        return scroll_area

    def create_axes_tab(self):
        """軸のタイトルや範囲を設定するUIを持つタブを作成する"""
        widget = QWidget()
        layout = QFormLayout(widget)

        # タイトルとラベル
        self.title_edit = QLineEdit()
        self.xaxis_edit = QLineEdit()
        self.yaxis_edit = QLineEdit()
        layout.addRow(QLabel("Title:"), self.title_edit)
        layout.addRow(QLabel("X-Axis Label:"), self.xaxis_edit)
        layout.addRow(QLabel("Y-Axis Label:"), self.yaxis_edit)
        
        layout.addRow(QLabel("---"))

        # ★--- 軸範囲の入力欄を追加 ---★
        # QDoubleValidatorを使って、数値（浮動小数点数）のみが入力できるように制限
        validator = QDoubleValidator()
        self.xmin_edit = QLineEdit()
        self.xmin_edit.setValidator(validator)
        self.xmax_edit = QLineEdit()
        self.xmax_edit.setValidator(validator)
        self.ymin_edit = QLineEdit()
        self.ymin_edit.setValidator(validator)
        self.ymax_edit = QLineEdit()
        self.ymax_edit.setValidator(validator)

        # 2つのQLineEditを横に並べるためのレイアウト
        x_range_layout = QHBoxLayout()
        x_range_layout.addWidget(self.xmin_edit)
        x_range_layout.addWidget(QLabel("to"))
        x_range_layout.addWidget(self.xmax_edit)
        
        y_range_layout = QHBoxLayout()
        y_range_layout.addWidget(self.ymin_edit)
        y_range_layout.addWidget(QLabel("to"))
        y_range_layout.addWidget(self.ymax_edit)

        layout.addRow(QLabel("X-Axis Range:"), x_range_layout)
        layout.addRow(QLabel("Y-Axis Range:"), y_range_layout)

        return widget
    
    def on_properties_changed(self):
        """
        UIから現在の設定値をすべて集めて辞書として返す。
        このメソッドは update_graph_properties から呼び出される。
        """
        props = {
            'title': self.title_edit.text(),
            'xlabel': self.xaxis_edit.text(),
            'ylabel': self.yaxis_edit.text(),
            'xmin': self.xmin_edit.text(),
            'xmax': self.xmax_edit.text(),
            'ymin': self.ymin_edit.text(),
            'ymax': self.ymax_edit.text(),
        }
        return props

    # open_single_color_dialog, open_subgroup_color_dialog, update_subgroup_color_ui, set_columns
    # は、これまでのコードから変更ありません（ここでは省略します）。
    def open_single_color_dialog(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.current_color = color.name()
            self.single_color_button.setStyleSheet(f"background-color: {self.current_color};")

    def open_subgroup_color_dialog(self, category):
        color = QColorDialog.getColor()
        if color.isValid():
            color_name = color.name()
            self.subgroup_colors[category] = color_name
            if category in self.subgroup_widgets:
                self.subgroup_widgets[category].setStyleSheet(f"background-color: {color_name};")

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