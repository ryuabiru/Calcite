from __future__ import annotations

import warnings

from PySide6.QtWidgets import QFileDialog, QMessageBox

warnings.warn(
    "calcite.handlers.graph_canvas_handler is legacy Python rendering scaffolding kept for parity checks.",
    DeprecationWarning,
    stacklevel=2,
)


class GraphCanvasHandler:
    def __init__(self, main_window):
        self.main = main_window

    def replace_canvas(self, new_fig):
        if hasattr(self.main.graph_widget, "canvas") and self.main.graph_widget.canvas:
            self.main.graph_widget.canvas.setParent(None)
            self.main.graph_widget.canvas.deleteLater()

        new_canvas = new_fig.canvas
        self.main.graph_widget.layout().addWidget(new_canvas)
        self.main.graph_widget.canvas = new_canvas
        self.main.graph_widget.fig = new_fig
        if hasattr(self.main.graph_widget.fig, "axes") and self.main.graph_widget.fig.axes:
            self.main.graph_widget.ax = self.main.graph_widget.fig.axes[0]

    def clear_canvas(self):
        if hasattr(self.main.graph_widget, "canvas") and self.main.graph_widget.canvas:
            self.main.graph_widget.canvas.figure.clear()
            self.main.graph_widget.canvas.draw()

    def save_graph(self):
        if not hasattr(self.main.graph_widget, "fig"):
            QMessageBox.warning(self.main, "Warning", "No graph to save.")
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self.main, "Save Graph", "", "PNG (*.png);;JPEG (*.jpg);;SVG (*.svg);;PDF (*.pdf)"
        )
        if file_path:
            try:
                self.main.graph_widget.fig.savefig(file_path, dpi=300, bbox_inches="tight")
                QMessageBox.information(self.main, "Success", f"Graph successfully saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self.main, "Error", f"Failed to save graph: {e}")
