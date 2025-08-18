# main.py

import sys
from PyQt6.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QSplitter, 
    QTableView,
    QWidget
)
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # ウィンドウのタイトルを "Calcite" に変更
        self.setWindowTitle("Calcite")
        self.setGeometry(100, 100, 1200, 800)

        # 左右に分割するためのスプリッターを作成
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左側のエリア: ここにデータテーブルを配置します
        self.table_view = QTableView()
        splitter.addWidget(self.table_view)

        # 右側のエリア: ここにグラフを配置します (今は空のウィジェットを配置)
        self.graph_placeholder = QWidget()
        splitter.addWidget(self.graph_placeholder)
        
        # スプリッターの初期サイズを調整 (左:右 = 1:2)
        splitter.setSizes([400, 800])

        # スプリッターをウィンドウの中央ウィジェットとして設定
        self.setCentralWidget(splitter)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())