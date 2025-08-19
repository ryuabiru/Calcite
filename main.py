# main.py

import sys
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QSplitter, 
    QTableView,
    QWidget,
    QFileDialog,
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QAbstractTableModel

# --- ここからが追加部分 ---

# PandasのデータフレームをPyQtのテーブルビューに表示するための「翻訳機」クラス
class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if index.isValid():
            if role == Qt.ItemDataRole.DisplayRole:
                return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._data.columns[section])
            if orientation == Qt.Orientation.Vertical:
                return str(self._data.index[section])
        return None

# --- 追加部分はここまで ---


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Calcite")
        self.setGeometry(100, 100, 1200, 800)
        
        # --- メニューバーの作成 ---
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File") # &F でショートカットキー(Alt+F)
        
        open_action = QAction("&Open CSV...", self)
        open_action.triggered.connect(self.open_csv_file) # アクションが実行されたらopen_csv_fileメソッドを呼び出す
        file_menu.addAction(open_action)
        # --- メニューバーここまで ---

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.table_view = QTableView()
        splitter.addWidget(self.table_view)
        self.graph_placeholder = QWidget()
        splitter.addWidget(self.graph_placeholder)
        splitter.setSizes([400, 800])
        self.setCentralWidget(splitter)

    # --- CSVファイルを開くためのメソッド ---
    def open_csv_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)")
        
        if file_path: # ファイルが選択された場合
            try:
                df = pd.read_csv(file_path)
                model = PandasModel(df)
                self.table_view.setModel(model)
            except Exception as e:
                print(f"Error opening file: {e}") # エラー処理（今はコンソールに出力するだけ）
    # --- メソッドここまで ---


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())