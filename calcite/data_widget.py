# calcite/data_widget.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PySide6.QtCore import Signal

from .tabs.data_tab import DataTab

class DataWidget(QWidget):
    graphUpdateRequest = Signal()
    subgroupColumnChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panelSurface")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        self.data_tab = DataTab()
        update_button = QPushButton("Update Graph")
        update_button.setObjectName("primaryButton")
        
        main_layout.addWidget(self.data_tab)
        main_layout.addWidget(update_button)

        self.data_tab.subgroupColumnChanged.connect(self.subgroupColumnChanged.emit)
        update_button.clicked.connect(self.graphUpdateRequest.emit)

    def get_current_settings(self):
        return self.data_tab.get_current_settings()
    
    def set_settings(self, props):
        self.data_tab.set_settings(props)

    def set_columns(self, columns):
        self.data_tab.set_columns(columns)

    def set_graph_type(self, graph_type):
        self.data_tab.set_graph_type(graph_type)
