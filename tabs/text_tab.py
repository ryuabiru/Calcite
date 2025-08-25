# tabs/text_tab.py

from PySide6.QtWidgets import (
    QWidget, QFormLayout, QLabel, QLineEdit, 
    QSpinBox, QScrollArea, QVBoxLayout, QGroupBox, QComboBox
)

class TextTab(QWidget):
    """テキストと凡例の設定タブのUIとロジック"""
    def __init__(self, parent=None):
        super().__init__(parent)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        main_widget = QWidget()
        scroll_area.setWidget(main_widget)

        # 全体をまとめる垂直レイアウト
        main_layout = QVBoxLayout(main_widget)

        # --- 1. テキストラベル グループ ---
        text_group = QGroupBox("Labels")
        text_layout = QFormLayout(text_group)
        
        self.title_edit = QLineEdit()
        self.xaxis_edit = QLineEdit()
        self.yaxis_edit = QLineEdit()
        
        text_layout.addRow(QLabel("Title:"), self.title_edit)
        text_layout.addRow(QLabel("X-Axis Label:"), self.xaxis_edit)
        text_layout.addRow(QLabel("Y-Axis Label:"), self.yaxis_edit)
        
        # Paired scatter labels
        self.paired_label1_label = QLabel("Paired Label 1:")
        self.paired_label1_edit = QLineEdit()
        self.paired_label2_label = QLabel("Paired Label 2:")
        self.paired_label2_edit = QLineEdit()
        text_layout.addRow(self.paired_label1_label, self.paired_label1_edit)
        text_layout.addRow(self.paired_label2_label, self.paired_label2_edit)
        self.paired_widgets = [self.paired_label1_label, self.paired_label1_edit, self.paired_label2_label, self.paired_label2_edit]
        self.update_paired_labels_visibility(False) # Initially hidden
        
        main_layout.addWidget(text_group)

        # --- 2. フォントサイズ グループ ---
        font_group = QGroupBox("Font Sizes")
        font_layout = QFormLayout(font_group)

        self.title_fontsize_spin = QSpinBox()
        self.title_fontsize_spin.setRange(6, 48); self.title_fontsize_spin.setValue(16)
        self.xlabel_fontsize_spin = QSpinBox()
        self.xlabel_fontsize_spin.setRange(6, 48); self.xlabel_fontsize_spin.setValue(12)
        self.ylabel_fontsize_spin = QSpinBox()
        self.ylabel_fontsize_spin.setRange(6, 48); self.ylabel_fontsize_spin.setValue(12)
        self.ticks_fontsize_spin = QSpinBox()
        self.ticks_fontsize_spin.setRange(6, 48); self.ticks_fontsize_spin.setValue(10)
        
        font_layout.addRow(QLabel("Title:"), self.title_fontsize_spin)
        font_layout.addRow(QLabel("X-Label:"), self.xlabel_fontsize_spin)
        font_layout.addRow(QLabel("Y-Label:"), self.ylabel_fontsize_spin)
        font_layout.addRow(QLabel("Ticks:"), self.ticks_fontsize_spin)
        
        main_layout.addWidget(font_group)
        
        # --- 3. 凡例グループ (ここからが追加/移設箇所) ---
        legend_group = QGroupBox("Legend")
        legend_layout = QFormLayout(legend_group)
        
        self.legend_pos_combo = QComboBox()
        positions = {
            "Automatic (Outside Right)": "best",
            "Upper Right": "upper right",
            "Upper Left": "upper left",
            "Lower Right": "lower right",
            "Lower Left": "lower left",
        }
        for name, key in positions.items():
            self.legend_pos_combo.addItem(name, key)
        self.legend_title_edit = QLineEdit()

        legend_layout.addRow(QLabel("Position:"), self.legend_pos_combo)
        legend_layout.addRow(QLabel("Title:"), self.legend_title_edit)
        
        main_layout.addWidget(legend_group)
        main_layout.addStretch() # スペーサー

        outer_layout = QVBoxLayout(self)
        outer_layout.addWidget(scroll_area)

    def get_properties(self):
        """このタブの設定値を取得する"""
        return {
            'title': self.title_edit.text(),
            'xlabel': self.xaxis_edit.text(),
            'ylabel': self.yaxis_edit.text(),
            'paired_label1': self.paired_label1_edit.text(),
            'paired_label2': self.paired_label2_edit.text(),
            'title_fontsize': self.title_fontsize_spin.value(),
            'xlabel_fontsize': self.xlabel_fontsize_spin.value(),
            'ylabel_fontsize': self.ylabel_fontsize_spin.value(),
            'ticks_fontsize': self.ticks_fontsize_spin.value(),
            # 凡例のプロパティを追加
            'legend_position': self.legend_pos_combo.currentData(),
            'legend_title': self.legend_title_edit.text(),
        }

    def update_paired_labels_visibility(self, visible):
        """Show or hide the paired scatter labels"""
        for widget in self.paired_widgets:
            widget.setVisible(visible)