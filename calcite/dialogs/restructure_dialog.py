"""
このモジュールは、データフレームをワイド形式からロング形式に変換するための
ユーザーインターフェースを提供するRestructureDialogクラスを定義します。
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QLineEdit,
    QPushButton, QDialogButtonBox, QAbstractItemView
)

class RestructureDialog(QDialog):
    """
    データフレームをワイド形式からロング形式に再構築するためのパラメータを取得するダイアログウィンドウ。

    このダイアログでは、ユーザーが識別子列（`id_vars`）と値列（`value_vars`）を選択し、
    新しい変数名と値の列の名前を指定できます。
    """
    def __init__(self, columns, parent=None):
        """
        RestructureDialogを初期化します。

        Args:
            columns (list[str]): データフレームの列名のリスト。
            parent (QWidget, optional): 親ウィジェット。デフォルトはNone。
        """
        super().__init__(parent)
        self.setWindowTitle("データ形式の再構築 (Wide to Long)")
        self.setMinimumSize(600, 400)

        main_layout = QVBoxLayout(self)
        columns_layout = QHBoxLayout()

        # 列選択用のウィジェット
        self.all_columns_list = QListWidget()
        self.all_columns_list.addItems(columns)
        self.all_columns_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self.id_vars_list = QListWidget()
        self.id_vars_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self.value_vars_list = QListWidget()
        self.value_vars_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        # 列を移動するためのボタン
        add_id_button = QPushButton(">>\nID列に追加")
        remove_id_button = QPushButton("<<\nID列から削除")
        add_value_button = QPushButton(">>\n値列に追加")
        remove_value_button = QPushButton("<<\n値列から削除")

        # 新しい列名のための入力欄
        self.var_name_input = QLineEdit("Replicate")
        self.value_name_input = QLineEdit("Value")

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        # レイアウトの組み立て
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("全ての列:"))
        left_panel.addWidget(self.all_columns_list)

        id_buttons_panel = QVBoxLayout()
        id_buttons_panel.addStretch()
        id_buttons_panel.addWidget(add_id_button)
        id_buttons_panel.addWidget(remove_id_button)
        id_buttons_panel.addStretch()

        value_buttons_panel = QVBoxLayout()
        value_buttons_panel.addStretch()
        value_buttons_panel.addWidget(add_value_button)
        value_buttons_panel.addWidget(remove_value_button)
        value_buttons_panel.addStretch()

        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("識別子列 (変更されない列):"))
        right_panel.addWidget(self.id_vars_list)
        right_panel.addWidget(QLabel("値列 (まとめられる列):"))
        right_panel.addWidget(self.value_vars_list)

        columns_layout.addLayout(left_panel)
        columns_layout.addLayout(id_buttons_panel)
        columns_layout.addLayout(right_panel)
        columns_layout.insertLayout(2, value_buttons_panel)

        main_layout.addLayout(columns_layout)
        main_layout.addWidget(QLabel("新しい変数名の列:"))
        main_layout.addWidget(self.var_name_input)
        main_layout.addWidget(QLabel("新しい値の列:"))
        main_layout.addWidget(self.value_name_input)
        main_layout.addWidget(button_box)

        # シグナルの接続
        add_id_button.clicked.connect(lambda: self.move_items(self.all_columns_list, self.id_vars_list))
        remove_id_button.clicked.connect(lambda: self.move_items(self.id_vars_list, self.all_columns_list))
        add_value_button.clicked.connect(lambda: self.move_items(self.all_columns_list, self.value_vars_list))
        remove_value_button.clicked.connect(lambda: self.move_items(self.value_vars_list, self.all_columns_list))

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def move_items(self, source_list: QListWidget, dest_list: QListWidget):
        """
        選択された項目を、移動元のQListWidgetから移動先のQListWidgetへ移します。

        Args:
            source_list (QListWidget): 項目を移動する元のリストウィジェット。
            dest_list (QListWidget): 項目を移動する先のリストウィジェット。
        """
        for item in source_list.selectedItems():
            dest_list.addItem(source_list.takeItem(source_list.row(item)))

    def get_settings(self) -> dict:
        """
        ユーザーがダイアログで設定した内容を取得します。

        Returns:
            dict: 選択された'id_vars'、'value_vars'、および新しい
                  'var_name'と'value_name'を含む辞書。
        """
        id_vars = [self.id_vars_list.item(i).text() for i in range(self.id_vars_list.count())]
        value_vars = [self.value_vars_list.item(i).text() for i in range(self.value_vars_list.count())]
        return {
            "id_vars": id_vars,
            "value_vars": value_vars,
            "var_name": self.var_name_input.text(),
            "value_name": self.value_name_input.text(),
        }