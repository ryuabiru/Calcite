import warnings

from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from PySide6.QtCore import Signal

from .data_tab_tidy import TidyDataTab

warnings.warn(
    "calcite.tabs.data_tab is part of the legacy Python UI and will be retired after the Rust migration.",
    DeprecationWarning,
    stacklevel=2,
)

class DataTab(QWidget):
    subgroupColumnChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stacked_widget = QStackedWidget()

        self.tidy_tab = TidyDataTab()

        self.stacked_widget.addWidget(self.tidy_tab)

        layout.addWidget(self.stacked_widget)

        self.tidy_tab.subgroupColumnChanged.connect(self.subgroupColumnChanged.emit)

    def set_graph_type(self, graph_type):
        if graph_type in ['scatter', 'summary_scatter', 'bar', 'countplot', 'stacked_bar', 'stacked_bar_100', 'proportion_plot', 'mosaic', 'heatmap', 'correlation_heatmap', 'histogram', 'boxplot', 'violin', 'pointplot', 'lineplot']:
            self.stacked_widget.setCurrentWidget(self.tidy_tab)
            self.tidy_tab.x_axis_label.setVisible(True)
            self.tidy_tab.x_axis_combo.setVisible(True)
            self.tidy_tab.y_axis_label.setVisible(True)
            self.tidy_tab.y_axis_combo.setVisible(True)

            if graph_type == 'histogram':
                self.tidy_tab.y_axis_label.setText("Value Column:")
                self.tidy_tab.x_axis_label.setVisible(False)
                self.tidy_tab.x_axis_combo.setVisible(False)
            elif graph_type == 'countplot':
                self.tidy_tab.x_axis_label.setText("X-Axis (Category):")
                self.tidy_tab.y_axis_label.setText("Count:")
                self.tidy_tab.y_axis_combo.setVisible(False)
            elif graph_type in ['stacked_bar', 'stacked_bar_100', 'proportion_plot', 'mosaic']:
                self.tidy_tab.x_axis_label.setText("X-Axis (Category):")
                self.tidy_tab.y_axis_label.setText("Count:")
                self.tidy_tab.y_axis_combo.setVisible(False)
            elif graph_type == 'heatmap':
                self.tidy_tab.x_axis_label.setText("X-Axis (Category):")
                self.tidy_tab.y_axis_label.setText("Y-Axis (Category):")
            elif graph_type == 'correlation_heatmap':
                self.tidy_tab.x_axis_label.setText("Auto:")
                self.tidy_tab.y_axis_label.setText("Auto:")
                self.tidy_tab.x_axis_combo.setVisible(False)
                self.tidy_tab.y_axis_combo.setVisible(False)
            else:
                self.tidy_tab.y_axis_label.setText("Y-Axis (Value):")
                self.tidy_tab.x_axis_label.setText("X-Axis (Category):")

    def set_columns(self, columns):
        self.tidy_tab.set_columns(columns)

    def get_current_settings(self):
        current_widget = self.stacked_widget.currentWidget()
        if hasattr(current_widget, 'get_settings'):
            return current_widget.get_settings()
        return {}
    
    def set_settings(self, settings):
        current_widget = self.stacked_widget.currentWidget()
        if hasattr(current_widget, 'set_settings'):
            current_widget.set_settings(settings)
