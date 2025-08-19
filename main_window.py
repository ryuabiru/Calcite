# main_window.py

import pandas as pd
import numpy as np
from PySide6.QtWidgets import (
    QMainWindow, 
    QSplitter, 
    QTableView,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from scipy.stats import ttest_ind
from scipy.stats import linregress

from pandas_model import PandasModel
from graph_widget import GraphWidget
from properties_widget import PropertiesWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calcite")
        self.setGeometry(100, 100, 1024, 512)
        
        self._create_menu_bar()

        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.table_view = QTableView()
        splitter.addWidget(self.table_view)
        
        self.graph_widget = GraphWidget()
        splitter.addWidget(self.graph_widget)
        
        splitter.setSizes([400, 800])
        self.setCentralWidget(splitter)
        
        self.properties_panel = PropertiesWidget()
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.properties_panel)
        self.properties_panel.propertiesChanged.connect(self.update_graph_properties)

    def _create_menu_bar(self):
        menu_bar = self.menuBar()
        
        # ファイルメニュー
        file_menu = menu_bar.addMenu("&File")
        open_action = QAction("&Open CSV...", self)
        open_action.triggered.connect(self.open_csv_file)
        file_menu.addAction(open_action)
        
        analysis_menu = menu_bar.addMenu("&Analysis")
        ttest_action = QAction("&Independent t-test...", self)
        ttest_action.triggered.connect(self.perform_t_test)
        analysis_menu.addAction(ttest_action)

        linreg_action = QAction("&Linear Regression...", self)
        linreg_action.triggered.connect(self.perform_linear_regression)
        analysis_menu.addAction(linreg_action)

    def open_csv_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)")
        if file_path:
            try:
                df = pd.read_csv(file_path)
                self.model = PandasModel(df)
                self.table_view.setModel(self.model)
                self.table_view.selectionModel().selectionChanged.connect(self.update_graph)
            except Exception as e:
                print(f"Error opening file: {e}")

    def perform_t_test(self):
        # データが読み込まれていないか、列が2つ選択されていなければ何もしない
        if not hasattr(self, 'model'):
            QMessageBox.warning(self, "Warning", "Please load data first.")
            return

        selected_indexes = self.table_view.selectionModel().selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(self, "Warning", "Please select two columns to compare.")
            return
            
        selected_columns = sorted(list(set(index.column() for index in selected_indexes)))

        if len(selected_columns) != 2:
            QMessageBox.warning(self, "Warning", "Please select exactly two columns.")
            return

        # 選択された2列のデータを取得
        df = self.model._data
        col1_index, col2_index = selected_columns
        col1_data = df.iloc[:, col1_index].dropna() # 欠損値は無視
        col2_data = df.iloc[:, col2_index].dropna()

        # t検定を実行
        t_stat, p_value = ttest_ind(col1_data, col2_data)

        # 結果をフォーマットして表示
        result_text = (
            f"Independent t-test results:\n\n"
            f"Comparing:\n- {df.columns[col1_index]} (Mean: {col1_data.mean():.3f})\n"
            f"- {df.columns[col2_index]} (Mean: {col2_data.mean():.3f})\n\n"
            f"t-statistic: {t_stat:.4f}\n"
            f"p-value: {p_value:.4f}\n\n"
        )

        if p_value < 0.05:
            result_text += "Conclusion: The difference is statistically significant (p < 0.05)."
        else:
            result_text += "Conclusion: The difference is not statistically significant (p >= 0.05)."

        QMessageBox.information(self, "t-test Result", result_text)

    def perform_linear_regression(self):
        if not hasattr(self, 'model'):
            QMessageBox.warning(self, "Warning", "Please load data first.")
            return

        selected_indexes = self.table_view.selectionModel().selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(self, "Warning", "Please select two columns for regression.")
            return
            
        selected_columns = sorted(list(set(index.column() for index in selected_indexes)))

        if len(selected_columns) != 2:
            QMessageBox.warning(self, "Warning", "Please select exactly two columns.")
            return

        df = self.model._data
        x_col_index, y_col_index = selected_columns
        
        # 欠損値を除外
        x_data = df.iloc[:, x_col_index].dropna()
        y_data = df.iloc[:, y_col_index].dropna()
        
        # 線形回帰を実行
        slope, intercept, r_value, p_value, std_err = linregress(x_data, y_data)
        r_squared = r_value**2

        # 回帰直線を描画するためのX値を準備
        x_line = np.array([x_data.min(), x_data.max()])
        y_line = slope * x_line + intercept

        # グラフを更新
        ax = self.graph_widget.ax
        # 既存の回帰直線を削除 (あれば)
        if hasattr(self, 'regression_line') and self.regression_line in ax.lines:
            self.regression_line.remove()
            
        # 新しい回帰直線をプロット
        self.regression_line, = ax.plot(x_line, y_line, color='red', linestyle='--', 
                                         label=f'R² = {r_squared:.4f}')
        
        ax.legend() # 凡例を表示
        self.graph_widget.canvas.draw() # キャンバスを再描画
        
    def update_graph_properties(self, properties):
        ax = self.graph_widget.ax
        
        if 'title' in properties:
            ax.set_title(properties['title'])
        if 'xlabel' in properties:
            ax.set_xlabel(properties['xlabel'])
        if 'ylabel' in properties:
            ax.set_ylabel(properties['ylabel'])
        
        self.graph_widget.fig.tight_layout()
        self.graph_widget.canvas.draw()
        
    def update_graph(self):
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