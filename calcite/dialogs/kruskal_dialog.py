# dialogs/kruskal_dialog.py (新規作成)

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QListWidget, QListWidgetItem,
    QDialogButtonBox, QAbstractItemView, QPushButton, QComboBox, QWidget
)
from PySide6.QtCore import Qt

class KruskalDialog(QDialog):
    """
    クラスカル・ウォリス検定のための設定を行うダイアログ。
    AnovaDialogをベースに作成。
    """
    _UNIQUE_SEPARATOR = '_#%%%_'

    def __init__(self, x_values, hue_values, x_name, hue_name, parent=None):
        super().__init__(parent)
        # ウィンドウのタイトルを変更
        self.setWindowTitle("Kruskal-Wallis H Test")
        self.setMinimumSize(400, 350)

        self.x_name = x_name
        self.hue_name = hue_name

        main_layout = QVBoxLayout(self)

        builder_widget = QWidget()
        builder_layout = QFormLayout(builder_widget)

        self.x_combo = QComboBox()
        self.x_combo.addItems(x_values)
        builder_layout.addRow(QLabel(f"{self.x_name}:"), self.x_combo)

        self.hue_combo = None
        if self.hue_name and hue_values:
            self.hue_combo = QComboBox()
            self.hue_combo.addItems(hue_values)
            builder_layout.addRow(QLabel(f"{self.hue_name}:"), self.hue_combo)

        add_button = QPushButton("Add Group to Comparison")
        
        main_layout.addWidget(builder_widget)
        main_layout.addWidget(add_button)
        main_layout.addWidget(QLabel("---"))

        main_layout.addWidget(QLabel("Groups to Compare (Select 2 or more):"))
        self.group_list = QListWidget()
        self.group_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        main_layout.addWidget(self.group_list)

        remove_button = QPushButton("Remove Selected Group(s)")
        main_layout.addWidget(remove_button)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(button_box)

        add_button.clicked.connect(self.add_group_to_list)
        remove_button.clicked.connect(self.remove_selected_groups)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def add_group_to_list(self):
        """（AnovaDialogと共通）"""
        x_val = self.x_combo.currentText()
        
        if self.hue_combo:
            hue_val = self.hue_combo.currentText()
            display_text = f"{self.x_name}: {x_val}, {self.hue_name}: {hue_val}"
            internal_name = f"{x_val}{self._UNIQUE_SEPARATOR}{hue_val}"
        else:
            display_text = f"{self.x_name}: {x_val}"
            internal_name = x_val

        for i in range(self.group_list.count()):
            if self.group_list.item(i).data(Qt.ItemDataRole.UserRole) == internal_name:
                return

        item = QListWidgetItem(display_text)
        item.setData(Qt.ItemDataRole.UserRole, internal_name)
        self.group_list.addItem(item)

    def remove_selected_groups(self):
        """（AnovaDialogと共通）"""
        for item in self.group_list.selectedItems():
            self.group_list.takeItem(self.group_list.row(item))

    def get_settings(self):
        """（AnovaDialogと共通）"""
        if self.group_list.count() < 2:
            return None
        
        selected_groups = []
        for i in range(self.group_list.count()):
            selected_groups.append(self.group_list.item(i).data(Qt.ItemDataRole.UserRole))
        return selected_groups