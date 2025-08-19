# graph_widget.py

import matplotlib
matplotlib.use('QtAgg') # PySide/PyQtを自動検出

from PySide6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class GraphWidget(QWidget):
    """
    Matplotlibのグラフを描画するためのウィジェット。
    FigureCanvasQTAggをラップし、PySide6のレイアウトに配置する。
    """
    def __init__(self, parent=None):
        """
        ウィジェットを初期化し、MatplotlibのFigureとAxesをセットアップする。
        """
        super().__init__(parent)

        # Matplotlibの図（Figure）と描画エリア（Axes）を作成
        self.fig = Figure(dpi=150)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)

        # ウィジェットのレイアウトを設定
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)


from matplotlib.figure import Figure

class GraphWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Matplotlibの図（Figure）と描画エリア（Axes）を作成
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)

        # ウィジェットのレイアウトを設定
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)