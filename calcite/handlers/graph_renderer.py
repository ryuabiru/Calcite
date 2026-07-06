from __future__ import annotations

import traceback

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import seaborn as sns
from PySide6.QtWidgets import QMessageBox
from statannotations.Annotator import Annotator
from statsmodels.graphics.mosaicplot import mosaic

from calcite.models import PlotRequest
from calcite.services.plot_service import (
    BASE_PLOT_KINDS,
    build_annotation_spec,
    build_base_plot_kwargs,
    build_facet_plot_data,
    build_heatmap_plot_data,
    build_mosaic_plot_data,
    build_stacked_bar_plot_data,
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
    prepare_plot_dataframe,
)


class GraphRenderer:
    def __init__(self, main_window):
        self.main = main_window

    def render_categorical_plot(self, df, request: PlotRequest):
        properties = request.properties
        current_x = request.x_col
        current_y = request.y_col
        if not current_x or (request.graph_type != "countplot" and not current_y):
            return None

        base_kind = request.graph_type
        visual_hue_col = request.subgroup_col or None
        facet_col = request.facet_col

        try:
            df_processed = prepare_plot_dataframe(df, request)
            x_order = get_x_order(df_processed, request)
            col_categories = get_facet_values(df_processed, request)
            n_rows, n_cols = 1, len(col_categories)

            fig, axes = plt.subplots(
                n_rows, n_cols, figsize=(n_cols * 5, n_rows * 4), sharex=False, sharey=True, squeeze=False, layout="constrained"
            )
            all_relevant_annotations = [
                ann for ann in self.main.app_state.statistical_annotations if ann.get("value_col") == current_y
            ]
            if request.graph_type == "countplot":
                all_relevant_annotations = []
            facet_plot_data = build_facet_plot_data(df_processed, request)

            for j, facet_data in enumerate(facet_plot_data):
                ax = axes[0, j]
                col_cat = facet_data.facet_value
                original_subset_df = facet_data.source_df
                if original_subset_df.empty:
                    ax.set_title(f"No data for {col_cat}")
                    continue

                plot_df = facet_data.plot_df
                self._draw_base_plot(ax, base_kind, request, plot_df, original_subset_df, x_order, properties)
                self._apply_facet_axis_state(ax, j, facet_col, col_cat)
                annotations_for_this_facet = [
                    ann for ann in all_relevant_annotations if ann.get("facet_value") == (col_cat if facet_col else None)
                ]
                hue_order = sorted(df_processed[visual_hue_col].unique()) if visual_hue_col else None
                self._apply_annotations(ax, df_processed, properties, hue_order, annotations_for_this_facet)

            self._apply_shared_legend(fig, axes, df_processed, request, properties, visual_hue_col)
            self._apply_shared_xlabel(fig, axes, n_cols > 1, current_x, properties)
            self._apply_overlay_lines_if_needed(axes, base_kind, n_cols > 1, properties)
            return fig
        except Exception as e:
            QMessageBox.critical(self.main, "Graph Error", f"An unexpected error occurred: {e}")
            traceback.print_exc()
            return None

    def render_paired_scatter(self, df, request: PlotRequest):
        properties = request.properties
        paired_plot_data = build_paired_plot_data(df, request)
        if paired_plot_data is None:
            return None

        col1 = request.col1
        col2 = request.col2
        fig, ax = plt.subplots(layout="constrained")
        try:
            plot_df_long = self._draw_paired_plot(ax, paired_plot_data, properties)
            if plot_df_long is not None and self.main.app_state.paired_annotations:
                annotations_to_plot = [
                    ann for ann in self.main.app_state.paired_annotations if set(ann["box_pair"]) == {col1, col2}
                ]
                annotation_spec = build_paired_annotation_spec(plot_df_long, annotations_to_plot, ax)
                if annotation_spec is not None:
                    annotator = Annotator(**annotation_spec.annotator_kwargs)
                    thresholds = [[1e-4, "****"], [1e-3, "***"], [1e-2, "**"], [0.05, "*"], [1.0, "n.s."]]
                    annotator.configure(text_format="star", loc="outside", verbose=0, pvalue_thresholds=thresholds)
                    annotator.set_pvalues(annotation_spec.p_values)
                    annotator.annotate()
            return fig
        except Exception as e:
            QMessageBox.critical(self.main, "Error", f"Failed to draw paired plot: {e}")
            return None

    def render_histogram(self, df, properties, data_settings):
        value_col = data_settings.get("y_col")
        if not value_col:
            return None
        hue_col = data_settings.get("subgroup_col") or None
        fig, ax = plt.subplots(layout="constrained")
        plot_kwargs = {}
        if hue_col:
            df[hue_col] = df[hue_col].astype(str)
            plot_kwargs["palette"] = {str(k): v for k, v in properties.get("subgroup_colors", {}).items()}
        else:
            plot_kwargs["color"] = properties.get("single_color")
        try:
            sns.histplot(data=df, x=value_col, hue=hue_col, ax=ax, **plot_kwargs)
            return fig
        except Exception:
            traceback.print_exc()
            return None

    def render_heatmap(self, df, request: PlotRequest):
        if not request.x_col or not request.y_col:
            return None

        try:
            df_processed = df.copy()
            df_processed[request.x_col] = df_processed[request.x_col].astype(str)
            df_processed[request.y_col] = df_processed[request.y_col].astype(str)
            heatmap_plot_data = build_heatmap_plot_data(df_processed, request)
            n_cols = max(len(heatmap_plot_data), 1)
            fig, axes = plt.subplots(
                1,
                n_cols,
                figsize=(n_cols * 5, 4),
                squeeze=False,
                layout="constrained",
            )

            for j, heatmap_data in enumerate(heatmap_plot_data):
                ax = axes[0, j]
                if heatmap_data.matrix.empty:
                    ax.set_title(f"No data for {heatmap_data.facet_value}")
                    ax.axis("off")
                    continue

                sns.heatmap(
                    heatmap_data.matrix,
                    ax=ax,
                    annot=True,
                    fmt=".0f",
                    cmap="Blues",
                    cbar=(j == n_cols - 1),
                )
                ax.set_xlabel(request.x_col)
                ax.set_ylabel(request.y_col)
                if request.facet_col:
                    ax.set_title(str(heatmap_data.facet_value))

            return fig
        except Exception as e:
            QMessageBox.critical(self.main, "Graph Error", f"An unexpected error occurred: {e}")
            traceback.print_exc()
            return None

    def render_correlation_heatmap(self, df, properties):
        numeric_df = df.select_dtypes(include="number")
        if numeric_df.shape[1] < 2:
            return None

        try:
            corr_matrix = numeric_df.corr(method="pearson")
            fig, ax = plt.subplots(layout="constrained")
            sns.heatmap(
                corr_matrix,
                ax=ax,
                annot=True,
                fmt=".2f",
                cmap="coolwarm",
                vmin=-1,
                vmax=1,
                center=0,
                square=True,
            )
            ax.set_xlabel("")
            ax.set_ylabel("")
            return fig
        except Exception as e:
            QMessageBox.critical(self.main, "Graph Error", f"An unexpected error occurred: {e}")
            traceback.print_exc()
            return None

    def render_stacked_bar(self, df, request: PlotRequest):
        if not request.x_col:
            return None

        try:
            df_processed = prepare_plot_dataframe(df, request)
            stacked_plot_data = build_stacked_bar_plot_data(df_processed, request)
            n_cols = max(len(stacked_plot_data), 1)
            fig, axes = plt.subplots(1, n_cols, figsize=(n_cols * 5, 4), squeeze=False, layout="constrained")
            palette = request.properties.get("subgroup_colors", {})

            for j, stacked_data in enumerate(stacked_plot_data):
                ax = axes[0, j]
                matrix = stacked_data.matrix
                if matrix.empty:
                    ax.set_title(f"No data for {stacked_data.facet_value}")
                    continue

                bottom = None
                for column in matrix.columns:
                    values = matrix[column].to_numpy()
                    color = palette.get(str(column))
                    ax.bar(
                        matrix.index,
                        values,
                        bottom=bottom,
                        label=str(column),
                        color=color,
                        edgecolor=request.properties.get("bar_edgecolor", "black"),
                        linewidth=request.properties.get("bar_edgewidth", 1.0),
                    )
                    bottom = values if bottom is None else bottom + values

                if request.graph_type == "stacked_bar_100":
                    ax.set_ylim(0, 1)
                    ax.set_ylabel("Proportion")
                else:
                    ax.set_ylabel("Count")
                ax.set_xlabel(request.x_col)
                if request.facet_col:
                    ax.set_title(str(stacked_data.facet_value))

            if request.subgroup_col:
                handles, labels = axes[0, -1].get_legend_handles_labels()
                if handles and request.properties.get("legend_position") != "hide":
                    axes[0, -1].legend(
                        handles=handles,
                        labels=labels,
                        title=request.properties.get("legend_title") or request.subgroup_col,
                        loc=request.properties.get("legend_position", "best"),
                    )
            return fig
        except Exception as e:
            QMessageBox.critical(self.main, "Graph Error", f"An unexpected error occurred: {e}")
            traceback.print_exc()
            return None

    def render_mosaic(self, df, request: PlotRequest):
        if not request.x_col or not request.subgroup_col:
            return None

        try:
            df_processed = prepare_plot_dataframe(df, request)
            mosaic_plot_data = build_mosaic_plot_data(df_processed, request)
            n_cols = max(len(mosaic_plot_data), 1)
            fig, axes = plt.subplots(1, n_cols, figsize=(n_cols * 5, 4), squeeze=False, layout="constrained")
            palette = request.properties.get("subgroup_colors", {})

            for j, mosaic_data in enumerate(mosaic_plot_data):
                ax = axes[0, j]
                if not mosaic_data.counts:
                    ax.set_title(f"No data for {mosaic_data.facet_value}")
                    ax.axis("off")
                    continue

                def _properties(key):
                    subgroup = key[1]
                    return {"color": palette.get(str(subgroup), None)}

                mosaic(mosaic_data.counts, ax=ax, properties=_properties, gap=0.01, labelizer=lambda _: "")
                ax.set_xlabel(request.x_col)
                ax.set_ylabel(request.subgroup_col)
                if request.facet_col:
                    ax.set_title(str(mosaic_data.facet_value))

            handles = [
                mpatches.Patch(color=palette.get(subgroup, "gray"), label=subgroup)
                for subgroup in mosaic_plot_data[0].subgroups
            ] if mosaic_plot_data else []
            if handles and request.properties.get("legend_position") != "hide":
                axes[0, -1].legend(
                    handles=handles,
                    title=request.properties.get("legend_title") or request.subgroup_col,
                    loc=request.properties.get("legend_position", "best"),
                )
            return fig
        except Exception as e:
            QMessageBox.critical(self.main, "Graph Error", f"An unexpected error occurred: {e}")
            traceback.print_exc()
            return None

    def apply_graph_properties(self, fig, properties):
        fig.suptitle(properties.get("title", ""), fontsize=properties.get("title_fontsize", 16))
        is_faceted = len(fig.axes) > 1
        axis_linewidth = properties.get("axis_linewidth", 1.0)
        tick_length = properties.get("tick_length", 4.0)
        tick_direction = properties.get("tick_direction", "out")

        for ax in fig.axes:
            if not is_faceted:
                ax.set_xlabel(properties.get("xlabel") or ax.get_xlabel(), fontsize=properties.get("xlabel_fontsize", 15))
            ax.set_ylabel(properties.get("ylabel") or ax.get_ylabel(), fontsize=properties.get("ylabel_fontsize", 15))
            ax.tick_params(
                axis="both",
                which="major",
                labelsize=properties.get("ticks_fontsize", 12),
                width=axis_linewidth,
                length=tick_length,
                direction=tick_direction,
            )
            for spine in ax.spines.values():
                spine.set_linewidth(axis_linewidth)
            if properties.get("hide_top_right_spines", True):
                ax.spines["right"].set_visible(False)
                ax.spines["top"].set_visible(False)
            ax.grid(properties.get("show_grid", False))
            if properties.get("x_log_scale"):
                ax.set_xscale("log")
            if properties.get("y_log_scale"):
                ax.set_yscale("log")

    def _draw_base_plot(self, ax, base_kind, request, plot_df, original_subset_df, x_order, properties):
        base_plot_map = {
            "bar": sns.barplot,
            "countplot": sns.barplot,
            "boxplot": sns.boxplot,
            "violin": sns.violinplot,
            "pointplot": sns.pointplot,
            "lineplot": sns.lineplot,
        }
        if base_kind in base_plot_map:
            base_kwargs = build_base_plot_kwargs(request, plot_df, x_order, properties)
            base_kwargs["ax"] = ax
            base_plot_map[base_kind](**base_kwargs)

        if base_kind in ["scatter", "summary_scatter"]:
            scatter_kwargs = build_scatter_plot_kwargs(request, plot_df, properties)
            scatter_kwargs["ax"] = ax
            sns.scatterplot(**scatter_kwargs)
            if base_kind == "summary_scatter":
                for errorbar_spec in build_summary_errorbar_specs(plot_df, request, properties):
                    ax.errorbar(**errorbar_spec)

        if (
            properties.get("scatter_overlay")
            and (base_kind in BASE_PLOT_KINDS)
            and base_kind != "countplot"
            and not original_subset_df.empty
        ):
            stripplot_kwargs = build_stripplot_kwargs(request, original_subset_df, x_order, properties)
            stripplot_kwargs["ax"] = ax
            sns.stripplot(**stripplot_kwargs)

    def _apply_facet_axis_state(self, ax, index, facet_col, facet_value):
        title_parts = []
        if facet_col:
            title_parts.append(f"{facet_value}")
        ax.set_title(" | ".join(title_parts))
        if index > 0:
            bottom, top = ax.get_ylim()
            extension = (top - bottom) * 0.10
            ax.spines["left"].set_bounds(bottom - extension, top)

    def _apply_annotations(self, ax, df, data_settings, hue_order, annotations_to_plot):
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
            thresholds = [[1e-4, "****"], [1e-3, "***"], [1e-2, "**"], [0.05, "*"], [1.0, "n.s."]]
            annotator.configure(text_format="star", loc="inside", verbose=0, pvalue_thresholds=thresholds)
            annotator.set_pvalues(annotation_spec.p_values)
            annotator.annotate()
        except Exception:
            traceback.print_exc()

    def _apply_shared_legend(self, fig, axes, df_processed, request, properties, visual_hue_col):
        if not visual_hue_col:
            return
        for ax in axes.flat:
            if ax.get_legend() is not None:
                ax.get_legend().remove()
        handles, labels = build_legend_handles_labels(df_processed, request, properties, axes.flat)
        if properties.get("legend_position") != "hide" and handles:
            target_ax = axes.flat[-1]
            target_ax.legend(
                handles=handles,
                labels=labels,
                title=properties.get("legend_title") or visual_hue_col,
                loc=properties.get("legend_position", "best"),
            )

    def _apply_shared_xlabel(self, fig, axes, is_faceted, current_x, properties):
        if not is_faceted:
            return
        shared_xlabel = properties.get("xlabel") or current_x
        for ax in axes.flat:
            ax.set_xlabel("")
        fig.supxlabel(shared_xlabel, fontsize=properties.get("xlabel_fontsize", 15))

    def _apply_overlay_lines_if_needed(self, axes, base_kind, is_faceted, properties):
        if base_kind not in ["scatter", "summary_scatter"] or is_faceted:
            return
        ax = axes[0, 0]
        overlay_lines = build_regression_overlay_lines(self.main.app_state.regression_line_params, properties)
        overlay_lines.extend(build_four_pl_overlay_lines(self.main.app_state.fit_params, properties))
        for overlay_line in overlay_lines:
            ax.plot(
                overlay_line.x,
                overlay_line.y,
                color=overlay_line.color,
                linestyle=properties.get("linestyle", "--"),
                linewidth=properties.get("linewidth", 1.5),
                label=overlay_line.label,
            )
        if overlay_lines:
            ax.legend()

    def _draw_paired_plot(self, ax, paired_plot_data, properties):
        plot_df_long = paired_plot_data.plot_df_long
        sns.lineplot(
            data=plot_df_long,
            x="Condition",
            y="Value",
            units="ID",
            estimator=None,
            color="gray",
            alpha=0.5,
            ax=ax,
            linestyle=properties.get("linestyle", "-"),
            linewidth=properties.get("linewidth", 1.5),
        )
        sns.scatterplot(
            data=plot_df_long,
            x="Condition",
            y="Value",
            color=properties.get("single_color", "black"),
            marker=properties.get("marker_style", "o"),
            edgecolor=properties.get("marker_edgecolor", "black"),
            linewidth=properties.get("marker_edgewidth", 1.0),
            ax=ax,
            legend=False,
        )
        ax.plot(
            paired_plot_data.mean_x,
            paired_plot_data.mean_y.values,
            color="red",
            marker="_",
            markersize=20,
            mew=2.5,
            linestyle="None",
            label="Mean",
        )
        ax.set_xticks([0, 1])
        ax.set_xticklabels(paired_plot_data.tick_labels)
        ax.set_xlabel("")
        handles, labels = ax.get_legend_handles_labels()
        if handles:
            legend_pos = properties.get("legend_position", "best")
            if legend_pos == "best":
                ax.legend(handles=handles, labels=labels, loc="upper left", bbox_to_anchor=(1.02, 1))
            else:
                ax.legend(handles=handles, labels=labels, loc=legend_pos)
        return plot_df_long
