from __future__ import annotations

from dataclasses import dataclass

import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

from calcite.models import PlotRequest


def normalize_plot_request(request: PlotRequest) -> PlotRequest:
    subgroup_col = request.subgroup_col
    if subgroup_col == request.x_col:
        subgroup_col = ""

    return PlotRequest(
        graph_type=request.graph_type,
        x_col=request.x_col,
        y_col=request.y_col,
        subgroup_col=subgroup_col,
        facet_col=request.facet_col,
        col1=request.col1,
        col2=request.col2,
        properties=request.properties,
    )


def prepare_plot_dataframe(df: pd.DataFrame, request: PlotRequest) -> pd.DataFrame:
    df_processed = df.copy()

    if request.subgroup_col:
        df_processed[request.subgroup_col] = df_processed[request.subgroup_col].astype(str)

    if request.graph_type not in ["scatter", "summary_scatter", "lineplot", "correlation_heatmap"] and request.x_col:
        df_processed[request.x_col] = df_processed[request.x_col].astype(str)

    return df_processed


@dataclass(frozen=True)
class FacetPlotData:
    facet_value: object
    source_df: pd.DataFrame
    plot_df: pd.DataFrame


@dataclass(frozen=True)
class OverlayLine:
    x: object
    y: object
    color: str
    label: str


@dataclass(frozen=True)
class AnnotationSpec:
    box_pairs: list
    p_values: list[float]
    annotator_kwargs: dict


@dataclass(frozen=True)
class PairedPlotData:
    plot_df_long: pd.DataFrame
    tick_labels: list[str]
    mean_x: pd.Index
    mean_y: pd.Series


@dataclass(frozen=True)
class HeatmapPlotData:
    facet_value: object
    matrix: pd.DataFrame


@dataclass(frozen=True)
class StackedBarPlotData:
    facet_value: object
    matrix: pd.DataFrame


@dataclass(frozen=True)
class MosaicPlotData:
    facet_value: object
    counts: dict[tuple[str, str], int]
    categories: list[str]
    subgroups: list[str]


BASE_PLOT_KINDS = {"bar", "boxplot", "violin", "pointplot", "lineplot", "countplot"}


def get_x_order(df: pd.DataFrame, request: PlotRequest):
    return df[request.x_col].unique()


def get_facet_values(df: pd.DataFrame, request: PlotRequest) -> list[object]:
    if request.facet_col:
        return list(df[request.facet_col].unique())
    return [None]


def build_facet_plot_data(df: pd.DataFrame, request: PlotRequest) -> list[FacetPlotData]:
    facet_data: list[FacetPlotData] = []

    for facet_value in get_facet_values(df, request):
        if request.facet_col:
            source_df = df[df[request.facet_col] == facet_value]
        else:
            source_df = df

        if source_df.empty:
            facet_data.append(FacetPlotData(facet_value=facet_value, source_df=source_df, plot_df=source_df))
            continue

        facet_data.append(
            FacetPlotData(
                facet_value=facet_value,
                source_df=source_df,
                plot_df=build_plot_dataframe_for_graph_type(source_df, request),
            )
        )

    return facet_data


def build_plot_dataframe_for_graph_type(df: pd.DataFrame, request: PlotRequest) -> pd.DataFrame:
    if request.graph_type == "countplot":
        count_df = df.copy()
        group_cols = [request.x_col]
        if request.subgroup_col and request.subgroup_col != request.x_col:
            group_cols.append(request.subgroup_col)
        count_df = count_df.groupby(group_cols, as_index=False).size().rename(columns={"size": "__count__"})
        return count_df

    if request.graph_type != "summary_scatter":
        return df

    group_cols = [request.x_col]
    if request.subgroup_col and request.subgroup_col != request.x_col:
        group_cols.append(request.subgroup_col)

    error_agg_func = request.properties.get("error_bar_type", "std")
    summary_stats = df.groupby(group_cols, as_index=False).agg(
        mean_y=(request.y_col, "mean"),
        err_y=(request.y_col, error_agg_func),
    )
    summary_stats.rename(columns={"mean_y": request.y_col}, inplace=True)
    return summary_stats


