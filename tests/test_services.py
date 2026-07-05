import unittest

import pandas as pd
from matplotlib.figure import Figure
from pathlib import Path
import tempfile
import numpy as np

from calcite.models import AnalysisRequest, PlotRequest
from calcite.services.plot_service import (
    build_annotation_spec,
    build_base_plot_kwargs,
    build_facet_plot_data,
    build_four_pl_overlay_lines,
    build_legend_handles_labels,
    build_paired_annotation_spec,
    build_paired_plot_data,
    build_plot_dataframe_for_graph_type,
    build_regression_overlay_lines,
    build_scatter_plot_kwargs,
    build_stripplot_kwargs,
    build_summary_errorbar_specs,
    normalize_plot_request,
    prepare_plot_dataframe,
)
from calcite.services.statistics_service import (
    UNIQUE_SEPARATOR,
    build_effective_groups,
    format_annotation_pair,
    normalize_analysis_request,
    prepare_analysis_dataframe,
    run_anova,
    run_kruskal,
)
from calcite.services.project_service import (
    ProjectState,
    dataframe_from_clipboard_text,
    optimize_imported_dataframe,
    read_project_archive,
    write_project_archive,
)
from calcite.services.data_service import (
    build_advanced_filter_query,
    filter_dataframe,
    pivot_dataframe,
    restructure_dataframe,
    subset_rows,
)


class StatisticsServiceTests(unittest.TestCase):
    def test_normalize_analysis_request_ignores_same_group_and_subgroup(self):
        request = AnalysisRequest(
            value_col="value",
            group_col="condition",
            subgroup_col="condition",
            facet_col="batch",
        )

        normalized = normalize_analysis_request(request)

        self.assertEqual(normalized.subgroup_col, "")
        self.assertEqual(normalized.group_col, "condition")

    def test_prepare_analysis_dataframe_coerces_group_columns(self):
        df = pd.DataFrame({"group": [1, 2], "subgroup": [3, 4], "value": [0.1, 0.2]})

        prepared, normalized = prepare_analysis_dataframe(
            df,
            AnalysisRequest(value_col="value", group_col="group", subgroup_col="subgroup"),
        )

        self.assertEqual(prepared["group"].tolist(), ["1", "2"])
        self.assertEqual(prepared["subgroup"].tolist(), ["3", "4"])
        self.assertEqual(normalized.subgroup_col, "subgroup")

    def test_build_effective_groups_combines_group_and_subgroup(self):
        df = pd.DataFrame({"group": ["A", "B"], "subgroup": ["x", "y"]})

        effective_groups, interaction_name = build_effective_groups(df, "group", "subgroup")

        self.assertEqual(interaction_name, "group_subgroup_interaction")
        self.assertEqual(
            effective_groups.tolist(),
            [f"A{UNIQUE_SEPARATOR}x", f"B{UNIQUE_SEPARATOR}y"],
        )

    def test_format_annotation_pair_expands_subgroup_pairs(self):
        pair = (f"A{UNIQUE_SEPARATOR}x", f"B{UNIQUE_SEPARATOR}y")

        formatted = format_annotation_pair(pair, "subgroup")

        self.assertEqual(formatted, (("A", "x"), ("B", "y")))

    def test_run_anova_returns_annotations_for_significant_groups(self):
        df = pd.DataFrame(
            {
                "group": ["A"] * 5 + ["B"] * 5 + ["C"] * 5,
                "value": [1, 1.1, 0.9, 1.2, 0.8, 5, 5.1, 4.9, 5.2, 4.8, 9, 9.1, 8.9, 9.2, 8.8],
            }
        )

        result = run_anova(
            df,
            value_col="value",
            group_col="group",
            subgroup_col="",
            facet_col="",
            selected_groups=["A", "B", "C"],
        )

        self.assertTrue(result.has_valid_samples)
        self.assertTrue(any("F-statistic" in line for line in result.summary_lines))
        self.assertTrue(result.annotations)

    def test_run_kruskal_returns_annotations_for_significant_groups(self):
        df = pd.DataFrame(
            {
                "group": ["A"] * 6 + ["B"] * 6 + ["C"] * 6,
                "value": [1, 1, 2, 2, 1, 2, 10, 11, 9, 10, 11, 9, 20, 21, 19, 20, 21, 19],
            }
        )

        result = run_kruskal(
            df,
            value_col="value",
            group_col="group",
            subgroup_col="",
            facet_col="",
            selected_groups=["A", "B", "C"],
        )

        self.assertTrue(result.has_valid_samples)
        self.assertTrue(any("Kruskal-Wallis" in line for line in result.summary_lines))
        self.assertTrue(result.annotations)


