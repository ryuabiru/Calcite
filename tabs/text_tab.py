# tabs/text_tab.py

from PySide6.QtWidgets import QWidget, QFormLayout, QLabel, QLineEdit, QSpinBox

class TextTab(QWidget):
    """テキスト設定タブのUIとロジック"""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QFormLayout(self)
        
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

    def get_properties(self):
        """このタブの設定値を取得する"""
        return {
            'title': self.title_edit.text(),
            'xlabel': self.xaxis_edit.text(),
            'ylabel': self.yaxis_edit.text(),
            'title_fontsize': self.title_fontsize_spin.value(),
            'xlabel_fontsize': self.xlabel_fontsize_spin.value(),
            'ylabel_fontsize': self.ylabel_fontsize_spin.value(),
            'ticks_fontsize': self.ticks_fontsize_spin.value(),
        }