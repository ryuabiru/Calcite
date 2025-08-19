# properties_widget.py

from PySide6.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QLabel, QLineEdit
from PySide6.QtCore import Signal, Qt

class PropertiesWidget(QDockWidget):
    # A signal that will be emitted when any property changes
    # It will send a dictionary like {'title': 'New Title'}
    propertiesChanged = Signal(dict)

    def __init__(self, parent=None):
        super().__init__("Properties", parent)

        # Create the main widget and layout for the panel
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)

        # --- Graph Title ---
        layout.addWidget(QLabel("Title:"))
        self.title_edit = QLineEdit()
        self.title_edit.editingFinished.connect(self.on_title_changed)
        layout.addWidget(self.title_edit)

        # --- X-Axis Label ---
        layout.addWidget(QLabel("X-Axis Label:"))
        self.xaxis_edit = QLineEdit()
        self.xaxis_edit.editingFinished.connect(self.on_xaxis_changed)
        layout.addWidget(self.xaxis_edit)

        # --- Y-Axis Label ---
        layout.addWidget(QLabel("Y-Axis Label:"))
        self.yaxis_edit = QLineEdit()
        self.yaxis_edit.editingFinished.connect(self.on_yaxis_changed)
        layout.addWidget(self.yaxis_edit)
        
        layout.addStretch() # Add a spacer at the bottom

        self.setWidget(main_widget)

    def on_title_changed(self):
        self.propertiesChanged.emit({'title': self.title_edit.text()})

    def on_xaxis_changed(self):
        self.propertiesChanged.emit({'xlabel': self.xaxis_edit.text()})

    def on_yaxis_changed(self):
        self.propertiesChanged.emit({'ylabel': self.yaxis_edit.text()})