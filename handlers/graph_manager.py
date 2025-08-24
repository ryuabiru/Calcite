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
        elif self.main.current_graph_type == 'histogram':
            fig = self.draw_histogram(df, properties, data_settings)
        else:
            fig = self.draw_categorical_plot(df, properties, data_settings)

        if fig:
            self.replace_canvas(fig)
            self.update_graph_properties(fig, properties)

    def apply_annotations(self, g, df, current_y, current_x, subgroup_col):
        data_settings = self.main.properties_panel.data_tab.get_current_settings()
        facet_col = data_settings.get('facet_col')
        
        current_annotations = [
            ann for ann in self.main.statistical_annotations 
            if ann.get('value_col') == current_y and 
               ann.get('group_col') == current_x and
               ann.get('hue_col') == subgroup_col and
               ann.get('facet_col') == (facet_col if facet_col and facet_col in df.columns else None)
        ]
        
        if not current_annotations: return
        try:
            for i, (ax_index, subset_df) in enumerate(g.facet_data()):
                ax_facet = g.axes.flat[i]
                facet_value = None
                if facet_col and g.col_names:
                    col_index = i % len(g.col_names)
                    facet_value = g.col_names[col_index]
                annotations_for_this_facet = [ann for ann in current_annotations if ann.get('facet_value') == facet_value]
                if not annotations_for_this_facet: continue
                box_pairs = [ann['box_pair'] for ann in annotations_for_this_facet]
                p_values = [ann['p_value'] for ann in annotations_for_this_facet]
                if not box_pairs: continue
                subset_df[current_x] = subset_df[current_x].astype(str)
                annotator = Annotator(ax_facet, box_pairs, data=subset_df, x=current_x, y=current_y, hue=subgroup_col, hue_order=g.hue_names)
                pvalue_thresholds = [[1e-4, "****"], [1e-3, "***"], [1e-2, "**"], [0.05, "*"], [1.0, "n.s."]]
                annotator.configure(text_format='star', loc='inside', verbose=0, pvalue_thresholds=pvalue_thresholds)
                annotator.set_pvalues(p_values)
                annotator.annotate()
        except Exception as e:
            print(f"Annotation Error during plotting: {e}")
            traceback.print_exc()

    def draw_categorical_plot(self, df, properties, data_settings):
        current_x = data_settings.get('x_col')
        current_y = data_settings.get('y_col')
        if not current_x or not current_y:
            self.clear_canvas()
            return None

        visual_hue_col = data_settings.get('subgroup_col')
        if not visual_hue_col: visual_hue_col = None

        analysis_hue_col = visual_hue_col
        if current_x == analysis_hue_col: analysis_hue_col = None
        
        facet_col = data_settings.get('facet_col')
        facet_row = data_settings.get('facet_row')
        if not facet_col: facet_col = None
        if not facet_row: facet_row = None
        
        if visual_hue_col and visual_hue_col in df.columns:
            df[visual_hue_col] = df[visual_hue_col].astype(str)

        base_kind = self.main.current_graph_type
        if base_kind not in ['bar', 'boxplot', 'violinplot', 'scatter']:
            base_kind = 'scatter'

        try:
            g = sns.catplot(
                data=df, x=current_x, y=current_y, hue=visual_hue_col,
                col=facet_col, row=facet_row,
                height=4, aspect=1.2, sharex=False, sharey=True,
                kind='strip', alpha=0.0, legend=False
            )

            for ax in g.axes.flat:
                original_title = ax.get_title()
                ax.clear()
                ax.set_title(original_title)

                if base_kind != 'scatter':
                    plot_func_map = {'bar': sns.barplot, 'boxplot': sns.boxplot, 'violinplot': sns.violinplot}
                    plot_func = plot_func_map[base_kind]
                    base_kwargs = {
                        'data': df, 'x': current_x, 'y': current_y, 'hue': visual_hue_col, 'ax': ax,
                        'palette': {str(k): v for k, v in properties.get('subgroup_colors', {}).items()} if visual_hue_col else None,
                        'color': properties.get('single_color') if not visual_hue_col else None
                    }
                    if base_kind == 'boxplot':
                        base_kwargs['showfliers'] = False
                    elif base_kind == 'bar':
                        base_kwargs['edgecolor'] = properties.get('bar_edgecolor', 'black')
                        base_kwargs['linewidth'] = properties.get('bar_edgewidth', 1.0)
                        base_kwargs['capsize'] = properties.get('capsize', 4) * 0.01
                    plot_func(**base_kwargs)

                if base_kind == 'scatter' or properties.get('scatter_overlay', False):
                    stripplot_kwargs = {
                        'data': df, 'x': current_x, 'y': current_y, 'ax': ax,
                        'marker': properties.get('marker_style', 'o'),
                        'edgecolor': 'gray', 'linewidth': 0.5
                    }
                    if base_kind == 'scatter':
                        stripplot_kwargs['hue'] = visual_hue_col
                        stripplot_kwargs['dodge'] = True
                        stripplot_kwargs['alpha'] = 1.0
                        stripplot_kwargs['palette'] = {str(k): v for k, v in properties.get('subgroup_colors', {}).items()} if visual_hue_col else None
                        stripplot_kwargs['color'] = properties.get('single_color') if not visual_hue_col else None
                    else:
                        stripplot_kwargs['hue'] = None
                        stripplot_kwargs['dodge'] = False
                        stripplot_kwargs['alpha'] = 0.6
                        stripplot_kwargs['color'] = 'black'
                        stripplot_kwargs['jitter'] = 0.2
                    sns.stripplot(**stripplot_kwargs)

            # --- 3. 凡例の処理 (リセットされた状態) ---
            if visual_hue_col:
                handles, labels = g.axes.flat[0].get_legend_handles_labels()
                if handles:
                    num_hues = len(df[visual_hue_col].unique())
                    g.add_legend(handles=handles[:num_hues], labels=labels[:num_hues], title=visual_hue_col)
            
            # --- ▼▼▼ ここからが今回の修正の核心部です ▼▼▼ ---
            # --- 4. ファセット使用時にX軸ラベルを共有する ---
            if facet_col or facet_row:
                # ユーザーがテキストタブで設定したX軸ラベル名を取得、なければカラム名を使う
                shared_xlabel = properties.get('xlabel') or current_x
                
                # 全てのサブプロットから個別のX軸ラベルを削除
                for ax in g.axes.flat:
                    ax.set_xlabel('')
                    
                # Figure全体の中央に1つのX軸ラベルを追加
                g.fig.supxlabel(shared_xlabel, y=0.02, fontsize=properties.get('xlabel_fontsize', 12))
            # --- ▲▲▲ 修正はここまで ▲▲▲ ---

            # --- 5. ファセットの区切り線を調整 ---
            if facet_col:
                # FacetGridのAxesは2次元配列で管理されている
                for i, ax_row in enumerate(g.axes):
                    for j, ax in enumerate(ax_row):
                        # 2列目以降のグラフに対してのみ処理を実行
                        if j > 0:
                            # Y軸の描画範囲を取得
                            bottom, top = ax.get_ylim()
                            # 下に延長する長さを、Y軸全体の高さの2%に設定
                            extension = (top - bottom) * 0.1
                            
                            # 左の枠線(spine)の描画範囲を、下に延長するように再設定
                            ax.spines['left'].set_bounds(bottom - extension, top)

            # --- 5. アノテーションを適用 ---
            self.apply_annotations(g, df, current_y, current_x, analysis_hue_col)
            return g.fig

        except Exception as e:
            print(f"Graph drawing error: {e}")
            traceback.print_exc()
            return None

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
        if not (col1 and col2 and col1 != col2): return None
        fig = Figure(tight_layout=True)
        FigureCanvas(fig)
        ax = fig.add_subplot(111)
        try:
            self._draw_paired_plot_seaborn(ax, df, col1, col2, properties)
            return fig
        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to draw paired plot: {e}")
            return None
        
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
        if hasattr(self, 'statistical_annotations'): self.main.statistical_annotations.clear()
        if hasattr(self, 'regression_line_params'): self.main.regression_line_params = None
        if hasattr(self, 'fit_params'): self.main.fit_params = None
        self.update_graph()

    def _draw_paired_plot_seaborn(self, ax, df, col1, col2, properties):
        try:
            plot_df = df[[col1, col2]].dropna().copy()
            if plot_df.empty: return
            plot_df['ID'] = range(len(plot_df))
            plot_df_long = pd.melt(plot_df, id_vars='ID', value_vars=[col1, col2], var_name='Condition', value_name='Value')
            label1 = properties.get('paired_label1') or col1
            label2 = properties.get('paired_label2') or col2
            sns.lineplot(data=plot_df_long, x='Condition', y='Value', units='ID', estimator=None, color='gray', alpha=0.5, ax=ax)
            sns.scatterplot(data=plot_df_long, x='Condition', y='Value', color=properties.get('single_color', 'black'), marker=properties.get('marker_style', 'o'), edgecolor=properties.get('marker_edgecolor', 'black'), linewidth=properties.get('marker_edgewidth', 1.0), ax=ax, legend=False)
            mean_df = plot_df_long.groupby('Condition')['Value'].mean().reindex([col1, col2])
            ax.plot(mean_df.index, mean_df.values, color='red', marker='_', markersize=20, mew=2.5, linestyle='None', label='Mean')
            ax.set_xticks([0, 1])
            ax.set_xticklabels([label1, label2])
            handles, labels = ax.get_legend_handles_labels()
            if handles: ax.legend(handles, labels)
        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to draw paired plot: {e}")
            
    def draw_histogram(self, df, properties, data_settings):
        value_col = data_settings.get('y_col')
        if not value_col: return None
        hue_col = data_settings.get('subgroup_col')
        if not hue_col: hue_col = None
        if hue_col and hue_col in df.columns: df[hue_col] = df[hue_col].astype(str)
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