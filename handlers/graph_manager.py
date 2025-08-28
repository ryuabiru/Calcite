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

        base_kind = self.main.current_graph_type
        visual_hue_col = data_settings.get('subgroup_col')
        if not visual_hue_col:
            visual_hue_col = None
        
        # 分析上のhueは、X軸と異なる場合のみ意味を持つ
        analysis_hue_col = visual_hue_col if visual_hue_col != current_x else None
        facet_col = data_settings.get('facet_col')

        try:
            df_processed = df.copy()
            if visual_hue_col:
                df_processed[visual_hue_col] = df_processed[visual_hue_col].astype(str)
            if base_kind not in ['scatter', 'summary_scatter', 'lineplot']:
                df_processed[current_x] = df_processed[current_x].astype(str)
            
            x_order = df_processed[current_x].unique()
            print(f"DEBUG: Determined X-axis order: {x_order}")
            
            subgroup_palette = properties.get('subgroup_colors', {})
            col_categories = sorted(df_processed[facet_col].unique()) if facet_col else [None]
            n_rows, n_cols = 1, len(col_categories)

            fig, axes = plt.subplots(
                n_rows, n_cols, figsize=(n_cols * 5, n_rows * 4),
                sharex=False, sharey=True, squeeze=False
            )
            all_relevant_annotations = [ann for ann in self.main.statistical_annotations if ann.get('value_col') == current_y]

            for j, col_cat in enumerate(col_categories):
                ax = axes[0, j]
                facet_selector = pd.Series(True, index=df_processed.index)
                if facet_col: facet_selector &= (df_processed[facet_col] == col_cat)
                original_subset_df = df_processed[facet_selector]

                if original_subset_df.empty:
                    ax.set_title(f"No data for {col_cat}"); continue
                
                plot_df = original_subset_df
                print(f"\n--- Drawing Facet (Col: {col_cat}) ---")

                if base_kind == 'summary_scatter':
                    print("[Layer 1] Preparing data...")
                    group_cols = [current_x]
                    if visual_hue_col and visual_hue_col != current_x: group_cols.append(visual_hue_col)
                    
                    error_agg_func = properties.get('error_bar_type', 'sem') # デフォルトはsem
                    print(f"DEBUG: Using '{error_agg_func}' for error bar calculation.")
                    
                    summary_stats = original_subset_df.groupby(group_cols, as_index=False).agg(
                        mean_y=(current_y, 'mean'),
                        err_y=(current_y, error_agg_func) # ここでsemかstdを切り替え
                    )
                    summary_stats.rename(columns={'mean_y': current_y}, inplace=True)
                    plot_df = summary_stats
                    print(" -> Data summarized.")
                
                base_plot_map = { 'bar': sns.barplot, 'boxplot': sns.boxplot, 'violin': sns.violinplot, 'pointplot': sns.pointplot, 'lineplot': sns.lineplot }
                if base_kind in base_plot_map:
                    print(f"[Layer 2] Drawing Base Plot: {base_kind}")
                    base_kwargs = {'data': plot_df, 'x': current_x, 'y': current_y, 'ax': ax, 'order': x_order}
                    if visual_hue_col:
                        base_kwargs['hue'] = visual_hue_col
                        base_kwargs['palette'] = subgroup_palette
                    else:
                        single_color = properties.get('single_color'); 
                        if single_color: base_kwargs['color'] = single_color
                    if base_kind == 'bar': base_kwargs.update({'edgecolor': properties.get('bar_edgecolor', 'black'), 'linewidth': properties.get('bar_edgewidth', 1.0), 'capsize': properties.get('capsize', 4) * 0.01})
                    if base_kind in ['pointplot', 'lineplot']: base_kwargs.update({'linestyle': properties.get('linestyle', '-'), 'linewidth': properties.get('linewidth', 1.5)})
                    if base_kind == 'pointplot': base_kwargs.update({'capsize': properties.get('capsize', 4) * 0.02})
                    # ★★★ legend=False を削除 ★★★
                    base_plot_map[base_kind](**base_kwargs)

                if base_kind in ['scatter', 'summary_scatter']:
                    print(f"[Layer 3] Drawing Scatter Plot: {base_kind}")
                    scatter_kwargs = {
                        'data': plot_df, 'x': current_x, 'y': current_y, 'ax': ax,
                        'marker': properties.get('marker_style', 'o'),
                        'edgecolor': properties.get('marker_edgecolor', 'black'),
                        'linewidth': properties.get('marker_edgewidth', 1.0),
                        's': properties.get('marker_size', 5.0)**2,
                        'alpha': properties.get('marker_alpha', 1.0),
                        'order': x_order
                    }
                    if visual_hue_col:
                        scatter_kwargs['hue'] = visual_hue_col; scatter_kwargs['palette'] = subgroup_palette
                    else:
                        single_color = properties.get('single_color'); 
                        if single_color: scatter_kwargs['color'] = single_color
                    # ★★★ legend=False を削除 ★★★
                    sns.scatterplot(**scatter_kwargs)
                    if base_kind == 'summary_scatter':
                        if visual_hue_col:
                            for hue_val, grp in plot_df.groupby(visual_hue_col):
                                ax.errorbar(x=grp[current_x], y=grp[current_y], yerr=grp['err_y'], fmt='none', capsize=properties.get('capsize', 4), ecolor=subgroup_palette.get(str(hue_val), 'black'))
                        else:
                            ax.errorbar(x=plot_df[current_x], y=plot_df[current_y], yerr=plot_df['err_y'], fmt='none', capsize=properties.get('capsize', 4), ecolor=properties.get('marker_edgecolor', 'black'))
                        print(" -> Added error bars.")

                if properties.get('scatter_overlay') and (base_kind in base_plot_map):
                    print("[Layer 4] Drawing Overlay Points...")
                    if not original_subset_df.empty:
                        # ▼▼▼ サブグループの有無に基づく、必然的な条件分岐を適用します ▼▼▼
                        should_dodge = bool(analysis_hue_col) and base_kind != 'pointplot'
                        
                        print(f"DEBUG: base_kind='{base_kind}', analysis_hue_col='{analysis_hue_col}', should_dodge={should_dodge}")
                        
                        sns.stripplot(
                            data=original_subset_df, x=current_x, y=current_y,
                            hue=visual_hue_col,
                            ax=ax,
                            jitter=True,
                            alpha=properties.get('marker_alpha', 0.6),
                            palette=subgroup_palette,
                            marker=properties.get('marker_style', 'o'),
                            edgecolor=properties.get('marker_edgecolor', 'black'),
                            linewidth=properties.get('marker_edgewidth', 1.0),
                            s=properties.get('marker_size', 5.0),
                            dodge=should_dodge,
                            order=x_order
                        )
                        print(" -> stripplot called with dodge=True.")
                
                title_parts = []; 
                if facet_col: title_parts.append(f"{facet_col} = {col_cat}")
                ax.set_title(" | ".join(title_parts))
                if j > 0:
                    bottom, top = ax.get_ylim(); extension = (top - bottom) * 0.10; ax.spines['left'].set_bounds(bottom - extension, top)
                annotations_for_this_facet = [ann for ann in all_relevant_annotations if ann.get('facet_value') == (col_cat if facet_col else None)]
                hue_order = sorted(df_processed[visual_hue_col].unique()) if visual_hue_col else None
                self.apply_annotations(ax, df_processed, data_settings, hue_order, annotations_for_this_facet)

            # --- 凡例統合レイヤー ---
            if visual_hue_col:
                print("Consolidating legend...")
                handles, labels = [], []

                # --- Step 1: 既存の凡例をすべてクリア ---
                for ax in axes.flat:
                    if ax.get_legend() is not None:
                        ax.get_legend().remove()
                print(" -> All subplot legends cleared.")

                # --- Step 2: グラフタイプに応じて凡例の「部品」を生成 ---
                base_kind = self.main.current_graph_type
                
                # Bar, Box, Violinの場合は、凡例の部品を手動で作成する
                if base_kind in ['bar', 'boxplot', 'violin']:
                    print(" -> Manually creating patch handles for legend.")
                    hue_categories = sorted(df_processed[visual_hue_col].unique())
                    palette = properties.get('subgroup_colors', {})
                    
                    for category in hue_categories:
                        str_category = str(category)
                        color = palette.get(str_category, 'black')
                        patch = mpatches.Patch(color=color, label=str_category)
                        if str_category not in labels:
                            handles.append(patch)
                            labels.append(str_category)

                # それ以外のグラフタイプは、自動生成された部品を収集する
                else:
                    print(" -> Collecting handles from axes.")
                    for ax in axes.flat:
                        h, l = ax.get_legend_handles_labels()
                        for i, label in enumerate(l):
                            if label not in labels:
                                labels.append(label)
                                handles.append(h[i])

                # --- Step 3: 収集・作成した部品を使って凡例を描画 ---
                if properties.get('legend_position') != 'hide' and handles:
                    legend_title = properties.get('legend_title') or visual_hue_col
                    legend_pos = properties.get('legend_position', 'best')
                    legend_alpha = properties.get('legend_alpha', 1.0)

                    target_ax = axes.flat[-1]
                    leg = target_ax.legend(
                        handles=handles, 
                        labels=labels, 
                        title=legend_title,
                        loc=legend_pos
                    )
                    if leg:
                        leg.get_frame().set_alpha(legend_alpha)
                    print(f" -> In-plot legend re-created with alpha={legend_alpha}.")
                else:
                    print(" -> Legend hidden by user setting or no handles found.")

            is_faceted = n_cols > 1
            if is_faceted:
                shared_xlabel = properties.get('xlabel') or current_x;
                for ax in axes.flat: ax.set_xlabel('')
                fig.supxlabel(shared_xlabel, fontsize=properties.get('xlabel_fontsize', 12))

            # ▼▼▼ メソッドの末尾近くにある、このブロックを修正します ▼▼▼
            if base_kind in ['scatter', 'summary_scatter'] and not is_faceted:
                ax = axes[0, 0]

                if self.main.regression_line_params:
                    params_dict = self.main.regression_line_params
                    # サブグループごとに描画するか、単一で描画するかを判断
                    if params_dict and 'x_line' not in params_dict: # サブグループごとのデータ
                        for group_name, params in params_dict.items():
                            color = properties.get('subgroup_colors', {}).get(str(group_name), 'red')
                            ax.plot(params["x_line"], params["y_line"], color=color,
                                    linestyle=properties.get('linestyle', '--'), linewidth=properties.get('linewidth', 1.5),
                                    label=f"{group_name} Fit (R²={params['r_squared']:.3f})")
                        ax.legend()
                    elif 'x_line' in params_dict: # 単一のデータ
                        params = params_dict
                        ax.plot(params["x_line"], params["y_line"], color=properties.get('regression_color', 'red'),
                                linestyle=properties.get('linestyle', '--'), linewidth=properties.get('linewidth', 1.5),
                                label=f"Linear Fit (R²={params['r_squared']:.3f})")
                        ax.legend()

                # ▼▼▼ 4PL非線形回帰の描画ロジックを修正 ▼▼▼
                if self.main.fit_params:
                    params_dict = self.main.fit_params
                    if params_dict and 'params' not in params_dict: # サブグループごとのデータ
                        for group_name, params_info in params_dict.items():
                            fit_params = params_info["params"]
                            x_min, x_max = params_info["log_x_data"].min(), params_info["log_x_data"].max()
                            x_fit = np.linspace(x_min, x_max, 200)
                            y_fit = self.sigmoid_4pl(x_fit, *fit_params)
                            color = properties.get('subgroup_colors', {}).get(str(group_name), 'red')
                            
                            ax.plot(10**x_fit, y_fit, color=color,
                                    linestyle=properties.get('linestyle', '--'), linewidth=properties.get('linewidth', 1.5),
                                    label=f"{group_name} 4PL (R²={params_info['r_squared']:.3f})")
                        ax.legend()
                    elif 'params' in params_dict: # 単一のデータ
                        params_info = params_dict
                        fit_params = params_info["params"]
                        x_min, x_max = params_info["log_x_data"].min(), params_info["log_x_data"].max()
                        x_fit = np.linspace(x_min, x_max, 200)
                        y_fit = self.sigmoid_4pl(x_fit, *fit_params)
                        
                        ax.plot(10**x_fit, y_fit, color=properties.get('regression_color', 'red'),
                                linestyle=properties.get('linestyle', '--'), linewidth=properties.get('linewidth', 1.5),
                                label=f"4PL Fit (R²={params_info['r_squared']:.3f})")
                        ax.legend()
            
            return fig
        except Exception as e:
            QMessageBox.critical(self.main, "Graph Error", f"An unexpected error occurred: {e}")
            print(f"Graph drawing error: {e}"); traceback.print_exc()
            return None


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


    def replace_canvas(self, new_fig):
        """
        古いFigureCanvasをウィジェットから削除し、新しいものに置き換える。
        """
        # --- デバッグ用のprint文 ---
        print("Replacing canvas with new figure...")
        
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
        
        print(" -> Canvas replaced successfully.")


    def update_graph_properties(self, fig, properties):
        """
        UIパネルの設定に基づいて、FigureとAxesの見た目を更新する。
        """
        print("Updating graph properties (titles, labels, etc.)...") # デバッグ用
        
        fig.suptitle(properties.get('title', ''), fontsize=properties.get('title_fontsize', 16))
        
        is_faceted = len(fig.axes) > 1

        for ax in fig.axes:
            # ファセットグラフではない場合にのみ、個別のX軸ラベルを設定する
            if not is_faceted:
                ax.set_xlabel(properties.get('xlabel') or ax.get_xlabel(), fontsize=properties.get('xlabel_fontsize', 12))
            
            # Y軸ラベルは常に個別で設定
            ax.set_ylabel(properties.get('ylabel') or ax.get_ylabel(), fontsize=properties.get('ylabel_fontsize', 12))
            
            ax.tick_params(axis='both', which='major', labelsize=properties.get('ticks_fontsize', 10))
            if properties.get('hide_top_right_spines', True):
                ax.spines['right'].set_visible(False); ax.spines['top'].set_visible(False)
            ax.grid(properties.get('show_grid', False))
            if properties.get('x_log_scale'): ax.set_xscale('log')
            if properties.get('y_log_scale'): ax.set_yscale('log')
            
        # 凡例などを考慮してレイアウトを自動調整
        print("DEBUG: Calling fig.tight_layout() with padding.")
        fig.tight_layout(pad=1.5)


    def clear_canvas(self):
        if hasattr(self.main.graph_widget, 'canvas') and self.main.graph_widget.canvas:
            self.main.graph_widget.canvas.figure.clear()
            self.main.graph_widget.canvas.draw()
            print("DEBUG: Canvas cleared.") # デバッグ用


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
        print("DEBUG: Clearing graph and resetting all plot states.")
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
        print("DEBUG: Clearing only annotations and redrawing graph.")
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