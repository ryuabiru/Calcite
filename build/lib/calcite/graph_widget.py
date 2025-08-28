# graph_widget.py

import matplotlib
matplotlib.use('QtAgg')

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

        # Figureを作成する。
        # main.pyの高DPI設定により、Qtが自動的にキャンバスをスケーリングするため、
        # ここで複雑なDPI計算は不要。Matplotlibは内部的に高品質な描画を行う。
        self.fig = Figure(tight_layout=True)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)

        # ウィジェットのレイアウトを設定
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0) # ウィジェット周りの余白をなくす
        layout.addWidget(self.canvas)
        self.setLayout(layout)