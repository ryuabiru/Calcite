# handlers/action_handler.py

import pandas as pd
import json
import zipfile
import tempfile
import numpy as np
import io
import os
import traceback

from PySide6.QtWidgets import QFileDialog, QMessageBox, QApplication, QVBoxLayout
from scipy.optimize import curve_fit
from statsmodels.stats.multicomp import pairwise_tukeyhsd
import scikit_posthocs as sp

from ..pandas_model import PandasModel

# --- Dialogs ---
from ..dialogs.restructure_dialog import RestructureDialog
from ..dialogs.calculate_dialog import CalculateDialog
from ..dialogs.pivot_dialog import PivotDialog
from ..dialogs.advanced_filter_dialog import AdvancedFilterDialog
from ..dialogs.license_dialog import LicenseDialog

from .statistical_handler import StatisticalHandler

class NumpyArrayEncoder(json.JSONEncoder):
    """
    NumPyのndarrayや数値型を、JSONが理解できるPythonの基本型に変換する。
    """
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist() # ndarray -> list
        if isinstance(obj, pd.Series):
            return obj.tolist()
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                            np.int16, np.int32, np.int64, np.uint8,
                            np.uint16, np.uint32, np.uint64)):
            return int(obj)     # numpy int -> python int
        if isinstance(obj, (np.float64, np.float16, np.float32)):
            return float(obj)  # numpy float -> python float
        return json.JSONEncoder.default(self, obj)

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
                
                # メモリ削減のためにcategory型に変換
                for col in df.select_dtypes(include=['object']).columns:
                    num_unique_values = df[col].nunique()
                    num_total_values = len(df[col])
                    # ユニークな値の割合が50%未満ならcategory型に変換
                    if num_unique_values / num_total_values < 0.5:
                        print(f"Converting column '{col}' to 'category' type.")
                        df[col] = df[col].astype('category')
                
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


    def save_project(self):
        """現在の作業状態を .calcite プロジェクトファイルとして保存する"""
        if not hasattr(self.main, 'model') or self.main.model is None:
            QMessageBox.warning(self.main, "Warning", "No data to save.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self.main, "Save Calcite Project", "", "Calcite Project Files (*.calcite)"
        )

        if not file_path:
            return

        try:
            # 一時的な作業ディレクトリを作成
            with tempfile.TemporaryDirectory() as temp_dir:
                print(f"DEBUG: Created temporary directory: {temp_dir}")
                
                # 1. データをCSVとして保存
                csv_path = os.path.join(temp_dir, 'data.csv')
                self.main.model._data.to_csv(csv_path, index=False)
                print("DEBUG: Saved data.csv")

                # 2. グラフ設定をJSONとして保存
                settings_path = os.path.join(temp_dir, 'settings.json')
                settings = self.main.properties_panel.get_properties()
                with open(settings_path, 'w') as f:
                    json.dump(settings, f, indent=4)
                print("DEBUG: Saved settings.json")

                # 3. 解析結果をJSONとして保存
                analysis_path = os.path.join(temp_dir, 'analysis.json')
                analysis_data = {
                    'statistical_annotations': self.main.statistical_annotations,
                    'paired_annotations': self.main.paired_annotations,
                    'regression_line_params': self.main.regression_line_params,
                    'fit_params': self.main.fit_params,
                }
                with open(analysis_path, 'w') as f:
                    json.dump(analysis_data, f, indent=4, cls=NumpyArrayEncoder)
                print("DEBUG: Saved analysis.json")

                # 4. 一時ディレクトリの中身をzipファイルに圧縮
                with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for root, _, files in os.walk(temp_dir):
                        for file in files:
                            full_path = os.path.join(root, file)
                            arcname = os.path.relpath(full_path, temp_dir)
                            zf.write(full_path, arcname)
                print(f"DEBUG: Project successfully zipped to {file_path}")

            QMessageBox.information(self.main, "Success", f"Project saved to:\n{file_path}")
            self.main.statusBar().showMessage(f"Project saved: {os.path.basename(file_path)}")

        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to save project: {e}")
            traceback.print_exc()


    def open_project(self):
        """ .calcite プロジェクトファイルを読み込み、作業状態を復元する"""
        file_path, _ = QFileDialog.getOpenFileName(
            self.main, "Open Calcite Project", "", "Calcite Project Files (*.calcite)"
        )

        if not file_path:
            return

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # zipファイルを一時ディレクトリに展開
                with zipfile.ZipFile(file_path, 'r') as zf:
                    zf.extractall(temp_dir)
                print(f"DEBUG: Project extracted to {temp_dir}")

                # 1. データをCSVから読み込む
                csv_path = os.path.join(temp_dir, 'data.csv')
                if os.path.exists(csv_path):
                    df = pd.read_csv(csv_path)
                    self.main.load_dataframe(df) # MainWindowの既存のメソッドを再利用
                    print("DEBUG: Loaded data.csv")

                # 2. グラフ設定をJSONから読み込む (TODO: 復元ロジック)
                settings_path = os.path.join(temp_dir, 'settings.json')
                if os.path.exists(settings_path):
                    with open(settings_path, 'r') as f:
                        settings = json.load(f)
                    self.main.properties_panel.set_properties(settings)
                    print("DEBUG: Loaded and applied settings.json to UI.")

                # 3. 解析結果をJSONから読み込む
                analysis_path = os.path.join(temp_dir, 'analysis.json')
                if os.path.exists(analysis_path):
                    with open(analysis_path, 'r') as f:
                        analysis_data = json.load(f)
                    self.main.statistical_annotations = analysis_data.get('statistical_annotations', [])
                    self.main.paired_annotations = analysis_data.get('paired_annotations', [])

                    reg_params = analysis_data.get('regression_line_params')
                    if reg_params:
                        if 'x_line' in reg_params: # 単一フィットの場合
                            reg_params['x_line'] = np.array(reg_params['x_line'])
                            reg_params['y_line'] = np.array(reg_params['y_line'])
                        else: # サブグループごとのフィットの場合
                            for group in reg_params:
                                reg_params[group]['x_line'] = np.array(reg_params[group]['x_line'])
                                reg_params[group]['y_line'] = np.array(reg_params[group]['y_line'])
                    self.main.regression_line_params = reg_params

                    # fit_params の復元
                    fit_params = analysis_data.get('fit_params')
                    if fit_params:
                        if 'params' in fit_params: # 単一フィットの場合
                            fit_params['params'] = np.array(fit_params['params'])
                            fit_params['log_x_data'] = np.array(fit_params['log_x_data'])
                        else: # サブグループごとのフィットの場合
                            for group in fit_params:
                                fit_params[group]['params'] = np.array(fit_params[group]['params'])
                                fit_params[group]['log_x_data'] = np.array(fit_params[group]['log_x_data'])
                    self.main.fit_params = fit_params

            self.main.graph_manager.update_graph()
            self.main.statusBar().showMessage(f"Project opened: {os.path.basename(file_path)}")

        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to open project: {e}")
            traceback.print_exc()


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


    def create_table_from_selection(self):
        """
        テーブルで選択されている行を抽出し、新しいウィンドウで表示する。
        """
        if not hasattr(self.main, 'model') or self.main.model is None:
            QMessageBox.warning(self.main, "Warning", "No data available.")
            return
        
        selection_model = self.main.table_view.selectionModel()
        selected_rows = selection_model.selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self.main, "Warning", "Please select one or more rows to create a new table.")
            return
        
        try:
            # 選択された行のインデックス（番号）を取得し、重複をなくしてソートする
            row_indices = sorted(list(set(index.row() for index in selected_rows)))
            
            # 元のデータフレームから、選択された行を番号で抽出する
            original_df = self.main.model._data
            new_df = original_df.iloc[row_indices].copy().reset_index(drop=True)
            
            # 既存のロジックを再利用して、新しいウィンドウを生成・表示
            new_window = self.main.__class__(data=new_df)
            new_window.setWindowTitle(self.main.windowTitle() + " [Subset]")
            new_window.show()
            
            # 新しいウィンドウをアプリケーションの管理リストに追加
            app = QApplication.instance()
            if not hasattr(app, 'main_windows'):
                app.main_windows = []
            app.main_windows.append(new_window)
            
        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to create new table from selection: {e}")
            traceback.print_exc()


    def show_license_dialog(self):
        """
        サードパーティライブラリのライセンス情報を表示するダイアログを開く。
        """
        try:
            
            other_licenses = []
            base_path = os.path.dirname(os.path.abspath(__file__))
            license_dir = os.path.join(base_path, '..', 'LICENSES')

            if os.path.isdir(license_dir):
                for filename in sorted(os.listdir(license_dir)):
                    if filename.endswith(".txt"):
                        lib_name = filename.replace("LICENSES_", "").replace(".txt", "")
                        with open(os.path.join(license_dir, filename), 'r', encoding='utf-8') as f:
                            content = f.read()
                            other_licenses.append(
                                f"----------------------------------------\n"
                                f"{lib_name.capitalize()}\n"
                                f"----------------------------------------\n"
                                f"{content}\n"
                            )
            
            pyside6_license = (
                "----------------------------------------\n"
                "PySide6 (LGPL v3)\n"
                "----------------------------------------\n"
                "This application uses PySide6, which is licensed under the GNU Lesser General Public License (LGPL), version 3.\n\n"
                "Under the terms of the LGPL, you have the right to access the source code of PySide6 and to replace the library with your own modified version.\n\n"
                "You can obtain the source code for PySide6 from its official repository:\n"
                "<a href='https://code.qt.io/cgit/pyside/pyside-setup.git/'>https://code.qt.io/cgit/pyside/pyside-setup.git/</a>\n\n"
            )
            
            # --- 3. すべてのライセンス情報を結合してダイアログを表示 ---
            final_text_content = "\n".join(other_licenses) + pyside6_license
            final_html = final_text_content.replace("\n", "<br>")
            
            dialog = LicenseDialog(final_html, self.main)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Could not display licenses: {e}")
            traceback.print_exc()