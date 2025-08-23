# tabs/data_tab.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from PySide6.QtCore import Signal

# 作成済みの2つのUI部品をインポート
from .data_tab_tidy import TidyDataTab
from .data_tab_paired import PairedDataTab

class DataTab(QWidget):
    """
    グラフタイプに応じてデータ選択UIを切り替えるコンテナウィジェット。
    """
    # TidyDataTabからのシグナルを中継するためのシグナル
    subgroupColumnChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0) # 余白をなくす

        # UIを切り替えるためのQStackedWidgetを作成
        self.stacked_widget = QStackedWidget()
        
        # 2種類のUIウィジェットをインスタンス化
        self.tidy_tab = TidyDataTab()
        self.paired_tab = PairedDataTab()
        
        # StackedWidgetに2つのUIを追加
        self.stacked_widget.addWidget(self.tidy_tab)
        self.stacked_widget.addWidget(self.paired_tab)
        
        layout.addWidget(self.stacked_widget)
        
        # TidyDataTabのシグナルを、このクラスのシグナルに接続して中継
        self.tidy_tab.subgroupColumnChanged.connect(self.subgroupColumnChanged.emit)

    def set_graph_type(self, graph_type):
        """表示するUIをグラフタイプに応じて切り替える"""
        if graph_type in ['scatter', 'bar', 'histogram']: # histogramを追加
            self.stacked_widget.setCurrentWidget(self.tidy_tab)

            if graph_type == 'histogram':
                self.tidy_tab.y_axis_label.setText("Value Column:")
                self.tidy_tab.x_axis_label.setVisible(False)
                self.tidy_tab.x_axis_combo.setVisible(False)
            else:
                self.tidy_tab.y_axis_label.setText("Y-Axis (Value):")
                self.tidy_tab.x_axis_label.setVisible(True)
                self.tidy_tab.x_axis_combo.setVisible(True)
        elif graph_type == 'paired_scatter':
            self.stacked_widget.setCurrentWidget(self.paired_tab)

    def set_columns(self, columns):
        """両方のタブのコンボボックスの選択肢を更新する"""
        self.tidy_tab.set_columns(columns)
        self.paired_tab.set_columns(columns)

    def get_current_settings(self):
        """現在表示されているタブの設定値を取得する"""
        current_widget = self.stacked_widget.currentWidget()
        if hasattr(current_widget, 'get_settings'):
            return current_widget.get_settings()
        return {}