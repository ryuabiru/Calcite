# action_handler.py

import pandas as pd
import numpy as np
import io
from PySide6.QtWidgets import QFileDialog, QMessageBox, QApplication, QDialog, QVBoxLayout, QTextEdit
from scipy.stats import ttest_ind, ttest_rel, f_oneway, linregress, chi2_contingency
from scipy.optimize import curve_fit
from statsmodels.stats.multicomp import pairwise_tukeyhsd

from pandas_model import PandasModel
# --- Dialogs ---
from dialogs.restructure_dialog import RestructureDialog
from dialogs.calculate_dialog import CalculateDialog
from dialogs.anova_dialog import AnovaDialog
from dialogs.ttest_dialog import TTestDialog
from dialogs.paired_ttest_dialog import PairedTTestDialog
from dialogs.fitting_dialog import FittingDialog
from dialogs.contingency_dialog import ContingencyDialog
from dialogs.pivot_dialog import PivotDialog

class ActionHandler:
    """
    UIからのアクション（メニュー選択など）に対応するデータ処理や統計解析のロジックを担当するクラス。
    """
    def __init__(self, main_window):
        """
        ActionHandlerを初期化します。

        Args:
            main_window (MainWindow): メインウィンドウのインスタンス。
        """
        self.main = main_window

    def open_csv_file(self):
        """CSVファイルを開き、内容をテーブルに読み込む。"""
        file_path, _ = QFileDialog.getOpenFileName(self.main, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)")
        if file_path:
            try:
                df = pd.read_csv(file_path)
                self.main.model = PandasModel(df)
                self.main.table_view.setModel(self.main.model)
                self.main.properties_panel.set_columns(df.columns)

                # データ変更がグラフに反映されるようにシグナルを接続
                # TODO: 将来的にはGraphManagerに通知する形にする
                self.main.table_view.selectionModel().selectionChanged.connect(self.main.update_graph)
                self.main.model.dataChanged.connect(self.main.update_graph)
                self.main.model.headerDataChanged.connect(self.main.update_graph)

            except Exception as e:
                QMessageBox.critical(self.main, "Error", f"Error opening file: {e}")

    def paste_from_clipboard(self):
        """クリップボードからタブ区切りテキストを読み込み、テーブルに貼り付ける。"""
        try:
            clipboard = QApplication.clipboard()
            text = clipboard.text()
            if not text:
                return

            df = pd.read_csv(io.StringIO(text), sep='\t')
            self.main.model = PandasModel(df)
            self.main.table_view.setModel(self.main.model)
            self.main.properties_panel.set_columns(df.columns)
            
            # シグナル接続
            self.main.table_view.selectionModel().selectionChanged.connect(self.main.update_graph)
            self.main.model.dataChanged.connect(self.main.update_graph)
            self.main.model.headerDataChanged.connect(self.main.update_graph)

        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to paste from clipboard: {e}")

    def show_calculate_dialog(self):
        """新しい列を計算するためのダイアログを表示し、設定に基づいて計算を実行する。"""
        if not hasattr(self.main, 'model'):
            QMessageBox.warning(self.main, "Warning", "Please load data first.")
            return

        df = self.main.model._data
        dialog = CalculateDialog(df.columns, self.main)
        
        if dialog.exec():
            settings = dialog.get_settings()
            if not settings['new_column_name'] or not settings['formula']:
                QMessageBox.warning(self.main, "Warning", "Please enter both a new column name and a formula.")
                return
            self.calculate_new_column(settings)

    def calculate_new_column(self, settings):
        """指定された計算式に基づいて新しい列を計算し、テーブルを更新する。"""
        try:
            df = self.main.model._data
            new_col_name = settings['new_column_name']
            formula = settings['formula']

            df[new_col_name] = df.eval(formula, engine='python')

            self.main.model.refresh_model()
            self.main.properties_panel.set_columns(df.columns)

        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to calculate column: {e}")

    def show_restructure_dialog(self):
        """ワイドフォーマットからロングフォーマットへデータを変換するためのダイアログを表示する。"""
        if not hasattr(self.main, 'model'):
            QMessageBox.warning(self.main, "Warning", "Please load data first.")
            return

        df = self.main.model._data
        dialog = RestructureDialog(df.columns, self.main)
        
        if dialog.exec():
            settings = dialog.get_settings()
            if not settings['id_vars'] or not settings['value_vars']:
                QMessageBox.warning(self.main, "Warning", "Please select both Identifier and Value columns.")
                return
            self.restructure_data(settings)
            
    def restructure_data(self, settings):
        """pd.meltを使用してデータをワイドからロングフォーマットに変換し、新しいウィンドウで結果を表示する。"""
        try:
            df = self.main.model._data
            new_df = pd.melt(
                df,
                id_vars=settings['id_vars'],
                value_vars=settings['value_vars'],
                var_name=settings['var_name'],
                value_name=settings['value_name']
            )
            
            # self.main.__class__() を使って新しいウィンドウを生成
            new_window = self.main.__class__()
            new_window.model = PandasModel(new_df)
            new_window.table_view.setModel(new_window.model)
            new_window.properties_panel.set_columns(new_df.columns)
            new_window.setWindowTitle(self.main.windowTitle() + " [Restructured]")
            new_window.show()
            
            new_window.table_view.selectionModel().selectionChanged.connect(new_window.update_graph)
            new_window.model.dataChanged.connect(new_window.update_graph)
            new_window.model.headerDataChanged.connect(new_window.update_graph)
            
            app = QApplication.instance()
            if not hasattr(app, 'main_windows'):
                app.main_windows = []
            app.main_windows.append(new_window)

        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to restructure data: {e}")
            
    def show_pivot_dialog(self):
        """ロングからワイドへのデータ変換ダイアログを表示する。"""
        if not hasattr(self.main, 'model'):
            QMessageBox.warning(self.main, "Warning", "Please load data first.")
            return

        df = self.main.model._data
        dialog = PivotDialog(df.columns, self.main)
        
        if dialog.exec():
            settings = dialog.get_settings()
            if not all(settings.values()):
                QMessageBox.warning(self.main, "Warning", "Please select all three columns.")
                return
            self.pivot_data(settings)

    def pivot_data(self, settings):
        """pd.pivot_tableを使用してデータをロングからワイドフォーマットに変換し、新しいウィンドウで結果を表示する。"""
        try:
            df = self.main.model._data
            new_df = pd.pivot_table(
                df,
                index=settings['id_vars'],
                columns=settings['var_name'],
                values=settings['value_name']
            ).reset_index()

            new_window = self.main.__class__()
            new_window.model = PandasModel(new_df)
            new_window.table_view.setModel(new_window.model)
            new_window.properties_panel.set_columns(new_df.columns)
            new_window.setWindowTitle(self.main.windowTitle() + " [Pivoted]")
            new_window.show()
            
            new_window.table_view.selectionModel().selectionChanged.connect(new_window.update_graph)
            new_window.model.dataChanged.connect(new_window.update_graph)
            new_window.model.headerDataChanged.connect(new_window.update_graph)

            app = QApplication.instance()
            if not hasattr(app, 'main_windows'):
                app.main_windows = []
            app.main_windows.append(new_window)

        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to pivot data: {e}")

    # --- Statistical Analysis ---
    
    def perform_t_test(self):
        """独立t検定を実行する。"""
        if not hasattr(self.main, 'model'):
            QMessageBox.warning(self.main, "Warning", "Please load data first.")
            return

        df = self.main.model._data
        dialog = TTestDialog(df.columns, df, self.main)

        if dialog.exec():
            settings = dialog.get_settings()
            value_col, group_col = settings['value_col'], settings['group_col']
            group1_name, group2_name = settings['group1'], settings['group2']

            if not all([value_col, group_col, group1_name, group2_name]):
                QMessageBox.warning(self.main, "Warning", "Please select all fields.")
                return
            
            try:
                group1_data = df[df[group_col] == group1_name][value_col].dropna()
                group2_data = df[df[group_col] == group2_name][value_col].dropna()

                if group1_data.empty or group2_data.empty:
                    QMessageBox.warning(self.main, "Warning", "One or both selected groups have no data.")
                    return

                t_stat, p_value = ttest_ind(group1_data, group2_data)

                annotation = {
                    "type": "ttest",
                    "p_value": p_value,
                    "group_col": group_col,
                    "value_col": value_col,
                    "groups": [group1_name, group2_name]
                }
                self.main.statistical_annotations.append(annotation)
                self.main.update_graph() # GraphManagerに委譲予定

                result_text = (f"Independent t-test results:\n...") # (結果表示のテキストは省略)
                self.show_results_dialog("t-test Result", result_text)

            except Exception as e:
                QMessageBox.critical(self.main, "Error", f"Failed to perform t-test: {e}")
                
    def perform_paired_t_test(self):
        """対応のあるt検定を実行する。"""
        if not hasattr(self.main, 'model'):
            QMessageBox.warning(self.main, "Warning", "Please load data first.")
            return

        df = self.main.model._data
        dialog = PairedTTestDialog(df.columns, self.main)

        if dialog.exec():
            settings = dialog.get_settings()
            col1, col2 = settings['col1'], settings['col2']
            # ... (以下、t検定のロジックは同様に main_window.py から移動) ...

    # ... (perform_one_way_anova, perform_chi_squared_testなども同様に移動) ...
    
    # --- Regression Analysis ---
    
    def perform_linear_regression(self):
        """線形回帰分析を実行する。"""
        if not hasattr(self.main, 'model'):
            QMessageBox.warning(self.main, "Warning", "Please load data first.")
            return
            
        selected_columns = sorted(list(set(index.column() for index in self.main.table_view.selectionModel().selectedIndexes())))

        if len(selected_columns) != 2:
            QMessageBox.warning(self.main, "Warning", "Please select exactly two columns.")
            return

        df = self.main.model._data
        x_col_index, y_col_index = selected_columns
        
        x_data = df.iloc[:, x_col_index].dropna()
        y_data = df.iloc[:, y_col_index].dropna()
        
        slope, intercept, r_value, p_value, std_err = linregress(x_data, y_data)

        self.main.regression_line_params = {
            "x_line": np.array([x_data.min(), x_data.max()]),
            "y_line": slope * np.array([x_data.min(), x_data.max()]) + intercept,
            "r_squared": r_value**2
        }
        self.main.fit_params = None
        self.main.update_graph() # GraphManagerに委譲予定

    # ... (perform_fittingも同様に移動) ...

    # --- Helper Methods ---

    def show_results_dialog(self, title, text):
        """解析結果などを表示するための汎用的なダイアログを表示する。"""
        dialog = QDialog(self.main)
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