# tabs/data_tab_paired.py

from PySide6.QtWidgets import QWidget, QFormLayout, QLabel, QComboBox

class PairedDataTab(QWidget):
    """
    ペアデータ形式（比較する2列）のためのデータ選択UI。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QFormLayout(self)
        
        # ウィジェットを作成
        self.col1_combo = QComboBox()
        self.col2_combo = QComboBox()
        
        # レイアウトにウィジェットを追加
        layout.addRow(QLabel("Column 1 (e.g., Before):"), self.col1_combo)
        layout.addRow(QLabel("Column 2 (e.g., After):"), self.col2_combo)

    def set_columns(self, columns):
        """コンボボックスの選択肢を更新する"""
        # 現在選択されている項目を保持
        current_col1 = self.col1_combo.currentText()
        current_col2 = self.col2_combo.currentText()

        # 一旦クリア
        self.col1_combo.clear()
        self.col2_combo.clear()
        
        # 空の選択肢を追加
        self.col1_combo.addItem("") 
        self.col2_combo.addItem("") 
        
        # 新しい列名を追加
        self.col1_combo.addItems(columns)
        self.col2_combo.addItems(columns)

        # 以前の選択状態を復元
        self.col1_combo.setCurrentText(current_col1)
        self.col2_combo.setCurrentText(current_col2)

    def get_settings(self):
        """現在の設定値を辞書として返す"""
        return {
            'col1': self.col1_combo.currentText(),
            'col2': self.col2_combo.currentText(),
        }