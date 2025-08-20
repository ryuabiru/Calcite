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
    QDialog,
    QVBoxLayout,
    QTextEdit,
)
from PySide6.QtGui import QAction, QActionGroup, QIcon
from PySide6.QtCore import Qt
from scipy.stats import ttest_ind, f_oneway, linregress
import io

from scipy.stats import ttest_ind, f_oneway, linregress, chi2_contingency
from scipy.optimize import curve_fit
from statsmodels.stats.multicomp import pairwise_tukeyhsd

from pandas_model import PandasModel
from graph_widget import GraphWidget
from properties_widget import PropertiesWidget
from restructure_dialog import RestructureDialog
from calculate_dialog import CalculateDialog
from anova_dialog import AnovaDialog
from fitting_dialog import FittingDialog
from contingency_dialog import ContingencyDialog

class MainWindow(QMainWindow):
    """
    アプリケーションのメインウィンドウ。
    テーブル表示、グラフ表示、各種データ操作・解析機能を持つ。
    """
    def __init__(self):
        """
        MainWindowの初期化。UIのセットアップ、シグナルとスロットの接続を行う。
        """
        super().__init__()
        self.setWindowTitle("Calcite")
        self.setGeometry(100, 100, 1000, 650)
        
        self.current_graph_type = 'scatter'
        self.header_editor = None
        self.regression_line = None
        self.fit_curve = None
        self.fit_params = None
        
        self._create_menu_bar()
        self._create_toolbar()

        # --- メインレイアウトの設定 ---
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.table_view = QTableView()
        splitter.addWidget(self.table_view)
        
        self.graph_widget = GraphWidget()
        splitter.addWidget(self.graph_widget)
        
        splitter.setSizes([550, 450])
        self.setCentralWidget(splitter)
        
        # --- プロパティパネルのドックウィジェット ---
        self.properties_panel = PropertiesWidget()
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.properties_panel)

        # --- シグナルとスロットの接続 ---
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.show_table_context_menu)
        self.table_view.horizontalHeader().sectionDoubleClicked.connect(self.edit_header)
        self.properties_panel.propertiesChanged.connect(self.update_graph_properties)
        self.properties_panel.graphUpdateRequest.connect(self.update_graph)
        self.properties_panel.subgroupColumnChanged.connect(self.on_subgroup_column_changed)

    def edit_header(self, logicalIndex):
        """
        テーブルビューのヘッダーがダブルクリックされたときに、
        ヘッダー名を編集するためのQLineEditを表示する。
        """
        if self.header_editor:
            self.header_editor.close()

        header = self.table_view.horizontalHeader()
        model = self.table_view.model()
        
        self.header_editor = QLineEdit(parent=header)
        self.header_editor.setText(model.headerData(logicalIndex, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole))
        
        self.header_editor.setGeometry(header.sectionViewportPosition(logicalIndex), 0, header.sectionSize(logicalIndex), header.height())
        self.header_editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_editor.editingFinished.connect(lambda: self.finish_header_edit(logicalIndex))
        
        self.header_editor.show()
        self.header_editor.setFocus()

    def finish_header_edit(self, logicalIndex):
        """
        ヘッダー名の編集が完了したときに、モデルのヘッダーデータを更新する。
        """
        if self.header_editor:
            new_text = self.header_editor.text()
            self.table_view.model().setHeaderData(logicalIndex, Qt.Orientation.Horizontal, new_text, Qt.ItemDataRole.EditRole)
            self.header_editor.close()
            self.header_editor = None

    def show_table_context_menu(self, position):
        """
        テーブルビューで右クリックされたときにコンテキストメニューを表示する。
        行・列の挿入・削除アクションを含む。
        """
        if not hasattr(self, 'model'):
            return

        menu = QMenu()
        
        insert_row_action = QAction("Insert Row Above", self)
        insert_row_action.triggered.connect(self.insert_row)
        menu.addAction(insert_row_action)

        remove_row_action = QAction("Remove Selected Row(s)", self)
        remove_row_action.triggered.connect(self.remove_row)
        menu.addAction(remove_row_action)

        menu.addSeparator()

        insert_col_action = QAction("Insert Column Left", self)
        insert_col_action.triggered.connect(self.insert_col)
        menu.addAction(insert_col_action)

        remove_col_action = QAction("Remove Selected Column(s)", self)
        remove_col_action.triggered.connect(self.remove_col)
        menu.addAction(remove_col_action)
        
        menu.exec(self.table_view.viewport().mapToGlobal(position))

    def insert_row(self):
        """選択された位置の上に行を挿入する。"""
        selected_index = self.table_view.currentIndex()
        row = selected_index.row() if selected_index.isValid() else self.model.rowCount()
        self.model.insertRows(row, 1)

    def remove_row(self):
        """選択された行を削除する。"""
        selected_rows = sorted(list(set(index.row() for index in self.table_view.selectionModel().selectedRows())))
        if not selected_rows:
            return
        
        # 後ろから削除しないとインデックスがずれる
        for row in reversed(selected_rows):
            self.model.removeRows(row, 1)

    def insert_col(self):
        """選択された位置の左に列を挿入する。"""
        selected_index = self.table_view.currentIndex()
        col = selected_index.column() if selected_index.isValid() else self.model.columnCount()
        self.model.insertColumns(col, 1)

    def remove_col(self):
        """選択された列を削除する。"""
        selected_cols = sorted(list(set(index.column() for index in self.table_view.selectionModel().selectedColumns())))
        if not selected_cols:
            return

        for col in reversed(selected_cols):
            self.model.removeColumns(col, 1)

    def _create_toolbar(self):
        """グラフタイプを選択するためのツールバーを作成する。"""
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
        """グラフのタイプ（散布図、棒グラフなど）を設定し、グラフを更新する。"""
        self.current_graph_type = graph_type
        self.update_graph()

    def _create_menu_bar(self):
        """メニューバーを作成し、各アクションをセットアップする。"""
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("&File")
        open_action = QAction("&Open CSV...", self)
        open_action.triggered.connect(self.open_csv_file)
        file_menu.addAction(open_action)
        file_menu.addSeparator() # 区切り線を追加
        
        # ラフ保存のアクション
        save_graph_action = QAction("&Save Graph As...", self)
        save_graph_action.triggered.connect(self.save_graph)
        file_menu.addAction(save_graph_action)

        # Edit Menu
        edit_menu = menu_bar.addMenu("&Edit")
        paste_action = QAction("&Paste", self)
        paste_action.triggered.connect(self.paste_from_clipboard)
        edit_menu.addAction(paste_action)

        # Data Menu
        data_menu = menu_bar.addMenu("&Data")
        restructure_action = QAction("&Restructure (Wide to Long)...", self)
        restructure_action.triggered.connect(self.show_restructure_dialog)
        data_menu.addAction(restructure_action)
        
        calculate_action = QAction("&Calculate New Column...", self)
        calculate_action.triggered.connect(self.show_calculate_dialog)
        data_menu.addAction(calculate_action)
        
        # Analysis Menu
        analysis_menu = menu_bar.addMenu("&Analysis")
        ttest_action = QAction("&Independent t-test...", self)
        ttest_action.triggered.connect(self.perform_t_test)
        analysis_menu.addAction(ttest_action)
        
        anova_action = QAction("&One-way ANOVA...", self)
        anova_action.triggered.connect(self.perform_one_way_anova)
        analysis_menu.addAction(anova_action)
        analysis_menu.addSeparator()

        chi_squared_action = QAction("&Chi-squared Test...", self)
        chi_squared_action.triggered.connect(self.perform_chi_squared_test)
        analysis_menu.addAction(chi_squared_action)
        analysis_menu.addSeparator()

        linreg_action = QAction("&Linear Regression...", self)
        linreg_action.triggered.connect(self.perform_linear_regression)
        analysis_menu.addAction(linreg_action)
        
        fitting_action = QAction("&Non-linear Regression...", self)
        fitting_action.triggered.connect(self.perform_fitting)
        analysis_menu.addAction(fitting_action)

    # ★--- グラフを保存するメソッドを追加 ---★
    def save_graph(self):
        """
        現在のグラフを画像ファイルとして保存する。
        """
        if not hasattr(self, 'model'):
            QMessageBox.warning(self, "Warning", "No data to save.")
            return

        # ファイル保存ダイアログを表示
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save Graph",
            "", # デフォルトのファイルパス
            "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg);;SVG Vector Image (*.svg);;PDF Document (*.pdf)"
        )

        # ユーザーがキャンセルしなかった場合
        if file_path:
            try:
                # Matplotlibのsavefigメソッドで、高解像度(300 dpi)を指定して保存
                self.graph_widget.fig.savefig(file_path, dpi=300)
                QMessageBox.information(self, "Success", f"Graph successfully saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save graph: {e}")

    def paste_from_clipboard(self):
        """クリップボードからタブ区切りテキストを読み込み、テーブルに貼り付ける。"""
        try:
            clipboard = QApplication.clipboard()
            text = clipboard.text()
            if not text:
                return

            df = pd.read_csv(io.StringIO(text), sep='	')
            self.model = PandasModel(df)
            self.table_view.setModel(self.model)
            self.properties_panel.set_columns(df.columns)
            
            # データ変更がグラフに反映されるようにシグナルを接続
            self.table_view.selectionModel().selectionChanged.connect(self.update_graph)
            self.model.dataChanged.connect(self.update_graph) 
            self.model.headerDataChanged.connect(self.update_graph)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to paste from clipboard: {e}")

    def show_calculate_dialog(self):
        """新しい列を計算するためのダイアログを表示し、設定に基づいて計算を実行する。"""
        if not hasattr(self, 'model'):
            QMessageBox.warning(self, "Warning", "Please load data first.")
            return

        df = self.model._data
        dialog = CalculateDialog(df.columns, self)
        
        if dialog.exec():
            settings = dialog.get_settings()
            if not settings['new_column_name'] or not settings['formula']:
                QMessageBox.warning(self, "Warning", "Please enter both a new column name and a formula.")
                return
            self.calculate_new_column(settings)

    def calculate_new_column(self, settings):
        """指定された計算式に基づいて新しい列を計算し、テーブルを更新する。"""
        try:
            df = self.model._data
            new_col_name = settings['new_column_name']
            formula = settings['formula']

            # pandas.evalを使用して新しい列を計算
            df[new_col_name] = df.eval(formula, engine='python')

            self.model.refresh_model()
            self.properties_panel.set_columns(df.columns)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to calculate column: {e}")

    def show_restructure_dialog(self):
        """ワイドフォーマットからロングフォーマットへデータを変換するためのダイアログを表示する。"""
        if not hasattr(self, 'model'):
            QMessageBox.warning(self, "Warning", "Please load data first.")
            return

        df = self.model._data
        dialog = RestructureDialog(df.columns, self)
        
        if dialog.exec():
            settings = dialog.get_settings()
            if not settings['id_vars'] or not settings['value_vars']:
                QMessageBox.warning(self, "Warning", "Please select both Identifier and Value columns.")
                return
            self.restructure_data(settings)
            
    def restructure_data(self, settings):
        """
        pd.meltを使用してデータをワイドからロングフォーマットに変換し、
        新しいウィンドウで結果を表示する。
        """
        try:
            df = self.model._data
            new_df = pd.melt(
                df,
                id_vars=settings['id_vars'],
                value_vars=settings['value_vars'],
                var_name=settings['var_name'],
                value_name=settings['value_name']
            )

            # 新しいウィンドウインスタンスを作成して表示
            new_window = MainWindow()
            new_window.model = PandasModel(new_df)
            new_window.table_view.setModel(new_window.model)
            new_window.properties_panel.set_columns(new_df.columns)
            new_window.setWindowTitle(self.windowTitle() + " [Restructured]")
            new_window.show()
            
            # アプリケーションのインスタンスに新しいウィンドウを登録（メモリ管理のため）
            app = QApplication.instance()
            if not hasattr(app, 'main_windows'):
                app.main_windows = []
            app.main_windows.append(new_window)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to restructure data: {e}")

    def on_subgroup_column_changed(self, column_name):
        """
        プロパティパネルでサブグループ（色分け）の列が変更されたときに呼び出され、
        サブグループの色設定UIを更新する。
        """
        if not hasattr(self, 'model') or not column_name:
            self.properties_panel.update_subgroup_color_ui([])
            return
        
        try:
            unique_categories = self.model._data[column_name].unique()
            self.properties_panel.update_subgroup_color_ui(sorted(unique_categories))
        except KeyError:
            self.properties_panel.update_subgroup_color_ui([])

    def open_csv_file(self):
        """CSVファイルを開き、内容をテーブルに読み込む。"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)")
        if file_path:
            try:
                df = pd.read_csv(file_path)
                self.model = PandasModel(df)
                self.table_view.setModel(self.model)
                self.properties_panel.set_columns(df.columns)
                
                # データ変更がグラフに反映されるようにシグナルを接続
                self.table_view.selectionModel().selectionChanged.connect(self.update_graph)
                self.model.dataChanged.connect(self.update_graph) 
                self.model.headerDataChanged.connect(self.update_graph)

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error opening file: {e}")

    # シグモイド曲線（4PL）の関数定義
    def sigmoid_4pl(self, x, bottom, top, hill_slope, ec50):
        """4パラメータロジスティック（4PL）モデルの関数"""
        # log-transformed x (concentration) を想定
        return bottom + (top - bottom) / (1 + 10**((np.log10(ec50) - x) * hill_slope))

    # 非線形フィッティングを実行するメソッドを追加
    def perform_fitting(self):
        if not hasattr(self, 'model'):
            QMessageBox.warning(self, "Warning", "Please load data first.")
            return

        df = self.model._data
        dialog = FittingDialog(df.columns, self)

        if dialog.exec():
            settings = dialog.get_settings()
            x_col, y_col = settings['x_col'], settings['y_col']

            if not x_col or not y_col:
                QMessageBox.warning(self, "Warning", "Please select both X and Y columns.")
                return

            try:
                # データの準備 (欠損値を除外し、Xをlog変換)
                fit_df = df[[x_col, y_col]].dropna().copy()
                if (fit_df[x_col] <= 0).any():
                    QMessageBox.warning(self, "Warning", "X-axis column contains non-positive values. Log transformation cannot be applied.")
                    return
                
                fit_df['log_x'] = np.log10(fit_df[x_col])
                
                x_data = fit_df['log_x']
                y_data = fit_df[y_col]

                # パラメータの初期値を推定
                p0 = [y_data.min(), y_data.max(), 1.0, np.median(fit_df[x_col])]
                
                # curve_fitでフィッティングを実行
                params, _ = curve_fit(self.sigmoid_4pl, x_data, y_data, p0=p0, maxfev=10000)
                
                bottom, top, hill_slope, ec50 = params
                
                # R-squared (決定係数) を計算
                y_pred = self.sigmoid_4pl(x_data, *params)
                ss_res = np.sum((y_data - y_pred) ** 2)
                ss_tot = np.sum((y_data - np.mean(y_data)) ** 2)
                r_squared = 1 - (ss_res / ss_tot)

                # 計算結果をインスタンス変数に保存
                self.fit_params = {
                    "params": params,
                    "r_squared": r_squared,
                    "x_col": x_col,
                    "y_col": y_col
                }

                # 結果をフォーマット
                result_text = "Non-linear Regression Results (Sigmoidal 4PL)\n"
                result_text += "==============================================\n\n"
                result_text += f"Top: {top:.4f}\n"
                result_text += f"Bottom: {bottom:.4f}\n"
                result_text += f"Hill Slope: {hill_slope:.4f}\n"
                result_text += f"EC50: {ec50:.4f}\n\n"
                result_text += f"R-squared: {r_squared:.4f}\n"
                
                self.show_results_dialog("Fitting Result", result_text)

                # グラフ全体を更新して、データと曲線を再描画
                self.update_graph()

                # グラフに曲線を描画
                ax = self.graph_widget.ax
                # 既存の線をクリア
                if self.regression_line and self.regression_line in ax.lines:
                    self.regression_line.remove()
                    self.regression_line = None
                if self.fit_curve and self.fit_curve in ax.lines:
                    self.fit_curve.remove()
                
                # 滑らかな曲線のためのX値を生成
                x_fit = np.linspace(x_data.min(), x_data.max(), 200)
                y_fit = self.sigmoid_4pl(x_fit, *params)
                
                # X軸を元のスケールに戻してプロット
                self.fit_curve, = ax.plot(10**x_fit, y_fit, color='blue', label=f'4PL Fit (R²={r_squared:.3f})')
                ax.set_xscale('log') # X軸を対数スケールに設定
                ax.legend()
                self.graph_widget.canvas.draw()

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to perform fitting: {e}")
    

    def perform_t_test(self):
        """
        テーブルで選択された2つの列に対して独立t検定を実行し、結果をダイアログで表示する。
        """
        if not hasattr(self, 'model'):
            QMessageBox.warning(self, "Warning", "Please load data first.")
            return

        selected_columns = sorted(list(set(index.column() for index in self.table_view.selectionModel().selectedIndexes())))

        if len(selected_columns) != 2:
            QMessageBox.warning(self, "Warning", "Please select exactly two columns.")
            return

        df = self.model._data
        col1_index, col2_index = selected_columns
        col1_data = df.iloc[:, col1_index].dropna()
        col2_data = df.iloc[:, col2_index].dropna()

        t_stat, p_value = ttest_ind(col1_data, col2_data)

        result_text = (
            f"Independent t-test results:"
            f"Comparing:- {df.columns[col1_index]} (Mean: {col1_data.mean():.3f})"
            f"- {df.columns[col2_index]} (Mean: {col2_data.mean():.3f})"
            f"t-statistic: {t_stat:.4f}"
            f"p-value: {p_value:.4f}"
        )

        if p_value < 0.05:
            result_text += "Conclusion: The difference is statistically significant (p < 0.05)."
        else:
            result_text += "Conclusion: The difference is not statistically significant (p >= 0.05)."

        self.show_results_dialog("t-test Result", result_text)

    def perform_linear_regression(self):
        if not hasattr(self, 'model'):
            QMessageBox.warning(self, "Warning", "Please load data first.")
            return
            
        selected_columns = sorted(list(set(index.column() for index in self.table_view.selectionModel().selectedIndexes())))

        if len(selected_columns) != 2:
            QMessageBox.warning(self, "Warning", "Please select exactly two columns.")
            return

        df = self.model._data
        x_col_index, y_col_index = selected_columns
        
        x_data = df.iloc[:, x_col_index].dropna()
        y_data = df.iloc[:, y_col_index].dropna()
        
        slope, intercept, r_value, p_value, std_err = linregress(x_data, y_data)
        r_squared = r_value**2

        x_line = np.array([x_data.min(), x_data.max()])
        y_line = slope * x_line + intercept

        # 既存のフィッティング曲線をクリア
        self.fit_params = None

        ax = self.graph_widget.ax
        
        # --- 既存の線をクリア ---
        if self.regression_line and self.regression_line in ax.lines:
            self.regression_line.remove()
        if self.fit_curve and self.fit_curve in ax.lines: # ★ 追加
            self.fit_curve.remove()
            self.fit_curve = None
            
        self.regression_line, = ax.plot(x_line, y_line, color='red', linestyle='--', 
                                         label=f'R² = {r_squared:.4f}')
        
        ax.set_xscale('linear') # ★ 軸を線形スケールに戻す
        ax.legend()
        self.graph_widget.canvas.draw()
        
    def perform_one_way_anova(self):
        """
        一元配置分散分析（ANOVA）を実行するためのダイアログを表示し、
        指定された列で検定を行い、結果をダイアログで表示する。
        """
        if not hasattr(self, 'model'):
            QMessageBox.warning(self, "Warning", "Please load data first.")
            return

        df = self.model._data
        dialog = AnovaDialog(df.columns, self)

        if dialog.exec():
            settings = dialog.get_settings()
            value_col, group_col = settings['value_col'], settings['group_col']

            if not value_col or not group_col:
                QMessageBox.warning(self, "Warning", "Please select both value and group columns.")
                return
            if value_col == group_col:
                QMessageBox.warning(self, "Warning", "Value and group columns cannot be the same.")
                return

            try:
                groups = df[group_col].unique()
                if len(groups) < 3:
                    QMessageBox.warning(self, "Warning", "ANOVA requires at least 3 groups.")
                    return
                    
                samples = [df[value_col][df[group_col] == g].dropna() for g in groups]
                
                f_stat, p_value = f_oneway(*samples)

                result_text = (
                    f"One-way ANOVA Results"
                    f"======================"
                    f"Comparing '{value_col}' across groups in '{group_col}'."
                    f"Number of groups: {len(groups)}"
                    f"F-statistic: {f_stat:.4f}"
                    f"p-value: {p_value:.4f}"
                )
                if p_value < 0.05:
                    result_text += "Conclusion: There is a statistically significant difference between group means (p < 0.05)."
                else:
                    result_text += "Conclusion: There is no statistically significant difference between group means (p >= 0.05)."

                self.show_results_dialog("ANOVA Result", result_text)

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to perform ANOVA: {e}")

    # ★--- カイ二乗検定を実行するメソッドを追加 ---★
    def perform_chi_squared_test(self):
        if not hasattr(self, 'model'):
            QMessageBox.warning(self, "Warning", "Please load data first.")
            return

        df = self.model._data
        dialog = ContingencyDialog(df.columns, self)

        if dialog.exec():
            settings = dialog.get_settings()
            rows_col = settings['rows_col']
            cols_col = settings['cols_col']

            if not rows_col or not cols_col:
                QMessageBox.warning(self, "Warning", "Please select both rows and columns.")
                return
            if rows_col == cols_col:
                QMessageBox.warning(self, "Warning", "Row and column selections cannot be the same.")
                return

            try:
                # pandas.crosstabで分割表（観測度数表）を作成
                contingency_table = pd.crosstab(df[rows_col], df[cols_col])

                # SciPyでカイ二乗検定を実行
                chi2, p, dof, expected = chi2_contingency(contingency_table)

                # 期待度数表をDataFrameに変換
                expected_table = pd.DataFrame(expected, index=contingency_table.index, columns=contingency_table.columns)

                # 結果をフォーマット
                result_text = "Chi-squared Test Results\n"
                result_text += "==========================\n\n"
                result_text += "Observed Frequencies:\n"
                result_text += f"{contingency_table.to_string()}\n\n"
                result_text += "Expected Frequencies:\n"
                result_text += f"{expected_table.round(2).to_string()}\n\n"
                result_text += "---\n"
                result_text += f"Chi-squared statistic: {chi2:.4f}\n"
                result_text += f"Degrees of Freedom: {dof}\n"
                result_text += f"p-value: {p:.4f}\n\n"

                if p < 0.05:
                    result_text += f"Conclusion: There is a statistically significant association between '{rows_col}' and '{cols_col}' (p < 0.05)."
                else:
                    result_text += f"Conclusion: There is no statistically significant association between '{rows_col}' and '{cols_col}' (p >= 0.05)."

                self.show_results_dialog("Chi-squared Test Result", result_text)

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to perform Chi-squared test: {e}")

    def show_results_dialog(self, title, text):
        """
        解析結果などを表示するための汎用的なダイアログを表示する。
        テキストは等幅フォントで表示される。
        """
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumSize(400, 300)
        
        layout = QVBoxLayout(dialog)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setText(text)
        
        font = text_edit.font()
        font.setFamily("Courier New")
        text_edit.setFont(font)
        
        layout.addWidget(text_edit)
        dialog.exec()

    def update_graph_properties(self, properties):
        """
        プロパティパネルから受け取った情報でグラフのテキスト要素（タイトル、軸ラベル）を更新する。
        """
        properties = self.properties_panel.get_properties()
        ax = self.graph_widget.ax
        
        # テキストとフォントサイズを設定
        ax.set_title(properties.get('title', ''), fontsize=properties.get('title_fontsize', 16))
        ax.set_xlabel(properties.get('xlabel', ''), fontsize=properties.get('xlabel_fontsize', 12))
        ax.set_ylabel(properties.get('ylabel', ''), fontsize=properties.get('ylabel_fontsize', 12))
        ax.tick_params(axis='both', which='major', labelsize=properties.get('ticks_fontsize', 10))

        # 軸範囲を設定
        try:
            xmin = float(properties['xmin']) if properties['xmin'] else None
            xmax = float(properties['xmax']) if properties['xmax'] else None
            if xmin is not None and xmax is not None:
                ax.set_xlim(xmin, xmax)

            ymin = float(properties['ymin']) if properties['ymin'] else None
            ymax = float(properties['ymax']) if properties['ymax'] else None
            if ymin is not None and ymax is not None:
                ax.set_ylim(ymin, ymax)
        except (ValueError, TypeError):
            pass
        
        # グリッドの表示/非表示
        ax.grid(properties.get('show_grid', False))

        self.graph_widget.fig.tight_layout()
        self.graph_widget.canvas.draw()

    def update_graph(self):
        """
        現在の設定に基づいてグラフ全体を再描画する。
        データの変更、グラフタイプの変更、プロパティの変更など、様々なトリガーから呼び出される。
        """
        if not hasattr(self, 'model'):
            return

        df = self.model._data
        ax = self.graph_widget.ax
        ax.clear()
        
        # 既存の線オブジェクトへの参照をリセット
        self.regression_line = None
        self.fit_curve = None

        # プロパティパネルから描画設定を取得
        y_col = self.properties_panel.y_axis_combo.currentText()
        x_col = self.properties_panel.x_axis_combo.currentText()
        subgroup_col = self.properties_panel.subgroup_combo.currentText()
        
        # スタイル情報を取得
        marker_style = self.properties_panel.marker_combo.currentData()
        single_color = self.properties_panel.current_color
        subgroup_colors_map = self.properties_panel.subgroup_colors
        show_scatter = self.properties_panel.scatter_overlay_check.isChecked()

        if not y_col or not x_col:
            self.graph_widget.canvas.draw()
            return
            
        # グラフタイプに応じて描画を分岐
        if self.current_graph_type == 'scatter':
            self._draw_scatter_plot(ax, df, x_col, y_col, marker_style, single_color)

        elif self.current_graph_type == 'bar':
            self.fit_params = None
            self._draw_bar_chart(ax, df, x_col, y_col, subgroup_col, single_color, subgroup_colors_map, show_scatter)

        # フィッティングパラメータが存在し、現在の表示列と一致する場合に曲線を描画
        if self.fit_params and self.fit_params['x_col'] == x_col and self.fit_params['y_col'] == y_col:
            
            fit_df = df[[x_col, y_col]].dropna().copy()
            if not (fit_df[x_col] <= 0).any():
                fit_df['log_x'] = np.log10(fit_df[x_col])
                x_data = fit_df['log_x']

                x_fit = np.linspace(x_data.min(), x_data.max(), 200)
                y_fit = self.sigmoid_4pl(x_fit, *self.fit_params['params'])
                
                r_squared = self.fit_params['r_squared']
                self.fit_curve, = ax.plot(10**x_fit, y_fit, color='blue', label=f'4PL Fit (R²={r_squared:.3f})')
                ax.set_xscale('log')
                ax.legend()

        else:
             ax.set_xscale('linear') # フィットがない場合は線形スケール

        # グラフの再描画
        #ax.set_xscale('linear') # ★ この行は不要になることが多いのでコメントアウト
        self.update_graph_properties() # 引数なしで呼び出すように変更

    def _draw_scatter_plot(self, ax, df, x_col, y_col, marker_style, color):
        """散布図を描画する内部メソッド。"""
        color_to_plot = color if color else '#1f77b4'
        if pd.api.types.is_numeric_dtype(df[y_col]) and pd.api.types.is_numeric_dtype(df[x_col]):
            ax.scatter(df[x_col], df[y_col], marker=marker_style, color=color_to_plot)
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)

    def _draw_bar_chart(self, ax, df, x_col, y_col, subgroup_col, single_color, subgroup_colors_map, show_scatter):
        """棒グラフを描画する内部メソッド。サブグループ化と実測値の重ね描きに対応。"""
        try:
            categories = sorted(df[x_col].unique())
            x_indices = np.arange(len(categories))
            
            if subgroup_col:
                # サブグループあり
                self._draw_grouped_bar_chart(ax, df, x_col, y_col, subgroup_col, categories, x_indices, subgroup_colors_map, show_scatter)
            else:
                # サブグループなし
                self._draw_simple_bar_chart(ax, df, x_col, y_col, categories, x_indices, single_color, show_scatter)
            
            ax.set_xticks(x_indices)
            ax.set_xticklabels(categories, rotation=0)
            ax.set_xlabel(x_col)
            ax.set_ylabel(f"Mean of {y_col}")

        except Exception as e:
            print(f"Could not generate bar chart: {e}")

    def _draw_simple_bar_chart(self, ax, df, x_col, y_col, categories, x_indices, color, show_scatter):
        """サブグループのない単純な棒グラフを描画する。"""
        summary = df.groupby(x_col)[y_col].agg(['mean', 'std']).reindex(categories)
        color_to_plot = color if color else '#1f77b4'
        
        ax.bar(x_indices, summary['mean'], width=0.8, yerr=summary['std'], capsize=4, color=color_to_plot)

        if show_scatter:
            for i, cat in enumerate(categories):
                points = df[df[x_col] == cat][y_col]
                jitter = np.random.uniform(-0.15, 0.15, len(points))
                ax.scatter(i + jitter, points, color='black', alpha=0.6, zorder=2)

    def _draw_grouped_bar_chart(self, ax, df, x_col, y_col, subgroup_col, categories, x_indices, subgroup_colors_map, show_scatter):
        """サブグループ化された棒グラフを描画する。"""
        subcategories = sorted(df[subgroup_col].unique())
        n_subgroups = len(subcategories)
        bar_width = 0.8
        sub_bar_width = bar_width / n_subgroups
        
        for i, subcat in enumerate(subcategories):
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
