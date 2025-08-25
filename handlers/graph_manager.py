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
import matplotlib.patches as mpatches

class GraphManager:
    def __init__(self, main_window):
        self.main = main_window

    def sigmoid_4pl(self, x, bottom, top, hill_slope, log_ec50):
        """4パラメータロジスティック（4PL）モデルの関数。xとlog_ec50はlog10スケール。"""
        return bottom + (top - bottom) / (1 + 10**((log_ec50 - x) * hill_slope))

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

    def apply_annotations(self, ax, df, data_settings, hue_order, annotations_to_plot):
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

        if self.main.current_graph_type not in ['scatter', 'lineplot']:
            df[current_x] = df[current_x].astype(str)
            if visual_hue_col:
                df[visual_hue_col] = df[visual_hue_col].astype(str)

        facet_col = data_settings.get('facet_col')
        facet_row = data_settings.get('facet_row')

        try:
            subgroup_palette = {}
            if visual_hue_col:
                user_colors = properties.get('subgroup_colors', {})
                unique_hues = sorted(df[visual_hue_col].unique())
                
                default_colors = sns.color_palette(n_colors=len(unique_hues))
                subgroup_palette = dict(zip(unique_hues, default_colors))
                
                for category, color in user_colors.items():
                    if category in subgroup_palette:
                        subgroup_palette[category] = color

            row_categories = df[facet_row].unique() if facet_row else [None]
            col_categories = df[facet_col].unique() if facet_col else [None]
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
                    
                    subset_df = subset_df.reset_index(drop=True)

                    base_kind = self.main.current_graph_type
                    
                    plot_kwargs = {'legend': False}

                    if base_kind == 'lineplot':
                        sns.lineplot(
                            data=subset_df, x=current_x, y=current_y,
                            hue=visual_hue_col, ax=ax,
                            palette=subgroup_palette if subgroup_palette else None,
                            color=properties.get('single_color') if not visual_hue_col else None,
                            linestyle=properties.get('linestyle', '-'),
                            linewidth=properties.get('linewidth', 1.5),
                            **plot_kwargs
                        )

                    if base_kind != 'scatter':
                        plot_func_map = {
                            'bar': sns.barplot, 'boxplot': sns.boxplot, 
                            'violin': sns.violinplot, 'pointplot': sns.pointplot
                        }
                        if base_kind in plot_func_map:
                            base_kwargs = {
                                'data': subset_df, 'x': current_x, 'y': current_y, 
                                'hue': visual_hue_col, 'ax': ax,
                                'palette': subgroup_palette if subgroup_palette else None,
                                'color': properties.get('single_color') if not visual_hue_col else None,
                            }
                            
                            if base_kind == 'bar':
                                base_kwargs.update({
                                    'edgecolor': properties.get('bar_edgecolor', 'black'),
                                    'linewidth': properties.get('bar_edgewidth', 1.0),
                                    'capsize': properties.get('capsize', 4) * 0.01
                                })

                            if base_kind == 'pointplot':
                                base_kwargs.update({
                                    'join': True, 
                                    'dodge': False,
                                    'capsize': properties.get('capsize', 4) * 0.02,
                                    'linestyle': properties.get('linestyle', '-')
                                })
                            
                            plot_func_map[base_kind](**base_kwargs, **plot_kwargs)

                    if base_kind == 'scatter' or properties.get('scatter_overlay'):
                        
                        stripplot_kwargs = {
                            'data': subset_df, 'x': current_x, 'y': current_y, 'ax': ax,
                            'marker': properties.get('marker_style', 'o'),
                            'edgecolor': properties.get('marker_edgecolor', 'black'),
                            'linewidth': properties.get('marker_edgewidth', 1.0),
                            'legend': False
                        }

                        should_dodge = True
                        if visual_hue_col == current_x:
                            should_dodge = False

                    if base_kind == 'scatter' or properties.get('scatter_overlay'):
                        
                        # ▼▼▼ ここからが修正箇所です ▼▼▼
                        if base_kind == 'scatter':
                            # --- 散布図の場合：scatterplotを使用 ---
                            scatter_kwargs = {
                                'data': subset_df, 'x': current_x, 'y': current_y, 'ax': ax,
                                'marker': properties.get('marker_style', 'o'),
                                'edgecolor': properties.get('marker_edgecolor', 'black'),
                                'linewidth': properties.get('marker_edgewidth', 1.0),
                                'hue': visual_hue_col,
                                'palette': subgroup_palette if subgroup_palette else None,
                                'legend': False 
                            }
                            sns.scatterplot(**scatter_kwargs)
                        
                        else: # --- 重ね描きの場合：これまで通りstripplotを使用 ---
                            stripplot_kwargs = {
                                'data': subset_df, 'x': current_x, 'y': current_y, 'ax': ax,
                                'marker': properties.get('marker_style', 'o'),
                                'edgecolor': properties.get('marker_edgecolor', 'black'),
                                'linewidth': properties.get('marker_edgewidth', 1.0),
                                'legend': False
                            }

                            should_dodge = True
                            if visual_hue_col == current_x:
                                should_dodge = False
                            
                            stripplot_kwargs.update({
                                'hue': visual_hue_col,
                                'palette': subgroup_palette if subgroup_palette else None,
                                'alpha': 0.6,
                                'dodge': should_dodge,
                                'jitter': 0.2
                            })
                            sns.stripplot(**stripplot_kwargs)

                    title_parts = []
                    if facet_row: title_parts.append(f"{facet_row} = {row_cat}")
                    if facet_col: title_parts.append(f"{facet_col} = {col_cat}")
                    ax.set_title(" | ".join(title_parts))
                    
                    annotations_for_this_facet = [ann for ann in all_relevant_annotations if ann.get('facet_value') == (col_cat if facet_col else None)]
                    hue_order = sorted(df[visual_hue_col].unique()) if visual_hue_col else None
                    self.apply_annotations(ax, subset_df, data_settings, hue_order, annotations_for_this_facet)

            is_faceted = n_rows > 1 or n_cols > 1
            if is_faceted:
                shared_xlabel = properties.get('xlabel') or current_x
                for ax in axes.flat:
                    ax.set_xlabel('')
                fig.supxlabel(shared_xlabel, y=0.02)

                for i in range(n_rows):
                    for j in range(n_cols):
                        if j > 0:
                            ax = axes[i, j]
                            bottom, top = ax.get_ylim()
                            extension = (top - bottom) * 0.10
                            ax.spines['left'].set_bounds(bottom - extension, top)

            if self.main.current_graph_type == 'scatter' and not (facet_col or facet_row):
                ax = axes[0, 0]
                if self.main.regression_line_params:
                    params = self.main.regression_line_params
                    r_squared = params.get("r_squared", 0)
                    ax.plot(params["x_line"], params["y_line"], 
                            color=properties.get('regression_color', 'red'), 
                            linestyle=properties.get('linestyle', '--'), 
                            linewidth=properties.get('linewidth', 1.5),
                            label=f'Linear Fit ($R^2$={r_squared:.3f})')
                if self.main.fit_params:
                    params_dict = self.main.fit_params
                    fit_params = params_dict["params"]
                    log_x_data = params_dict["log_x_data"]
                    r_squared = params_dict.get("r_squared", 0)
                    x_smooth_log = np.linspace(log_x_data.min(), log_x_data.max(), 200)
                    y_smooth = self.sigmoid_4pl(x_smooth_log, *fit_params)
                    ax.plot(10**x_smooth_log, y_smooth, 
                            color=properties.get('regression_color', 'red'), # 参照先を統一
                            linestyle=properties.get('linestyle', '--'), 
                            linewidth=properties.get('linewidth', 1.5),
                            label=f'4PL Fit ($R^2$={r_squared:.3f})')
                if self.main.regression_line_params or self.main.fit_params:
                    handles, labels = ax.get_legend_handles_labels()
                    if handles:
                        legend_pos = properties.get('legend_position', 'best')
                        if ax.get_legend() is not None:
                            ax.get_legend().remove()
                        ax.legend(handles=handles, loc=legend_pos)

            if visual_hue_col:
                for ax in axes.flat:
                    if ax.get_legend() is not None:
                        ax.get_legend().remove()
                legend_title = properties.get('legend_title') or visual_hue_col
                legend_pos = properties.get('legend_position', 'best')
                handles = [mpatches.Patch(color=color, label=label) for label, color in subgroup_palette.items()]
                legend_ax = axes[0, -1]
                kwargs = {}
                if legend_pos == 'best':
                    kwargs['loc'] = 'upper left'
                    kwargs['bbox_to_anchor'] = (1.02, 1)
                else:
                    kwargs['loc'] = legend_pos
                legend_ax.legend(handles=handles, title=legend_title, **kwargs)
                
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
            
        fig.tight_layout(rect=[0.05, 0.05, 0.90, 0.95])

    def draw_paired_scatter(self, df, properties, data_settings):
        col1 = data_settings.get('col1')
        col2 = data_settings.get('col2')
        if not (col1 and col2 and col1 != col2): return None
        fig, ax = plt.subplots(tight_layout=True)
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
                self.main.graph_widget.fig.savefig(file_path, dpi=300, bbox_inches='tight')
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
        fig, ax = plt.subplots(tight_layout=True)
        plot_kwargs = {}
        if hue_col:
             df[hue_col] = df[hue_col].astype(str)
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