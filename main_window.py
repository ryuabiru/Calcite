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
    QApplication,
)
from PySide6.QtGui import QAction, QActionGroup, QIcon
from PySide6.QtCore import Qt
from scipy.stats import ttest_ind
from scipy.stats import linregress

from pandas_model import PandasModel
from graph_widget import GraphWidget
from properties_widget import PropertiesWidget
from restructure_dialog import RestructureDialog

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
        self.properties_panel.subgroupColumnChanged.connect(self.on_subgroup_column_changed)

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

        # ★--- データメニューを新設 ---★
        data_menu = menu_bar.addMenu("&Data")
        restructure_action = QAction("&Restructure (Wide to Long)...", self)
        restructure_action.triggered.connect(self.show_restructure_dialog)
        data_menu.addAction(restructure_action)
        
        # 解析メニュー
        analysis_menu = menu_bar.addMenu("&Analysis")
        ttest_action = QAction("&Independent t-test...", self)
        ttest_action.triggered.connect(self.perform_t_test)
        analysis_menu.addAction(ttest_action)
        linreg_action = QAction("&Linear Regression...", self)
        linreg_action.triggered.connect(self.perform_linear_regression)
        analysis_menu.addAction(linreg_action)

    # ★--- ダイアログ表示とデータ変換のメソッドを2つ追加 ---★
    def show_restructure_dialog(self):
        if not hasattr(self, 'model'):
            QMessageBox.warning(self, "Warning", "Please load data first.")
            return

        df = self.model._data
        dialog = RestructureDialog(df.columns, self)
        
        # ダイアログでOKが押されたら、データを変換する
        if dialog.exec():
            settings = dialog.get_settings()
            if not settings['id_vars'] or not settings['value_vars']:
                QMessageBox.warning(self, "Warning", "Please select both Identifier and Value columns.")
                return
            self.restructure_data(settings)
            
    def restructure_data(self, settings):
        try:
            df = self.model._data
            new_df = pd.melt(
                df,
                id_vars=settings['id_vars'],
                value_vars=settings['value_vars'],
                var_name=settings['var_name'],
                value_name=settings['value_name']
            )

            new_window = MainWindow()
            new_window.model = PandasModel(new_df)
            new_window.table_view.setModel(new_window.model)
            new_window.properties_panel.set_columns(new_df.columns)
            new_window.setWindowTitle(self.windowTitle() + " [Restructured]")
            new_window.show()
            
            # ★--- ここから修正 ---★
            # qApp の代わりに QApplication.instance() を使用する
            app = QApplication.instance()
            if not hasattr(app, 'main_windows'):
                app.main_windows = []
            app.main_windows.append(new_window)
            # ★--- ここまで修正 ---★

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to restructure data: {e}")

    # ★--- サブグループ列が選択されたときに呼ばれるメソッド ---★
    def on_subgroup_column_changed(self, column_name):
        if not hasattr(self, 'model') or not column_name:
            self.properties_panel.update_subgroup_color_ui([]) # 空のリストでUIをクリア
            return
        
        try:
            # 選択された列のユニークな値を取得してUIを更新
            unique_categories = self.model._data[column_name].unique()
            self.properties_panel.update_subgroup_color_ui(sorted(unique_categories))
        except KeyError:
            self.properties_panel.update_subgroup_color_ui([])

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

    # ★--- update_graphメソッドを修正 ---★
    def update_graph(self):
        if not hasattr(self, 'model'):
            return

        df = self.model._data
        ax = self.graph_widget.ax
        ax.clear()

        # --- プロパティパネルから情報を取得 ---
        y_col = self.properties_panel.y_axis_combo.currentText()
        x_col = self.properties_panel.x_axis_combo.currentText()
        subgroup_col = self.properties_panel.subgroup_combo.currentText()
        
        # --- スタイル情報を取得 ---
        marker_style = self.properties_panel.marker_combo.currentData()
        single_color = self.properties_panel.current_color
        subgroup_colors_map = self.properties_panel.subgroup_colors
        show_scatter = self.properties_panel.scatter_overlay_check.isChecked()

        if not y_col or not x_col:
            self.graph_widget.canvas.draw()
            return
            
        if self.current_graph_type == 'scatter':
            color_to_plot = single_color if single_color else '#1f77b4'
            if pd.api.types.is_numeric_dtype(df[y_col]) and pd.api.types.is_numeric_dtype(df[x_col]):
                ax.scatter(df[x_col], df[y_col], marker=marker_style, color=color_to_plot)
                ax.set_xlabel(x_col)
                ax.set_ylabel(y_col)

        # ★--- ここから棒グラフのロジックを全面的に書き換え ---★
        elif self.current_graph_type == 'bar':
            try:
                ax.clear()
                
                # X軸のカテゴリをソートして順序を固定
                categories = sorted(df[x_col].unique())
                x_indices = np.arange(len(categories))
                
                if subgroup_col:
                    # サブグループありの場合
                    subcategories = sorted(df[subgroup_col].unique())
                    n_subgroups = len(subcategories)
                    
                    bar_width = 0.8
                    sub_bar_width = bar_width / n_subgroups
                    
                    for i, subcat in enumerate(subcategories):
                        # 各サブカテゴリの棒の位置を計算
                        offsets = (i - (n_subgroups - 1) / 2.) * sub_bar_width
                        bar_positions = x_indices + offsets

                        means = []
                        stds = []
                        for cat in categories:
                            subset = df[(df[x_col] == cat) & (df[subgroup_col] == subcat)][y_col]
                            means.append(subset.mean())
                            stds.append(subset.std())
                        
                        color = subgroup_colors_map.get(subcat)
                        ax.bar(bar_positions, means, width=sub_bar_width * 0.9, yerr=stds, label=subcat, capsize=4, color=color)

                        if show_scatter:
                            for k, cat in enumerate(categories):
                                points = df[(df[x_col] == cat) & (df[subgroup_col] == subcat)][y_col]
                                jitter_width = sub_bar_width * 0.4
                                jitter = np.random.uniform(-jitter_width / 2, jitter_width / 2, len(points))
                                ax.scatter(bar_positions[k] + jitter, points, color='black', alpha=0.6, zorder=2)
                    
                    ax.legend(title=subgroup_col)

                else:
                    # サブグループなしの場合
                    summary = df.groupby(x_col)[y_col].agg(['mean', 'std']).reindex(categories)
                    color_to_plot = single_color if single_color else '#1f77b4'
                    
                    ax.bar(x_indices, summary['mean'], width=0.8, yerr=summary['std'], capsize=4, color=color_to_plot)

                    if show_scatter:
                        for i, cat in enumerate(categories):
                            points = df[df[x_col] == cat][y_col]
                            jitter_width = 0.8 * 0.4
                            jitter = np.random.uniform(-jitter_width / 2, jitter_width / 2, len(points))
                            ax.scatter(i + jitter, points, color='black', alpha=0.6, zorder=2)
                
                # X軸のラベルを設定
                ax.set_xticks(x_indices)
                ax.set_xticklabels(categories, rotation=0)
                ax.set_xlabel(x_col)
                ax.set_ylabel(f"Mean of {y_col}")

            except Exception as e:
                print(f"Could not generate bar chart: {e}")
        
        # --- グラフの再描画 ---
        self.update_graph_properties(self.properties_panel.on_properties_changed() or {})
        self.graph_widget.fig.tight_layout()
        self.graph_widget.canvas.draw()