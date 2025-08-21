# properties_widget.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTabWidget
from PySide6.QtCore import Signal

from tabs.data_tab import DataTab
from tabs.format_tab import FormatTab
from tabs.text_tab import TextTab
from tabs.axes_tab import AxesTab

class PropertiesWidget(QWidget):
    propertiesChanged = Signal()
    graphUpdateRequest = Signal()
    # DataTabのシグナルを中継する
    subgroupColumnChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        tab_widget = QTabWidget()

        self.data_tab = DataTab()
        self.format_tab = FormatTab()
        self.text_tab = TextTab()
        self.axes_tab = AxesTab()

        tab_widget.addTab(self.data_tab, "データ")
        tab_widget.addTab(self.format_tab, "フォーマット")
        tab_widget.addTab(self.text_tab, "テキスト")
        tab_widget.addTab(self.axes_tab, "軸")

        update_button = QPushButton("Update Graph")
        
        main_layout.addWidget(tab_widget)
        main_layout.addWidget(update_button)

        self.connect_signals()
        update_button.clicked.connect(self.graphUpdateRequest.emit)

    def connect_signals(self):
        """各タブからのシグナルを接続する"""
        # DataTab -> FormatTab (サブグループUI更新のため)
        self.data_tab.subgroupColumnChanged.connect(self.format_tab.update_subgroup_color_ui)
        # DataTab -> MainWindow (グラフ更新のトリガーのため)
        self.data_tab.subgroupColumnChanged.connect(self.subgroupColumnChanged.emit)

        # 各タブの変更をpropertiesChangedシグナルとして中継
        self.format_tab.propertiesChanged.connect(self.propertiesChanged.emit)
        
        # TextTab
        self.text_tab.title_edit.editingFinished.connect(self.propertiesChanged.emit)
        self.text_tab.xaxis_edit.editingFinished.connect(self.propertiesChanged.emit)
        self.text_tab.yaxis_edit.editingFinished.connect(self.propertiesChanged.emit)
        # valueChangedシグナルをlambdaでラップする
        self.text_tab.title_fontsize_spin.valueChanged.connect(lambda: self.propertiesChanged.emit())
        self.text_tab.xlabel_fontsize_spin.valueChanged.connect(lambda: self.propertiesChanged.emit())
        self.text_tab.ylabel_fontsize_spin.valueChanged.connect(lambda: self.propertiesChanged.emit())
        self.text_tab.ticks_fontsize_spin.valueChanged.connect(lambda: self.propertiesChanged.emit())

        # AxesTab
        self.axes_tab.xmin_edit.editingFinished.connect(self.propertiesChanged.emit)
        self.axes_tab.xmax_edit.editingFinished.connect(self.propertiesChanged.emit)
        self.axes_tab.ymin_edit.editingFinished.connect(self.propertiesChanged.emit)
        self.axes_tab.ymax_edit.editingFinished.connect(self.propertiesChanged.emit)
        # stateChangedシグナルをlambdaでラップする
        self.axes_tab.grid_check.stateChanged.connect(lambda: self.propertiesChanged.emit())
        self.axes_tab.x_log_scale_check.stateChanged.connect(lambda: self.propertiesChanged.emit())
        self.axes_tab.y_log_scale_check.stateChanged.connect(lambda: self.propertiesChanged.emit())

    def get_properties(self):
        """全てのタブから設定値を取得し、一つの辞書に統合して返す"""
        props = {}
        # データ選択タブの値は、GraphManagerが直接参照する
        # props.update(self.data_tab.get_properties())
        
        # 他のタブから設定値を取得
        props.update(self.format_tab.get_properties())
        props.update(self.text_tab.get_properties())
        props.update(self.axes_tab.get_properties())
        return props

    def set_columns(self, columns):
        """DataTabに列名リストを渡す"""
        self.data_tab.set_columns(columns)