class PlotServiceTests(unittest.TestCase):
    def test_normalize_plot_request_ignores_same_x_and_subgroup(self):
        request = PlotRequest(
            graph_type="bar",
            x_col="condition",
            y_col="value",
            subgroup_col="condition",
        )

        normalized = normalize_plot_request(request)

        self.assertEqual(normalized.subgroup_col, "")

    def test_prepare_plot_dataframe_stringifies_categorical_x(self):
        df = pd.DataFrame({"x": [1, 2], "y": [0.1, 0.2]})

        prepared = prepare_plot_dataframe(
            df,
            PlotRequest(graph_type="bar", x_col="x", y_col="y"),
        )

        self.assertEqual(prepared["x"].tolist(), ["1", "2"])

    def test_build_plot_dataframe_for_summary_scatter_aggregates_values(self):
        df = pd.DataFrame(
            {
                "x": ["A", "A", "B", "B"],
                "y": [1.0, 3.0, 2.0, 6.0],
            }
        )

        summary = build_plot_dataframe_for_graph_type(
            df,
            PlotRequest(graph_type="summary_scatter", x_col="x", y_col="y", properties={"error_bar_type": "std"}),
        )

        self.assertEqual(summary["y"].tolist(), [2.0, 4.0])
        self.assertIn("err_y", summary.columns)

    def test_build_facet_plot_data_splits_by_facet(self):
        df = pd.DataFrame(
            {
                "x": ["A", "A", "B", "B"],
                "y": [1.0, 2.0, 3.0, 4.0],
                "facet": ["left", "left", "right", "right"],
            }
        )

        facet_data = build_facet_plot_data(
            df,
            PlotRequest(graph_type="scatter", x_col="x", y_col="y", facet_col="facet"),
        )

        self.assertEqual([item.facet_value for item in facet_data], ["left", "right"])
        self.assertEqual(facet_data[0].source_df["y"].tolist(), [1.0, 2.0])

    def test_build_base_plot_kwargs_applies_lineplot_rules(self):
        kwargs = build_base_plot_kwargs(
            PlotRequest(graph_type="lineplot", x_col="x", y_col="y", subgroup_col="group"),
            pd.DataFrame({"x": [1], "y": [2], "group": ["a"]}),
            ["1"],
            {"subgroup_colors": {"a": "red"}, "linewidth": 2.0, "linestyle": ":"},
        )

        self.assertNotIn("order", kwargs)
        self.assertEqual(kwargs["hue"], "group")
        self.assertEqual(kwargs["linewidth"], 2.0)

    def test_build_scatter_plot_kwargs_uses_single_color_without_hue(self):
        kwargs = build_scatter_plot_kwargs(
            PlotRequest(graph_type="scatter", x_col="x", y_col="y"),
            pd.DataFrame({"x": [1], "y": [2]}),
            {"single_color": "green", "marker_size": 3.0},
        )

        self.assertEqual(kwargs["color"], "green")
        self.assertEqual(kwargs["s"], 9.0)

    def test_build_stripplot_kwargs_sets_dodge_from_request(self):
        kwargs = build_stripplot_kwargs(
            PlotRequest(graph_type="bar", x_col="x", y_col="y", subgroup_col="group"),
            pd.DataFrame({"x": ["A"], "y": [1], "group": ["g1"]}),
            ["A"],
            {"subgroup_colors": {"g1": "blue"}},
        )

        self.assertTrue(kwargs["dodge"])
        self.assertEqual(kwargs["hue"], "group")

    def test_build_legend_handles_labels_for_patch_based_plots(self):
        df = pd.DataFrame({"group": ["A", "B"]})
        fig = Figure()
        ax = fig.add_subplot(111)

        handles, labels = build_legend_handles_labels(
            df,
            PlotRequest(graph_type="bar", x_col="x", y_col="y", subgroup_col="group"),
            {"subgroup_colors": {"A": "red", "B": "blue"}},
            [ax],
        )

        self.assertEqual(labels, ["A", "B"])
        self.assertEqual(len(handles), 2)

    def test_build_summary_errorbar_specs_for_grouped_summary_scatter(self):
        plot_df = pd.DataFrame(
            {
                "x": ["A", "A"],
                "y": [2.0, 3.0],
                "group": ["g1", "g2"],
                "err_y": [0.1, 0.2],
            }
        )

        specs = build_summary_errorbar_specs(
            plot_df,
            PlotRequest(graph_type="summary_scatter", x_col="x", y_col="y", subgroup_col="group"),
            {"capsize": 4, "subgroup_colors": {"g1": "red", "g2": "blue"}},
        )

        self.assertEqual(len(specs), 2)
        self.assertEqual(specs[0]["capsize"], 4)

    def test_build_regression_overlay_lines_for_single_fit(self):
        lines = build_regression_overlay_lines(
            {"x_line": [1, 2], "y_line": [3, 4], "r_squared": 0.9},
            {"regression_color": "orange"},
        )

        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0].color, "orange")
        self.assertIn("Linear Fit", lines[0].label)

    def test_build_four_pl_overlay_lines_for_grouped_fits(self):
        fit_params = {
            "g1": {"params": [0.0, 1.0, 1.0, 0.0], "r_squared": 0.8, "log_x_data": pd.Series([0.0, 1.0])},
            "g2": {"params": [0.0, 2.0, 1.0, 0.5], "r_squared": 0.7, "log_x_data": pd.Series([0.0, 1.0])},
        }

        lines = build_four_pl_overlay_lines(
            fit_params,
            {"subgroup_colors": {"g1": "red", "g2": "blue"}},
        )

        self.assertEqual(len(lines), 2)
        self.assertEqual({line.color for line in lines}, {"red", "blue"})

    def test_build_annotation_spec_with_hue(self):
        df = pd.DataFrame({"x": ["A"], "y": [1.0], "group": ["g1"]})
        request = PlotRequest(graph_type="bar", x_col="x", y_col="y", subgroup_col="group")

        spec = build_annotation_spec(
            df,
            request,
            [{"box_pair": (("A", "g1"), ("A", "g1")), "p_value": 0.01}],
            ax=object(),
            hue_order=["g1"],
        )

        self.assertIsNotNone(spec)
        self.assertEqual(spec.p_values, [0.01])
        self.assertEqual(spec.annotator_kwargs["hue"], "group")

    def test_build_paired_plot_data_returns_long_form(self):
        df = pd.DataFrame({"before": [1, 2], "after": [2, 3]})
        request = PlotRequest(
            graph_type="paired_scatter",
            col1="before",
            col2="after",
            properties={"paired_label1": "Before", "paired_label2": "After"},
        )

        paired_data = build_paired_plot_data(df, request)

        self.assertIsNotNone(paired_data)
        self.assertEqual(paired_data.tick_labels, ["Before", "After"])
        self.assertEqual(len(paired_data.plot_df_long), 4)

    def test_build_paired_annotation_spec_returns_condition_axes(self):
        plot_df_long = pd.DataFrame(
            {"Condition": ["before", "after"], "Value": [1.0, 2.0]}
        )

        spec = build_paired_annotation_spec(
            plot_df_long,
            [{"box_pair": ("before", "after"), "p_value": 0.02}],
            ax=object(),
        )

        self.assertIsNotNone(spec)
        self.assertEqual(spec.annotator_kwargs["x"], "Condition")
        self.assertEqual(spec.p_values, [0.02])


