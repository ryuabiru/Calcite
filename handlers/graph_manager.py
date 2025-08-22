# handlers/graph_manager.py

import numpy as np
import pandas as pd
from PySide6.QtWidgets import QFileDialog, QMessageBox
import seaborn as sns
from statannotations.Annotator import Annotator
import traceback
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

class GraphManager:
    def __init__(self, main_window):
        self.main = main_window

    def update_graph(self):
        if not hasattr(self.main, 'model') or self.main.model is None:
            return

        df = self.main.model._data.copy()
        
        # --- 描画設定の取得 ---
        properties = self.main.properties_panel.get_properties()
        data_settings = self.main.properties_panel.data_tab.get_current_settings()
        
        current_x = data_settings.get('x_col')
        current_y = data_settings.get('y_col')
        
        # 必須項目が選択されていなければ描画しない
        if not current_x or not current_y:
            # 念のためキャンバスをクリア
            if self.main.graph_widget.layout() is not None:
                 old_canvas = self.main.graph_widget.canvas
                 if old_canvas:
                     old_canvas.figure.clear()
                     old_canvas.draw()
            return
        
        subgroup_col = data_settings.get('subgroup_col')
        facet_col = data_settings.get('facet_col')
        facet_row = data_settings.get('facet_row')

        # 空文字列をNoneに変換
        if not subgroup_col: subgroup_col = None
        if not facet_col: facet_col = None
        if not facet_row: facet_row = None
        
        # --- グラフ描画 ---
        try:
            # seaborn.catplotでグラフオブジェクト(FacetGrid)を生成
            g = sns.catplot(
                data=df,
                x=current_x,
                y=current_y,
                hue=subgroup_col,
                col=facet_col,
                row=facet_row,
                kind=self.main.current_graph_type,
                height=4, 
                aspect=1.2,
                sharex=False, # ファセットごとにX軸を独立させる
                sharey=False  # ファセットごとにY軸を独立させる
            )

            # --- アノテーションの描画 ---
            current_annotations = [ann for ann in self.main.statistical_annotations if ann.get('value_col') == current_y and ann.get('group_col') == current_x]
            if current_annotations:
                box_pairs = [ann['box_pair'] for ann in current_annotations]
                p_values = [ann['p_value'] for ann in current_annotations]
                
                # catplotの各Axes(ax)にアノテーションを適用
                for ax in g.axes.flat:
                    annotator = Annotator(ax, box_pairs, data=df, x=current_x, y=current_y, hue=subgroup_col)
                    annotator.configure(text_format='star', loc='inside', verbose=0)
                    annotator.set_pvalues(p_values)
                    annotator.annotate()

            # --- 古いキャンバスを削除し、新しいキャンバスをUIに配置 ---
            if self.main.graph_widget.layout() is not None:
                old_canvas = self.main.graph_widget.canvas
                if old_canvas:
                    old_canvas.setParent(None)
                    old_canvas.deleteLater()

            new_canvas = g.fig.canvas
            self.main.graph_widget.layout().addWidget(new_canvas)
            self.main.graph_widget.canvas = new_canvas
            self.main.graph_widget.fig = g.fig

            # プロパティを適用
            self.update_graph_properties(g, properties)

        except Exception as e:
            print(f"Graph drawing error: {e}")
            traceback.print_exc()

    def update_graph_properties(self, g, properties):
        """catplotで生成されたグラフにプロパティを適用する"""
        
        # Figure全体に適用する設定
        g.fig.suptitle(properties.get('title', ''), fontsize=properties.get('title_fontsize', 16))
        
        # 各Axes(サブプロット)にプロパティを適用
        for ax in g.axes.flat:
            ax.tick_params(axis='both', which='major', labelsize=properties.get('ticks_fontsize', 10))
            
            # X/Y軸ラベルのフォントサイズ設定
            ax.xaxis.label.set_fontsize(properties.get('xlabel_fontsize', 12))
            ax.yaxis.label.set_fontsize(properties.get('ylabel_fontsize', 12))

            # 枠線の表示設定
            if properties.get('hide_top_right_spines', True):
                ax.spines['right'].set_visible(False)
                ax.spines['top'].set_visible(False)
            else:
                ax.spines['right'].set_visible(True)
                ax.spines['top'].set_visible(True)
            
            # グリッド
            ax.grid(properties.get('show_grid', False))
            
            # 対数スケール
            if properties.get('x_log_scale'): ax.set_xscale('log')
            if properties.get('y_log_scale'): ax.set_yscale('log')
        
        # レイアウト調整
        g.fig.tight_layout(rect=[0, 0, 1, 0.96]) # suptitleとの重なりを避ける

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
        if hasattr(self, 'statistical_annotations'):
            self.main.statistical_annotations.clear()
        self.main.regression_line_params = None
        self.main.fit_params = None
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