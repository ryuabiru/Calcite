# graph_widget.py

import matplotlib
matplotlib.use('QtAgg')

from PySide6.QtWidgets import QWidget, QVBoxLayout, QApplication
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

        # 高DPIに対応するために、画面の物理DPIを取得
        dpi = 96 # デフォルト値
        try:
            screen = QApplication.primaryScreen()
            if screen:
                dpi = screen.physicalDotsPerInch()
        except Exception:
            pass

        # Figureを作成。DPIはここで一度設定する。
        # tight_layout=True は、軸ラベルなどがはみ出ないように自動調整する
        self.fig = Figure(dpi=dpi, tight_layout=True)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)

        # ウィジェットのレイアウトを設定
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def resizeEvent(self, event):
        """
        ウィジェットがリサイズされたときに呼び出されるイベントハンドラ。
        このイベントを捕捉して、MatplotlibのFigureのサイズを更新する。
        """
        super().resizeEvent(event)
        
        # event.size() は、新しいウィジェットのサイズをピクセル単位で返す
        # Qt6では高DPI環境で自動的にスケーリングされるため、devicePixelRatioを乗算する必要はない
        width = event.size().width()
        height = event.size().height()
        
        if width > 0 and height > 0:
            # Figureのサイズをインチ単位で設定し直す
            # Matplotlibはインチ単位でサイズを管理するため、ピクセル数をDPIで割る
            self.fig.set_size_inches(width / self.fig.dpi, height / self.fig.dpi)
            
            # レイアウトを再計算して描画を更新
            # tight_layout()を再度呼び出すことで、新しいサイズに最適化される
            self.fig.tight_layout()
            self.canvas.draw()
