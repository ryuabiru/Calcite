# properties_widget.py

from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QLabel, QLineEdit, 
    QComboBox, QFormLayout, QPushButton, QColorDialog, QHBoxLayout,
    QScrollArea, QCheckBox
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor
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

        # 1. スクロールエリアを作成
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # 2. 全てのUI要素を配置するための「中身の」ウィジェットを作成
        content_widget = QWidget()
        
        # 3. 中身のウィジェットにレイアウトを設定
        layout = QFormLayout(content_widget)
        layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        
        # --- ここから、これまで通りレイアウトにウィジェットを追加 ---

        # Graph Title & Labels
        self.title_edit = QLineEdit()
        self.title_edit.editingFinished.connect(self.on_properties_changed)
        layout.addRow(QLabel("Title:"), self.title_edit)
        self.xaxis_edit = QLineEdit()
        self.xaxis_edit.editingFinished.connect(self.on_properties_changed)
        layout.addRow(QLabel("X-Axis Label:"), self.xaxis_edit)
        self.yaxis_edit = QLineEdit()
        self.yaxis_edit.editingFinished.connect(self.on_properties_changed)
        layout.addRow(QLabel("Y-Axis Label:"), self.yaxis_edit)

        # Graph Data Mapping
        layout.addRow(QLabel("---"))
        self.y_axis_combo = QComboBox()
        self.x_axis_combo = QComboBox()
        self.subgroup_combo = QComboBox()
        self.subgroup_combo.currentTextChanged.connect(self.subgroupColumnChanged.emit)
        layout.addRow(QLabel("Y-Axis (Value):"), self.y_axis_combo)
        layout.addRow(QLabel("X-Axis (Group):"), self.x_axis_combo)
        layout.addRow(QLabel("Sub-group (Color):"), self.subgroup_combo)

        # Graph Styling
        layout.addRow(QLabel("---"))
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

        # Update Button
        layout.addRow(QLabel("---"))
        update_button = QPushButton("Update Graph")
        update_button.clicked.connect(self.graphUpdateRequest.emit)
        layout.addRow(update_button)

        # --- 最後に構造を確定させる ---
        # 4. 中身のウィジェットを、スクロールエリアにセット
        scroll_area.setWidget(content_widget)
        
        # 5. ドックウィジェット自身のメインウィジェットとして、スクロールエリアをセット
        self.setWidget(scroll_area)

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
        # 既存のウィジェットを正しくクリアする
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

    def on_properties_changed(self):
        props = {
            'title': self.title_edit.text(),
            'xlabel': self.xaxis_edit.text(),
            'ylabel': self.yaxis_edit.text(),
        }
        self.propertiesChanged.emit(props)