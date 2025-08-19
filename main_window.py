# main_window.py

import pandas as pd
import numpy as np
from PySide6.QtWidgets import (
    QMainWindow, 
    QSplitter, 
    QTableView,
    QFileDialog,
    QMessageBox,
    QToolBar,
    QMenu,
    QLineEdit,
)
from PySide6.QtGui import QAction, QActionGroup, QIcon
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
        
        self.current_graph_type = 'scatter'
        self.header_editor = None
        
        self._create_menu_bar()
        self._create_toolbar()

        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.table_view = QTableView()
        splitter.addWidget(self.table_view)
        
        self.graph_widget = GraphWidget()
        # 右クリックメニューを有効にする
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.show_table_context_menu)
        self.table_view.horizontalHeader().sectionDoubleClicked.connect(self.edit_header)
        
        splitter.addWidget(self.graph_widget)
        
        splitter.setSizes([400, 800])
        self.setCentralWidget(splitter)
        
        self.properties_panel = PropertiesWidget()
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.properties_panel)
        self.properties_panel.propertiesChanged.connect(self.update_graph_properties)
        self.properties_panel.graphUpdateRequest.connect(self.update_graph)

    # ★--- ヘッダー編集用のメソッドを2つ追加 ---★
    def edit_header(self, logicalIndex):
        # 既存のエディタがあれば閉じる
        if self.header_editor:
            self.header_editor.close()

        header = self.table_view.horizontalHeader()
        model = self.table_view.model()
        
        # 編集用のQLineEditを作成し、現在のヘッダー名を設定
        self.header_editor = QLineEdit(parent=header)
        self.header_editor.setText(model.headerData(logicalIndex, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole))
        
        # エディタをヘッダーの正しい位置に表示
        self.header_editor.setGeometry(header.sectionViewportPosition(logicalIndex), 0, header.sectionSize(logicalIndex), header.height())
        self.header_editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 編集が完了したらfinish_header_editを呼び出す
        self.header_editor.editingFinished.connect(lambda: self.finish_header_edit(logicalIndex))
        
        self.header_editor.show()
        self.header_editor.setFocus()

    def finish_header_edit(self, logicalIndex):
        if self.header_editor:
            new_text = self.header_editor.text()
            self.table_view.model().setHeaderData(logicalIndex, Qt.Orientation.Horizontal, new_text, Qt.ItemDataRole.EditRole)
            
            # エディタを閉じて削除
            self.header_editor.close()
            self.header_editor = None

    def show_table_context_menu(self, position):
        if not hasattr(self, 'model'):
            return

        menu = QMenu()
        
        insert_row_action = QAction("Insert Row Above", self)
        insert_row_action.triggered.connect(lambda: self.insert_row())
        menu.addAction(insert_row_action)

        remove_row_action = QAction("Remove Selected Row(s)", self)
        remove_row_action.triggered.connect(lambda: self.remove_row())
        menu.addAction(remove_row_action)

        menu.addSeparator()

        insert_col_action = QAction("Insert Column Left", self)
        insert_col_action.triggered.connect(lambda: self.insert_col())
        menu.addAction(insert_col_action)

        remove_col_action = QAction("Remove Selected Column(s)", self)
        remove_col_action.triggered.connect(lambda: self.remove_col())
        menu.addAction(remove_col_action)
        
        # メニューをカーソル位置に表示
        menu.exec(self.table_view.viewport().mapToGlobal(position))

    def insert_row(self):
        selected_index = self.table_view.currentIndex()
        row = selected_index.row() if selected_index.isValid() else self.model.rowCount()
        self.model.insertRows(row, 1)

    def remove_row(self):
        selected_rows = sorted(list(set(index.row() for index in self.table_view.selectionModel().selectedRows())))
        if not selected_rows:
            return
        
        # 後ろから削除しないとインデックスがずれる
        for row in reversed(selected_rows):
            self.model.removeRows(row, 1)

    def insert_col(self):
        selected_index = self.table_view.currentIndex()
        col = selected_index.column() if selected_index.isValid() else self.model.columnCount()
        self.model.insertColumns(col, 1)

    def remove_col(self):
        selected_cols = sorted(list(set(index.column() for index in self.table_view.selectionModel().selectedColumns())))
        if not selected_cols:
            return

        for col in reversed(selected_cols):
            self.model.removeColumns(col, 1)

    def _create_toolbar(self):
        toolbar = QToolBar("Graph Type")
        self.addToolBar(toolbar)

        action_group = QActionGroup(self)
        action_group.setExclusive(True)

        scatter_action = QAction("Scatter Plot", self)
        scatter_action.setCheckable(True)
        scatter_action.setChecked(True)
        scatter_action.triggered.connect(lambda: self.set_graph_type('scatter'))
        toolbar.addAction(scatter_action)
        action_group.addAction(scatter_action)

        bar_action = QAction("Bar Chart", self)
        bar_action.setCheckable(True)
        bar_action.triggered.connect(lambda: self.set_graph_type('bar'))
        toolbar.addAction(bar_action)
        action_group.addAction(bar_action)

    def set_graph_type(self, graph_type):
        self.current_graph_type = graph_type
        self.update_graph() # グラフタイプが変更されたらグラフを再描画

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
                
                # ★--- プロパティパネルにカラム名を設定 ---★
                self.properties_panel.set_columns(df.columns)
                
                # シグナルとスロットを接続
                self.table_view.selectionModel().selectionChanged.connect(self.update_graph)
                self.model.dataChanged.connect(self.update_graph) 
                
                # ★--- ヘッダーのデータ変更もグラフ更新に接続 ---★
                self.model.headerDataChanged.connect(self.update_graph)

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

    # ★--- update_graphメソッドを全面的に書き換え ---★
    def update_graph(self):
        if not hasattr(self, 'model'):
            return

        df = self.model._data
        ax = self.graph_widget.ax
        ax.clear()

        # プロパティパネルから選択された列名を取得
        y_col = self.properties_panel.y_axis_combo.currentText()
        x_col = self.properties_panel.x_axis_combo.currentText()
        subgroup_col = self.properties_panel.subgroup_combo.currentText()

        # Y軸とX軸が選択されていなければ何もしない
        if not y_col or not x_col:
            self.graph_widget.canvas.draw()
            return
            
        # グラフの種類に応じて描画
        if self.current_graph_type == 'scatter':
            # 散布図は2つの数値列が必要
            if pd.api.types.is_numeric_dtype(df[y_col]) and pd.api.types.is_numeric_dtype(df[x_col]):
                ax.scatter(df[x_col], df[y_col])
                ax.set_xlabel(x_col)
                ax.set_ylabel(y_col)

        elif self.current_graph_type == 'bar':
            try:
                # サブグループが指定されているかで処理を分岐
                if subgroup_col:
                    # Multi-indexで集計 (クロス集計)
                    summary = df.groupby([x_col, subgroup_col])[y_col].agg(['mean', 'std'])
                    summary.unstack().plot(kind='bar', y='mean', yerr='std', ax=ax, capsize=4, rot=0)

                else:
                    # 単一のグループで集計
                    summary = df.groupby(x_col)[y_col].agg(['mean', 'std'])
                    summary.plot(kind='bar', y='mean', yerr='std', ax=ax, capsize=4, rot=0, legend=False)
                
                ax.set_xlabel(x_col)
                ax.set_ylabel(f"Mean of {y_col}")

            except Exception as e:
                print(f"Could not generate bar chart: {e}")

        # グラフの再描画とプロパティの適用
        self.update_graph_properties(self.properties_panel.on_properties_changed() or {})
        self.graph_widget.fig.tight_layout()
        self.graph_widget.canvas.draw()