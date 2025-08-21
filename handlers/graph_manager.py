# graph_manager.py

import numpy as np
import pandas as pd
from PySide6.QtWidgets import QFileDialog, QMessageBox

class GraphManager:
    """
    グラフの描画と更新に関する全てのロジックを担当するクラス。
    """
    def __init__(self, main_window):
        """
        GraphManagerを初期化します。

        Args:
            main_window (MainWindow): メインウィンドウのインスタンス。
        """
        self.main = main_window

    def update_graph(self):
        """
        現在の設定に基づいてグラフ全体を再描画する。
        """
        if not hasattr(self.main, 'model') or self.main.model is None:
            return

        df = self.main.model._data
        ax = self.main.graph_widget.ax
        ax.clear()
        
        properties = self.main.properties_panel.get_properties()
        data_settings = self.main.properties_panel.data_tab.get_current_settings()
        
        bar_categories, bar_x_indices = None, None
        paired_categories, paired_x_indices = None, None
        
        if self.main.current_graph_type == 'scatter':
            y_col = data_settings.get('y_col')
            x_col = data_settings.get('x_col')
            if not y_col or not x_col:
                self.main.graph_widget.canvas.draw()
                return
                
            marker_style = properties.get('marker_style', 'o')
            single_color = self.main.properties_panel.format_tab.current_color
            self._draw_scatter_plot(ax, df, x_col, y_col, marker_style, single_color, properties)

        elif self.main.current_graph_type == 'bar':
            y_col = data_settings.get('y_col')
            x_col = data_settings.get('x_col')
            subgroup_col = data_settings.get('subgroup_col')
            if not y_col or not x_col:
                self.main.graph_widget.canvas.draw()
                return

            single_color = self.main.properties_panel.format_tab.current_color
            subgroup_colors_map = self.main.properties_panel.format_tab.subgroup_colors
            show_scatter = self.main.properties_panel.format_tab.scatter_overlay_check.isChecked()
            
            self.main.fit_params = None 
            self.main.regression_line_params = None
            bar_categories, bar_x_indices = self._draw_bar_chart(ax, df, x_col, y_col, subgroup_col, single_color, subgroup_colors_map, show_scatter, properties)

        elif self.main.current_graph_type == 'paired_scatter':
            self.main.fit_params = None
            self.main.regression_line_params = None
            col1 = data_settings.get('col1')
            col2 = data_settings.get('col2')
            if col1 and col2 and col1 != col2:
                # _draw_paired_plot から返り値を受け取る
                paired_categories, paired_x_indices = self._draw_paired_plot(ax, df, col1, col2, properties)

        # 回帰直線とフィッティング曲線
        linestyle = properties.get('linestyle', '-')
        linewidth = properties.get('linewidth', 1.5)
        if self.main.regression_line_params:
            params = self.main.regression_line_params
            ax.plot(params["x_line"], params["y_line"], color='red', label=f'R² = {params["r_squared"]:.4f}', linestyle=linestyle, linewidth=linewidth)
        
            current_x_col = self.main.properties_panel.data_tab.tidy_tab.x_axis_combo.currentText()
            current_y_col = self.main.properties_panel.data_tab.tidy_tab.y_axis_combo.currentText()
            if self.main.fit_params and self.main.fit_params['x_col'] == current_x_col and self.main.fit_params['y_col'] == current_y_col:
                x_data = self.main.fit_params['log_x_data']
                x_fit = np.linspace(x_data.min(), x_data.max(), 200)
                y_fit = self.main.action_handler.sigmoid_4pl(x_fit, *self.main.fit_params['params'])
                r_squared = self.main.fit_params['r_squared']
                ax.plot(10**x_fit, y_fit, color='blue', label=f'4PL Fit (R²={r_squared:.3f})', linestyle=linestyle, linewidth=linewidth)

        if self.main.current_graph_type == 'bar' and bar_categories is not None:
            ax.set_xticks(bar_x_indices)
            ax.set_xticklabels(bar_categories, rotation=0)
        # paired_scatter のための条件分岐を追加
        elif self.main.current_graph_type == 'paired_scatter' and paired_categories is not None:
            ax.set_xticks(paired_x_indices)
            ax.set_xticklabels(paired_categories)
            # xlimの設定もこちらに移動
            ax.set_xlim(-0.5, 1.5)

        self.main.graph_widget.fig.tight_layout()
        self.main.graph_widget.canvas.draw()

    def update_graph_properties(self):
        """プロパティパネルから現在の全設定を取得し、グラフに適用する。"""
        if not hasattr(self.main, 'model') or self.main.model is None:
            return
        properties = self.main.properties_panel.get_properties()
        ax = self.main.graph_widget.ax
        
        ax.set_title(properties.get('title', ''), fontsize=properties.get('title_fontsize', 16))
        ax.set_xlabel(properties.get('xlabel', ''), fontsize=properties.get('xlabel_fontsize', 12))
        ax.set_ylabel(properties.get('ylabel', ''), fontsize=properties.get('ylabel_fontsize', 12))
        ax.tick_params(axis='both', which='major', labelsize=properties.get('ticks_fontsize', 10))

        # ユーザーが値を入力した場合のみ、軸の範囲を設定する。
        # elseブロックのautoscale呼び出しを削除し、Matplotlibのデフォルトに任せる。
        try:
            ymin = float(properties['ymin']) if properties['ymin'] else None
            ymax = float(properties['ymax']) if properties['ymax'] else None
            if ymin is not None and ymax is not None:
                ax.set_ylim(ymin, ymax)
        except (ValueError, TypeError):
            pass # 不正な入力は無視
        
        if self.main.current_graph_type not in ['bar', 'paired_scatter']:
            try:
                xmin = float(properties['xmin']) if properties['xmin'] else None
                xmax = float(properties['xmax']) if properties['xmax'] else None
                if xmin is not None and xmax is not None:
                    ax.set_xlim(xmin, xmax)
            except (ValueError, TypeError):
                pass
        
        ax.grid(properties.get('show_grid', False))
        
        # スケール
        if self.main.current_graph_type in ['bar', 'paired_scatter']:
            ax.set_xscale('linear')
        elif self.main.fit_params and self.main.fit_params['x_col'] == self.main.properties_panel.data_tab.tidy_tab.x_axis_combo.currentText():
            ax.set_xscale('log')
        else:
            ax.set_xscale('log' if properties.get('x_log_scale') else 'linear')
        
        ax.set_yscale('log' if properties.get('y_log_scale') else 'linear')
        
        if properties.get('hide_top_right_spines', True):
            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)
        else:
            ax.spines['right'].set_visible(True)
            ax.spines['top'].set_visible(True)

        if ax.get_legend_handles_labels()[1]:
            ax.legend()

        self.main.graph_widget.fig.tight_layout()
        self.main.graph_widget.canvas.draw()

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

    # --- Private Drawing Helpers ---

    def _draw_scatter_plot(self, ax, df, x_col, y_col, marker_style, color, properties):
        color_to_plot = color if color else '#1f77b4'
        edgecolor = properties.get('marker_edgecolor', 'black')
        linewidth = properties.get('marker_edgewidth', 1.0)
        if pd.api.types.is_numeric_dtype(df[y_col]) and pd.api.types.is_numeric_dtype(df[x_col]):
            ax.scatter(df[x_col], df[y_col], marker=marker_style, color=color_to_plot, edgecolors=edgecolor, linewidths=linewidth)
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)

    def _draw_bar_chart(self, ax, df, x_col, y_col, subgroup_col, single_color, subgroup_colors_map, show_scatter, properties):
        try:
            categories = sorted(df[x_col].unique())
            x_indices = np.arange(len(categories))
            if subgroup_col:
                self._draw_grouped_bar_chart(ax, df, x_col, y_col, subgroup_col, categories, x_indices, subgroup_colors_map, show_scatter, properties)
            else:
                self._draw_simple_bar_chart(ax, df, x_col, y_col, categories, x_indices, single_color, show_scatter, properties)
            ax.set_xlabel(properties.get('xlabel') or x_col)
            ax.set_ylabel(properties.get('ylabel') or f"Mean of {y_col}")
            return categories, x_indices
        except Exception as e:
            print(f"Could not generate bar chart: {e}")
            return None, None

    def _draw_simple_bar_chart(self, ax, df, x_col, y_col, categories, x_indices, color, show_scatter, properties):
        summary = df.groupby(x_col)[y_col].agg(['mean', 'std']).reindex(categories)
        color_to_plot = color if color else '#1f77b4'
        capsize = properties.get('capsize', 4)
        edgecolor = properties.get('bar_edgecolor', 'black')
        linewidth = properties.get('bar_edgewidth', 1.0)
        ax.bar(x_indices, summary['mean'], width=0.8, yerr=summary['std'], capsize=capsize, color=color_to_plot, edgecolor=edgecolor, linewidth=linewidth)
        if show_scatter:
            for i, cat in enumerate(categories):
                points = df[df[x_col] == cat][y_col]
                jitter = np.random.uniform(-0.15, 0.15, len(points))
                ax.scatter(i + jitter, points, color='black', alpha=0.6, zorder=2)

    def _draw_grouped_bar_chart(self, ax, df, x_col, y_col, subgroup_col, categories, x_indices, subgroup_colors_map, show_scatter, properties):
        """サブグループ化された棒グラフを描画する。"""
        subcategories = sorted(df[subgroup_col].unique())
        n_subgroups = len(subcategories)
        bar_width = 0.8
        sub_bar_width = bar_width / n_subgroups

        capsize = properties.get('capsize', 4)
        edgecolor = properties.get('bar_edgecolor', 'black')
        linewidth = properties.get('bar_edgewidth', 1.0)
       
        for i, subcat in enumerate(subcategories):
            offsets = (i - (n_subgroups - 1) / 2.) * sub_bar_width
            bar_positions = x_indices + offsets

            means = []
            stds = []
            for cat in categories:
                subset = df[(df[x_col] == cat) & (df[subgroup_col] == subcat)][y_col]
                means.append(subset.mean())
                stds.append(subset.std())
            
            color = subgroup_colors_map.get(subcat)
            ax.bar(bar_positions, means, width=sub_bar_width * 0.9, yerr=stds, 
                   label=subcat, capsize=capsize, color=color,
                   edgecolor=edgecolor, linewidth=linewidth)
            if show_scatter:
                for k, cat in enumerate(categories):
                    points = df[(df[x_col] == cat) & (df[subgroup_col] == subcat)][y_col]
                    jitter_width = sub_bar_width * 0.4
                    jitter = np.random.uniform(-jitter_width / 2, jitter_width / 2, len(points))
                    ax.scatter(bar_positions[k] + jitter, points, color='black', alpha=0.6, zorder=2)
        
        ax.legend(title=subgroup_col)

    def _draw_paired_plot(self, ax, df, col1, col2, properties):
        """ペアデータの散布図を描画する。"""
        try:
            plot_df = df[[col1, col2]].dropna().copy()
            if plot_df.empty:
                QMessageBox.warning(self.main, "Warning", "No valid paired data to plot.")
                return

            label1 = properties.get('paired_label1') or col1
            label2 = properties.get('paired_label2') or col2
            categories = [label1, label2]
            x_indices = [0, 1]

            # フォーマットタブからプロパティを取得
            marker_style = properties.get('marker_style', 'o')
            marker_edgecolor = properties.get('marker_edgecolor', 'black')
            marker_edgewidth = properties.get('marker_edgewidth', 1.0)
            
            mean_linestyle = properties.get('linestyle', '--')
            mean_linewidth = properties.get('linewidth', 2)

            # 取得したプロパティを描画に適用
            for index, row in plot_df.iterrows():
                ax.plot(x_indices, [row[col1], row[col2]], 
                        color='gray', 
                        marker=marker_style, 
                        linestyle='-', 
                        alpha=0.5,
                        markeredgecolor=marker_edgecolor,
                        markeredgewidth=marker_edgewidth)

            mean1 = plot_df[col1].mean()
            mean2 = plot_df[col2].mean()
            ax.plot(x_indices, [mean1, mean2], 
                    color='red', 
                    marker=marker_style, 
                    linestyle=mean_linestyle, 
                    linewidth=mean_linewidth, 
                    label="Mean",
                    markeredgecolor=marker_edgecolor,
                    markeredgewidth=marker_edgewidth)

            ax.set_xlabel(properties.get('xlabel', 'Condition'))
            ax.set_ylabel(properties.get('ylabel', 'Value'))
            
            ax.legend()
            
            return categories, x_indices

        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to draw paired plot: {e}")
            return None, None
        
    def _draw_annotations(self):
        """統計的有意差のアノテーションを描画する。"""
        if self.main.current_graph_type != 'bar' or not hasattr(self.main, 'model') or not self.main.statistical_annotations:
            return

        ax = self.main.graph_widget.ax
        df = self.main.model._data
        
        base_group_col = self.main.statistical_annotations[0].get('group_col')
        if not base_group_col or base_group_col not in df.columns: return
            
        categories = sorted([str(c) for c in df[base_group_col].unique()])
        occupied_levels = {cat: -1 for cat in categories}

        def get_span(annotation):
            try:
                g1, g2 = annotation['groups']
                idx1, idx2 = categories.index(str(g1)), categories.index(str(g2))
                return abs(idx1 - idx2)
            except (ValueError, KeyError):
                return float('inf')
        sorted_annotations = sorted(self.main.statistical_annotations, key=get_span)

        max_bar_y = 0
        df_str_group = df.copy()
        df_str_group[base_group_col] = df_str_group[base_group_col].astype(str)
        value_col_for_max = self.main.statistical_annotations[0]['value_col']
        for cat in categories:
            cat_data = df_str_group[df_str_group[base_group_col] == cat][value_col_for_max].dropna()
            if not cat_data.empty:
                mean = cat_data.mean()
                std = cat_data.std() if pd.notna(cat_data.std()) else 0
                max_bar_y = max(max_bar_y, mean + std)

        y_range = ax.get_ylim()[1] - ax.get_ylim()[0]
        level_height = y_range * 0.15
        highest_annotation_y = 0

        for annotation in sorted_annotations:
            group_col, value_col = annotation['group_col'], annotation['value_col']
            group1_name, group2_name = annotation['groups']
            p_value = annotation['p_value']
            if group_col != base_group_col: continue
            try:
                g1_str, g2_str = str(group1_name), str(group2_name)
                idx1, idx2 = categories.index(g1_str), categories.index(g2_str)
                x1, x2 = min(idx1, idx2), max(idx1, idx2)
            except ValueError: continue

            level_check_range = categories[x1:x2+1]
            max_level_in_span = max(occupied_levels[cat] for cat in level_check_range)
            new_level = max_level_in_span + 1
            
            initial_gap_from_bar = level_height * 0.3
            base_y = max_bar_y + initial_gap_from_bar + (new_level * level_height)
            bracket_y = base_y + (level_height * 0.2)
            text_y = bracket_y + (level_height * 0.05)
            highest_annotation_y = max(highest_annotation_y, text_y)

            if p_value < 0.001: significance = '***'
            elif p_value < 0.01: significance = '**'
            elif p_value < 0.05: significance = '*'
            else: significance = 'ns'

            ax.plot([x1, x1, x2, x2], [base_y, bracket_y, bracket_y, base_y], lw=1.5, c='black')
            ax.text((x1 + x2) * 0.5, text_y, significance, ha='center', va='bottom', fontsize=14)

            for i in range(x1, x2 + 1):
                occupied_levels[categories[i]] = new_level

        if highest_annotation_y > 0:
            current_ylim = ax.get_ylim()
            if highest_annotation_y > current_ylim[1]:
                new_ylim_top = highest_annotation_y + (level_height * 0.2)
                ax.set_ylim(current_ylim[0], new_ylim_top)