import unittest

import pandas as pd
from matplotlib.figure import Figure
from pathlib import Path
import tempfile
import numpy as np
import json
import zipfile

from calcite.models import AnalysisRequest, PlotRequest
from calcite.services.plot_service import (
    build_annotation_spec,
    build_base_plot_kwargs,
    build_facet_plot_data,
    build_four_pl_overlay_lines,
    build_heatmap_matrix,
    build_legend_handles_labels,
    build_mosaic_plot_data,
    build_paired_annotation_spec,
    build_paired_plot_data,
    build_plot_dataframe_for_graph_type,
    build_regression_overlay_lines,
    build_scatter_plot_kwargs,
    build_stacked_bar_matrix,
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
from calcite.application.project_use_cases import OpenProjectUseCase, SaveProjectUseCase
from calcite.application.state import AppState
from calcite.application.ui_controller import resolve_legend_position_for_graph_type
from calcite.application.window_use_cases import build_child_window_title
from calcite.application.data_use_cases import (
    ApplyAdvancedFilterUseCase,
    CreateSubsetUseCase,
    PivotDataUseCase,
    RestructureDataUseCase,
)
from calcite.application.import_use_cases import OpenCsvUseCase, PasteClipboardUseCase
from calcite.application.export_use_cases import SaveTextUseCase
from calcite.application.statistics_formatters import (
    format_binary_test_result,
    format_chi_squared_result,
    format_pearson_correlation_result,
    format_paired_test_result,
    format_regression_summary,
    format_shapiro_result,
    format_spearman_correlation_result,
    format_two_proportion_result,
)
from calcite.application.statistics_use_cases import (
    RunChiSquaredAnalysisUseCase,
    RunPearsonCorrelationUseCase,
    RunRegressionAnalysisUseCase,
    RunShapiroAnalysisUseCase,
    RunSpearmanCorrelationUseCase,
    RunTwoProportionAnalysisUseCase,
)
from calcite.application.table_controller import build_clipboard_text, parse_clipboard_text
from calcite.handlers import ActionHandler, GraphManager, StatisticalHandler
from calcite.main_window_history import DataframeHistoryManager
from calcite.services.project_service import (
    ANALYSIS_FILENAME,
    DATAFRAME_FILENAME,
    MANIFEST_FILENAME,
    PROJECT_SCHEMA_VERSION,
    SETTINGS_FILENAME,
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

    def test_build_plot_dataframe_for_countplot_aggregates_counts(self):
        df = pd.DataFrame({"x": ["A", "A", "B"], "group": ["g1", "g1", "g2"]})

        counted = build_plot_dataframe_for_graph_type(
            df,
            PlotRequest(graph_type="countplot", x_col="x", subgroup_col="group"),
        )

        self.assertEqual(counted["__count__"].tolist(), [2, 1])

    def test_build_base_plot_kwargs_for_countplot_uses_internal_count_column(self):
        kwargs = build_base_plot_kwargs(
            PlotRequest(graph_type="countplot", x_col="x", subgroup_col="group"),
            pd.DataFrame({"x": ["A"], "group": ["g1"], "__count__": [2]}),
            ["A"],
            {"subgroup_colors": {"g1": "red"}},
        )

        self.assertEqual(kwargs["y"], "__count__")
        self.assertEqual(kwargs["hue"], "group")

    def test_build_heatmap_matrix_counts_categorical_pairs(self):
        matrix = build_heatmap_matrix(
            pd.DataFrame(
                {
                    "x": ["A", "A", "B", "B"],
                    "y": ["top", "top", "top", "bottom"],
                }
            ),
            PlotRequest(graph_type="heatmap", x_col="x", y_col="y"),
        )

        self.assertEqual(matrix.loc["top", "A"], 2)
        self.assertEqual(matrix.loc["bottom", "B"], 1)
        self.assertEqual(list(matrix.columns), ["A", "B"])
        self.assertEqual(list(matrix.index), ["top", "bottom"])

    def test_build_stacked_bar_matrix_counts_categories(self):
        matrix = build_stacked_bar_matrix(
            pd.DataFrame(
                {
                    "x": ["A", "A", "B", "B"],
                    "group": ["g1", "g2", "g1", "g1"],
                }
            ),
            PlotRequest(graph_type="stacked_bar", x_col="x", subgroup_col="group"),
        )

        self.assertEqual(matrix.loc["A", "g1"], 1)
        self.assertEqual(matrix.loc["A", "g2"], 1)
        self.assertEqual(matrix.loc["B", "g1"], 2)

    def test_build_stacked_bar_matrix_normalizes_for_100_percent(self):
        matrix = build_stacked_bar_matrix(
            pd.DataFrame(
                {
                    "x": ["A", "A", "B", "B"],
                    "group": ["g1", "g2", "g1", "g1"],
                }
            ),
            PlotRequest(graph_type="stacked_bar_100", x_col="x", subgroup_col="group"),
            normalize=True,
        )

        self.assertAlmostEqual(matrix.loc["A"].sum(), 1.0)
        self.assertAlmostEqual(matrix.loc["B"].sum(), 1.0)

    def test_build_mosaic_plot_data_flattens_counts(self):
        plot_data = build_mosaic_plot_data(
            pd.DataFrame(
                {
                    "x": ["A", "A", "B", "B"],
                    "group": ["g1", "g2", "g1", "g1"],
                }
            ),
            PlotRequest(graph_type="mosaic", x_col="x", subgroup_col="group"),
        )

        self.assertEqual(len(plot_data), 1)
        self.assertEqual(plot_data[0].counts[("A", "g1")], 1)
        self.assertEqual(plot_data[0].counts[("B", "g1")], 2)

    def test_prepare_plot_dataframe_keeps_numeric_x_for_correlation_heatmap(self):
        df = pd.DataFrame({"x": [1, 2], "y": [3, 4]})

        prepared = prepare_plot_dataframe(
            df,
            PlotRequest(graph_type="correlation_heatmap", x_col="x", y_col="y"),
        )

        self.assertEqual(prepared["x"].tolist(), [1, 2])

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


class ApplicationUseCaseTests(unittest.TestCase):
    def test_app_state_resets_analysis_results(self):
        state = AppState(
            statistical_annotations=[{"p_value": 0.01}],
            paired_annotations=[{"box_pair": ("A", "B")}],
            regression_line_params={"x_line": np.array([1, 2])},
            fit_params={"params": np.array([1, 2, 3, 4])},
        )

        state.reset_analysis_results()

        self.assertEqual(state.statistical_annotations, [])
        self.assertEqual(state.paired_annotations, [])
        self.assertIsNone(state.regression_line_params)
        self.assertIsNone(state.fit_params)

    def test_app_state_deduplicates_annotations(self):
        state = AppState()
        annotation = {"p_value": 0.01}
        paired_annotation = {"box_pair": ("A", "B")}

        state.add_statistical_annotation(annotation)
        state.add_statistical_annotation(annotation)
        state.add_paired_annotation(paired_annotation)
        state.add_paired_annotation(paired_annotation)

        self.assertEqual(state.statistical_annotations, [annotation])
        self.assertEqual(state.paired_annotations, [paired_annotation])

    def test_resolve_legend_position_hides_summary_scatter_legend(self):
        resolved = resolve_legend_position_for_graph_type(
            previous_graph_type="scatter",
            next_graph_type="summary_scatter",
            current_legend_position="best",
        )

        self.assertEqual(resolved, "hide")

    def test_resolve_legend_position_restores_default_after_summary_scatter(self):
        resolved = resolve_legend_position_for_graph_type(
            previous_graph_type="summary_scatter",
            next_graph_type="scatter",
            current_legend_position="hide",
        )

        self.assertEqual(resolved, "best")

    def test_resolve_legend_position_hides_heatmap_legend(self):
        resolved = resolve_legend_position_for_graph_type(
            previous_graph_type="scatter",
            next_graph_type="heatmap",
            current_legend_position="best",
        )

        self.assertEqual(resolved, "hide")

    def test_resolve_legend_position_hides_correlation_heatmap_legend(self):
        resolved = resolve_legend_position_for_graph_type(
            previous_graph_type="scatter",
            next_graph_type="correlation_heatmap",
            current_legend_position="best",
        )

        self.assertEqual(resolved, "hide")

    def test_project_use_cases_round_trip_project_archive(self):
        df = pd.DataFrame({"group": ["A", "B"], "value": [1.0, 2.0]})
        state = ProjectState(
            dataframe=df,
            settings={"title": "Example"},
            statistical_annotations=[{"value_col": "value"}],
            paired_annotations=[],
            regression_line_params={"x_line": np.array([1, 2]), "y_line": np.array([3, 4]), "r_squared": 0.9},
            fit_params=None,
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = str(Path(tmp_dir) / "sample.calcite")

            SaveProjectUseCase().execute(file_path, state)
            restored = OpenProjectUseCase().execute(file_path)

        self.assertEqual(restored.dataframe.to_dict(orient="list"), df.to_dict(orient="list"))
        self.assertEqual(restored.settings, {"title": "Example"})
        self.assertEqual(restored.statistical_annotations, [{"value_col": "value"}])
        self.assertTrue(np.array_equal(restored.regression_line_params["x_line"], np.array([1, 2])))

    def test_write_project_archive_uses_versioned_manifest_schema(self):
        df = pd.DataFrame({"group": ["A"], "value": [1.0]})
        state = ProjectState(
            dataframe=df,
            settings={"title": "Example"},
            statistical_annotations=[],
            paired_annotations=[],
            regression_line_params=None,
            fit_params=None,
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = str(Path(tmp_dir) / "sample.calcite")
            write_project_archive(file_path, state)

            with zipfile.ZipFile(file_path, "r") as archive:
                members = set(archive.namelist())
                manifest = json.loads(archive.read(MANIFEST_FILENAME).decode("utf-8"))

        self.assertIn(DATAFRAME_FILENAME, members)
        self.assertIn(SETTINGS_FILENAME, members)
        self.assertIn(ANALYSIS_FILENAME, members)
        self.assertEqual(manifest["schema_version"], PROJECT_SCHEMA_VERSION)
        self.assertEqual(manifest["files"]["dataframe"], DATAFRAME_FILENAME)

    def test_read_project_archive_supports_legacy_layout(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "legacy.calcite"
            with zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("data.csv", "group,value\nA,1.0\nB,2.0\n")
                archive.writestr("settings.json", json.dumps({"title": "Legacy"}))
                archive.writestr(
                    "analysis.json",
                    json.dumps({"statistical_annotations": [{"value_col": "value"}]}),
                )

            restored = read_project_archive(str(file_path))

        self.assertEqual(restored.dataframe.to_dict(orient="list"), {"group": ["A", "B"], "value": [1.0, 2.0]})
        self.assertEqual(restored.settings, {"title": "Legacy"})
        self.assertEqual(restored.statistical_annotations, [{"value_col": "value"}])

    def test_build_child_window_title_appends_suffix(self):
        self.assertEqual(build_child_window_title("Calcite", "Filtered"), "Calcite [Filtered]")

    def test_data_use_cases_wrap_service_workflows(self):
        df = pd.DataFrame(
            {
                "id": [1, 1, 2, 2],
                "condition": ["A", "B", "A", "B"],
                "value": [10, 20, 30, 40],
                "group": ["x", "x", "y", "y"],
            }
        )

        restructured = RestructureDataUseCase().execute(
            df[["id", "condition", "value"]],
            {"id_vars": ["id"], "value_vars": ["condition", "value"], "var_name": "metric", "value_name": "result"},
        )
        pivoted = PivotDataUseCase().execute(
            df[["id", "condition", "value"]],
            {"id_vars": ["id"], "var_name": "condition", "value_name": "value"},
        )
        filtered = ApplyAdvancedFilterUseCase().execute(
            df,
            [{"column": "group", "operator": "==", "value": "x"}],
        )
        subset = CreateSubsetUseCase().execute(df, [0, 3])

        self.assertEqual(list(restructured.columns), ["id", "metric", "result"])
        self.assertEqual(pivoted.to_dict(orient="list"), {"id": [1, 2], "A": [10.0, 30.0], "B": [20.0, 40.0]})
        self.assertEqual(filtered.dataframe["group"].tolist(), ["x", "x"])
        self.assertIn("`group` == \"x\"", filtered.query)
        self.assertEqual(subset["value"].tolist(), [10, 40])

    def test_table_controller_clipboard_helpers_round_trip_grid(self):
        text = build_clipboard_text(
            [
                (2, 1, "b"),
                (1, 0, "a"),
                (2, 0, "c"),
            ]
        )

        self.assertEqual(text, "a\t\nc\tb")
        self.assertEqual(parse_clipboard_text(text), [["a", ""], ["c", "b"]])

    def test_import_use_cases_open_csv_and_clipboard(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "sample.csv"
            file_path.write_text("group,value\nA,1\nB,2\n", encoding="utf-8")

            csv_df = OpenCsvUseCase().execute(str(file_path))
            clipboard_df = PasteClipboardUseCase().execute("group\tvalue\nA\t1\nB\t2\n")

        self.assertEqual(csv_df.to_dict(orient="list"), {"group": ["A", "B"], "value": [1, 2]})
        self.assertEqual(clipboard_df.to_dict(orient="list"), {"group": ["A", "B"], "value": [1, 2]})

    def test_save_text_use_case_writes_export_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "results.txt"
            SaveTextUseCase().execute(str(file_path), "analysis output")

            self.assertEqual(file_path.read_text(encoding="utf-8"), "analysis output")

    def test_statistics_formatters_build_readable_summaries(self):
        binary_text = format_binary_test_result(
            title="Independent t-test results (on current graph):",
            value_col="value",
            group_1_label="group=A",
            group_1_n=3,
            group_2_label="group=B",
            group_2_n=3,
            statistic_label="t-statistic",
            statistic_value=2.5,
            p_value=0.02,
            group_1_mean=1.0,
            group_2_mean=2.0,
        )
        paired_text = format_paired_test_result(
            title="Paired t-test results:",
            col1="before",
            col2="after",
            statistic_label="t-statistic",
            statistic_value=3.0,
            p_value=0.07,
            col1_mean=1.2,
            col2_mean=1.5,
        )
        regression_text = format_regression_summary("linear", ["Y = 1.0000 * X + 0.0000"])
        chi_text = format_chi_squared_result(
            RunChiSquaredAnalysisUseCase().execute(
                pd.DataFrame({"rows": ["A", "A", "B", "B"], "cols": ["X", "Y", "X", "Y"]}),
                "rows",
                "cols",
            ),
            "rows",
            "cols",
        )
        spearman_text = format_spearman_correlation_result(
            RunSpearmanCorrelationUseCase().execute(
                pd.DataFrame({"x": [1, 2, 3], "y": [1, 2, 4]}),
                "x",
                "y",
            ),
            "x",
            "y",
        )
        pearson_text = format_pearson_correlation_result(
            RunPearsonCorrelationUseCase().execute(
                pd.DataFrame({"x": [1, 2, 3], "y": [2, 4, 6]}),
                "x",
                "y",
            ),
            "x",
            "y",
        )
        proportion_text = format_two_proportion_result(
            RunTwoProportionAnalysisUseCase().execute(
                pd.DataFrame(
                    {
                        "group": ["A"] * 10 + ["B"] * 10,
                        "outcome": ["Yes"] * 8 + ["No"] * 2 + ["Yes"] * 3 + ["No"] * 7,
                    }
                ),
                "group",
                "outcome",
            ),
            "group",
            "outcome",
        )
        shapiro_text = format_shapiro_result(
            RunShapiroAnalysisUseCase().execute(
                pd.DataFrame({"value": [1, 2, 3, 4, 5, 6]}),
                "value",
                pd.Series(["A", "A", "A", "B", "B", "B"]),
                "group",
            )
        )

        self.assertIn("Conclusion: The difference is statistically significant", binary_text)
        self.assertIn("Conclusion: The difference is not statistically significant", paired_text)
        self.assertIn("Linear Regression Results", regression_text)
        self.assertIn("Chi-squared statistic", chi_text)
        self.assertIn("Pearson's r", pearson_text)
        self.assertIn("Spearman's rho", spearman_text)
        self.assertIn("2-Proportion z-test Results", proportion_text)
        self.assertIn("95% CI for difference", proportion_text)
        self.assertIn("Shapiro-Wilk Normality Test Results", shapiro_text)

    def test_run_regression_analysis_use_case_returns_overlay_params_and_summary(self):
        df = pd.DataFrame({"x": [1, 2, 3, 4], "y": [2, 4, 6, 8]})

        result = RunRegressionAnalysisUseCase().execute(
            dataframe=df,
            x_col="x",
            y_col="y",
            model="linear",
        )

        self.assertIsNone(result.fit_params)
        self.assertIsNotNone(result.regression_line_params)
        self.assertIn("r_squared", result.regression_line_params)
        self.assertTrue(result.summary_lines)

    def test_statistical_use_cases_return_structured_results(self):
        chi_result = RunChiSquaredAnalysisUseCase().execute(
            pd.DataFrame({"rows": ["A", "A", "B", "B"], "cols": ["X", "Y", "X", "Y"]}),
            "rows",
            "cols",
        )
        pearson_result = RunPearsonCorrelationUseCase().execute(
            pd.DataFrame({"x": [1, 2, 3, 4], "y": [2, 4, 6, 8]}),
            "x",
            "y",
        )
        proportion_result = RunTwoProportionAnalysisUseCase().execute(
            pd.DataFrame(
                {
                    "group": ["A"] * 10 + ["B"] * 10,
                    "outcome": ["Yes"] * 8 + ["No"] * 2 + ["Yes"] * 3 + ["No"] * 7,
                }
            ),
            "group",
            "outcome",
        )
        spearman_result = RunSpearmanCorrelationUseCase().execute(
            pd.DataFrame({"x": [1, 2, 3, 4], "y": [2, 4, 6, 8]}),
            "x",
            "y",
        )
        shapiro_result = RunShapiroAnalysisUseCase().execute(
            pd.DataFrame({"value": [1, 2, 3, 4, 5, 6]}),
            "value",
            pd.Series(["A", "A", "A", "B", "B", "B"]),
            "group",
        )

        self.assertEqual(list(chi_result.contingency_table.columns), ["X", "Y"])
        self.assertEqual(chi_result.standardized_residuals.shape, (2, 2))
        self.assertEqual(chi_result.contribution_table.shape, (2, 2))
        self.assertEqual(chi_result.cramers_v, 0.0)
        self.assertEqual(pearson_result.sample_size, 4)
        self.assertAlmostEqual(pearson_result.r, 1.0)
        self.assertEqual(proportion_result.group1_label, "A")
        self.assertLess(proportion_result.ci_low_group1, proportion_result.proportion_group1)
        self.assertGreater(proportion_result.ci_high_group1, proportion_result.proportion_group1)
        self.assertLess(proportion_result.ci_low_difference, proportion_result.difference_in_proportions)
        self.assertGreater(proportion_result.ci_high_difference, proportion_result.difference_in_proportions)
        self.assertLess(proportion_result.p_value, 0.05)
        self.assertEqual(spearman_result.sample_size, 4)
        self.assertEqual(len(shapiro_result.groups), 2)

    def test_handler_package_exports_public_entrypoints(self):
        self.assertEqual(ActionHandler.__name__, "ActionHandler")
        self.assertEqual(GraphManager.__name__, "GraphManager")
        self.assertEqual(StatisticalHandler.__name__, "StatisticalHandler")

    def test_dataframe_history_manager_undo_redo_round_trip(self):
        original = pd.DataFrame({"value": [1, 2]})
        changed = pd.DataFrame({"value": [1, 3]})
        transitions = []
        manager = DataframeHistoryManager(on_change=lambda can_undo, can_redo: transitions.append((can_undo, can_redo)))
        manager.reset(original)
        manager.record_change(original, changed)

        undone = manager.undo(changed)
        redone = manager.redo(undone)

        self.assertEqual(undone.to_dict(orient="list"), {"value": [1, 2]})
        self.assertEqual(redone.to_dict(orient="list"), {"value": [1, 3]})
        self.assertIn((False, False), transitions)
        self.assertIn((True, False), transitions)
        self.assertIn((False, True), transitions)

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
