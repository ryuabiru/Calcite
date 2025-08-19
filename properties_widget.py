# properties_widget.py

from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QLabel, QLineEdit, 
    QComboBox, QFormLayout, QPushButton, QColorDialog
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor

class PropertiesWidget(QDockWidget):
    # A signal that will be emitted when any property changes
    # It will send a dictionary like {'title': 'New Title'}
    propertiesChanged = Signal(dict)
    graphUpdateRequest = Signal()
    
    def __init__(self, parent=None):
        super().__init__("Properties", parent)

        # Create the main widget and layout for the panel
        main_widget = QWidget()
        layout = QFormLayout(main_widget)
        layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows) # ラベルが長い場合に折り返す

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

        # ★--- ここからグラフ描画UIを追加 ---★
        layout.addRow(QLabel("---")) # セパレーター

        self.y_axis_combo = QComboBox()
        self.x_axis_combo = QComboBox()
        self.subgroup_combo = QComboBox()
        
        # ドロップダウンが変更されたらグラフ更新をリクエストする
        self.y_axis_combo.currentTextChanged.connect(self.graphUpdateRequest.emit)
        self.x_axis_combo.currentTextChanged.connect(self.graphUpdateRequest.emit)
        self.subgroup_combo.currentTextChanged.connect(self.graphUpdateRequest.emit)

        layout.addRow(QLabel("Y-Axis (Value):"), self.y_axis_combo)
        layout.addRow(QLabel("X-Axis (Group):"), self.x_axis_combo)
        layout.addRow(QLabel("Sub-group (Color):"), self.subgroup_combo)

        # ★--- ここからグラフスタイルUIを追加 ---★
        layout.addRow(QLabel("---"))

        # マーカースタイル選択
        self.marker_combo = QComboBox()
        markers = {'Circle': 'o', 'Square': 's', 'Triangle': '^', 'Diamond': 'D', 'None': 'None'}
        for name, style in markers.items():
            self.marker_combo.addItem(name, style) # 表示名と値(matplotlibで使う記号)をセット
        self.marker_combo.currentTextChanged.connect(self.graphUpdateRequest.emit)
        layout.addRow(QLabel("Marker Style:"), self.marker_combo)

        # 色選択
        self.color_button = QPushButton("Select Color")
        self.color_button.clicked.connect(self.open_color_dialog)
        layout.addRow(QLabel("Graph Color:"), self.color_button)
        # ★--- ここまで追加 ---★

        self.setWidget(main_widget)
        
    # ★--- 色選択ダイアログを開くメソッドを追加 ---★
    def open_color_dialog(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.current_color = color.name() # 色名を #RRGGBB 形式で保存
            # ボタンの背景色を選択した色に変更して、どの色が選ばれているか分かりやすくする
            self.color_button.setStyleSheet(f"background-color: {self.current_color};")
            self.graphUpdateRequest.emit() # グラフ更新をリクエスト

    # ★--- カラム名をドロップダウンに設定するメソッドを追加 ---★
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
