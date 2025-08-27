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
            # ★★★ 新しい描画関数を呼び出す ★★★
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
        """
        レイヤー化アーキテクチャに基づき、カテゴリカルなグラフを描画する。
        """
        current_x = data_settings.get('x_col')
        current_y = data_settings.get('y_col')
        if not current_x or not current_y:
            self.clear_canvas()
            return None
        
        # --- 描画設定の準備 ---
        base_kind = self.main.current_graph_type
        visual_hue_col = data_settings.get('subgroup_col')
        if not visual_hue_col:
            visual_hue_col = None
            
        analysis_hue_col = visual_hue_col # 統計解析用のhue列
        facet_col = data_settings.get('facet_col')
        facet_row = data_settings.get('facet_row')
        
        # --- データ型の事前準備 ---
        if base_kind not in ['scatter', 'summary_scatter', 'lineplot']:
            df[current_x] = df[current_x].astype(str)
            if visual_hue_col:
                df[visual_hue_col] = df[visual_hue_col].astype(str)
                
        try:
            # ==================================================================
            # ▼ レイヤー 1: データ準備レイヤー ▼
            # ==================================================================
            plot_df = df.copy()  # デフォルトでは元のデータを使用
            
            if base_kind == 'summary_scatter':
                print("[Layer 1] Preparing data for Summary Scatter...")
                group_cols = [current_x]
                if visual_hue_col and visual_hue_col != current_x:
                    group_cols.append(visual_hue_col)
                    
                summary_stats = df.groupby(group_cols, as_index=False).agg(
                    mean_y=(current_y, 'mean'),
                    err_y=(current_y, 'sem')
                )
                summary_stats.rename(columns={'mean_y': current_y}, inplace=True)
                plot_df = summary_stats  # 描画用データを要約済みのものに差し替える
                print(" -> Data summarized.")
            # ==================================================================
            # ▲ データ準備レイヤーここまで ▲
            # ==================================================================
            
            # --- 描画の準備 (Matplotlib-first) ---
            subgroup_palette = properties.get('subgroup_colors', {})
            row_categories = sorted(df[facet_row].unique()) if facet_row else [None]
            col_categories = sorted(df[facet_col].unique()) if facet_col else [None]
            n_rows, n_cols = len(row_categories), len(col_categories)
            
            fig, axes = plt.subplots(
                n_rows, n_cols, figsize=(n_cols * 5, n_rows * 4),
                sharex=False, sharey=True, squeeze=False
            )
            
            all_relevant_annotations = [ann for ann in self.main.statistical_annotations if ann.get('value_col') == current_y]
            
            # --- ファセットのループ (分割統治) ---
            for i, row_cat in enumerate(row_categories):
                for j, col_cat in enumerate(col_categories):
                    ax = axes[i, j]
                    
                    # ファセットに対応する描画用データ(plot_df)のsubsetを作成
                    subset_selector = pd.Series(True, index=plot_df.index)
                    if facet_row: subset_selector &= (plot_df[facet_row] == row_cat)
                    if facet_col: subset_selector &= (plot_df[facet_col] == col_cat)
                    subset_df = plot_df[subset_selector]
                    
                    print(f"\n--- Drawing Facet (Row: {row_cat}, Col: {col_cat}) ---")
                    
                    # ==================================================================
                    # ▼ レイヤー 2: ベースレイヤー ▼
                    # ==================================================================
                    base_plot_map = {
                        'bar': sns.barplot, 'boxplot': sns.boxplot,
                        'violin': sns.violinplot, 'pointplot': sns.pointplot,
                        'lineplot': sns.lineplot
                    }
                    if base_kind in base_plot_map:
                        print(f"[Layer 2] Drawing Base Plot: {base_kind}")
                        
                        base_kwargs = {
                            'data': subset_df, 'x': current_x, 'y': current_y,
                            'ax': ax
                        }
                        if visual_hue_col:
                            # サブグループがある場合：hueとpaletteを指定
                            base_kwargs['hue'] = visual_hue_col
                            base_kwargs['palette'] = subgroup_palette
                        else:
                            # サブグループがない場合：ユーザーが色を選んでいればcolorを指定
                            single_color = properties.get('single_color')
                            if single_color:
                                base_kwargs['color'] = single_color
                            print(f" -> without Subgroup. Using color: {properties.get('single_color')}") # デバッグ用
                        
                        if base_kind == 'bar':
                            base_kwargs.update({'edgecolor': properties.get('bar_edgecolor', 'black'), 'linewidth': properties.get('bar_edgewidth', 1.0), 'capsize': properties.get('capsize', 4) * 0.01})
                        if base_kind in ['pointplot', 'lineplot']:
                            base_kwargs.update({'linestyle': properties.get('linestyle', '-'), 'linewidth': properties.get('linewidth', 1.5)})
                        if base_kind == 'pointplot':
                             base_kwargs.update({'dodge': True, 'capsize': properties.get('capsize', 4) * 0.02})
                            
                        base_plot_map[base_kind](**base_kwargs, legend=False)
                    # ==================================================================
                    # ▲ ベースレイヤーここまで ▲
                    # ==================================================================
                    
                    # ==================================================================
                    # ▼ レイヤー 3: 散布図レイヤー ▼
                    # ==================================================================
                    if base_kind in ['scatter', 'summary_scatter']:
                        print(f"[Layer 3] Drawing Scatter Plot: {base_kind}")
                        scatter_kwargs = {
                            'data': subset_df, 'x': current_x, 'y': current_y, 'ax': ax,
                            'marker': properties.get('marker_style', 'o'),
                            'edgecolor': properties.get('marker_edgecolor', 'black'),
                            'linewidth': properties.get('marker_edgewidth', 1.0)
                        }
                        if visual_hue_col:
                            scatter_kwargs['hue'] = visual_hue_col
                            scatter_kwargs['palette'] = subgroup_palette
                        else:
                            single_color = properties.get('single_color')
                            if single_color:
                                scatter_kwargs['color'] = single_color
                        sns.scatterplot(**scatter_kwargs, legend=False)
                        
                        if base_kind == 'summary_scatter':
                            if visual_hue_col:
                                for hue_val, grp in subset_df.groupby(visual_hue_col):
                                    ax.errorbar(x=grp[current_x], y=grp[current_y], yerr=grp['err_y'], fmt='none', capsize=properties.get('capsize', 4), ecolor=subgroup_palette.get(str(hue_val), 'black'))
                            else:
                                ax.errorbar(x=subset_df[current_x], y=subset_df[current_y], yerr=subset_df['err_y'], fmt='none', capsize=properties.get('capsize', 4), ecolor=properties.get('marker_edgecolor', 'black'))
                            print(" -> Added error bars.")
                    # ==================================================================
                    # ▲ 散布図レイヤーここまで ▲
                    # ==================================================================
                    
                    # ==================================================================
                    # ▼ レイヤー 4: オーバーレイレイヤー ▼
                    # ==================================================================
                    if properties.get('scatter_overlay') and base_kind not in ['scatter', 'summary_scatter', 'lineplot']:
                        print("[Layer 4] Drawing Overlay Points...")
                        # オーバーレイは「要約されていない」元のデータ(df)を使う
                        original_subset_selector = pd.Series(True, index=df.index)
                        if facet_row: original_subset_selector &= (df[facet_row] == row_cat)
                        if facet_col: original_subset_selector &= (df[facet_col] == col_cat)
                        original_subset_df = df[original_subset_selector]
                        
                        if not original_subset_df.empty:
                            sns.stripplot(
                                data=original_subset_df, x=current_x, y=current_y, hue=visual_hue_col,
                                ax=ax, jitter=0.2, alpha=0.6, palette=subgroup_palette,
                                marker=properties.get('marker_style', 'o'),
                                edgecolor=properties.get('marker_edgecolor', 'black'),
                                linewidth=properties.get('marker_edgewidth', 1.0),
                                legend=False, dodge=False # ★★★ 常にFalse ★★★
                            )
                            print(" -> stripplot called with dodge=False.")
                    # ==================================================================
                    # ▲ オーバーレイレイヤーここまで ▲
                    # ==================================================================
                    
                    # --- 描画の後処理 (タイトル、アノテーション) ---
                    title_parts = []
                    if facet_row: title_parts.append(f"{facet_row} = {row_cat}")
                    if facet_col: title_parts.append(f"{facet_col} = {col_cat}")
                    ax.set_title(" | ".join(title_parts))
                    
                    annotations_for_this_facet = [ann for ann in all_relevant_annotations if ann.get('facet_value') == (col_cat if facet_col else None)]
                    hue_order = sorted(df[visual_hue_col].unique()) if visual_hue_col else None
                    # ★アノテーションに渡すデータフレームを元のdfに修正
                    self.apply_annotations(ax, df, data_settings, hue_order, annotations_for_this_facet)
                    
            # --- 全体の後処理 (凡例、回帰分析など) ---
            if visual_hue_col and any(ax.get_legend_handles_labels()[0] for ax in axes.flat):
                legend_title = properties.get('legend_title') or visual_hue_col
                legend_pos = properties.get('legend_position', 'best')
                handles = [mpatches.Patch(color=color, label=label) for label, color in subgroup_palette.items()]
                kwargs = {'loc': 'upper left', 'bbox_to_anchor': (1.02, 1)} if legend_pos == 'best' else {'loc': legend_pos}
                # 凡例はfigに対してつける
                fig.legend(handles=handles, title=legend_title, **kwargs)
                
            if base_kind in ['scatter', 'summary_scatter'] and not (facet_col or facet_row):
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
                            color=properties.get('regression_color', 'red'),
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
                        
            return fig
        
        except Exception as e:
            QMessageBox.critical(self.main, "Graph Error", f"An unexpected error occurred while drawing the graph:\n\n{e}")
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
            plot_df_long = self._draw_paired_plot_seaborn(ax, df, col1, col2, properties)
            
            if plot_df_long is not None and self.main.paired_annotations:
                # このプロットに関連するアノテーションのみを抽出
                annotations_to_plot = [
                    ann for ann in self.main.paired_annotations
                    if set(ann['box_pair']) == {col1, col2}
                ]
                if annotations_to_plot:
                    pairs = [ann['box_pair'] for ann in annotations_to_plot]
                    p_values = [ann['p_value'] for ann in annotations_to_plot]
                    
                    annotator = Annotator(
                        ax, pairs, data=plot_df_long,
                        x='Condition', y='Value'
                    )
                    pvalue_thresholds = [[1e-4, "****"], [1e-3, "***"], [1e-2, "**"], [0.05, "*"], [1.0, "n.s."]]
                    annotator.configure(text_format='star', loc='outside', verbose=0, pvalue_thresholds=pvalue_thresholds)
                    annotator.set_pvalues(p_values)
                    annotator.annotate()
            
            self.update_graph_properties(fig, properties)
            
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
        self.main.paired_annotations.clear()
        self.main.regression_line_params = None
        self.main.fit_params = None
        self.update_graph()


    def _draw_paired_plot_seaborn(self, ax, df, col1, col2, properties):
        try:
            plot_df = df[[col1, col2]].dropna().copy()
            if plot_df.empty: return None
            plot_df['ID'] = range(len(plot_df))
            plot_df_long = pd.melt(plot_df, id_vars='ID', value_vars=[col1, col2], var_name='Condition', value_name='Value')
            
            # 1. 専用のラベルを取得（なければ元の列名を使用）
            label1 = properties.get('paired_label1') or col1
            label2 = properties.get('paired_label2') or col2
            
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
            
            mean_df = plot_df_long.groupby('Condition')['Value'].mean().reindex([col1, col2])
            ax.plot(mean_df.index, mean_df.values, color='red', marker='_', markersize=20, mew=2.5, linestyle='None', label='Mean')
            
            # 4. X軸の目盛りラベルを設定
            ax.set_xticks([0, 1])
            ax.set_xticklabels([label1, label2])
            
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