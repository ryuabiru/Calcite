# main_window.py

import pandas as pd
from PySide6.QtWidgets import (
    QMainWindow, 
    QSplitter, 
    QTableView,
    QFileDialog,
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

from pandas_model import PandasModel
from graph_widget import GraphWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calcite")
        self.setGeometry(100, 100, 1200, 800)
        
        self._create_menu_bar()

        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.table_view = QTableView()
        splitter.addWidget(self.table_view)
        
        self.graph_widget = GraphWidget()
        splitter.addWidget(self.graph_widget)
        
        splitter.setSizes([400, 800])
        self.setCentralWidget(splitter)

        # self.table_view.selectionModel().selectionChanged.connect(self.update_graph) # ★ この行を削除します！

    def _create_menu_bar(self):
        # ... (このメソッドに変更はありません) ...
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        open_action = QAction("&Open CSV...", self)
        open_action.triggered.connect(self.open_csv_file)
        file_menu.addAction(open_action)

    def open_csv_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)")
        if file_path:
            try:
                df = pd.read_csv(file_path)
                self.model = PandasModel(df)
                self.table_view.setModel(self.model)
                
                # ★ 削除した行を、モデルがセットされた後のここに追加します！
                self.table_view.selectionModel().selectionChanged.connect(self.update_graph)
                
            except Exception as e:
                print(f"Error opening file: {e}")

    def update_graph(self):
        # ... (このメソッドに変更はありません) ...
        if not hasattr(self, 'model'):
            return

        selected_indexes = self.table_view.selectionModel().selectedIndexes()
        if not selected_indexes:
            return

        selected_columns = sorted(list(set(index.column() for index in selected_indexes)))

        if len(selected_columns) == 2:
            df = self.model._data
            x_col_index, y_col_index = selected_columns
            
            if pd.api.types.is_numeric_dtype(df.iloc[:, x_col_index]) and pd.api.types.is_numeric_dtype(df.iloc[:, y_col_index]):
                x_data = df.iloc[:, x_col_index]
                y_data = df.iloc[:, y_col_index]
                
                ax = self.graph_widget.ax
                ax.clear()
                ax.scatter(x_data, y_data)
                ax.set_xlabel(df.columns[x_col_index])
                ax.set_ylabel(df.columns[y_col_index])
                ax.set_title(f'{df.columns[y_col_index]} vs {df.columns[x_col_index]}')
                self.graph_widget.fig.tight_layout()
                self.graph_widget.canvas.draw()