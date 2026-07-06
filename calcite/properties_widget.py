# properties_widget.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PySide6.QtCore import Signal

from .application.ui_controller import resolve_legend_position_for_graph_type
from .tabs.format_tab import FormatTab
from .tabs.text_tab import TextTab
from .tabs.axes_tab import AxesTab

class PropertiesWidget(QWidget):
    propertiesChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        inner_tab_widget = QTabWidget()

        self.format_tab = FormatTab()
        self.text_tab = TextTab()
        self.axes_tab = AxesTab()

        inner_tab_widget.addTab(self.format_tab, "フォーマット")
        inner_tab_widget.addTab(self.text_tab, "テキストと凡例")
        inner_tab_widget.addTab(self.axes_tab, "軸")

        main_layout.addWidget(inner_tab_widget)

    def get_properties(self):
        """全てのタブから設定値を取得し、一つの辞書に統合して返す"""
        props = {}
        props.update(self.format_tab.get_properties())
        props.update(self.text_tab.get_properties())
        props.update(self.axes_tab.get_properties())
        return props
    
    def set_properties(self, props):
        """全てのタブに設定値を渡し、UIを復元する"""
        self.format_tab.set_properties(props)
        self.text_tab.set_properties(props)
        self.axes_tab.set_properties(props)

    def sync_graph_type(self, graph_type, previous_graph_type):
        self.text_tab.update_paired_labels_visibility(graph_type == "paired_scatter")

        next_legend_position = resolve_legend_position_for_graph_type(
            previous_graph_type=previous_graph_type,
            next_graph_type=graph_type,
            current_legend_position=self.text_tab.get_legend_position(),
        )
        self.text_tab.set_legend_position(next_legend_position)