class ProjectServiceTests(unittest.TestCase):
    def test_optimize_imported_dataframe_converts_low_cardinality_object_column(self):
        df = pd.DataFrame({"group": ["A", "A", "A", "B", "B"], "value": [1, 2, 3, 4, 5]})

        optimized = optimize_imported_dataframe(df)

        self.assertEqual(str(optimized["group"].dtype), "category")

    def test_dataframe_from_clipboard_text_parses_tsv(self):
        df = dataframe_from_clipboard_text("a\tb\n1\t2\n3\t4\n")

        self.assertEqual(df.columns.tolist(), ["a", "b"])
        self.assertEqual(df["a"].tolist(), [1, 3])

    def test_project_archive_round_trip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "sample.calcite"
            state = ProjectState(
                dataframe=pd.DataFrame({"x": [1, 2], "y": [3, 4]}),
                settings={"title": "Example"},
                statistical_annotations=[{"box_pair": ("A", "B"), "p_value": 0.01}],
                paired_annotations=[{"box_pair": ("before", "after"), "p_value": 0.02}],
                regression_line_params={"x_line": np.array([1, 2]), "y_line": np.array([3, 4]), "r_squared": 0.9},
                fit_params={"params": np.array([0.0, 1.0, 1.0, 0.0]), "log_x_data": np.array([0.0, 1.0]), "r_squared": 0.8},
            )

            write_project_archive(str(project_path), state)
            restored = read_project_archive(str(project_path))

            self.assertEqual(restored.dataframe["x"].tolist(), [1, 2])
            self.assertEqual(restored.settings["title"], "Example")
            self.assertEqual(restored.regression_line_params["x_line"].tolist(), [1, 2])
            self.assertEqual(restored.fit_params["params"].tolist(), [0.0, 1.0, 1.0, 0.0])


