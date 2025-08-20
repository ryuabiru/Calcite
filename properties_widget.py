# properties_widget.py

from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QComboBox, QFormLayout, QPushButton, QColorDialog, QHBoxLayout,
    QScrollArea, QCheckBox, QTabWidget, QSpinBox
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor, QDoubleValidator
from functools import partial

class PropertiesWidget(QDockWidget):
    propertiesChanged = Signal() # 引数をなくし、単なる更新トリガーとする
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

        # --- 各タブの中身を作成 ---
        data_tab = self.create_data_tab()
        format_tab = self.create_format_tab()
        text_tab = self.create_text_tab() # ★ 新しいタブ
        axes_tab = self.create_axes_tab()

        # --- タブウィジェットに各タブを追加 ---
        tab_widget.addTab(data_tab, "データ")
        tab_widget.addTab(format_tab, "フォーマット")
        tab_widget.addTab(text_tab, "テキスト") # ★ 追加
        tab_widget.addTab(axes_tab, "軸")

        update_button = QPushButton("Update Graph")
        update_button.clicked.connect(self.graphUpdateRequest.emit)
        
        main_layout.addWidget(tab_widget)
        main_layout.addWidget(update_button)

        self.setWidget(main_widget)
        
        # すべてのインタラクティブなウィジェットに変更を接続
        self.connect_signals()

    def connect_signals(self):
        """全てのUI要素の変更をpropertiesChangedシグナルに接続する"""
        # テキストタブ
        self.title_edit.editingFinished.connect(self.propertiesChanged.emit)
        self.xaxis_edit.editingFinished.connect(self.propertiesChanged.emit)
        self.yaxis_edit.editingFinished.connect(self.propertiesChanged.emit)
        self.title_fontsize_spin.valueChanged.connect(self.propertiesChanged.emit)
        self.xlabel_fontsize_spin.valueChanged.connect(self.propertiesChanged.emit)
        self.ylabel_fontsize_spin.valueChanged.connect(self.propertiesChanged.emit)
        self.ticks_fontsize_spin.valueChanged.connect(self.propertiesChanged.emit)
        # 軸タブ
        self.xmin_edit.editingFinished.connect(self.propertiesChanged.emit)
        self.xmax_edit.editingFinished.connect(self.propertiesChanged.emit)
        self.ymin_edit.editingFinished.connect(self.propertiesChanged.emit)
        self.ymax_edit.editingFinished.connect(self.propertiesChanged.emit)
        self.grid_check.stateChanged.connect(self.propertiesChanged.emit)
        self.x_log_scale_check.stateChanged.connect(self.propertiesChanged.emit)
        self.y_log_scale_check.stateChanged.connect(self.propertiesChanged.emit)


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

    def create_text_tab(self):
        """テキスト関連のUIを持つタブを作成する"""
        widget = QWidget()
        layout = QFormLayout(widget)

        # ラベルテキスト
        self.title_edit = QLineEdit()
        self.xaxis_edit = QLineEdit()
        self.yaxis_edit = QLineEdit()
        layout.addRow(QLabel("Title:"), self.title_edit)
        layout.addRow(QLabel("X-Axis Label:"), self.xaxis_edit)
        layout.addRow(QLabel("Y-Axis Label:"), self.yaxis_edit)
        
        layout.addRow(QLabel("---"))

        # フォントサイズ
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
        """軸の範囲やスケールを設定するUIを持つタブを作成する"""
        widget = QWidget()
        layout = QFormLayout(widget)

        # 軸範囲
        # ... (変更なし) ...
        
        layout.addRow(QLabel("---"))

        # グリッド
        self.grid_check = QCheckBox("Show Grid")
        layout.addRow(self.grid_check)

        layout.addRow(QLabel("---")) # 区切り線

        # ★--- スケール変換のチェックボックスを追加 ---★
        self.x_log_scale_check = QCheckBox("Logarithmic Scale")
        self.y_log_scale_check = QCheckBox("Logarithmic Scale")
        layout.addRow(QLabel("X-Axis Scale:"), self.x_log_scale_check)
        layout.addRow(QLabel("Y-Axis Scale:"), self.y_log_scale_check)

        return widget
    
    def get_properties(self):
        """UIから現在の設定値をすべて集めて辞書として返す。"""
        return {
            # ... (既存のプロパティは変更なし) ...
            'ymin': self.ymin_edit.text(),
            'ymax': self.ymax_edit.text(),
            'show_grid': self.grid_check.isChecked(),
            # ★--- 新しいプロパティを追加 ---★
            'x_log_scale': self.x_log_scale_check.isChecked(),
            'y_log_scale': self.y_log_scale_check.isChecked(),
        }

    def open_single_color_dialog(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.current_color = color.name()
            self.single_color_button.setStyleSheet(f"background-color: {self.current_color};")
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
            button.clicked.connect(self.propertiesChanged.emit)
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