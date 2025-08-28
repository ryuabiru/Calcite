# dialogs/mannwhitney_dialog.py (新規作成)

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QComboBox, 
    QDialogButtonBox, QWidget
)

class MannWhitneyDialog(QDialog):
    """
    マン・ホイットニーのU検定のために2つのグループを選択させるダイアログ。
    TTestDialogをベースに作成。
    """
    def __init__(self, x_values, hue_values, x_name, hue_name, parent=None):
        super().__init__(parent)
        # ウィンドウのタイトルを変更
        self.setWindowTitle("Mann-Whitney U Test")
        
        self.x_name = x_name
        self.hue_name = hue_name

        main_layout = QVBoxLayout(self)
        group_selectors_layout = QHBoxLayout()

        self.group1_widget = self._create_group_selector("Group 1", x_values, hue_values)
        self.group2_widget = self._create_group_selector("Group 2", x_values, hue_values)
        
        group_selectors_layout.addWidget(self.group1_widget)
        group_selectors_layout.addWidget(self.group2_widget)
        
        main_layout.addLayout(group_selectors_layout)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(button_box)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def _create_group_selector(self, title, x_values, hue_values):
        """片方のグループを選択するためのUIウィジェットを作成する（TTestDialogと共通）"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        layout.addRow(QLabel(f"<b>{title}</b>"))

        x_combo = QComboBox()
        x_combo.addItems(x_values)
        layout.addRow(QLabel(f"{self.x_name}:"), x_combo)
        
        if self.hue_name and hue_values:
            hue_combo = QComboBox()
            hue_combo.addItems(hue_values)
            layout.addRow(QLabel(f"{self.hue_name}:"), hue_combo)
        
        return widget

    def get_settings(self):
        """ユーザーが選択した2つのグループの条件を返す（TTestDialogと共通）"""
        
        def get_widget_values(group_widget):
            combos = group_widget.findChildren(QComboBox)
            x_val = combos[0].currentText()
            hue_val = combos[1].currentText() if len(combos) > 1 else None
            return {"x": x_val, "hue": hue_val}

        g1_settings = get_widget_values(self.group1_widget)
        g2_settings = get_widget_values(self.group2_widget)
        
        if not g1_settings["x"] or not g2_settings["x"]:
            return None
        if self.hue_name and (not g1_settings["hue"] or not g2_settings["hue"]):
            return None

        return {"group1": g1_settings, "group2": g2_settings}