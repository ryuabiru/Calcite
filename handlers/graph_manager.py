# handlers/graph_manager.py

import numpy as np
import pandas as pd
from PySide6.QtWidgets import QFileDialog, QMessageBox
import seaborn as sns
from statannotations.Annotator import Annotator
import traceback
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

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

    # ▼▼▼ 消えていたこの関数を元に戻します ▼▼▼
    def apply_annotations(self, ax, df, data_settings, hue_order, annotations_to_plot):
        """
        指定されたax（サブプロット）に、指定されたアノテーションリストを描画する。
        """
        if not annotations_to_plot:
            return

        try:
            current_y = data_settings.get('y_col')
            current_x = data_settings.get('x_col')
            subgroup_col = data_settings.get('subgroup_col')
            if current_x == subgroup_col:
                subgroup_col = None

            box_pairs = [ann['box_pair'] for ann in annotations_to_plot]
            p_values = [ann['p_value'] for ann in annotations_to_plot]

            if not box_pairs:
                return

            annotator_kwargs = {
                'ax': ax,
                'pairs': box_pairs,
                'data': df,
                'x': current_x,
                'y': current_y,
            }
            if subgroup_col:
                annotator_kwargs['hue'] = subgroup_col
                annotator_kwargs['hue_order'] = hue_order
            
            annotator = Annotator(**annotator_kwargs)
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
        if not visual_hue_col:
            visual_hue_col = None
            
        analysis_hue_col = visual_hue_col
        if current_x == analysis_hue_col:
            analysis_hue_col = None

        df[current_x] = df[current_x].astype(str)
        if visual_hue_col:
            df[visual_hue_col] = df[visual_hue_col].astype(str)

        facet_col = data_settings.get('facet_col')
        facet_row = data_settings.get('facet_row')

        try:
            subgroup_palette = properties.get('subgroup_colors')
            
            # (パレットの型変換処理は変更なし)
            if subgroup_palette and visual_hue_col and pd.api.types.is_numeric_dtype(df[visual_hue_col]):
                # This part is complex because the original dtype could be int or float.
                # We try to convert palette keys back to the original dtype.
                try:
                    # Attempt to convert keys to the series' dtype
                    original_dtype = df[visual_hue_col].dtype
                    subgroup_palette = {original_dtype.type(k): v for k, v in subgroup_palette.items()}
                except (ValueError, TypeError):
                    # Fallback for mixed types or other conversion errors
                    pass

            if not subgroup_palette:
                subgroup_palette = None

            row_categories = sorted(df[facet_row].unique()) if facet_row else [None]
            col_categories = sorted(df[facet_col].unique()) if facet_col else [None]
            n_rows, n_cols = len(row_categories), len(col_categories)

            fig, axes = plt.subplots(
                n_rows, n_cols, figsize=(n_cols * 5, n_rows * 4),
                sharex=False, sharey=True, squeeze=False
            )

            all_relevant_annotations = [
                ann for ann in self.main.statistical_annotations
                if ann.get('value_col') == current_y and
                   ann.get('group_col') == current_x and
                   ann.get('hue_col') == analysis_hue_col
            ]

            for i, row_cat in enumerate(row_categories):
                for j, col_cat in enumerate(col_categories):
                    ax = axes[i, j]
                    
                    subset_df = df.copy()
                    if facet_row:
                        subset_df = subset_df[subset_df[facet_row] == row_cat]
                    if facet_col:
                        subset_df = subset_df[subset_df[facet_col] == col_cat]
                    
                    # ▼▼▼ ここが最後の修正箇所です ▼▼▼
                    # action_handlerと状態を同期するため、インデックスをリセットする
                    subset_df = subset_df.reset_index(drop=True)
                    # ▲▲▲ ここまで ▲▲▲

                    base_kind = self.main.current_graph_type
                    
                    if base_kind != 'scatter':
                        # (描画ロジックは変更なし)
                        plot_func_map = {
                            'bar': sns.barplot, 
                            'boxplot': sns.boxplot, 
                            'violin': sns.violinplot, 
                            'pointplot': sns.pointplot
                        }
                        if base_kind in plot_func_map:
                            base_kwargs = {
                                'data': subset_df, 'x': current_x, 'y': current_y, 
                                'hue': visual_hue_col, 'ax': ax,
                                'palette': subgroup_palette,
                                'color': properties.get('single_color') if not visual_hue_col else None
                            }
                            
                            if base_kind == 'pointplot':
                                base_kwargs['join'] = True
                                base_kwargs['dodge'] = 0.3
                                base_kwargs['capsize'] = properties.get('capsize', 4) * 0.02
                                base_kwargs['linestyle'] = properties.get('linestyle', '-')
                            
                            plot_func_map[base_kind](**base_kwargs)

                    if base_kind == 'scatter' or properties.get('scatter_overlay'):
                        # (描画ロジックは変更なし)
                        plot_kwargs = {
                            'data': subset_df, 'x': current_x, 'y': current_y, 'ax': ax,
                            'marker': properties.get('marker_style', 'o'),
                            'edgecolor': properties.get('marker_edgecolor', 'black'),
                            'linewidth': properties.get('marker_edgewidth', 1.0)
                        }
                        if base_kind == 'scatter':
                            plot_kwargs.update({
                                'hue': visual_hue_col, 
                                'palette': subgroup_palette,
                                'alpha': 1.0, 'legend': False,
                                'color': properties.get('single_color') if not visual_hue_col else None
                            })
                        else:
                             plot_kwargs.update({'color': 'black', 'alpha': 0.6, 'jitter': 0.2})
                        sns.stripplot(**plot_kwargs)

                    title_parts = []
                    if facet_row: title_parts.append(f"{facet_row} = {row_cat}")
                    if facet_col: title_parts.append(f"{facet_col} = {col_cat}")
                    ax.set_title(" | ".join(title_parts))
                    
                    annotations_for_this_facet = [
                        ann for ann in all_relevant_annotations
                        if ann.get('facet_value') == (col_cat if facet_col else None)
                    ]
                    
                    hue_order = sorted(df[visual_hue_col].unique()) if visual_hue_col else None
                    self.apply_annotations(ax, subset_df, data_settings, hue_order, annotations_for_this_facet)

            if visual_hue_col:
                # (凡例ロジックは変更なし)
                handles, labels = axes[0,0].get_legend_handles_labels()
                if handles:
                    by_label = dict(zip(labels, handles))
                    legend_title = properties.get('legend_title') or visual_hue_col
                    
                    legend_pos = properties.get('legend_position', 'best')
                    if legend_pos == 'best':
                        legend_pos = 'upper right'
                    
                    fig.legend(by_label.values(), by_label.keys(),
                               title=legend_title,
                               loc=legend_pos)

            return fig

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
            ax.set_xlabel(properties.get('xlabel') or ax.get_xlabel(), fontsize=properties.get('xlabel_fontsize', 12))
            ax.set_ylabel(properties.get('ylabel') or ax.get_ylabel(), fontsize=properties.get('ylabel_fontsize', 12))
            ax.tick_params(axis='both', which='major', labelsize=properties.get('ticks_fontsize', 10))
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
        self.main.statistical_annotations.clear()
        self.main.regression_line_params = None
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