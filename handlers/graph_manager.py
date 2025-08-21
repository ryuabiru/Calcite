# handlers/graph_manager.py

import numpy as np
import pandas as pd
from PySide6.QtWidgets import QFileDialog, QMessageBox
import seaborn as sns
from statannotations.Annotator import Annotator

class GraphManager:
    """
    グラフの描画と更新に関する全てのロジックを担当するクラス。
    """
    def __init__(self, main_window):
        self.main = main_window

    def update_graph(self):
        """
        現在の設定に基づいてグラフ全体を再描画する。
        """
        if not hasattr(self.main, 'model') or self.main.model is None:
            return

        df = self.main.model._data
        ax = self.main.graph_widget.ax
        ax.clear()
        
        properties = self.main.properties_panel.get_properties()
        data_settings = self.main.properties_panel.data_tab.get_current_settings()
        
        plot_params = {}
        current_x = data_settings.get('x_col')
        current_y = data_settings.get('y_col')
        
        if self.main.current_graph_type == 'scatter':
            if not current_y or not current_x:
                self.main.graph_widget.canvas.draw()
                return
            self._draw_scatter_plot(ax, df, current_x, current_y, 
                                    properties.get('marker_style', 'o'), 
                                    properties.get('single_color'), 
                                    properties)

        elif self.main.current_graph_type == 'bar':
            if not current_y or not current_x:
                self.main.graph_widget.canvas.draw()
                return
            
            subgroup_col = data_settings.get('subgroup_col')
            
            # ★★★ ここから修正 ★★★
            # サブグループの色設定（palette）のキーを文字列に変換する
            palette = None
            if subgroup_col:
                subgroup_colors = self.main.properties_panel.format_tab.subgroup_colors
                # キーを文字列に変換した新しい辞書を作成
                palette = {str(k): v for k, v in subgroup_colors.items()}
            # ★★★ ここまで修正 ★★★

            sns.barplot(
                x=current_x, y=current_y, data=df, ax=ax,
                hue=subgroup_col if subgroup_col else None,
                palette=palette, # 修正したpaletteを使用
                color=properties.get('single_color', '#1f77b4') if not subgroup_col else None,
                capsize=properties.get('capsize', 4) * 0.01,
                errwidth=properties.get('bar_edgewidth', 1.0),
                edgecolor=properties.get('bar_edgecolor', 'black'),
                linewidth=properties.get('bar_edgewidth', 1.0)
            )
            plot_params = {'x': current_x, 'y': current_y, 'hue': subgroup_col, 'data': df}

        elif self.main.current_graph_type == 'paired_scatter':
            col1 = data_settings.get('col1')
            col2 = data_settings.get('col2')
            if col1 and col2 and col1 != col2:
                self._draw_paired_plot(ax, df, col1, col2, properties)
            plot_params = None

        if plot_params and self.main.statistical_annotations:
            box_pairs = [
                ann['box_pair'] for ann in self.main.statistical_annotations
                if ann.get('value_col') == current_y and ann.get('group_col') == current_x
            ]
            
            if box_pairs:
                try:
                    annotator = Annotator(ax, box_pairs, **plot_params)
                    annotator.configure(test=None, text_format='star', loc='inside', verbose=0)
                    annotator.apply_and_annotate()
                except Exception as e:
                    print(f"Statannotations error: {e}")

        self.update_graph_properties()
        self.main.graph_widget.fig.tight_layout()
        self.main.graph_widget.canvas.draw()

    def update_graph_properties(self):
        """プロパティパネルから現在の全設定を取得し、グラフに適用する。"""
        if not hasattr(self.main, 'graph_widget'): return
        properties = self.main.properties_panel.get_properties()
        ax = self.main.graph_widget.ax
        
        data_settings = self.main.properties_panel.data_tab.get_current_settings()
        
        ax.set_title(properties.get('title', ''), fontsize=properties.get('title_fontsize', 16))
        ax.set_xlabel(properties.get('xlabel') or data_settings.get('x_col', ''))
        ax.set_ylabel(properties.get('ylabel') or data_settings.get('y_col', ''))

        ax.tick_params(axis='both', which='major', labelsize=properties.get('ticks_fontsize', 10))

        try:
            ymin = float(properties['ymin']) if properties['ymin'] else None
            ymax = float(properties['ymax']) if properties['ymax'] else None
            if ymin is not None and ymax is not None: ax.set_ylim(ymin, ymax)
        except (ValueError, TypeError): pass
        
        if self.main.current_graph_type not in ['bar', 'paired_scatter']:
            try:
                xmin = float(properties['xmin']) if properties['xmin'] else None
                xmax = float(properties['xmax']) if properties['xmax'] else None
                if xmin is not None and xmax is not None: ax.set_xlim(xmin, xmax)
            except (ValueError, TypeError): pass
        
        ax.grid(properties.get('show_grid', False))
        ax.set_xscale('log' if properties.get('x_log_scale') else 'linear')
        ax.set_yscale('log' if properties.get('y_log_scale') else 'linear')
        
        if properties.get('hide_top_right_spines', True):
            ax.spines['right'].set_visible(False); ax.spines['top'].set_visible(False)
        else:
            ax.spines['right'].set_visible(True); ax.spines['top'].set_visible(True)

        if ax.get_legend(): ax.legend()

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

    def _draw_scatter_plot(self, ax, df, x_col, y_col, marker_style, color, properties):
        color_to_plot = color if color else '#1f77b4'
        edgecolor = properties.get('marker_edgecolor', 'black')
        linewidth = properties.get('marker_edgewidth', 1.0)
        if pd.api.types.is_numeric_dtype(df[y_col]) and pd.api.types.is_numeric_dtype(df[x_col]):
            ax.scatter(df[x_col], df[y_col], marker=marker_style, color=color_to_plot, edgecolors=edgecolor, linewidths=linewidth)

    def _draw_paired_plot(self, ax, df, col1, col2, properties):
        try:
            plot_df = df[[col1, col2]].dropna().copy()
            if plot_df.empty: return None, None

            label1 = properties.get('paired_label1') or col1
            label2 = properties.get('paired_label2') or col2
            categories = [label1, label2]
            x_indices = [0, 1]

            marker_style = properties.get('marker_style', 'o')
            marker_edgecolor = properties.get('marker_edgecolor', 'black')
            marker_edgewidth = properties.get('marker_edgewidth', 1.0)
            
            mean_linestyle = properties.get('linestyle', '--')
            mean_linewidth = properties.get('linewidth', 2)

            for index, row in plot_df.iterrows():
                ax.plot(x_indices, [row[col1], row[col2]], color='gray', marker=marker_style, linestyle='-', alpha=0.5, markeredgecolor=marker_edgecolor, markeredgewidth=marker_edgewidth)

            mean1 = plot_df[col1].mean()
            mean2 = plot_df[col2].mean()
            ax.plot(x_indices, [mean1, mean2], color='red', marker=marker_style, linestyle=mean_linestyle, linewidth=mean_linewidth, label="Mean", markeredgecolor=marker_edgecolor, markeredgewidth=marker_edgewidth)
            ax.legend()
            
            return categories, x_indices
        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to draw paired plot: {e}")
            return None, None