# handlers/action_handler.py

import pandas as pd
import numpy as np
import io
from PySide6.QtWidgets import QFileDialog, QMessageBox, QApplication, QVBoxLayout
from scipy.optimize import curve_fit
from statsmodels.stats.multicomp import pairwise_tukeyhsd
import scikit_posthocs as sp

from pandas_model import PandasModel
# --- Dialogs ---
from dialogs.restructure_dialog import RestructureDialog
from dialogs.calculate_dialog import CalculateDialog
from dialogs.anova_dialog import AnovaDialog
from dialogs.kruskal_dialog import KruskalDialog
from dialogs.ttest_dialog import TTestDialog
from dialogs.mannwhitney_dialog import MannWhitneyDialog
from dialogs.paired_ttest_dialog import PairedTTestDialog
from dialogs.wilcoxon_dialog import WilcoxonDialog
from dialogs.correlation_dialog import CorrelationDialog
from dialogs.regression_dialog import RegressionDialog
from dialogs.contingency_dialog import ContingencyDialog
from dialogs.pivot_dialog import PivotDialog
from dialogs.advanced_filter_dialog import AdvancedFilterDialog
from handlers.statistical_handler import StatisticalHandler

import traceback

class ActionHandler:
    
    _UNIQUE_SEPARATOR = '_#%%%_'
    
    def __init__(self, main_window):
        self.main = main_window
        # StatisticalHandlerのインスタンスを生成し、参照を保持する
        self.statistical_handler = StatisticalHandler(main_window)


    def save_table_as_csv(self):
        """現在表示されているテーブルデータをCSVとして保存する"""
        if not hasattr(self.main, 'model') or self.main.model is None:
            QMessageBox.warning(self.main, "Warning", "No data to save.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(self.main, "Save CSV File", "", "CSV Files (*.csv);;All Files (*)")
        
        if file_path:
            try:
                df = self.main.model._data
                df.to_csv(file_path, index=False)
                QMessageBox.information(self.main, "Success", f"Table successfully saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self.main, "Error", f"Failed to save table: {e}")



    def open_csv_file(self):
        """CSVファイルを開き、内容をテーブルに読み込む。"""
        file_path, _ = QFileDialog.getOpenFileName(self.main, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)")
        if file_path:
            try:
                df = pd.read_csv(file_path)
                self.main.model = PandasModel(df)
                self.main.table_view.setModel(self.main.model)
                self.main.properties_panel.set_columns(df.columns)
                self.main.results_widget.clear_results()
                
                # GraphManagerのupdate_graphに接続する
                self.main.table_view.selectionModel().selectionChanged.connect(self.main.graph_manager.update_graph)
                self.main.model.dataChanged.connect(self.main.graph_manager.update_graph)
                self.main.model.headerDataChanged.connect(self.main.graph_manager.update_graph)
                
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
            self.main.results_widget.clear_results() # ★★★ 追加 ★★★
            
            self.main.table_view.selectionModel().selectionChanged.connect(self.main.graph_manager.update_graph)
            self.main.model.dataChanged.connect(self.main.graph_manager.update_graph)
            self.main.model.headerDataChanged.connect(self.main.graph_manager.update_graph)
            
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

# ---データハンドリング---

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
            
            new_window.table_view.selectionModel().selectionChanged.connect(new_window.graph_manager.update_graph)
            new_window.model.dataChanged.connect(new_window.graph_manager.update_graph)
            new_window.model.headerDataChanged.connect(new_window.graph_manager.update_graph)
            
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
            
            new_window.table_view.selectionModel().selectionChanged.connect(new_window.graph_manager.update_graph)
            new_window.model.dataChanged.connect(new_window.graph_manager.update_graph)
            new_window.model.headerDataChanged.connect(new_window.graph_manager.update_graph)
            
            app = QApplication.instance()
            if not hasattr(app, 'main_windows'):
                app.main_windows = []
            app.main_windows.append(new_window)
            
        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to pivot data: {e}")


# --- フィルタリング ---


    def show_advanced_filter_dialog(self):
        """高度なフィルタリング条件を設定するダイアログを表示する"""
        if not hasattr(self.main, 'model') or self.main.model is None:
            QMessageBox.warning(self.main, "Warning", "Please load data first.")
            return
        
        df = self.main.model._data
        dialog = AdvancedFilterDialog(df, self.main)
        
        if dialog.exec():
            settings = dialog.get_settings()
            if not settings:
                QMessageBox.warning(self.main, "Warning", "One or more filter conditions are incomplete or invalid.")
                return
            self.apply_advanced_filter(settings)


    def apply_advanced_filter(self, settings):
        """指定された複数条件に基づいてデータをフィルタリングする"""
        query_parts = []
        try:
            df = self.main.model._data.copy()
            
            # --- 翻訳担当のコアロジック ---
            for i, condition in enumerate(settings):
                col = condition['column']
                op = condition['operator']
                val = condition['value']
                
                # 値を安全にクエリ文字列用にフォーマット
                query_val = f'"{val}"' if isinstance(val, str) else str(val)
                
                # 個々の条件式を作成
                if op in ["contains", "not contains", "startswith", "endswith"]:
                    if op == "not contains":
                        part = f'~`{col}`.str.contains({query_val})'
                    else:
                        part = f'`{col}`.str.{op}({query_val})'
                else:
                    part = f'`{col}` {op} {query_val}'
                    
                # 最初の条件でなければ、AND/ORで連結する
                if i > 0:
                    connector = condition['connector']
                    query_parts.append(f" {connector} ({part})")
                else:
                    query_parts.append(f"({part})")
            
            final_query = "".join(query_parts)
            
            new_df = df.query(final_query, engine='python').reset_index(drop=True)
            
            if new_df.empty:
                QMessageBox.information(self.main, "Info", "The filter returned no data.")
                return
            
            # 新しいウィンドウで結果を表示
            new_window = self.main.__class__(data=new_df)
            new_window.setWindowTitle(self.main.windowTitle() + " [Filtered]")
            new_window.show()
            
            app = QApplication.instance()
            if not hasattr(app, 'main_windows'): app.main_windows = []
            app.main_windows.append(new_window)
            
        except Exception as e:
            final_query_str = "".join(query_parts)
            QMessageBox.critical(self.main, "Error", f"Failed to apply filter: {e}\n\nAttempted Query: {final_query_str}")
            traceback.print_exc()
