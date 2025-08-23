# dialogs/ttest_dialog_simple.py (新規作成)

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QListWidget, QDialogButtonBox, QAbstractItemView
)

class TTestDialogSimple(QDialog):
    """
    t検定のために、リストから2つのグループを選択するシンプルなダイアログ。
    """
    def __init__(self, group_values, group_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Independent t-test: Select Two Groups")
        
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.group_list = QListWidget()
        self.group_list.addItems(group_values)
        # 複数選択を可能にする
        self.group_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        form_layout.addRow(QLabel(f"Select two groups from '{group_name}':"), self.group_list)
        
        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def get_settings(self):
        """
        選択された2つのグループ名を返す。2つ以外が選択された場合はNoneを返す。
        """
        selected_items = self.group_list.selectedItems()
        if len(selected_items) != 2:
            return None
        return {
            "group1": selected_items[0].text(),
            "group2": selected_items[1].text(),
        }