def build_heatmap_matrix(df: pd.DataFrame, request: PlotRequest) -> pd.DataFrame:
    if not request.x_col or not request.y_col:
        return pd.DataFrame()

    source_df = df[[request.x_col, request.y_col]].dropna().copy()
    if source_df.empty:
        return pd.DataFrame()

    x_values = source_df[request.x_col].astype(str)
    y_values = source_df[request.y_col].astype(str)
    matrix = pd.crosstab(y_values, x_values)
    row_order = pd.Index(y_values.drop_duplicates())
    col_order = pd.Index(x_values.drop_duplicates())
    return matrix.reindex(index=row_order, columns=col_order, fill_value=0)


def build_heatmap_plot_data(df: pd.DataFrame, request: PlotRequest) -> list[HeatmapPlotData]:
    heatmap_data: list[HeatmapPlotData] = []

    for facet_value in get_facet_values(df, request):
        if request.facet_col:
            source_df = df[df[request.facet_col] == facet_value]
        else:
            source_df = df

        heatmap_data.append(
            HeatmapPlotData(
                facet_value=facet_value,
                matrix=build_heatmap_matrix(source_df, request),
            )
        )

    return heatmap_data


def build_stacked_bar_matrix(df: pd.DataFrame, request: PlotRequest, normalize: bool = False) -> pd.DataFrame:
    if not request.x_col:
        return pd.DataFrame()

    source_cols = [request.x_col]
    if request.subgroup_col and request.subgroup_col != request.x_col:
        source_cols.append(request.subgroup_col)
    source_df = df[source_cols].dropna().copy()
    if source_df.empty:
        return pd.DataFrame()

    x_values = source_df[request.x_col].astype(str)
    if len(source_cols) == 1:
        matrix = pd.crosstab(index=x_values, columns=pd.Series(["Count"] * len(x_values), index=source_df.index))
    else:
        hue_values = source_df[request.subgroup_col].astype(str)
        matrix = pd.crosstab(index=x_values, columns=hue_values)

    row_order = pd.Index(x_values.drop_duplicates())
    col_order = pd.Index(matrix.columns)
    matrix = matrix.reindex(index=row_order, columns=col_order, fill_value=0)

    if normalize:
        totals = matrix.sum(axis=1).replace(0, np.nan)
        matrix = matrix.div(totals, axis=0).fillna(0.0)

    return matrix


def build_stacked_bar_plot_data(df: pd.DataFrame, request: PlotRequest) -> list[StackedBarPlotData]:
    stacked_data: list[StackedBarPlotData] = []
    normalize = request.graph_type == "stacked_bar_100"

    for facet_value in get_facet_values(df, request):
        if request.facet_col:
            source_df = df[df[request.facet_col] == facet_value]
        else:
            source_df = df

        stacked_data.append(
            StackedBarPlotData(
                facet_value=facet_value,
                matrix=build_stacked_bar_matrix(source_df, request, normalize=normalize),
            )
        )

    return stacked_data


def build_mosaic_plot_data(df: pd.DataFrame, request: PlotRequest) -> list[MosaicPlotData]:
    mosaic_data: list[MosaicPlotData] = []

    for facet_value in get_facet_values(df, request):
        if request.facet_col:
            source_df = df[df[request.facet_col] == facet_value]
        else:
            source_df = df

        matrix = build_stacked_bar_matrix(source_df, request, normalize=False)
        counts: dict[tuple[str, str], int] = {}
        if not matrix.empty:
            for category in matrix.index:
                for subgroup in matrix.columns:
                    counts[(str(category), str(subgroup))] = int(matrix.loc[category, subgroup])

        mosaic_data.append(
            MosaicPlotData(
                facet_value=facet_value,
                counts=counts,
                categories=[str(value) for value in matrix.index],
                subgroups=[str(value) for value in matrix.columns],
            )
        )

    return mosaic_data


def build_base_plot_kwargs(
    request: PlotRequest,
    plot_df: pd.DataFrame,
    x_order,
    properties: dict,
) -> dict:
    kwargs = {
        "data": plot_df,
        "x": request.x_col,
        "order": x_order,
    }

    if request.graph_type == "countplot":
        kwargs["y"] = "__count__"
    else:
        kwargs["y"] = request.y_col

    if request.graph_type == "lineplot":
        kwargs.pop("order", None)

    if request.subgroup_col:
        kwargs["hue"] = request.subgroup_col
        kwargs["palette"] = properties.get("subgroup_colors", {})
    else:
        single_color = properties.get("single_color")
        if single_color:
            kwargs["color"] = single_color

    if request.graph_type in {"bar", "countplot"}:
        kwargs.update(
            {
                "edgecolor": properties.get("bar_edgecolor", "black"),
                "linewidth": properties.get("bar_edgewidth", 1.0),
                "capsize": properties.get("capsize", 0) * 0.01,
            }
        )
    if request.graph_type in {"pointplot", "lineplot"}:
        kwargs.update(
            {
                "linestyle": properties.get("linestyle", "-"),
                "linewidth": properties.get("linewidth", 1.5),
            }
        )
    if request.graph_type == "pointplot":
        kwargs["capsize"] = properties.get("capsize", 0) * 0.02

    return kwargs


