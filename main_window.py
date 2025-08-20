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
from ttest_dialog import TTestDialog
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
        self.setGeometry(100, 100, 1000, 650) # ウィンドウの高さを少し広げました
        
        self.current_graph_type = 'scatter'
        self.header_editor = None
        self.regression_line_params = None # 以前の修正で追加
        self.fit_params = None
        self.statistical_annotations = []
        
        self._create_menu_bar()
        self._create_toolbar()

        # --- メインレイアウトの設定 (ここからが新しいレイアウト) ---
        main_splitter = QSplitter(Qt.Orientation.Vertical)

        # --- 上段ウィジェット (テーブルとグラフ用の水平スプリッター) ---
        top_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.table_view = QTableView()
        top_splitter.addWidget(self.table_view)
        
        self.graph_widget = GraphWidget()
        top_splitter.addWidget(self.graph_widget)
        
        top_splitter.setSizes([550, 450]) # 上段の左右の初期サイズ

        # --- 下段ウィジェット (プロパティパネル) ---
        self.properties_panel = PropertiesWidget()

        # --- メインの垂直スプリッターに上段と下段を追加 ---
        main_splitter.addWidget(top_splitter)
        main_splitter.addWidget(self.properties_panel)
        
        # ★★★ ご要望の初期サイズ設定 ★★★
        # 上段に550px, 下段に250pxを割り当てます (お好みで調整してください)
        main_splitter.setSizes([550, 250])

        self.setCentralWidget(main_splitter)
        
        # --- シグナルとスロットの接続 ---
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.show_table_context_menu)
        self.table_view.horizontalHeader().sectionDoubleClicked.connect(self.edit_header)
        self.properties_panel.propertiesChanged.connect(self.update_graph)
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
        
        edit_menu.addSeparator()
        clear_annotations_action = QAction("Clear Annotations", self)
        clear_annotations_action.triggered.connect(self.clear_annotations)
        edit_menu.addAction(clear_annotations_action)

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
                    "y_col": y_col,
                    "log_x_data": x_data # 再描画のためにXデータを保存
                }
                
                # 既存の回帰直線をクリア
                self.regression_line_params = None

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

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to perform fitting: {e}")
    

    def perform_t_test(self):
        """
        Tidy Data形式に対応した独立t検定を実行し、結果をアノテーションとして保存する。
        """
        if not hasattr(self, 'model'):
            QMessageBox.warning(self, "Warning", "Please load data first.")
            return

        df = self.model._data
        # t検定ダイアログのインポートをここで行う
        from ttest_dialog import TTestDialog
        dialog = TTestDialog(df.columns, df, self)

        if dialog.exec():
            settings = dialog.get_settings()
            value_col = settings['value_col']
            group_col = settings['group_col']
            group1_name = settings['group1']
            group2_name = settings['group2']

            if not all([value_col, group_col, group1_name, group2_name]):
                QMessageBox.warning(self, "Warning", "Please select all fields.")
                return
            if value_col == group_col:
                QMessageBox.warning(self, "Warning", "Value and group columns cannot be the same.")
                return
            if group1_name == group2_name:
                QMessageBox.warning(self, "Warning", "Please select two different groups.")
                return

            try:
                group1_data = df[df[group_col] == group1_name][value_col].dropna()
                group2_data = df[df[group_col] == group2_name][value_col].dropna()

                if group1_data.empty or group2_data.empty:
                    QMessageBox.warning(self, "Warning", "One or both selected groups have no data.")
                    return

                t_stat, p_value = ttest_ind(group1_data, group2_data)

                # ★--- ここからが追加・変更箇所 ---★
                # アノテーション情報を辞書として作成
                annotation = {
                    "type": "ttest",
                    "p_value": p_value,
                    "group_col": group_col,
                    "value_col": value_col,
                    "groups": [group1_name, group2_name]
                }
                # 既存のアノテーションをクリアして新しいものを追加
                self.statistical_annotations.append(annotation)

                # グラフを更新してアノテーションを描画
                self.update_graph()
                # ★--- ここまで ---★

                # --- 結果表示ダイアログ (変更なし) ---
                result_text = (
                    f"Independent t-test results:\n"
                    f"===========================\n\n"
                    f"Comparing '{value_col}' between:\n"
                    f"- Group 1: '{group1_name}' (Mean: {group1_data.mean():.3f})\n"
                    f"- Group 2: '{group2_name}' (Mean: {group2_data.mean():.3f})\n\n"
                    f"---\n"
                    f"t-statistic: {t_stat:.4f}\n"
                    f"p-value: {p_value:.4f}\n\n"
                )
                if p_value < 0.05:
                    result_text += "Conclusion: The difference is statistically significant (p < 0.05)."
                else:
                    result_text += "Conclusion: The difference is not statistically significant (p >= 0.05)."
                self.show_results_dialog("t-test Result", result_text)

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to perform t-test: {e}")

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

        # 描画に必要なパラメータをインスタンス変数に保存する
        self.regression_line_params = {
            "x_line": np.array([x_data.min(), x_data.max()]),
            "y_line": slope * np.array([x_data.min(), x_data.max()]) + intercept,
            "r_squared": r_value**2
        }

        # 既存のフィッティング曲線をクリア
        self.fit_params = None

        # グラフ全体の更新をトリガーする
        self.update_graph()
        
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

    def update_graph_properties(self):
        """プロパティパネルから現在の全設定を取得し、グラフに適用する。"""
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
            else:
                # 片方でも空なら自動スケールに戻す
                ax.autoscale(enable=True, axis='x')


            ymin = float(properties['ymin']) if properties['ymin'] else None
            ymax = float(properties['ymax']) if properties['ymax'] else None
            if ymin is not None and ymax is not None:
                ax.set_ylim(ymin, ymax)
            else:
                ax.autoscale(enable=True, axis='y')
        except (ValueError, TypeError):
            pass
        
        # グリッドの表示/非表示
        ax.grid(properties.get('show_grid', False))
        
        # ★--- スケール設定ロジックをここに集約 ---★
        # 非線形フィット中はX軸を強制的に対数スケールにする
        if self.fit_params and self.fit_params['x_col'] == self.properties_panel.x_axis_combo.currentText():
            ax.set_xscale('log')
        else:
            ax.set_xscale('log' if properties.get('x_log_scale') else 'linear')
        
        ax.set_yscale('log' if properties.get('y_log_scale') else 'linear')
        
        # 凡例が必要な場合のみ表示
        if ax.get_legend_handles_labels()[1]:
            ax.legend()

        self.graph_widget.fig.tight_layout()
        self.graph_widget.canvas.draw()
        
    def update_graph(self):
        """
        現在の設定に基づいてグラフ全体を再描画する。
        """
        if not hasattr(self, 'model'):
            return

        df = self.model._data
        ax = self.graph_widget.ax
        ax.clear()
        
        properties = self.properties_panel.get_properties()
        
        y_col = self.properties_panel.y_axis_combo.currentText()
        x_col = self.properties_panel.x_axis_combo.currentText()
        subgroup_col = self.properties_panel.subgroup_combo.currentText()
        
        marker_style = properties.get('marker_style', 'o')
        single_color = self.properties_panel.current_color
        subgroup_colors_map = self.properties_panel.subgroup_colors
        show_scatter = self.properties_panel.scatter_overlay_check.isChecked()

        if not y_col or not x_col:
            self.graph_widget.canvas.draw()
            return
            
        if self.current_graph_type == 'scatter':
            self._draw_scatter_plot(ax, df, x_col, y_col, marker_style, single_color, properties)
        elif self.current_graph_type == 'bar':
            # 棒グラフに切り替えたらフィット情報はクリア
            self.fit_params = None 
            self.regression_line_params = None
            self._draw_bar_chart(ax, df, x_col, y_col, subgroup_col, single_color, subgroup_colors_map, show_scatter, properties)

        # ここで回帰直線とフィッティング曲線を再描画
        linestyle = properties.get('linestyle', '-')
        linewidth = properties.get('linewidth', 1.5)

        # 線形回帰直線が存在する場合に再描画
        if hasattr(self, 'regression_line_params') and self.regression_line_params:
            params = self.regression_line_params
            ax.plot(params["x_line"], params["y_line"], color='red', 
                    label=f'R² = {params["r_squared"]:.4f}',
                    linestyle=linestyle,
                    linewidth=linewidth)

        # 非線形フィッティング曲線が存在する場合に再描画
        if self.fit_params and self.fit_params['x_col'] == x_col and self.fit_params['y_col'] == y_col:
            x_data = self.fit_params['log_x_data']
            x_fit = np.linspace(x_data.min(), x_data.max(), 200)
            y_fit = self.sigmoid_4pl(x_fit, *self.fit_params['params'])
            r_squared = self.fit_params['r_squared']
            ax.plot(10**x_fit, y_fit, color='blue', 
                      label=f'4PL Fit (R²={r_squared:.3f})',
                      linestyle=linestyle,
                      linewidth=linewidth)

        # ★ アノテーションを描画する
        self._draw_annotations()

        # グラフのプロパティを最後にまとめて適用
        self.update_graph_properties()

    def _draw_scatter_plot(self, ax, df, x_col, y_col, marker_style, color, properties):
        """散布図を描画する内部メソッド。"""
        color_to_plot = color if color else '#1f77b4'
        
        edgecolor = properties.get('marker_edgecolor', 'black')
        linewidth = properties.get('marker_edgewidth', 1.0)
        
        if pd.api.types.is_numeric_dtype(df[y_col]) and pd.api.types.is_numeric_dtype(df[x_col]):
            ax.scatter(df[x_col], df[y_col], marker=marker_style, color=color_to_plot, 
                       edgecolors=edgecolor, linewidths=linewidth)
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)

    def _draw_bar_chart(self, ax, df, x_col, y_col, subgroup_col, single_color, subgroup_colors_map, show_scatter, properties):
        """棒グラフを描画する内部メソッド。サブグループ化と実測値の重ね描きに対応。"""
        try:
            categories = sorted(df[x_col].unique())
            x_indices = np.arange(len(categories))
            
            if subgroup_col:
                # サブグループあり
                                self._draw_grouped_bar_chart(ax, df, x_col, y_col, subgroup_col, categories, x_indices, subgroup_colors_map, show_scatter, properties)
            else:
                # サブグループなし
                self._draw_simple_bar_chart(ax, df, x_col, y_col, categories, x_indices, single_color, show_scatter, properties)
            
            ax.set_xticks(x_indices)
            ax.set_xticklabels(categories, rotation=0)
            ax.set_xlabel(x_col)
            ax.set_ylabel(f"Mean of {y_col}")

        except Exception as e:
            print(f"Could not generate bar chart: {e}")

    def _draw_simple_bar_chart(self, ax, df, x_col, y_col, categories, x_indices, color, show_scatter, properties):
        """サブグループのない単純な棒グラフを描画する。"""
        summary = df.groupby(x_col)[y_col].agg(['mean', 'std']).reindex(categories)
        color_to_plot = color if color else '#1f77b4'
        
        # ★ properties から棒グラフ用の設定値を取得
        capsize = properties.get('capsize', 4)
        edgecolor = properties.get('bar_edgecolor', 'black')
        linewidth = properties.get('bar_edgewidth', 1.0)
        
        # ★ edgecolor と linewidth を ax.bar に適用
        ax.bar(x_indices, summary['mean'], width=0.8, yerr=summary['std'], 
               capsize=capsize, color=color_to_plot,
               edgecolor=edgecolor, linewidth=linewidth)
        
        capsize = properties.get('capsize', 4)
        ax.bar(x_indices, summary['mean'], width=0.8, yerr=summary['std'], capsize=capsize, color=color_to_plot)


        if show_scatter:
            for i, cat in enumerate(categories):
                points = df[df[x_col] == cat][y_col]
                jitter = np.random.uniform(-0.15, 0.15, len(points))
                ax.scatter(i + jitter, points, color='black', alpha=0.6, zorder=2)

    def _draw_grouped_bar_chart(self, ax, df, x_col, y_col, subgroup_col, categories, x_indices, subgroup_colors_map, show_scatter, properties):
        """サブグループ化された棒グラフを描画する。"""
        subcategories = sorted(df[subgroup_col].unique())
        n_subgroups = len(subcategories)
        bar_width = 0.8
        sub_bar_width = bar_width / n_subgroups

        # ★ properties から棒グラフ用の設定値を取得
        capsize = properties.get('capsize', 4)
        edgecolor = properties.get('bar_edgecolor', 'black')
        linewidth = properties.get('bar_edgewidth', 1.0)

        capsize = properties.get('capsize', 4)
       
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
            ax.bar(bar_positions, means, width=sub_bar_width * 0.9, yerr=stds, 
                   label=subcat, capsize=capsize, color=color,
                   edgecolor=edgecolor, linewidth=linewidth)
            if show_scatter:
                for k, cat in enumerate(categories):
                    points = df[(df[x_col] == cat) & (df[subgroup_col] == subcat)][y_col]
                    jitter_width = sub_bar_width * 0.4
                    jitter = np.random.uniform(-jitter_width / 2, jitter_width / 2, len(points))
                    ax.scatter(bar_positions[k] + jitter, points, color='black', alpha=0.6, zorder=2)
        
        ax.legend(title=subgroup_col)

    # ★ MainWindowクラスの一番最後に、このメソッドを丸ごと追加してください ★
    def _draw_annotations(self):
        """
        保存されている統計解析結果に基づいて、グラフにアノテーションを描画する。
        """
        if self.current_graph_type != 'bar' or not hasattr(self, 'model'):
            return

        ax = self.graph_widget.ax
        df = self.model._data

        for annotation in self.statistical_annotations:
            if annotation['type'] == 'ttest':
                group_col = annotation['group_col']
                value_col = annotation['value_col']
                group1_name, group2_name = annotation['groups']
                p_value = annotation['p_value']

                # グラフに表示されているカテゴリのリストと、そのX座標を取得
                categories = sorted(df[group_col].unique())
                try:
                    x1 = categories.index(group1_name)
                    x2 = categories.index(group2_name)
                except ValueError:
                    continue # 比較対象のグループが現在のグラフにない場合はスキップ

                # 2つの棒の最大高さを計算 (エラーバー含む)
                y1_mean = df[df[group_col] == group1_name][value_col].mean()
                y1_std = df[df[group_col] == group1_name][value_col].std()
                y2_mean = df[df[group_col] == group2_name][value_col].mean()
                y2_std = df[df[group_col] == group2_name][value_col].std()
                
                max_y = max(y1_mean + y1_std, y2_mean + y2_std)
                
                # ブラケットの高さを決定
                bracket_height = max_y * 1.05 # 棒の最大値より5%高い位置
                text_height = max_y * 1.08    # テキストはさらにその少し上

                # p値からアスタリスクに変換
                if p_value < 0.001:
                    significance = '***'
                elif p_value < 0.01:
                    significance = '**'
                elif p_value < 0.05:
                    significance = '*'
                else:
                    significance = 'ns' # Not Significant

                # ブラケットを描画
                ax.plot([x1, x1, x2, x2], [bracket_height, text_height, text_height, bracket_height], lw=1.5, c='black')
                # テキスト(アスタリスク)を描画
                ax.text((x1 + x2) * 0.5, text_height, significance, ha='center', va='bottom', fontsize=14)
                
    def clear_annotations(self):
        """
        グラフ上のすべてのアノテーションをクリアする。
        """
        if hasattr(self, 'statistical_annotations'):
            self.statistical_annotations.clear()
            self.update_graph()