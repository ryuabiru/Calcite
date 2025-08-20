# ttest_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QComboBox, 
    QDialogButtonBox, QListWidget, QAbstractItemView
)

class TTestDialog(QDialog):
    """
    独立t検定のための設定を行うダイアログ（Tidy Data形式対応）。
    値の列、グループ分けの列、そして比較する2つのグループを選択させる。
    """
    def __init__(self, columns, df, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Independent t-test")
        self.df = df
        self.columns = columns

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # --- ウィジェットの作成 ---
        self.value_column_combo = QComboBox()
        self.group_column_combo = QComboBox()
        self.group1_list = QListWidget()
        self.group2_list = QListWidget()

        self.value_column_combo.addItems(self.columns)
        self.group_column_combo.addItems(self.columns)

        # グループ選択リストは単一選択に
        self.group1_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.group2_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        # --- レイアウトの組み立て ---
        form_layout.addRow(QLabel("Value Column (Dependent Variable):"), self.value_column_combo)
        form_layout.addRow(QLabel("Group Column (Independent Variable):"), self.group_column_combo)
        form_layout.addRow(QLabel("Select Group 1:"), self.group1_list)
        form_layout.addRow(QLabel("Select Group 2:"), self.group2_list)
        
        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)

        # --- シグナルの接続 ---
        self.group_column_combo.currentTextChanged.connect(self.update_group_lists)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # 初期状態を更新
        self.update_group_lists(self.group_column_combo.currentText())

    def update_group_lists(self, group_col):
        """グループ列が選択されたら、その列のユニークな値をリストに表示する"""
        self.group1_list.clear()
        self.group2_list.clear()
        if group_col and not self.df.empty:
            try:
                unique_groups = sorted(self.df[group_col].unique().astype(str))
                self.group1_list.addItems(unique_groups)
                self.group2_list.addItems(unique_groups)
            except KeyError:
                pass # 列が存在しない場合は何もしない

    def get_settings(self):
        """ユーザーが選択した設定を取得する"""
        g1_items = self.group1_list.selectedItems()
        g2_items = self.group2_list.selectedItems()
        return {
            "value_col": self.value_column_combo.currentText(),
            "group_col": self.group_column_combo.currentText(),
            "group1": g1_items[0].text() if g1_items else None,
            "group2": g2_items[0].text() if g2_items else None,
        }