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
    """
    グラフのプロパティ（タイトル、軸ラベル、色、マーカーなど）を
    編集するためのUIを提供するドックウィジェット。
    """
    # シグナル定義
    propertiesChanged = Signal(dict)      # グラフのテキストプロパティが変更されたときに発行
    graphUpdateRequest = Signal()         # 「Update Graph」ボタンが押されたときに発行
    subgroupColumnChanged = Signal(str)   # サブグループ（色分け）に使用する列が変更されたときに発行

    def __init__(self, parent=None):
        """
        ウィジェットのUIを初期化する。
        """
        super().__init__("Properties", parent)

        self.current_color = None
        self.subgroup_colors = {}
        self.subgroup_widgets = {}

        # スクロール可能なエリアを作成し、UI要素がはみ出さないようにする
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # UI要素を配置するコンテナウィジェット
        content_widget = QWidget()
        
        # フォーム形式のレイアウトを作成
        layout = QFormLayout(content_widget)
        layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        
        # --- グラフのテキスト関連ウィジェット ---
        self.title_edit = QLineEdit()
        self.title_edit.editingFinished.connect(self.on_properties_changed)
        layout.addRow(QLabel("Title:"), self.title_edit)
        self.xaxis_edit = QLineEdit()
        self.xaxis_edit.editingFinished.connect(self.on_properties_changed)
        layout.addRow(QLabel("X-Axis Label:"), self.xaxis_edit)
        self.yaxis_edit = QLineEdit()
        self.yaxis_edit.editingFinished.connect(self.on_properties_changed)
        layout.addRow(QLabel("Y-Axis Label:"), self.yaxis_edit)

        # --- データマッピング関連ウィジェット ---
        layout.addRow(QLabel("---"))
        self.y_axis_combo = QComboBox()
        self.x_axis_combo = QComboBox()
        self.subgroup_combo = QComboBox()
        self.subgroup_combo.currentTextChanged.connect(self.subgroupColumnChanged.emit)
        layout.addRow(QLabel("Y-Axis (Value):"), self.y_axis_combo)
        layout.addRow(QLabel("X-Axis (Group):"), self.x_axis_combo)
        layout.addRow(QLabel("Sub-group (Color):"), self.subgroup_combo)

        # --- スタイリング関連ウィジェット ---
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
        
        # サブグループごとの色設定UIを配置するレイアウト
        self.subgroup_color_layout = QFormLayout()
        layout.addRow(QLabel("Graph Color (Sub-group):"))
        layout.addRow(self.subgroup_color_layout)

        # --- 更新ボタン ---
        layout.addRow(QLabel("---"))
        update_button = QPushButton("Update Graph")
        update_button.clicked.connect(self.graphUpdateRequest.emit)
        layout.addRow(update_button)

        # --- レイアウト構造の確定 ---
        scroll_area.setWidget(content_widget)
        self.setWidget(scroll_area)

    def open_single_color_dialog(self):
        """単色選択のためのカラーダイアログを開く。"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.current_color = color.name()
            self.single_color_button.setStyleSheet(f"background-color: {self.current_color};")

    def open_subgroup_color_dialog(self, category):
        """サブグループの各カテゴリの色を選択するためのカラーダイアログを開く。"""
        color = QColorDialog.getColor()
        if color.isValid():
            color_name = color.name()
            self.subgroup_colors[category] = color_name
            if category in self.subgroup_widgets:
                self.subgroup_widgets[category].setStyleSheet(f"background-color: {color_name};")

    def update_subgroup_color_ui(self, categories):
        """
        サブグループのカテゴリが変更された際に、色選択UIを動的に更新する。
        """
        # 既存のウィジェットをクリア
        while self.subgroup_color_layout.count():
            item = self.subgroup_color_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.subgroup_widgets.clear()
        self.subgroup_colors.clear()

        # 新しいカテゴリに基づいてウィジェットを再作成
        for category in categories:
            label = QLabel(f"{category}:")
            button = QPushButton("Select Color")
            # partialを使って、クリックされたボタンがどのカテゴリに対応するかを渡す
            button.clicked.connect(partial(self.open_subgroup_color_dialog, category))
            
            self.subgroup_color_layout.addRow(label, button)
            self.subgroup_widgets[category] = button

    def set_columns(self, columns):
        """
        データがロードされた際に、各ドロップダウンリストにカラム名を設定する。
        """
        # 一旦クリア
        self.y_axis_combo.clear()
        self.x_axis_combo.clear()
        self.subgroup_combo.clear()
        
        # 空の選択肢を追加
        self.y_axis_combo.addItem("") 
        self.x_axis_combo.addItem("")
        self.subgroup_combo.addItem("")
        
        # カラム名リストを追加
        self.y_axis_combo.addItems(columns)
        self.x_axis_combo.addItems(columns)
        self.subgroup_combo.addItems(columns)

    def on_properties_changed(self):
        """
        タイトルや軸ラベルが変更されたときにpropertiesChangedシグナルを発行する。
        """
        props = {
            'title': self.title_edit.text(),
            'xlabel': self.xaxis_edit.text(),
            'ylabel': self.yaxis_edit.text(),
        }
        self.propertiesChanged.emit(props)