def build_scatter_plot_kwargs(request: PlotRequest, plot_df: pd.DataFrame, properties: dict) -> dict:
    kwargs = {
        "data": plot_df,
        "x": request.x_col,
        "y": request.y_col,
        "marker": properties.get("marker_style", "o"),
        "edgecolor": properties.get("marker_edgecolor", "black"),
        "linewidth": properties.get("marker_edgewidth", 1.0),
        "s": properties.get("marker_size", 5.0) ** 2,
        "alpha": properties.get("marker_alpha", 1.0),
    }

    if request.subgroup_col:
        kwargs["hue"] = request.subgroup_col
        kwargs["palette"] = properties.get("subgroup_colors", {})
    else:
        single_color = properties.get("single_color")
        if single_color:
            kwargs["color"] = single_color

    return kwargs


def build_stripplot_kwargs(
    request: PlotRequest,
    source_df: pd.DataFrame,
    x_order,
    properties: dict,
) -> dict:
    return {
        "data": source_df,
        "x": request.x_col,
        "y": request.y_col,
        "hue": request.subgroup_col or None,
        "jitter": True,
        "alpha": properties.get("marker_alpha", 0.6),
        "palette": properties.get("subgroup_colors", {}),
        "marker": properties.get("marker_style", "o"),
        "edgecolor": properties.get("marker_edgecolor", "black"),
        "linewidth": properties.get("marker_edgewidth", 1.0),
        "s": properties.get("marker_size", 5.0),
        "dodge": bool(request.subgroup_col) and request.graph_type != "pointplot",
        "order": x_order,
    }


def build_legend_handles_labels(df: pd.DataFrame, request: PlotRequest, properties: dict, axes_flat):
    handles = []
    labels = []

    if not request.subgroup_col:
        return handles, labels

    if request.graph_type in {"bar", "boxplot", "violin"}:
        hue_categories = sorted(df[request.subgroup_col].unique())
        palette = properties.get("subgroup_colors", {})

        for category in hue_categories:
            str_category = str(category)
            color = palette.get(str_category, "black")
            patch = mpatches.Patch(color=color, label=str_category)
            if str_category not in labels:
                handles.append(patch)
                labels.append(str_category)
        return handles, labels

    for ax in axes_flat:
        h, l = ax.get_legend_handles_labels()
        for i, label in enumerate(l):
            if label not in labels:
                labels.append(label)
                handles.append(h[i])

    return handles, labels


def build_summary_errorbar_specs(plot_df: pd.DataFrame, request: PlotRequest, properties: dict) -> list[dict]:
    capsize = properties.get("capsize", 0)
    if request.graph_type != "summary_scatter" or "err_y" not in plot_df.columns:
        return []

    if request.subgroup_col:
        palette = properties.get("subgroup_colors", {})
        specs = []
        for hue_value, group_df in plot_df.groupby(request.subgroup_col):
            specs.append(
                {
                    "x": group_df[request.x_col],
                    "y": group_df[request.y_col],
                    "yerr": group_df["err_y"],
                    "fmt": "none",
                    "capsize": capsize,
                    "ecolor": palette.get(str(hue_value), "black"),
                }
            )
        return specs

    return [
        {
            "x": plot_df[request.x_col],
            "y": plot_df[request.y_col],
            "yerr": plot_df["err_y"],
            "fmt": "none",
            "capsize": capsize,
            "ecolor": properties.get("marker_edgecolor", "black"),
        }
    ]


