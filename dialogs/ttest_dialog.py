# dialogs/ttest_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QComboBox, 
    QDialogButtonBox, QWidget, QHBoxLayout, QPushButton, QScrollArea
)
from functools import partial

class TTestDialog(QDialog):
    """
    独立t検定のための設定を行うダイアログ（Tidy Data形式対応）。
    複数のフィルタリング条件で2つのグループを定義し、比較させることができる。
    """
    def __init__(self, columns, df, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Independent t-test")
        self.df = df
        self.columns = [col for col in columns if df[col].dtype == 'object' or df[col].dtype == 'int64']
        self.value_columns = [col for col in columns if df[col].dtype == 'float64' or df[col].dtype == 'int64']
        
        self.setMinimumSize(600, 400)

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # --- Value Column Selection ---
        self.value_column_combo = QComboBox()
        self.value_column_combo.addItems(self.value_columns)
        form_layout.addRow(QLabel("Value Column (Dependent Variable):"), self.value_column_combo)
        
        main_layout.addLayout(form_layout)

        # --- Group Definition Areas ---
        splitter = QHBoxLayout()
        self.group1_widget = self._create_group_widget("Group 1")
        self.group2_widget = self._create_group_widget("Group 2")
        splitter.addWidget(self.group1_widget)
        splitter.addWidget(self.group2_widget)
        main_layout.addLayout(splitter)

        # --- OK/Cancel Buttons ---
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def _create_group_widget(self, title):
        """片方のグループを定義するためのUIウィジェットを作成する"""
        group_box = QWidget()
        layout = QVBoxLayout(group_box)
        layout.addWidget(QLabel(f"<b>{title}</b>"))
        
        add_filter_button = QPushButton("Add Filter")
        
        # フィルターを追加するためのレイアウト
        filters_widget = QWidget()
        filters_layout = QFormLayout(filters_widget)
        
        add_filter_button.clicked.connect(partial(self._add_filter, filters_layout))
        
        layout.addWidget(add_filter_button)
        layout.addWidget(filters_widget)
        
        # ウィジェットにレイアウトを保持させる
        group_box.filters_layout = filters_layout
        
        # 最初のフィルターを自動で追加
        self._add_filter(filters_layout)
        
        return group_box

    def _add_filter(self, layout):
        """フィルター条件を追加する（列と値のコンボボックス）"""
        col_combo = QComboBox()
        col_combo.addItems(self.columns)
        
        val_combo = QComboBox()
        
        # 列コンボボックスの選択が変更されたら、値コンボボックスの中身を更新
        col_combo.currentTextChanged.connect(partial(self._update_value_combo, col_combo, val_combo))
        
        # 初期状態を更新
        self._update_value_combo(col_combo, val_combo)

        layout.addRow(col_combo, val_combo)

    def _update_value_combo(self, col_combo, val_combo, new_text=None):
        """列の選択に応じて、値のコンボボックスの選択肢を更新する"""
        col_name = col_combo.currentText()
        if col_name and not self.df.empty:
            try:
                # 選択された列のユニークな値を取得してリストに追加
                unique_values = sorted(self.df[col_name].unique().astype(str))
                current_val = val_combo.currentText() # 以前の選択を保持
                val_combo.clear()
                val_combo.addItems(unique_values)
                val_combo.setCurrentText(current_val) # 可能であれば復元
            except KeyError:
                val_combo.clear()
    
    def get_settings(self):
        """ダイアログの設定を辞書として取得する"""
        settings = {
            "value_col": self.value_column_combo.currentText(),
            "group1_filters": self._get_filters_from_layout(self.group1_widget.filters_layout),
            "group2_filters": self._get_filters_from_layout(self.group2_widget.filters_layout)
        }
        return settings

    def _get_filters_from_layout(self, layout):
        """レイアウトからフィルター条件を辞書として抽出する"""
        filters = {}
        for i in range(layout.rowCount()):
            col_combo = layout.itemAt(i, QFormLayout.ItemRole.LabelRole).widget()
            val_combo = layout.itemAt(i, QFormLayout.ItemRole.FieldRole).widget()
            col_name = col_combo.currentText()
            value = val_combo.currentText()
            if col_name and value:
                filters[col_name] = value
        return filters