class DataServiceTests(unittest.TestCase):
    def test_restructure_dataframe_melts_columns(self):
        df = pd.DataFrame({"id": [1, 2], "a": [10, 20], "b": [30, 40]})

        result = restructure_dataframe(
            df,
            {"id_vars": ["id"], "value_vars": ["a", "b"], "var_name": "kind", "value_name": "value"},
        )

        self.assertEqual(result.columns.tolist(), ["id", "kind", "value"])
        self.assertEqual(len(result), 4)

    def test_pivot_dataframe_restores_wide_shape(self):
        df = pd.DataFrame(
            {"id": [1, 1, 2, 2], "kind": ["a", "b", "a", "b"], "value": [10, 30, 20, 40]}
        )

        result = pivot_dataframe(
            df,
            {"id_vars": "id", "var_name": "kind", "value_name": "value"},
        )

        self.assertEqual(set(result.columns.tolist()), {"id", "a", "b"})

    def test_build_advanced_filter_query_supports_string_ops(self):
        query = build_advanced_filter_query(
            [
                {"column": "name", "operator": "contains", "value": "ab", "connector": "and"},
                {"column": "value", "operator": ">", "value": 1, "connector": "and"},
            ]
        )

        self.assertIn(".str.contains", query)
        self.assertIn("`value` > 1", query)

    def test_filter_dataframe_applies_query(self):
        df = pd.DataFrame({"name": ["abc", "def"], "value": [2, 0]})

        result, query = filter_dataframe(
            df,
            [
                {"column": "name", "operator": "contains", "value": "ab", "connector": "and"},
                {"column": "value", "operator": ">", "value": 1, "connector": "and"},
            ],
        )

        self.assertEqual(result["name"].tolist(), ["abc"])
        self.assertTrue(query)

    def test_subset_rows_returns_selected_rows(self):
        df = pd.DataFrame({"x": [1, 2, 3]})

        result = subset_rows(df, [0, 2])

        self.assertEqual(result["x"].tolist(), [1, 3])


if __name__ == "__main__":
    unittest.main()