def build_regression_overlay_lines(regression_line_params: dict, properties: dict) -> list[OverlayLine]:
    if not regression_line_params:
        return []

    if "x_line" in regression_line_params:
        return [
            OverlayLine(
                x=regression_line_params["x_line"],
                y=regression_line_params["y_line"],
                color=properties.get("regression_color", "red"),
                label=f"Linear Fit (R²={regression_line_params['r_squared']:.3f})",
            )
        ]

    palette = properties.get("subgroup_colors", {})
    lines = []
    for group_name, params in regression_line_params.items():
        lines.append(
            OverlayLine(
                x=params["x_line"],
                y=params["y_line"],
                color=palette.get(str(group_name), "red"),
                label=f"{group_name} Fit (R²={params['r_squared']:.3f})",
            )
        )
    return lines


def sigmoid_4pl(x, bottom, top, hill_slope, log_ec50):
    return bottom + (top - bottom) / (1 + 10 ** ((log_ec50 - x) * hill_slope))


def build_four_pl_overlay_lines(fit_params: dict, properties: dict) -> list[OverlayLine]:
    if not fit_params:
        return []

    def _build_single_line(params_info: dict, color: str, label: str) -> OverlayLine:
        params = params_info["params"]
        x_min = params_info["log_x_data"].min()
        x_max = params_info["log_x_data"].max()
        x_fit = np.linspace(x_min, x_max, 200)
        y_fit = sigmoid_4pl(x_fit, *params)
        return OverlayLine(x=10**x_fit, y=y_fit, color=color, label=label)

    if "params" in fit_params:
        return [
            _build_single_line(
                fit_params,
                properties.get("regression_color", "red"),
                f"4PL Fit (R²={fit_params['r_squared']:.3f})",
            )
        ]

    palette = properties.get("subgroup_colors", {})
    lines = []
    for group_name, params_info in fit_params.items():
        lines.append(
            _build_single_line(
                params_info,
                palette.get(str(group_name), "red"),
                f"{group_name} 4PL (R²={params_info['r_squared']:.3f})",
            )
        )
    return lines


def build_annotation_spec(
    plot_df: pd.DataFrame,
    request: PlotRequest,
    annotations_to_plot: list[dict],
    ax,
    hue_order=None,
) -> AnnotationSpec | None:
    if not annotations_to_plot:
        return None

    box_pairs = [ann["box_pair"] for ann in annotations_to_plot]
    p_values = [ann["p_value"] for ann in annotations_to_plot]
    if not box_pairs:
        return None

    annotator_kwargs = {
        "ax": ax,
        "pairs": box_pairs,
        "data": plot_df,
        "x": request.x_col,
        "y": request.y_col,
    }
    if request.subgroup_col:
        annotator_kwargs["hue"] = request.subgroup_col
        annotator_kwargs["hue_order"] = hue_order

    return AnnotationSpec(
        box_pairs=box_pairs,
        p_values=p_values,
        annotator_kwargs=annotator_kwargs,
    )


def build_paired_plot_data(df: pd.DataFrame, request: PlotRequest) -> PairedPlotData | None:
    if not (request.col1 and request.col2 and request.col1 != request.col2):
        return None

    plot_df = df[[request.col1, request.col2]].dropna().copy()
    if plot_df.empty:
        return None

    plot_df["ID"] = range(len(plot_df))
    plot_df_long = pd.melt(
        plot_df,
        id_vars="ID",
        value_vars=[request.col1, request.col2],
        var_name="Condition",
        value_name="Value",
    )
    mean_y = plot_df_long.groupby("Condition")["Value"].mean().reindex([request.col1, request.col2])
    tick_labels = [
        request.properties.get("paired_label1") or request.col1,
        request.properties.get("paired_label2") or request.col2,
    ]

    return PairedPlotData(
        plot_df_long=plot_df_long,
        tick_labels=tick_labels,
        mean_x=mean_y.index,
        mean_y=mean_y,
    )


def build_paired_annotation_spec(plot_df_long: pd.DataFrame, annotations_to_plot: list[dict], ax) -> AnnotationSpec | None:
    if not annotations_to_plot:
        return None

    box_pairs = [ann["box_pair"] for ann in annotations_to_plot]
    p_values = [ann["p_value"] for ann in annotations_to_plot]
    if not box_pairs:
        return None

    return AnnotationSpec(
        box_pairs=box_pairs,
        p_values=p_values,
        annotator_kwargs={
            "ax": ax,
            "pairs": box_pairs,
            "data": plot_df_long,
            "x": "Condition",
            "y": "Value",
        },
    )
