# tabs/data_tab_tidy.py

from PySide6.QtWidgets import QWidget, QFormLayout, QLabel, QComboBox
from PySide6.QtCore import Signal

class TidyDataTab(QWidget):
    """
    Tidy Data形式（Y軸, X軸, サブグループ）のためのデータ選択UI。
    """
    # サブグループの列が変更されたことを通知するシグナル
    subgroupColumnChanged = Signal(str)


    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QFormLayout(self)
        
        # ウィジェットを作成
        self.y_axis_combo = QComboBox()
        self.x_axis_combo = QComboBox()
        self.subgroup_combo = QComboBox()
        self.facet_col_combo = QComboBox() # 列で分割
        
        # ★★★ ラベルにもselfを付けてアクセス可能にする ★★★
        self.y_axis_label = QLabel("Y-Axis (Value):")
        self.x_axis_label = QLabel("X-Axis (Group):")
        
        # シグナルを接続
        self.subgroup_combo.currentTextChanged.connect(self.subgroupColumnChanged.emit)
        
        # レイアウトにウィジェットを追加
        layout.addRow(self.y_axis_label, self.y_axis_combo)
        layout.addRow(self.x_axis_label, self.x_axis_combo)
        layout.addRow(QLabel("Sub-group (Color):"), self.subgroup_combo)
        layout.addRow(QLabel("Facet (Columns):"), self.facet_col_combo)


    def set_columns(self, columns):
        """コンボボックスの選択肢を更新する"""
        # 現在選択されている項目を保持
        current_y = self.y_axis_combo.currentText()
        current_x = self.x_axis_combo.currentText()
        current_sub = self.subgroup_combo.currentText()
        current_facet_col = self.facet_col_combo.currentText()
        
        # 一旦クリア
        self.y_axis_combo.clear()
        self.x_axis_combo.clear()
        self.subgroup_combo.clear()
        self.facet_col_combo.clear()
        
        # 空の選択肢を追加
        self.y_axis_combo.addItem("") 
        self.x_axis_combo.addItem("")
        self.subgroup_combo.addItem("")
        self.facet_col_combo.addItem("")
        
        # 新しい列名を追加
        self.y_axis_combo.addItems(columns)
        self.x_axis_combo.addItems(columns)
        self.subgroup_combo.addItems(columns)
        self.facet_col_combo.addItems(columns)
        
        # 以前の選択状態を復元
        self.y_axis_combo.setCurrentText(current_y)
        self.x_axis_combo.setCurrentText(current_x)
        self.subgroup_combo.setCurrentText(current_sub)
        self.facet_col_combo.setCurrentText(current_facet_col)


    def get_settings(self):
        """現在の設定値を辞書として返す"""
        return {
            'y_col': self.y_axis_combo.currentText(),
            'x_col': self.x_axis_combo.currentText(),
            'subgroup_col': self.subgroup_combo.currentText(),
            'facet_col': self.facet_col_combo.currentText(),
        }