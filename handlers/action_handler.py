# handlers/action_handler.py

import pandas as pd
import numpy as np
import io
from PySide6.QtWidgets import QFileDialog, QMessageBox, QApplication, QDialog, QVBoxLayout, QTextEdit
from scipy.stats import ttest_ind, ttest_rel, f_oneway, linregress, chi2_contingency
from scipy.optimize import curve_fit
from statsmodels.stats.multicomp import pairwise_tukeyhsd

from pandas_model import PandasModel
from dialogs.restructure_dialog import RestructureDialog
from dialogs.calculate_dialog import CalculateDialog
from dialogs.anova_dialog import AnovaDialog
from dialogs.ttest_dialog import TTestDialog
from dialogs.paired_ttest_dialog import PairedTTestDialog
from dialogs.fitting_dialog import FittingDialog
from dialogs.contingency_dialog import ContingencyDialog
from dialogs.pivot_dialog import PivotDialog

class ActionHandler:
    def __init__(self, main_window):
        self.main = main_window

    # open_csv_fileからpivot_dataまでは変更なし

    def perform_t_test(self):
        """独立t検定を実行する。 statannotations を利用する形式に修正。"""
        if not hasattr(self.main, 'model'): return
        df = self.main.model._data
        dialog = TTestDialog(df.columns, df, self.main)

        if dialog.exec():
            settings = dialog.get_settings()
            value_col = settings['value_col']
            g1_filters = settings['group1_filters']
            g2_filters = settings['group2_filters']

            if not value_col or not g1_filters or not g2_filters:
                QMessageBox.warning(self.main, "Warning", "Please define both groups and select a value column.")
                return
            try:
                group1_data = df.copy()
                for col, val in g1_filters.items():
                    group1_data = group1_data[group1_data[col].astype(str) == str(val)]
                
                group2_data = df.copy()
                for col, val in g2_filters.items():
                    group2_data = group2_data[group2_data[col].astype(str) == str(val)]

                group1_values = group1_data[value_col].dropna()
                group2_values = group2_data[value_col].dropna()

                if group1_values.empty or group2_values.empty:
                    QMessageBox.warning(self.main, "Warning", "One or both selected groups have no data after filtering.")
                    return
                
                t_stat, p_value = ttest_ind(group1_values, group2_values)

                # どの列の値が違うのかを特定する
                diff_key = None
                diff_values = []
                all_keys = set(g1_filters.keys()) | set(g2_filters.keys())
                for key in all_keys:
                    if g1_filters.get(key) != g2_filters.get(key):
                        diff_key = key
                        diff_values = [g1_filters.get(key), g2_filters.get(key)]
                        break
                
                # p値が有意な場合のみアノテーション情報を追加
                if diff_key and p_value < 0.05:
                    annotation = {
                        "value_col": value_col,
                        "group_col": diff_key,
                        "box_pair": (str(diff_values[0]), str(diff_values[1]))
                    }
                    # 既存のアノテーションと重複しないかチェック
                    if annotation not in self.main.statistical_annotations:
                        self.main.statistical_annotations.append(annotation)
                    
                    self.main.graph_manager.update_graph()

                g1_name = " & ".join([f"{k}='{v}'" for k, v in g1_filters.items()])
                g2_name = " & ".join([f"{k}='{v}'" for k, v in g2_filters.items()])
                result_text = (
                    f"Independent t-test results:\n"
                    f"===========================\n\n"
                    f"Comparing '{value_col}' between:\n"
                    f"- Group 1: {g1_name} (Mean: {group1_values.mean():.3f})\n"
                    f"- Group 2: {g2_name} (Mean: {group2_values.mean():.3f})\n\n"
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
                QMessageBox.critical(self.main, "Error", f"Failed to perform t-test: {e}")

    def perform_one_way_anova(self):
        """一元配置分散分析を実行する。 statannotations を利用する形式に修正。"""
        if not hasattr(self.main, 'model'): return
        df = self.main.model._data
        dialog = AnovaDialog(df.columns, self.main)

        if dialog.exec():
            settings = dialog.get_settings()
            value_col, group_col = settings['value_col'], settings['group_col']
            if not value_col or not group_col or value_col == group_col: return
            try:
                groups = df[group_col].dropna().unique()
                if len(groups) < 2: 
                    QMessageBox.warning(self.main, "Warning", "ANOVA requires at least 2 groups.")
                    return
                
                samples = [df[value_col][df[group_col] == g].dropna() for g in groups]
                f_stat, p_value = f_oneway(*samples)

                result_text = f"One-way ANOVA Results\n======================\n\nF-statistic: {f_stat:.4f}\np-value: {p_value:.4f}\n\n"
                
                if p_value < 0.05 and len(groups) > 2:
                    all_data = pd.concat([s for s in samples if not s.empty])
                    group_labels = np.repeat([str(g) for g, s in zip(groups, samples) if not s.empty], [len(s) for s in samples if not s.empty])
                    
                    tukey_result = pairwise_tukeyhsd(endog=all_data, groups=group_labels, alpha=0.05)
                    df_tukey = pd.DataFrame(data=tukey_result._results_table.data[1:], columns=tukey_result._results_table.data[0])
                    
                    for _, row in df_tukey.iterrows():
                        if row['p-adj'] < 0.05:
                            annotation = {
                                "value_col": value_col,
                                "group_col": group_col,
                                "box_pair": (str(row['group1']), str(row['group2']))
                            }
                            if annotation not in self.main.statistical_annotations:
                                self.main.statistical_annotations.append(annotation)
                    
                    result_text += "Post-hoc test (Tukey's HSD):\n"
                    result_text += str(tukey_result)
                    self.main.graph_manager.update_graph()
                
                self.show_results_dialog("ANOVA Result", result_text)
            except Exception as e:
                QMessageBox.critical(self.main, "Error", f"Failed to perform ANOVA: {e}")
                
    def perform_paired_t_test(self):
        """対応のあるt検定を実行する。"""
        if not hasattr(self.main, 'model'): return
        df = self.main.model._data
        dialog = PairedTTestDialog(df.columns, self.main)

        if dialog.exec():
            settings = dialog.get_settings()
            col1, col2 = settings['col1'], settings['col2']
            if not col1 or not col2 or col1 == col2:
                QMessageBox.warning(self.main, "Warning", "Please select two different columns.")
                return
            try:
                data1 = df[col1].dropna()
                data2 = df[col2].dropna()
                min_len = min(len(data1), len(data2))
                if min_len < 2:
                     QMessageBox.warning(self.main, "Warning", "Not enough paired data to perform the test.")
                     return
                
                t_stat, p_value = ttest_rel(data1[:min_len], data2[:min_len])

                result_text = (
                    f"Paired t-test results:\n"
                    f"=====================\n\n"
                    f"Comparing:\n"
                    f"- Column 1: '{col1}' (Mean: {data1.mean():.3f})\n"
                    f"- Column 2: '{col2}' (Mean: {data2.mean():.3f})\n\n"
                    f"---\n"
                    f"t-statistic: {t_stat:.4f}\n"
                    f"p-value: {p_value:.4f}\n\n"
                )
                if p_value < 0.05:
                    result_text += "Conclusion: The difference is statistically significant (p < 0.05)."
                else:
                    result_text += "Conclusion: The difference is not statistically significant (p >= 0.05)."
                self.show_results_dialog("Paired t-test Result", result_text)

            except Exception as e:
                QMessageBox.critical(self.main, "Error", f"Failed to perform paired t-test: {e}")

    def perform_one_way_anova(self):
        """一元配置分散分析を実行する。"""
        if not hasattr(self.main, 'model'): return
        df = self.main.model._data
        dialog = AnovaDialog(df.columns, self.main)

        if dialog.exec():
            settings = dialog.get_settings()
            value_col, group_col = settings['value_col'], settings['group_col']
            if not value_col or not group_col or value_col == group_col: return
            try:
                groups = df[group_col].dropna().unique()
                if len(groups) < 2: 
                    QMessageBox.warning(self.main, "Warning", "ANOVA requires at least 2 groups.")
                    return
                
                samples = [df[value_col][df[group_col] == g].dropna() for g in groups]
                f_stat, p_value = f_oneway(*samples)

                result_text = f"One-way ANOVA Results\n======================\n\nF-statistic: {f_stat:.4f}\np-value: {p_value:.4f}\n\n"
                
                if p_value < 0.05 and len(groups) > 2:
                    all_data = pd.concat(samples)
                    group_labels = np.repeat([str(g) for g in groups], [len(s) for s in samples])
                    tukey_result = pairwise_tukeyhsd(endog=all_data, groups=group_labels, alpha=0.05)
                    df_tukey = pd.DataFrame(data=tukey_result._results_table.data[1:], columns=tukey_result._results_table.data[0])
                    
                    for _, row in df_tukey.iterrows():
                        if row['p-adj'] < 0.05:
                            annotation = {"type": "ttest", "p_value": row['p-adj'], "group_col": group_col, "value_col": value_col, "groups": [row['group1'], row['group2']]}
                            self.main.statistical_annotations.append(annotation)
                    
                    result_text += "Post-hoc test (Tukey's HSD):\n"
                    result_text += str(tukey_result)
                    self.main.graph_manager.update_graph()
                
                self.show_results_dialog("ANOVA Result", result_text)
            except Exception as e:
                QMessageBox.critical(self.main, "Error", f"Failed to perform ANOVA: {e}")

    def perform_chi_squared_test(self):
        """カイ二乗検定を実行する。"""
        if not hasattr(self.main, 'model'): return
        df = self.main.model._data
        dialog = ContingencyDialog(df.columns, self.main)
        if dialog.exec():
            settings = dialog.get_settings()
            rows_col, cols_col = settings['rows_col'], settings['cols_col']
            if not rows_col or not cols_col or rows_col == cols_col: return
            try:
                contingency_table = pd.crosstab(df[rows_col], df[cols_col])
                chi2, p, dof, expected = chi2_contingency(contingency_table)
                expected_table = pd.DataFrame(expected, index=contingency_table.index, columns=contingency_table.columns)

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
                QMessageBox.critical(self.main, "Error", f"Failed to perform Chi-squared test: {e}")

    # --- Regression Analysis ---
    
    def perform_linear_regression(self):
        """線形回帰分析を実行する。"""
        if not hasattr(self.main, 'model'): return
        selected_columns = sorted(list(set(index.column() for index in self.main.table_view.selectionModel().selectedIndexes())))
        if len(selected_columns) != 2: 
            QMessageBox.warning(self.main, "Warning", "Please select exactly two columns.")
            return

        df = self.main.model._data
        x_col_index, y_col_index = selected_columns
        x_data, y_data = df.iloc[:, x_col_index].dropna(), df.iloc[:, y_col_index].dropna()
        
        slope, intercept, r_value, p_value, std_err = linregress(x_data, y_data)

        self.main.regression_line_params = {
            "x_line": np.array([x_data.min(), x_data.max()]),
            "y_line": slope * np.array([x_data.min(), x_data.max()]) + intercept,
            "r_squared": r_value**2
        }
        self.main.fit_params = None
        self.main.graph_manager.update_graph()

    def sigmoid_4pl(self, x, bottom, top, hill_slope, log_ec50):
        """4パラメータロジスティック（4PL）モデルの関数。xとlog_ec50はlog10スケール。"""
        # 関数内部のlog10(ec50)をなくし、直接log_ec50を使用
        return bottom + (top - bottom) / (1 + 10**((log_ec50 - x) * hill_slope))

    def perform_fitting(self):
        """非線形回帰分析を実行する。"""
        if not hasattr(self.main, 'model'): return
        df = self.main.model._data
        dialog = FittingDialog(df.columns, self.main)
        if dialog.exec():
            settings = dialog.get_settings()
            x_col, y_col = settings['x_col'], settings['y_col']
            if not x_col or not y_col: return
            try:
                fit_df = df[[x_col, y_col]].dropna().copy()
                if (fit_df[x_col] <= 0).any():
                    QMessageBox.warning(self.main, "Warning", "X-axis column for fitting contains non-positive values.")
                    return
                
                fit_df['log_x'] = np.log10(fit_df[x_col])
                x_data, y_data = fit_df['log_x'], fit_df[y_col]

                # 初期推測値のEC50をlogスケールに変更
                p0 = [y_data.min(), y_data.max(), 1.0, np.log10(np.median(fit_df[x_col]))]
                
                params, _ = curve_fit(self.sigmoid_4pl, x_data, y_data, p0=p0, maxfev=10000)
                
                # パラメータをアンパックし、log_ec50を線形スケールに戻す
                bottom, top, hill_slope, log_ec50 = params
                ec50 = 10**log_ec50
                
                y_pred = self.sigmoid_4pl(x_data, *params)
                r_squared = 1 - (np.sum((y_data - y_pred) ** 2) / np.sum((y_data - np.mean(y_data)) ** 2))

                self.main.fit_params = {"params": params, "r_squared": r_squared, "x_col": x_col, "y_col": y_col, "log_x_data": x_data}
                self.main.regression_line_params = None
                self.main.graph_manager.update_graph()

                # 結果表示では線形スケールのec50を使用
                result_text = "Non-linear Regression Results (Sigmoidal 4PL)\n"
                result_text += "==============================================\n\n"
                result_text += f"Top: {top:.4f}\n"
                result_text += f"Bottom: {bottom:.4f}\n"
                result_text += f"Hill Slope: {hill_slope:.4f}\n"
                result_text += f"EC50: {ec50:.4f}\n\n"
                result_text += f"R-squared: {r_squared:.4f}\n"
                self.show_results_dialog("Fitting Result", result_text)

            except Exception as e:
                QMessageBox.critical(self.main, "Error", f"Failed to perform fitting: {e}")
    
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