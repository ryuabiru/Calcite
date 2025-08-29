# tabs/format_tab.py

from PySide6.QtWidgets import (
    QWidget, QFormLayout, QLabel, QComboBox, QPushButton, QColorDialog,
    QScrollArea, QCheckBox, QSpinBox, QDoubleSpinBox, QVBoxLayout, QGroupBox
)
from PySide6.QtCore import Signal
from functools import partial
import seaborn as sns

class NoScrollComboBox(QComboBox):
    """
    マウスホイールのスクロールイベントを無視するQComboBoxのカスタムクラス。
    """
    def wheelEvent(self, e):
        # wheelEventを何もしないようにオーバーライドする
        e.ignore()

class NoScrollSpinBox(QSpinBox):
    """
    マウスホイールのスクロールイベントを無視するQSpinBoxのカスタムクラス。
    """
    def wheelEvent(self, e):
        e.ignore()

class NoScrollDoubleSpinBox(QDoubleSpinBox):
    """
    マウスホイールのスクロールイベントを無視するQDoubleSpinBoxのカスタムクラス。
    """
    def wheelEvent(self, e):
        e.ignore()

class FormatTab(QWidget):
    """フォーマット設定タブのUIとロジック"""
    propertiesChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_marker_edgecolor = 'black'
        self.current_bar_edgecolor = 'black'
        self.current_regression_color = 'red'
        self.current_color = None # サブグループなしの場合の単色
        self.subgroup_colors = {}
        self.subgroup_widgets = {}
        self.current_categories = []


        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        main_widget = QWidget()
        scroll_area.setWidget(main_widget)
        
        main_layout = QVBoxLayout(main_widget)

        # --- 1. 全体スタイル グループ (Matplotlibベース) ---
        style_group = QGroupBox("Global Style")
        style_layout = QFormLayout(style_group)
        
        self.spines_check = QCheckBox("Remove Top/Right Axis Lines")
        self.spines_check.setChecked(True)
        style_layout.addRow(self.spines_check)
        
        main_layout.addWidget(style_group)

        # --- 2. 個別要素 グループ (Seabornベース) ---
        elements_group = QGroupBox("Plot Elements")
        elements_layout = QVBoxLayout(elements_group) # 垂直レイアウトに変更

        # --- 2a. Markers のサブグループ ---
        marker_sub_group = QGroupBox("Markers (for Scatter, Overlay, etc.)")
        marker_layout = QFormLayout(marker_sub_group)

        self.marker_style_combo = NoScrollComboBox()
        markers = {'Circle': 'o', 'Square': 's', 'Triangle': '^', 'Diamond': 'D', 'None': 'None'}
        for name, style in markers.items():
            self.marker_style_combo.addItem(name, style)
        marker_layout.addRow(QLabel("Style:"), self.marker_style_combo)

        self.marker_size_spin = NoScrollDoubleSpinBox()
        self.marker_size_spin.setRange(1, 20); self.marker_size_spin.setSingleStep(0.5); self.marker_size_spin.setValue(5.0)
        marker_layout.addRow(QLabel("Size:"), self.marker_size_spin)

        self.marker_alpha_spin = NoScrollDoubleSpinBox()
        self.marker_alpha_spin.setRange(0.0, 1.0); self.marker_alpha_spin.setSingleStep(0.1); self.marker_alpha_spin.setValue(1.0)
        marker_layout.addRow(QLabel("Alpha (Transparency):"), self.marker_alpha_spin)
        
        self.marker_edgecolor_button = QPushButton("Select Color")
        self.marker_edgecolor_button.setStyleSheet(f"background-color: {self.current_marker_edgecolor};")
        marker_layout.addRow(QLabel("Edge Color:"), self.marker_edgecolor_button)

        self.marker_edgewidth_spin = NoScrollDoubleSpinBox()
        self.marker_edgewidth_spin.setRange(0, 10); self.marker_edgewidth_spin.setSingleStep(0.5); self.marker_edgewidth_spin.setValue(1.0)
        marker_layout.addRow(QLabel("Edge Width:"), self.marker_edgewidth_spin)
        
        elements_layout.addWidget(marker_sub_group)

        # --- 2b. Bars のサブグループ ---
        bar_sub_group = QGroupBox("Bars (for Bar Chart)")
        bar_layout = QFormLayout(bar_sub_group)
        
        self.bar_edgecolor_button = QPushButton("Select Color")
        self.bar_edgecolor_button.setStyleSheet(f"background-color: {self.current_bar_edgecolor};")
        bar_layout.addRow(QLabel("Edge Color:"), self.bar_edgecolor_button)

        self.bar_edgewidth_spin = NoScrollDoubleSpinBox()
        self.bar_edgewidth_spin.setRange(0, 10); self.bar_edgewidth_spin.setSingleStep(0.5); self.bar_edgewidth_spin.setValue(1.0)
        bar_layout.addRow(QLabel("Edge Width:"), self.bar_edgewidth_spin)

        elements_layout.addWidget(bar_sub_group)

        # --- 2c. Error Bars のサブグループ ---
        error_bar_sub_group = QGroupBox("Error Bars (for Summary Scatter, etc.)")
        error_bar_layout = QFormLayout(error_bar_sub_group)

        self.error_bar_combo = NoScrollComboBox()
        self.error_bar_combo.addItem("SEM (Standard Error)", "sem")
        self.error_bar_combo.addItem("SD (Standard Deviation)", "std")
        error_bar_layout.addRow(QLabel("Type:"), self.error_bar_combo)
        
        self.capsize_spin = NoScrollSpinBox()
        self.capsize_spin.setRange(0, 20); self.capsize_spin.setValue(4)
        error_bar_layout.addRow(QLabel("Cap Size:"), self.capsize_spin)

        elements_layout.addWidget(error_bar_sub_group)
        
        # --- 2c. Lines のサブグループ ---
        
        line_sub_group = QGroupBox("Lines (for Line, Point, Fit)")
        line_layout = QFormLayout(line_sub_group)

        self.linestyle_combo = NoScrollComboBox()
        linestyles = {'Solid': '-', 'Dashed': '--', 'Dotted': ':', 'Dash-Dot': '-.'}
        for name, style in linestyles.items():
            self.linestyle_combo.addItem(name, style)
        line_layout.addRow(QLabel("Style:"), self.linestyle_combo)

        self.linewidth_spin = NoScrollDoubleSpinBox()
        self.linewidth_spin.setRange(0.5, 10.0); self.linewidth_spin.setSingleStep(0.5); self.linewidth_spin.setValue(1.5)
        line_layout.addRow(QLabel("Width:"), self.linewidth_spin)
        
        self.regression_color_button = QPushButton("Select Color")
        self.regression_color_button.setStyleSheet(f"background-color: {self.current_regression_color};")
        line_layout.addRow(QLabel("Fit Line Color:"), self.regression_color_button)

        elements_layout.addWidget(line_sub_group)
        
        main_layout.addWidget(elements_group)

        # --- 3. カラー設定グループ ---
        color_group = QGroupBox("Color Palette")
        color_layout = QFormLayout(color_group)
        
        self.scatter_overlay_check = QCheckBox("Show individual points (on Bar/Box/Violin)")
        color_layout.addRow(QLabel("Overlays:"), self.scatter_overlay_check)
        
        self.single_color_button = QPushButton("Select Color")
        color_layout.addRow(QLabel("Single Color (if no Sub-group):"), self.single_color_button)
        
        color_layout.addRow(QLabel("<b>Sub-group Colors</b>"))
        
        self.palette_combo = NoScrollComboBox()
        palettes = [
            "default", "deep", "muted", "pastel", "bright", "dark", "colorblind", 
            "Paired", "Set2", "tab10",
            "viridis", "plasma", "inferno", "magma", "cividis",
            "rocket", "mako", "flare", "crest"
        ]
        self.palette_combo.addItems(palettes)
        color_layout.addRow(QLabel("Palette:"), self.palette_combo)

        self.subgroup_color_layout = QFormLayout()
        color_layout.addRow(self.subgroup_color_layout)
        
        main_layout.addWidget(color_group)
        main_layout.addStretch()

        outer_layout = QVBoxLayout(self)
        outer_layout.addWidget(scroll_area)
        
        self.connect_signals()

    def connect_signals(self):
        self.spines_check.stateChanged.connect(lambda: self.propertiesChanged.emit())
        self.scatter_overlay_check.stateChanged.connect(lambda: self.propertiesChanged.emit())
        self.marker_style_combo.currentIndexChanged.connect(lambda: self.propertiesChanged.emit())
        self.marker_edgecolor_button.clicked.connect(self.open_marker_edgecolor_dialog)
        self.marker_edgewidth_spin.valueChanged.connect(lambda: self.propertiesChanged.emit())
        self.marker_size_spin.valueChanged.connect(lambda: self.propertiesChanged.emit())
        self.marker_alpha_spin.valueChanged.connect(lambda: self.propertiesChanged.emit())
        self.linestyle_combo.currentIndexChanged.connect(lambda: self.propertiesChanged.emit())
        self.bar_edgewidth_spin.valueChanged.connect(lambda: self.propertiesChanged.emit())
        self.capsize_spin.valueChanged.connect(lambda: self.propertiesChanged.emit())
        self.linewidth_spin.valueChanged.connect(lambda: self.propertiesChanged.emit())
        self.single_color_button.clicked.connect(self.open_single_color_dialog)
        self.bar_edgecolor_button.clicked.connect(self.open_bar_edgecolor_dialog)
        self.regression_color_button.clicked.connect(self.open_regression_color_dialog)
        self.palette_combo.currentTextChanged.connect(self.on_palette_changed)
        self.error_bar_combo.currentIndexChanged.connect(lambda:self.propertiesChanged.emit())


    def get_properties(self):
        return {
            'hide_top_right_spines': self.spines_check.isChecked(),
            'scatter_overlay': self.scatter_overlay_check.isChecked(),
            
            # Marker properties
            'marker_style': self.marker_style_combo.currentData(),
            'marker_edgecolor': self.current_marker_edgecolor,
            'marker_edgewidth': self.marker_edgewidth_spin.value(),
            'marker_size': self.marker_size_spin.value(),
            'marker_alpha': self.marker_alpha_spin.value(),

            # Bar properties
            'bar_edgecolor': self.current_bar_edgecolor,
            'bar_edgewidth': self.bar_edgewidth_spin.value(),
            'capsize': self.capsize_spin.value(),
            
            # error bar
            'capsize': self.capsize_spin.value(),
            'error_bar_type': self.error_bar_combo.currentData(),
            
            # Line properties
            'linestyle': self.linestyle_combo.currentData(),
            'linewidth': self.linewidth_spin.value(),
            'regression_color': self.current_regression_color,
            
            # Color properties
            'single_color': self.current_color,
            'subgroup_colors': self.subgroup_colors,
        }

    def open_regression_color_dialog(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.current_regression_color = color.name()
            self.regression_color_button.setStyleSheet(f"background-color: {self.current_regression_color};")
            self.propertiesChanged.emit()

    def on_palette_changed(self):
        """
        パレット選択に応じて、サブグループの色設定を更新する
        """
        # 現在表示されているカテゴリを使ってUIを再描画
        self.update_subgroup_color_ui(self.current_categories)
        # グラフ本体も更新するように通知
        self.propertiesChanged.emit()

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
        # ★★★ メソッドのロジックを全面的に修正 ★★★
        self.current_categories = categories # 現在のカテゴリを保存

        # 既存のUIをクリア
        while self.subgroup_color_layout.count():
            item = self.subgroup_color_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.subgroup_widgets.clear()
        
        if not categories:
            return

        # 選択されたパレットを取得
        selected_palette = self.palette_combo.currentText()
        if selected_palette == "default":
            # "default"の場合は、引数なしでseabornのデフォルトパレットを取得
            palette = sns.color_palette(n_colors=len(categories))
        else:
            palette = sns.color_palette(selected_palette, n_colors=len(categories))

        # パレットの色を16進数文字列に変換
        hex_colors = [f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}" for r, g, b in palette]
        
        # self.subgroup_colorsを新しいパレットの色で完全に上書き
        self.subgroup_colors.clear()
        for i, category in enumerate(categories):
            str_category = str(category)
            self.subgroup_colors[str_category] = hex_colors[i]
        
        # 新しい色設定に基づいてUIを再構築
        for category in categories:
            str_category = str(category)
            button = QPushButton("Select Color")
            button.setStyleSheet(f"background-color: {self.subgroup_colors[str_category]};")
            
            button.clicked.connect(partial(self.open_subgroup_color_dialog, str_category))
            self.subgroup_color_layout.addRow(QLabel(f"{str_category}:"), button)
            self.subgroup_widgets[str_category] = button