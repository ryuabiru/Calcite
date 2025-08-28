# properties_widget.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTabWidget
from PySide6.QtCore import Signal

from .tabs.data_tab import DataTab
from .tabs.format_tab import FormatTab
from .tabs.text_tab import TextTab
from .tabs.axes_tab import AxesTab

class PropertiesWidget(QWidget):
    propertiesChanged = Signal()
    graphUpdateRequest = Signal()
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
        # ▼▼▼ タブ名を変更 ▼▼▼
        tab_widget.addTab(self.text_tab, "テキストと凡例")
        # ▲▲▲ ここまで ▲▲▲
        tab_widget.addTab(self.axes_tab, "軸")

        update_button = QPushButton("Update Graph")
        
        main_layout.addWidget(tab_widget)
        main_layout.addWidget(update_button)

        self.connect_signals()
        update_button.clicked.connect(self.graphUpdateRequest.emit)

    def connect_signals(self):
        """各タブからのシグナルを接続する"""
        self.data_tab.subgroupColumnChanged.connect(self.format_tab.update_subgroup_color_ui)
        self.data_tab.subgroupColumnChanged.connect(self.subgroupColumnChanged.emit)

        self.format_tab.propertiesChanged.connect(self.propertiesChanged.emit)
        
        # TextTab
        self.text_tab.title_edit.editingFinished.connect(self.propertiesChanged.emit)
        self.text_tab.xaxis_edit.editingFinished.connect(self.propertiesChanged.emit)
        self.text_tab.yaxis_edit.editingFinished.connect(self.propertiesChanged.emit)
        self.text_tab.title_fontsize_spin.valueChanged.connect(lambda val: self.propertiesChanged.emit())
        self.text_tab.xlabel_fontsize_spin.valueChanged.connect(lambda val: self.propertiesChanged.emit())
        self.text_tab.ylabel_fontsize_spin.valueChanged.connect(lambda val: self.propertiesChanged.emit())
        self.text_tab.ticks_fontsize_spin.valueChanged.connect(lambda val: self.propertiesChanged.emit())
        # ▼▼▼ 新しく移設した凡例ウィジェットのシグナルを接続 ▼▼▼
        self.text_tab.legend_pos_combo.currentIndexChanged.connect(lambda: self.propertiesChanged.emit())
        self.text_tab.legend_title_edit.editingFinished.connect(self.propertiesChanged.emit)
        # ▲▲▲ ここまで ▲▲▲

        # AxesTab
        self.axes_tab.xmin_edit.editingFinished.connect(self.propertiesChanged.emit)
        self.axes_tab.xmax_edit.editingFinished.connect(self.propertiesChanged.emit)
        self.axes_tab.ymin_edit.editingFinished.connect(self.propertiesChanged.emit)
        self.axes_tab.ymax_edit.editingFinished.connect(self.propertiesChanged.emit)
        self.axes_tab.grid_check.stateChanged.connect(lambda state: self.propertiesChanged.emit())
        self.axes_tab.x_log_scale_check.stateChanged.connect(lambda state: self.propertiesChanged.emit())
        self.axes_tab.y_log_scale_check.stateChanged.connect(lambda state: self.propertiesChanged.emit())

    def get_properties(self):
        """全てのタブから設定値を取得し、一つの辞書に統合して返す"""
        props = {}
        props.update(self.format_tab.get_properties())
        props.update(self.text_tab.get_properties())
        props.update(self.axes_tab.get_properties())
        return props

    def set_columns(self, columns):
        """DataTabに列名リストを渡す"""
        self.data_tab.set_columns(columns)