# graph_manager.py

import numpy as np
import pandas as pd
from PySide6.QtWidgets import QFileDialog, QMessageBox

class GraphManager:
    """
    グラフの描画と更新に関する全てのロジックを担当するクラス。
    """
    def __init__(self, main_window):
        """
        GraphManagerを初期化します。

        Args:
            main_window (MainWindow): メインウィンドウのインスタンス。
        """
        self.main = main_window

    def update_graph(self):
        """
        現在の設定に基づいてグラフ全体を再描画する。
        """
        if not hasattr(self.main, 'model'):
            return

        df = self.main.model._data
        ax = self.main.graph_widget.ax
        ax.clear()
        
        properties = self.main.properties_panel.get_properties()
        
        bar_categories, bar_x_indices = None, None
            
        if self.main.current_graph_type == 'scatter':
            y_col = self.main.properties_panel.y_axis_combo.currentText()
            x_col = self.main.properties_panel.x_axis_combo.currentText()
            if not y_col or not x_col:
                self.main.graph_widget.canvas.draw()
                return
                
            marker_style = properties.get('marker_style', 'o')
            single_color = self.main.properties_panel.current_color
            self._draw_scatter_plot(ax, df, x_col, y_col, marker_style, single_color, properties)

        elif self.main.current_graph_type == 'bar':
            y_col = self.main.properties_panel.y_axis_combo.currentText()
            x_col = self.main.properties_panel.x_axis_combo.currentText()
            if not y_col or not x_col:
                self.main.graph_widget.canvas.draw()
                return

            subgroup_col = self.main.properties_panel.subgroup_combo.currentText()
            single_color = self.main.properties_panel.current_color
            subgroup_colors_map = self.main.properties_panel.subgroup_colors
            show_scatter = self.main.properties_panel.scatter_overlay_check.isChecked()
            
            self.main.fit_params = None 
            self.main.regression_line_params = None
            bar_categories, bar_x_indices = self._draw_bar_chart(ax, df, x_col, y_col, subgroup_col, single_color, subgroup_colors_map, show_scatter, properties)

        elif self.main.current_graph_type == 'paired_scatter':
            self.main.fit_params = None
            self.main.regression_line_params = None
            if hasattr(self.main, 'paired_plot_cols'):
                col1 = self.main.paired_plot_cols['col1']
                col2 = self.main.paired_plot_cols['col2']
                self._draw_paired_plot(ax, df, col1, col2, properties)

        # 回帰直線とフィッティング曲線
        linestyle = properties.get('linestyle', '-')
        linewidth = properties.get('linewidth', 1.5)
        if self.main.regression_line_params:
            params = self.main.regression_line_params
            ax.plot(params["x_line"], params["y_line"], color='red', label=f'R² = {params["r_squared"]:.4f}', linestyle=linestyle, linewidth=linewidth)
        
        current_x_col = self.main.properties_panel.x_axis_combo.currentText()
        current_y_col = self.main.properties_panel.y_axis_combo.currentText()
        if self.main.fit_params and self.main.fit_params['x_col'] == current_x_col and self.main.fit_params['y_col'] == current_y_col:
            x_data = self.main.fit_params['log_x_data']
            x_fit = np.linspace(x_data.min(), x_data.max(), 200)
            # sigmoid_4plはActionHandlerが持っているのでそこから呼び出す
            y_fit = self.main.action_handler.sigmoid_4pl(x_fit, *self.main.fit_params['params'])
            r_squared = self.main.fit_params['r_squared']
            ax.plot(10**x_fit, y_fit, color='blue', label=f'4PL Fit (R²={r_squared:.3f})', linestyle=linestyle, linewidth=linewidth)

        self._draw_annotations()
        self.update_graph_properties()

        if self.main.current_graph_type == 'bar' and bar_categories is not None:
            ax.set_xticks(bar_x_indices)
            ax.set_xticklabels(bar_categories, rotation=0)

        self.main.graph_widget.fig.tight_layout()
        self.main.graph_widget.canvas.draw()

    def update_graph_properties(self):
        """プロパティパネルから現在の全設定を取得し、グラフに適用する。"""
        properties = self.main.properties_panel.get_properties()
        ax = self.main.graph_widget.ax
        
        ax.set_title(properties.get('title', ''), fontsize=properties.get('title_fontsize', 16))
        ax.set_xlabel(properties.get('xlabel', ''), fontsize=properties.get('xlabel_fontsize', 12))
        ax.set_ylabel(properties.get('ylabel', ''), fontsize=properties.get('ylabel_fontsize', 12))
        ax.tick_params(axis='both', which='major', labelsize=properties.get('ticks_fontsize', 10))

        # Y軸の範囲
        try:
            ymin = float(properties['ymin']) if properties['ymin'] else None
            ymax = float(properties['ymax']) if properties['ymax'] else None
            ax.set_ylim(ymin, ymax)
        except (ValueError, TypeError):
            ax.autoscale(enable=True, axis='y')
        
        # X軸の範囲 (棒グラフなどを除く)
        if self.main.current_graph_type not in ['bar', 'paired_scatter']:
            try:
                xmin = float(properties['xmin']) if properties['xmin'] else None
                xmax = float(properties['xmax']) if properties['xmax'] else None
                ax.set_xlim(xmin, xmax)
            except (ValueError, TypeError):
                ax.autoscale(enable=True, axis='x')
        
        ax.grid(properties.get('show_grid', False))
        
        # スケール
        if self.main.current_graph_type in ['bar', 'paired_scatter']:
            ax.set_xscale('linear')
        elif self.main.fit_params and self.main.fit_params['x_col'] == self.main.properties_panel.x_axis_combo.currentText():
            ax.set_xscale('log')
        else:
            ax.set_xscale('log' if properties.get('x_log_scale') else 'linear')
        
        ax.set_yscale('log' if properties.get('y_log_scale') else 'linear')
        
        # 枠線
        if properties.get('hide_top_right_spines', True):
            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)
        else:
            ax.spines['right'].set_visible(True)
            ax.spines['top'].set_visible(True)

        if ax.get_legend_handles_labels()[1]:
            ax.legend()

        self.main.graph_widget.fig.tight_layout()
        self.main.graph_widget.canvas.draw()

    def save_graph(self):
        """現在のグラフを画像ファイルとして保存する。"""
        if not hasattr(self.main, 'model'):
            QMessageBox.warning(self.main, "Warning", "No data to save.")
            return
        file_path, _ = QFileDialog.getSaveFileName(self.main, "Save Graph", "", "PNG (*.png);;JPEG (*.jpg);;SVG (*.svg);;PDF (*.pdf)")
        if file_path:
            try:
                self.main.graph_widget.fig.savefig(file_path, dpi=300)
                QMessageBox.information(self.main, "Success", f"Graph successfully saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self.main, "Error", f"Failed to save graph: {e}")

    def clear_annotations(self):
        """グラフ上のすべてのアノテーションをクリアする。"""
        if hasattr(self.main, 'statistical_annotations'):
            self.main.statistical_annotations.clear()
            self.update_graph()

    # --- Private Drawing Helpers ---

    def _draw_scatter_plot(self, ax, df, x_col, y_col, marker_style, color, properties):
        color_to_plot = color if color else '#1f77b4'
        edgecolor = properties.get('marker_edgecolor', 'black')
        linewidth = properties.get('marker_edgewidth', 1.0)
        if pd.api.types.is_numeric_dtype(df[y_col]) and pd.api.types.is_numeric_dtype(df[x_col]):
            ax.scatter(df[x_col], df[y_col], marker=marker_style, color=color_to_plot, edgecolors=edgecolor, linewidths=linewidth)
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)

    def _draw_bar_chart(self, ax, df, x_col, y_col, subgroup_col, single_color, subgroup_colors_map, show_scatter, properties):
        try:
            categories = sorted(df[x_col].unique())
            x_indices = np.arange(len(categories))
            if subgroup_col:
                self._draw_grouped_bar_chart(ax, df, x_col, y_col, subgroup_col, categories, x_indices, subgroup_colors_map, show_scatter, properties)
            else:
                self._draw_simple_bar_chart(ax, df, x_col, y_col, categories, x_indices, single_color, show_scatter, properties)
            ax.set_xlabel(properties.get('xlabel') or x_col)
            ax.set_ylabel(properties.get('ylabel') or f"Mean of {y_col}")
            return categories, x_indices
        except Exception as e:
            print(f"Could not generate bar chart: {e}")
            return None, None

    def _draw_simple_bar_chart(self, ax, df, x_col, y_col, categories, x_indices, color, show_scatter, properties):
        summary = df.groupby(x_col)[y_col].agg(['mean', 'std']).reindex(categories)
        color_to_plot = color if color else '#1f77b4'
        capsize = properties.get('capsize', 4)
        edgecolor = properties.get('bar_edgecolor', 'black')
        linewidth = properties.get('bar_edgewidth', 1.0)
        ax.bar(x_indices, summary['mean'], width=0.8, yerr=summary['std'], capsize=capsize, color=color_to_plot, edgecolor=edgecolor, linewidth=linewidth)
        if show_scatter:
            for i, cat in enumerate(categories):
                points = df[df[x_col] == cat][y_col]
                jitter = np.random.uniform(-0.15, 0.15, len(points))
                ax.scatter(i + jitter, points, color='black', alpha=0.6, zorder=2)

    def _draw_grouped_bar_chart(self, ax, df, x_col, y_col, subgroup_col, categories, x_indices, subgroup_colors_map, show_scatter, properties):
        # ... (ロジックはmain_window.pyからそのまま移動) ...
        pass

    def _draw_paired_plot(self, ax, df, col1, col2, properties):
        # ... (ロジックはmain_window.pyからそのまま移動) ...
        pass
        
    def _draw_annotations(self):
        # ... (ロジックはmain_window.pyからそのまま移動) ...
        pass