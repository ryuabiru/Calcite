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

        df = self.main.model._data.copy() # ★★★ 変更：dfをコピーして使用
        ax = self.main.graph_widget.ax
        ax.clear()
        
        properties = self.main.properties_panel.get_properties()
        data_settings = self.main.properties_panel.data_tab.get_current_settings()
        
        plot_params = {}
        current_x = data_settings.get('x_col')
        current_y = data_settings.get('y_col')
        subgroup_col = data_settings.get('subgroup_col')
        
        # サブグループ列が存在する場合、データ型を文字列に変換
        if subgroup_col and subgroup_col in df.columns:
            df[subgroup_col] = df[subgroup_col].astype(str)

        if self.main.current_graph_type == 'scatter':
            if not current_y or not current_x:
                self.main.graph_widget.canvas.draw()
                return
            
            sns.scatterplot(
                data=df, x=current_x, y=current_y, ax=ax,
                hue=subgroup_col if subgroup_col else None,
                palette=self.main.properties_panel.format_tab.subgroup_colors if subgroup_col else None,
                color=properties.get('single_color') if not subgroup_col else None,
                marker=properties.get('marker_style', 'o'),
                edgecolor=properties.get('marker_edgecolor', 'black'),
                linewidth=properties.get('marker_edgewidth', 1.0)
            )

        elif self.main.current_graph_type == 'bar':
            if not current_y or not current_x:
                self.main.graph_widget.canvas.draw()
                return
            
            palette = None
            if subgroup_col:
                palette = {str(k): v for k, v in self.main.properties_panel.format_tab.subgroup_colors.items()}

            sns.barplot(
                data=df, x=current_x, y=current_y, ax=ax,
                hue=subgroup_col if subgroup_col else None,
                palette=palette,
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
                self._draw_paired_plot_seaborn(ax, df, col1, col2, properties)
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
        
        xlabel = properties.get('xlabel') or (data_settings.get('x_col') if data_settings else '')
        ylabel = properties.get('ylabel') or (data_settings.get('y_col') if data_settings else '')
        ax.set_xlabel(xlabel, fontsize=properties.get('xlabel_fontsize', 12))
        ax.set_ylabel(ylabel, fontsize=properties.get('ylabel_fontsize', 12))

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

    def _draw_paired_plot_seaborn(self, ax, df, col1, col2, properties):
        """ペアデータの散布図を Seaborn を使って描画する。"""
        try:
            plot_df = df[[col1, col2]].dropna().copy()
            if plot_df.empty: return

            plot_df['ID'] = range(len(plot_df))
            plot_df_long = pd.melt(plot_df, id_vars='ID', value_vars=[col1, col2], var_name='Condition', value_name='Value')

            label1 = properties.get('paired_label1') or col1
            label2 = properties.get('paired_label2') or col2
            
            sns.lineplot(data=plot_df_long, x='Condition', y='Value', units='ID',
                         estimator=None, color='gray', alpha=0.5, ax=ax)
            sns.scatterplot(data=plot_df_long, x='Condition', y='Value',
                            color=properties.get('single_color', 'black'), 
                            marker=properties.get('marker_style', 'o'),
                            edgecolor=properties.get('marker_edgecolor', 'black'),
                            linewidth=properties.get('marker_edgewidth', 1.0),
                            ax=ax, legend=False)
            
            mean_df = plot_df_long.groupby('Condition')['Value'].mean().reindex([col1, col2])
            ax.plot(mean_df.index, mean_df.values,
                    color='red', marker='_', markersize=20, mew=2.5, linestyle='None', label='Mean')

            ax.set_xticklabels([label1, label2])
            ax.set_xlim(-0.5, 1.5)
            ax.legend()

        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to draw paired plot: {e}")