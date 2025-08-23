# dialogs/anova_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QListWidget, 
    QDialogButtonBox, QAbstractItemView
)

class AnovaDialog(QDialog):
    """
    一元配置分散分析（One-way ANOVA）のための設定を行うダイアログ。
    リストから検定対象のグループを複数選択させる。
    """
    def __init__(self, group_values, group_name, parent=None):
        """
        ダイアログのUIを初期化する。

        Args:
            group_values (list): 検定対象となるユニークなグループ名のリスト。
            group_name (str): グループ分けに使用した列の名前。
            parent (QWidget, optional): 親ウィジェット。
        """
        super().__init__(parent)
        self.setWindowTitle("One-way ANOVA")

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # --- Widgets ---
        self.group_list = QListWidget()
        self.group_list.addItems(group_values)
        # 複数選択を可能にする
        self.group_list.setSelectionMode(
            QAbstractItemView.SelectionMode.MultiSelection
        )
        
        # OK and Cancel buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )

        # --- Assemble Layout ---
        form_layout.addRow(QLabel(f"Select 3 or more groups from '{group_name}':"), self.group_list)
        
        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)

        # --- Connect Signals ---
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def get_settings(self):
        """
        ユーザーが選択したグループ名のリストを返す。
        3つ未満の場合はNoneを返す。
        """
        selected_items = self.group_list.selectedItems()
        if len(selected_items) < 2: # 2群でも比較できるよう修正
            return None
        return [item.text() for item in selected_items]