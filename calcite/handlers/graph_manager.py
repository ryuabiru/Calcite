# handlers/graph_manager.py

from PySide6.QtWidgets import QFileDialog, QMessageBox
import seaborn as sns
from statannotations.Annotator import Annotator
import traceback
import matplotlib.pyplot as plt
from calcite.models import PlotRequest
from calcite.services.plot_service import (
    BASE_PLOT_KINDS,
    build_annotation_spec,
    build_facet_plot_data,
    build_base_plot_kwargs,
    build_four_pl_overlay_lines,
    build_legend_handles_labels,
    build_paired_annotation_spec,
    build_paired_plot_data,
    build_regression_overlay_lines,
    build_scatter_plot_kwargs,
    build_stripplot_kwargs,
    build_summary_errorbar_specs,
    get_facet_values,
    get_x_order,
    normalize_plot_request,
    prepare_plot_dataframe,
)

class GraphManager:
    def __init__(self, main_window):
        self.main = main_window


    def update_graph(self):
        if not hasattr(self.main, 'model') or self.main.model is None:
            self.clear_canvas()
            return
        
        df = self.main.model._data
        request = PlotRequest.from_sources(
            graph_type=self.main.current_graph_type,
            data_settings=self.main.data_widget.get_current_settings(),
            properties=self.main.properties_widget.get_properties(),
        )
        request = normalize_plot_request(request)
        
        fig = None
        if request.graph_type == 'paired_scatter':
            fig = self.draw_paired_scatter(df, request)
        elif request.graph_type == 'histogram':
            fig = self.draw_histogram(df, request.properties, request.properties)
        else:
            fig = self.draw_categorical_plot(df, request)
            
        if fig:
            self.replace_canvas(fig)
            self.update_graph_properties(fig, request.properties)


    def apply_annotations(self, ax, df, data_settings, hue_order, annotations_to_plot):
        try:
            annotation_spec = build_annotation_spec(
                df,
                PlotRequest(
                    graph_type="",
                    x_col=data_settings.get("x_col", ""),
                    y_col=data_settings.get("y_col", ""),
                    subgroup_col=data_settings.get("subgroup_col", ""),
                ),
                annotations_to_plot,
                ax,
                hue_order,
            )
            if annotation_spec is None:
                return

            annotator = Annotator(**annotation_spec.annotator_kwargs)
            pvalue_thresholds = [[1e-4, "****"], [1e-3, "***"], [1e-2, "**"], [0.05, "*"], [1.0, "n.s."]]
            annotator.configure(text_format='star', loc='inside', verbose=0, pvalue_thresholds=pvalue_thresholds)
            annotator.set_pvalues(annotation_spec.p_values)
            annotator.annotate()
            
        except Exception as e:
            print(f"Annotation Error during plotting: {e}")
            traceback.print_exc()


    def draw_categorical_plot(self, df, request: PlotRequest):
        """
        レイヤー化アーキテクチャに基づき、カテゴリカルなグラフを描画する。
        """
        properties = request.properties
        current_x = request.x_col
        current_y = request.y_col
        if not current_x or not current_y:
            self.clear_canvas()
            return None

        base_kind = request.graph_type
        visual_hue_col = request.subgroup_col or None
        facet_col = request.facet_col

        try:
            df_processed = prepare_plot_dataframe(df, request)
            x_order = get_x_order(df_processed, request)
            
            subgroup_palette = properties.get('subgroup_colors', {})
            col_categories = get_facet_values(df_processed, request)
            n_rows, n_cols = 1, len(col_categories)

            fig, axes = plt.subplots(
                n_rows, n_cols, figsize=(n_cols * 5, n_rows * 4),
                sharex=False, sharey=True, squeeze=False, layout='constrained'
            )
            all_relevant_annotations = [ann for ann in self.main.statistical_annotations if ann.get('value_col') == current_y]
            facet_plot_data = build_facet_plot_data(df_processed, request)

            for j, facet_data in enumerate(facet_plot_data):
                ax = axes[0, j]
                col_cat = facet_data.facet_value
                original_subset_df = facet_data.source_df

                if original_subset_df.empty:
                    ax.set_title(f"No data for {col_cat}"); continue
                
                plot_df = facet_data.plot_df
                
                base_plot_map = { 'bar': sns.barplot, 'boxplot': sns.boxplot, 'violin': sns.violinplot, 'pointplot': sns.pointplot, 'lineplot': sns.lineplot }
                if base_kind in base_plot_map:
                    base_kwargs = build_base_plot_kwargs(request, plot_df, x_order, properties)
                    base_kwargs['ax'] = ax
                    base_plot_map[base_kind](**base_kwargs)

                if base_kind in ['scatter', 'summary_scatter']:
                    scatter_kwargs = build_scatter_plot_kwargs(request, plot_df, properties)
                    scatter_kwargs['ax'] = ax
                    sns.scatterplot(**scatter_kwargs)
                    if base_kind == 'summary_scatter':
                        for errorbar_spec in build_summary_errorbar_specs(plot_df, request, properties):
                            ax.errorbar(**errorbar_spec)
                if properties.get('scatter_overlay') and (base_kind in BASE_PLOT_KINDS):
                    if not original_subset_df.empty:
                        stripplot_kwargs = build_stripplot_kwargs(request, original_subset_df, x_order, properties)
                        stripplot_kwargs['ax'] = ax
                        sns.stripplot(**stripplot_kwargs)
                
                title_parts = []; 
                if facet_col: title_parts.append(f"{col_cat}")
                ax.set_title(" | ".join(title_parts))
                if j > 0:
                    bottom, top = ax.get_ylim(); extension = (top - bottom) * 0.10; ax.spines['left'].set_bounds(bottom - extension, top)
                annotations_for_this_facet = [ann for ann in all_relevant_annotations if ann.get('facet_value') == (col_cat if facet_col else None)]
                hue_order = sorted(df_processed[visual_hue_col].unique()) if visual_hue_col else None
                self.apply_annotations(ax, df_processed, properties, hue_order, annotations_for_this_facet)

            # --- 凡例統合レイヤー ---
            if visual_hue_col:
                for ax in axes.flat:
                    if ax.get_legend() is not None:
                        ax.get_legend().remove()

                handles, labels = build_legend_handles_labels(df_processed, request, properties, axes.flat)
                if properties.get('legend_position') != 'hide' and handles:
                    legend_title = properties.get('legend_title') or visual_hue_col
                    legend_pos = properties.get('legend_position', 'best')

                    target_ax = axes.flat[-1]
                    target_ax.legend(
                        handles=handles, 
                        labels=labels, 
                        title=legend_title,
                        loc=legend_pos
                    )

            is_faceted = n_cols > 1
            if is_faceted:
                shared_xlabel = properties.get('xlabel') or current_x;
                for ax in axes.flat: ax.set_xlabel('')
                fig.supxlabel(shared_xlabel, fontsize=properties.get('xlabel_fontsize', 15))

            if base_kind in ['scatter', 'summary_scatter'] and not is_faceted:
                ax = axes[0, 0]

                overlay_lines = build_regression_overlay_lines(self.main.regression_line_params, properties)
                overlay_lines.extend(build_four_pl_overlay_lines(self.main.fit_params, properties))
                for overlay_line in overlay_lines:
                    ax.plot(
                        overlay_line.x,
                        overlay_line.y,
                        color=overlay_line.color,
                        linestyle=properties.get('linestyle', '--'),
                        linewidth=properties.get('linewidth', 1.5),
                        label=overlay_line.label,
                    )
                if overlay_lines:
                    ax.legend()
            
            return fig
        except Exception as e:
            QMessageBox.critical(self.main, "Graph Error", f"An unexpected error occurred: {e}")
            print(f"Graph drawing error: {e}"); traceback.print_exc()
            return None


    def draw_paired_scatter(self, df, request: PlotRequest):
        properties = request.properties
        paired_plot_data = build_paired_plot_data(df, request)
        if paired_plot_data is None:
            return None

        col1 = request.col1
        col2 = request.col2
        fig, ax = plt.subplots(layout='constrained')
        try:
            plot_df_long = self._draw_paired_plot_seaborn(ax, paired_plot_data, properties)
            
            if plot_df_long is not None and self.main.paired_annotations:
                # このプロットに関連するアノテーションのみを抽出
                annotations_to_plot = [
                    ann for ann in self.main.paired_annotations
                    if set(ann['box_pair']) == {col1, col2}
                ]
                annotation_spec = build_paired_annotation_spec(plot_df_long, annotations_to_plot, ax)
                if annotation_spec is not None:
                    annotator = Annotator(**annotation_spec.annotator_kwargs)
                    pvalue_thresholds = [[1e-4, "****"], [1e-3, "***"], [1e-2, "**"], [0.05, "*"], [1.0, "n.s."]]
                    annotator.configure(text_format='star', loc='outside', verbose=0, pvalue_thresholds=pvalue_thresholds)
                    annotator.set_pvalues(annotation_spec.p_values)
                    annotator.annotate()
            
            self.update_graph_properties(fig, properties)
            
            return fig
        
        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to draw paired plot: {e}")
            return None


    def replace_canvas(self, new_fig):
        """
        古いFigureCanvasをウィジェットから削除し、新しいものに置き換える。
        """
        
        # 既存のキャンバスがあれば、レイアウトから削除して安全に破棄する
        if hasattr(self.main.graph_widget, 'canvas') and self.main.graph_widget.canvas:
            self.main.graph_widget.canvas.setParent(None)
            self.main.graph_widget.canvas.deleteLater()
        
        # 新しいFigureから新しいキャンバスを作成
        new_canvas = new_fig.canvas
        # GraphWidgetのレイアウトに新しいキャンバスを追加
        self.main.graph_widget.layout().addWidget(new_canvas)
        
        # 新しいキャンバスとFigureへの参照を保持
        self.main.graph_widget.canvas = new_canvas
        self.main.graph_widget.fig = new_fig
        if hasattr(self.main.graph_widget.fig, 'axes') and self.main.graph_widget.fig.axes:
             self.main.graph_widget.ax = self.main.graph_widget.fig.axes[0]


    def update_graph_properties(self, fig, properties):
        """
        UIパネルの設定に基づいて、FigureとAxesの見た目を更新する。
        """
        fig.suptitle(properties.get('title', ''), fontsize=properties.get('title_fontsize', 16))
        
        is_faceted = len(fig.axes) > 1

        axis_linewidth = properties.get('axis_linewidth', 1.0)
        tick_length = properties.get('tick_length', 4.0)
        tick_direction = properties.get('tick_direction', 'out')

        for ax in fig.axes:
            # ファセットグラフではない場合にのみ、個別のX軸ラベルを設定する
            if not is_faceted:
                ax.set_xlabel(properties.get('xlabel') or ax.get_xlabel(), fontsize=properties.get('xlabel_fontsize', 15))
            
            # Y軸ラベルは常に個別で設定
            ax.set_ylabel(properties.get('ylabel') or ax.get_ylabel(), fontsize=properties.get('ylabel_fontsize', 15))
            
            ax.tick_params(
                axis='both', which='major', 
                labelsize=properties.get('ticks_fontsize', 12),
                width=axis_linewidth,
                length=tick_length,
                direction=tick_direction
            )
            
            for spine in ax.spines.values():
                spine.set_linewidth(axis_linewidth)
            
            if properties.get('hide_top_right_spines', True):
                ax.spines['right'].set_visible(False); ax.spines['top'].set_visible(False)
            ax.grid(properties.get('show_grid', False))
            if properties.get('x_log_scale'): ax.set_xscale('log')
            if properties.get('y_log_scale'): ax.set_yscale('log')
            



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
        self.main.paired_annotations.clear()
        self.main.regression_line_params = None
        self.main.fit_params = None
        self.update_graph()


    def clear_graph(self):
        """
        グラフキャンバスをクリアし、すべてのプロット関連パラメータをリセットする。
        """
        # すべての注釈とフィットパラメータをクリア
        self.main.statistical_annotations.clear()
        self.main.paired_annotations.clear()
        self.main.regression_line_params = None
        self.main.fit_params = None
        # Matplotlibのキャンバスをクリア
        self.clear_canvas()


    def clear_annotations(self):
        """
        統計的な注釈のみをクリアし、グラフを再描画する。
        """
        self.main.statistical_annotations.clear()
        self.main.paired_annotations.clear()
        self.main.regression_line_params = None
        self.main.fit_params = None
        self.update_graph()


    def _draw_paired_plot_seaborn(self, ax, paired_plot_data, properties):
        try:
            plot_df_long = paired_plot_data.plot_df_long
            
            # 2. 線のスタイルをプロパティから適用
            sns.lineplot(data=plot_df_long, x='Condition', y='Value', units='ID', 
                        estimator=None, color='gray', alpha=0.5, ax=ax,
                        linestyle=properties.get('linestyle', '-'),
                        linewidth=properties.get('linewidth', 1.5))
            
            # 3. マーカーのスタイルをプロパティから適用
            sns.scatterplot(data=plot_df_long, x='Condition', y='Value', 
                            color=properties.get('single_color', 'black'), 
                            marker=properties.get('marker_style', 'o'), 
                            edgecolor=properties.get('marker_edgecolor', 'black'), 
                            linewidth=properties.get('marker_edgewidth', 1.0), 
                            ax=ax, legend=False)
            
            ax.plot(
                paired_plot_data.mean_x,
                paired_plot_data.mean_y.values,
                color='red',
                marker='_',
                markersize=20,
                mew=2.5,
                linestyle='None',
                label='Mean',
            )
            
            # 4. X軸の目盛りラベルを設定
            ax.set_xticks([0, 1])
            ax.set_xticklabels(paired_plot_data.tick_labels)
            
            # 5. X軸のメインラベルは不要なので消去
            ax.set_xlabel('')
            
            # 6. 凡例の位置をプロパティから適用
            handles, labels = ax.get_legend_handles_labels()
            if handles:
                legend_pos = properties.get('legend_position', 'best')
                # 'best'は枠外配置に対応していないため、手動で調整
                if legend_pos == 'best':
                    ax.legend(handles=handles, labels=labels, loc='upper left', bbox_to_anchor=(1.02, 1))
                else:
                    ax.legend(handles=handles, labels=labels, loc=legend_pos)
                    
            return plot_df_long
        
        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to draw paired plot: {e}")


    def draw_histogram(self, df, properties, data_settings):
        value_col = data_settings.get('y_col')
        if not value_col: return None
        hue_col = data_settings.get('subgroup_col')
        if not hue_col: hue_col = None
        fig, ax = plt.subplots(layout='constrained')
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
