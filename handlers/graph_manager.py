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
            self.clear_canvas()
            return

        df = self.main.model._data.copy()
        properties = self.main.properties_panel.get_properties()
        data_settings = self.main.properties_panel.data_tab.get_current_settings()

        fig = None
        if self.main.current_graph_type == 'paired_scatter':
            fig = self.draw_paired_scatter(df, properties, data_settings)
        # ★★★ ここから追加 ★★★
        elif self.main.current_graph_type == 'histogram':
            fig = self.draw_histogram(df, properties, data_settings)
        # ★★★ ここまで ★★★
        else:
            fig = self.draw_categorical_plot(df, properties, data_settings)

        if fig:
            self.replace_canvas(fig)
            self.update_graph_properties(fig, properties)

    def draw_categorical_plot(self, df, properties, data_settings):
        current_x = data_settings.get('x_col')
        current_y = data_settings.get('y_col')
        
        if not current_x or not current_y:
            self.clear_canvas()
            return
        
        subgroup_col = data_settings.get('subgroup_col')
        facet_col = data_settings.get('facet_col')
        facet_row = data_settings.get('facet_row')

        if not subgroup_col: subgroup_col = None
        if not facet_col: facet_col = None
        if not facet_row: facet_row = None
        
        if subgroup_col and subgroup_col in df.columns:
            df[subgroup_col] = df[subgroup_col].astype(str)

        plot_kind = 'strip' if self.main.current_graph_type == 'scatter' else 'bar'
        
        plot_kwargs = {}
        if plot_kind == 'bar':
            plot_kwargs['edgecolor'] = properties.get('bar_edgecolor', 'black')
            plot_kwargs['linewidth'] = properties.get('bar_edgewidth', 1.0)
            plot_kwargs['capsize'] = properties.get('capsize', 4) * 0.01
            plot_kwargs['err_kws'] = {'linewidth': properties.get('bar_edgewidth', 1.0)}
        elif plot_kind == 'strip':
            plot_kwargs['marker'] = properties.get('marker_style', 'o')
            plot_kwargs['edgecolor'] = properties.get('marker_edgecolor', 'black')
            plot_kwargs['linewidth'] = properties.get('marker_edgewidth', 1.0)
        
        ui_subgroup_col = data_settings.get('subgroup_col')
        if subgroup_col:
            if subgroup_col == ui_subgroup_col:
                plot_kwargs['palette'] = {str(k): v for k, v in properties.get('subgroup_colors', {}).items()}
        else:
            plot_kwargs['color'] = properties.get('single_color')

        try:
            # ★★★【修正】sharey=True を追加 ★★★
            g = sns.catplot(
                data=df, x=current_x, y=current_y, hue=subgroup_col,
                col=facet_col, row=facet_row, kind=plot_kind,
                height=4, aspect=1.2, sharex=False, sharey=True, # <--- 修正箇所
                **plot_kwargs
            )

            self.apply_annotations(g, df, current_y, current_x, subgroup_col)
            self.replace_canvas(g.fig)
            self.update_graph_properties(g.fig, properties)

        except Exception as e:
            print(f"Graph drawing error: {e}")
            traceback.print_exc()
    
    def apply_annotations(self, g, df, current_y, current_x, subgroup_col):
        """グラフに統計アノテーションを適用する"""
        
        data_settings = self.main.properties_panel.data_tab.get_current_settings()
        facet_col = data_settings.get('facet_col')

        print(f"【GraphManager】Applying annotations. Graph: Y={current_y}, X={current_x}, Hue={subgroup_col}, Facet={facet_col}")
        
        current_annotations = [
            ann for ann in self.main.statistical_annotations 
            if ann.get('value_col') == current_y and 
               ann.get('group_col') == current_x and
               ann.get('hue_col') == subgroup_col and
               ann.get('facet_col') == (facet_col if facet_col and facet_col in df.columns else None)
        ]
        
        if not current_annotations:
            return

        try:
            # --- ★★★【修正】seabornのFacetGridから直接サブプロットの情報を取得 ★★★
            # g.facet_dataは (インデックス, データ) のタプルのリスト
            for i, (ax_index, subset_df) in enumerate(g.facet_data()):
                ax_facet = g.axes.flat[i] # 対応するAxesオブジェクトを取得
                
                # ファセットのカテゴリ値を取得
                facet_value = None
                if facet_col and g.col_names:
                    facet_value = g.col_names[i % len(g.col_names)]

                annotations_for_this_facet = [
                    ann for ann in current_annotations
                    if ann.get('facet_value') == facet_value
                ]

                if not annotations_for_this_facet:
                    continue

                box_pairs = [ann['box_pair'] for ann in annotations_for_this_facet]
                p_values = [ann['p_value'] for ann in annotations_for_this_facet]

                if not box_pairs:
                    continue
                
                # subset_dfのX軸列を文字列に変換しておく
                subset_df[current_x] = subset_df[current_x].astype(str)

                print(f"【GraphManager】Annotating Facet '{facet_value}': pairs={box_pairs}")
                
                annotator = Annotator(ax_facet, box_pairs, data=subset_df, x=current_x, y=current_y, hue=subgroup_col)
                pvalue_thresholds = [[1e-4, "****"], [1e-3, "***"], [1e-2, "**"], [0.05, "*"], [1.0, "n.s."]]
                annotator.configure(text_format='star', loc='inside', verbose=0, pvalue_thresholds=pvalue_thresholds)
                annotator.set_pvalues(p_values)
                annotator.annotate()

        except Exception as e:
            print(f"Annotation Error during plotting: {e}")
            traceback.print_exc()


    def replace_canvas(self, new_fig):
        if hasattr(self.main.graph_widget, 'canvas') and self.main.graph_widget.canvas:
            self.main.graph_widget.canvas.setParent(None)
            self.main.graph_widget.canvas.deleteLater()
        
        new_canvas = new_fig.canvas
        self.main.graph_widget.layout().addWidget(new_canvas)
        self.main.graph_widget.canvas = new_canvas
        self.main.graph_widget.fig = new_fig
        if hasattr(self.main.graph_widget.fig, 'axes') and self.main.graph_widget.fig.axes:
             self.main.graph_widget.ax = self.main.graph_widget.fig.axes[0]

    def update_graph_properties(self, fig, properties):
        fig.suptitle(properties.get('title', ''), fontsize=properties.get('title_fontsize', 16))
        for ax in fig.axes:
            ax.tick_params(axis='both', which='major', labelsize=properties.get('ticks_fontsize', 10))
            if ax.get_xlabel(): ax.xaxis.label.set_fontsize(properties.get('xlabel_fontsize', 12))
            if ax.get_ylabel(): ax.yaxis.label.set_fontsize(properties.get('ylabel_fontsize', 12))
            if properties.get('hide_top_right_spines', True):
                ax.spines['right'].set_visible(False); ax.spines['top'].set_visible(False)
            ax.grid(properties.get('show_grid', False))
            if properties.get('x_log_scale'): ax.set_xscale('log')
            if properties.get('y_log_scale'): ax.set_yscale('log')
        fig.tight_layout(rect=[0, 0, 1, 0.96])

    def draw_paired_scatter(self, df, properties, data_settings):
        col1 = data_settings.get('col1')
        col2 = data_settings.get('col2')
        if not (col1 and col2 and col1 != col2):
            return None

        # 新しいFigureとAxesをここで作成する
        fig = Figure(tight_layout=True)
        FigureCanvas(fig)
        ax = fig.add_subplot(111)

        try:
            # 描画ロジック自体は _draw_paired_plot_seaborn を流用
            self._draw_paired_plot_seaborn(ax, df, col1, col2, properties)
            return fig # ★ 完成したFigureオブジェクトを返す

        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to draw paired plot: {e}")
            return None # ★ エラー時はNoneを返す
        
    def clear_canvas(self):
        if hasattr(self.main.graph_widget, 'canvas') and self.main.graph_widget.canvas:
            self.main.graph_widget.canvas.figure.clear()
            self.main.graph_widget.canvas.draw()

    def save_graph(self):
        if not hasattr(self.main.graph_widget, 'fig'):
            QMessageBox.warning(self.main, "Warning", "No graph to save.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(self.main, "Save Graph", "", "PNG (*.png);;JPEG (*.jpg);;SVG (*.svg);;PDF (*.pdf)")
        if file_path:
            try:
                self.main.graph_widget.fig.savefig(file_path, dpi=300)
                QMessageBox.information(self.main, "Success", f"Graph successfully saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self.main, "Error", f"Failed to save graph: {e}")

    def clear_annotations(self):
        if hasattr(self.main, 'statistical_annotations'):
            self.main.statistical_annotations.clear()
        
        if hasattr(self.main, 'regression_line_params'):
            self.main.regression_line_params = None
        if hasattr(self.main, 'fit_params'):
            self.main.fit_params = None

        self.update_graph()

    def _draw_paired_plot_seaborn(self, ax, df, col1, col2, properties):
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

            ax.set_xticks([0, 1]) # X軸の目盛りの位置を明示的に指定
            ax.set_xticklabels([label1, label2]) # それからラベルを設定
            
            # 凡例が空でない場合のみ表示するように修正
            handles, labels = ax.get_legend_handles_labels()
            if handles:
                ax.legend(handles, labels)

        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to draw paired plot: {e}")
            
    def draw_histogram(self, df, properties, data_settings):
        value_col = data_settings.get('y_col') # TidyDataTabのY軸をValueとして使う
        if not value_col:
            return None

        hue_col = data_settings.get('subgroup_col')
        if not hue_col:
            hue_col = None

        if hue_col and hue_col in df.columns:
            df[hue_col] = df[hue_col].astype(str)

        fig = Figure(tight_layout=True)
        FigureCanvas(fig)
        ax = fig.add_subplot(111)

        plot_kwargs = {}
        if hue_col:
             plot_kwargs['palette'] = {str(k): v for k, v in properties.get('subgroup_colors', {}).items()}
        else:
            plot_kwargs['color'] = properties.get('single_color')

        try:
            sns.histplot(data=df, x=value_col, hue=hue_col, ax=ax, **plot_kwargs)
            return fig
        except Exception as e:
            print(f"Graph drawing error: {e}")
            traceback.print_exc()
            return None