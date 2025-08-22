# dialogs/ttest_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QComboBox, 
    QDialogButtonBox, QWidget
)

class TTestDialog(QDialog):
    """
    X軸とサブグループ(hue)の組み合わせで2つのグループを選択し、
    独立t検定を行うためのダイアログ。
    """
    def __init__(self, x_values, hue_values, x_name, hue_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Independent t-test")
        
        self.x_name = x_name
        self.hue_name = hue_name

        # ★★★ ここからレイアウト構造を修正 ★★★
        # 全体を縦に並べるメインのレイアウト
        main_layout = QVBoxLayout(self)

        # グループ選択部分を横に並べるためのレイアウト
        group_selectors_layout = QHBoxLayout()

        # グループ1とグループ2の選択UIを作成
        self.group1_widget = self._create_group_selector("Group 1", x_values, hue_values)
        self.group2_widget = self._create_group_selector("Group 2", x_values, hue_values)
        
        group_selectors_layout.addWidget(self.group1_widget)
        group_selectors_layout.addWidget(self.group2_widget)
        
        # メインレイアウトにグループ選択部分を追加
        main_layout.addLayout(group_selectors_layout)
        
        # OK/Cancelボタンを追加
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(button_box)
        # ★★★ ここまで ★★★

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def _create_group_selector(self, title, x_values, hue_values):
        """片方のグループを選択するためのUIウィジェットを作成する"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        layout.addRow(QLabel(f"<b>{title}</b>"))

        x_combo = QComboBox()
        x_combo.addItems(x_values)
        layout.addRow(QLabel(f"{self.x_name}:"), x_combo)
        
        # サブグループ(hue)が存在する場合のみ、その選択肢を追加
        if self.hue_name and hue_values:
            hue_combo = QComboBox()
            hue_combo.addItems(hue_values)
            layout.addRow(QLabel(f"{self.hue_name}:"), hue_combo)
        
        return widget

    def get_settings(self):
        """ユーザーが選択した2つのグループの条件を返す"""
        
        def get_widget_values(group_widget):
            """指定されたウィジェットから選択値を取得するヘルパー関数"""
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