# properties_widget.py

from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QLabel, QLineEdit, 
    QComboBox, QFormLayout, QPushButton, QColorDialog, QHBoxLayout, QScrollArea, QCheckBox
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor

class PropertiesWidget(QDockWidget):
    propertiesChanged = Signal(dict)
    graphUpdateRequest = Signal()
    subgroupColumnChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__("Properties", parent)

        self.current_color = None
        self.subgroup_colors = {}
        self.subgroup_widgets = {}
        
        # ★--- ここから修正 ---★
        # 1. スクロールエリアを作成し、ドックウィジェットのメインウィジェットにする
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.setWidget(scroll_area)

        # 2. 全てのUI要素を乗せるための、これまで通りの main_widget を作成
        main_widget = QWidget()
        layout = QFormLayout(main_widget)
        layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        
        # 3. main_widget をスクロールエリアの中に配置する
        scroll_area.setWidget(main_widget)
        # ★--- ここまで修正 ---★

        # --- Graph Title & Labels ---
        self.title_edit = QLineEdit()
        self.title_edit.editingFinished.connect(self.on_properties_changed)
        layout.addRow(QLabel("Title:"), self.title_edit)

        self.xaxis_edit = QLineEdit()
        self.xaxis_edit.editingFinished.connect(self.on_properties_changed)
        layout.addRow(QLabel("X-Axis Label:"), self.xaxis_edit)

        self.yaxis_edit = QLineEdit()
        self.yaxis_edit.editingFinished.connect(self.on_properties_changed)
        layout.addRow(QLabel("Y-Axis Label:"), self.yaxis_edit)

        layout.addRow(QLabel("---")) # セパレーター

        self.y_axis_combo = QComboBox()
        self.x_axis_combo = QComboBox()
        self.subgroup_combo = QComboBox()

        # ★--- ここを修正 ---★
        # サブグループのドロップダウンが変更された時だけシグナルを発行する
        self.subgroup_combo.currentTextChanged.connect(self.subgroupColumnChanged.emit)
        # (自動更新のための y_axis_combo と x_axis_combo の接続は削除)
        # ★--- ここまで ---★

        layout.addRow(QLabel("Y-Axis (Value):"), self.y_axis_combo)
        layout.addRow(QLabel("X-Axis (Group):"), self.x_axis_combo)
        layout.addRow(QLabel("Sub-group (Color):"), self.subgroup_combo)

        layout.addRow(QLabel("---"))
        
        # 散布図オーバーレイのチェックボックス
        self.scatter_overlay_check = QCheckBox()
        layout.addRow(QLabel("Overlay Individual Points:"), self.scatter_overlay_check)

        # マーカースタイル選択
        self.marker_combo = QComboBox()
        markers = {'Circle': 'o', 'Square': 's', 'Triangle': '^', 'Diamond': 'D', 'None': 'None'}
        for name, style in markers.items():
            self.marker_combo.addItem(name, style) # 表示名と値(matplotlibで使う記号)をセット
        layout.addRow(QLabel("Marker Style:"), self.marker_combo)

        self.single_color_button = QPushButton("Select Color")
        self.single_color_button.clicked.connect(self.open_single_color_dialog)
        layout.addRow(QLabel("Graph Color (Single):"), self.single_color_button)

        self.subgroup_color_layout = QFormLayout()
        layout.addRow(QLabel("Graph Color (Sub-group):"))
        layout.addRow(self.subgroup_color_layout)

        layout.addRow(QLabel("---"))
        update_button = QPushButton("Update Graph")
        update_button.clicked.connect(self.graphUpdateRequest.emit)
        layout.addRow(update_button)
        
        # 3. メインウィジェットをスクロールエリアにセット
        scroll_area.setWidget(main_widget)
        
        # 4. ドックウィジェットのメインウィジェットとして、スクロールエリアをセット
        self.setWidget(scroll_area)

        self.setWidget(main_widget)
        
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
            # 対応するボタンの色を更新
            if category in self.subgroup_widgets:
                self.subgroup_widgets[category].setStyleSheet(f"background-color: {color_name};")

    def update_subgroup_color_ui(self, categories):
        # 既存のウィジェットをクリア
        for i in reversed(range(self.subgroup_color_layout.count())): 
            self.subgroup_color_layout.itemAt(i).widget().setParent(None)
        self.subgroup_widgets.clear()
        self.subgroup_colors.clear()

        # カテゴリごとに色選択ボタンを作成
        for category in categories:
            label = QLabel(f"{category}:")
            button = QPushButton("Select Color")
            # functools.partial を使うと、ループ変数(category)を正しく渡せる
            from functools import partial
            button.clicked.connect(partial(self.open_subgroup_color_dialog, category))
            
            self.subgroup_color_layout.addRow(label, button)
            self.subgroup_widgets[category] = button

    def set_columns(self, columns):
        # いったんクリア
        self.y_axis_combo.clear()
        self.x_axis_combo.clear()
        self.subgroup_combo.clear()

        # 空の選択肢を追加
        self.y_axis_combo.addItem("") 
        self.x_axis_combo.addItem("")
        self.subgroup_combo.addItem("")

        # カラム名を追加
        self.y_axis_combo.addItems(columns)
        self.x_axis_combo.addItems(columns)
        self.subgroup_combo.addItems(columns)



    def on_properties_changed(self):
        # 複数のプロパティを一度に送信するように変更
        props = {
            'title': self.title_edit.text(),
            'xlabel': self.xaxis_edit.text(),
            'ylabel': self.yaxis_edit.text(),
        }
        self.propertiesChanged.emit(props)
