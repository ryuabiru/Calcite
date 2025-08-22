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
        
        if self.main.statistical_annotations:
            context = self.main.statistical_annotations[0]
            y = context.get('value_col')
            x = context.get('group_col')
            filters = context.get('common_filters', {})
            
            plot_data = df.copy()
            if filters:
                for col, val in filters.items():
                    plot_data = plot_data[plot_data[col].astype(str) == str(val)]
            
            hue = list(filters.keys())[0] if filters else None
            self.draw_catplot_and_annotate(plot_data, properties, y, x, hue, context)
        else:
            if self.main.current_graph_type == 'paired_scatter':
                self.draw_paired_scatter(df, properties)
            else:
                data_settings = self.main.properties_panel.data_tab.get_current_settings()
                y = data_settings.get('y_col')
                x = data_settings.get('x_col')
                hue = data_settings.get('subgroup_col')
                
                if not x or not y:
                    self.clear_canvas()
                    return
                
                self.draw_catplot_and_annotate(df, properties, y, x, hue, None)

    def draw_catplot_and_annotate(self, df, properties, y, x, hue, context):
        if hue and hue in df.columns:
            df[hue] = df[hue].astype(str)

        plot_kind = 'strip' if self.main.current_graph_type == 'scatter' else 'bar'
        
        plot_kwargs = {}
        if plot_kind == 'bar':
            plot_kwargs['edgecolor'] = properties.get('bar_edgecolor', 'black')
            plot_kwargs['linewidth'] = properties.get('bar_edgewidth', 1.0)
            plot_kwargs['capsize'] = properties.get('capsize', 4) * 0.01
            plot_kwargs['errwidth'] = properties.get('bar_edgewidth', 1.0)
        elif plot_kind == 'strip':
            plot_kwargs['marker'] = properties.get('marker_style', 'o')
            plot_kwargs['edgecolor'] = properties.get('marker_edgecolor', 'black')
            plot_kwargs['linewidth'] = properties.get('marker_edgewidth', 1.0)
        
        ui_subgroup_col = self.main.properties_panel.data_tab.get_current_settings().get('subgroup_col')
        if hue:
            if hue == ui_subgroup_col:
                plot_kwargs['palette'] = {str(k): v for k, v in properties.get('subgroup_colors', {}).items()}
        else:
            plot_kwargs['color'] = properties.get('single_color')

        try:
            g = sns.catplot(
                data=df, x=x, y=y, hue=hue, kind=plot_kind,
                height=4, aspect=1.2, sharex=False, sharey=False,
                **plot_kwargs
            )

            if context:
                self.apply_annotations(g, df, y, x, hue, context)

            self.replace_canvas(g.fig)
            self.update_graph_properties(g.fig, properties)

        except Exception as e:
            print(f"Graph drawing error: {e}")
            traceback.print_exc()
    
    # ★★★ ここを修正 ★★★
    def apply_annotations(self, g, df, current_y, current_x, subgroup_col, context):
        annotations_data = context.get("annotations")
        if not annotations_data:
            return

        plot_data = df.copy()
        filters = context.get('common_filters', {})
        if filters:
            for col, val in filters.items():
                plot_data = plot_data[plot_data[col].astype(str) == str(val)]
        
        use_hue = subgroup_col and plot_data[subgroup_col].nunique() > 1
        
        original_pairs = [ann['box_pair'] for ann in annotations_data]
        p_values = [ann['p_value'] for ann in annotations_data]

        if use_hue:
            hue_values = plot_data[subgroup_col].unique()
            box_pairs = [((pair[0], str(hv)), (pair[1], str(hv))) for hv in hue_values for pair in original_pairs]
            p_values = np.tile(p_values, len(hue_values))
        else:
            box_pairs = original_pairs
        
        if not box_pairs:
            return
            
        try:
            for ax_facet in g.axes.flat:
                annotator = Annotator(ax_facet, box_pairs, data=plot_data, x=current_x, y=current_y, 
                                      hue=subgroup_col if use_hue else None)
                annotator.configure(text_format='star', loc='inside', verbose=0)
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

    def draw_paired_scatter(self, df, properties):
        data_settings = self.main.properties_panel.data_tab.get_current_settings()
        ax = self.main.graph_widget.ax
        ax.clear()
        col1 = data_settings.get('col1')
        col2 = data_settings.get('col2')
        if not (col1 and col2 and col1 != col2):
            self.main.graph_widget.canvas.draw()
            return
            
        self._draw_paired_plot_seaborn(ax, df, col1, col2, properties)
        self.update_graph_properties(self.main.graph_widget.fig, properties)
        self.main.graph_widget.canvas.draw()
        
    def clear_canvas(self):
        if hasattr(self.main.graph_widget, 'canvas') and self.main.graph_widget.canvas:
            self.main.graph_widget.canvas.figure.clear()
            self.main.graph_widget.canvas.draw()

    def save_graph(self):
        if not hasattr(self.main.graph_widget, 'fig'):
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
        if hasattr(self.main, 'statistical_annotations'):
            self.main.statistical_annotations.clear()
        self.update_graph()
    
    def _draw_paired_plot_seaborn(self, ax, df, col1, col2, properties):
        pass # 実装は省略