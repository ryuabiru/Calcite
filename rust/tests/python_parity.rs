use std::path::PathBuf;
use std::process::Command;

use calcite_rust::analysis::{
    run_chi_squared_analysis, run_independent_t_test_analysis, run_linear_regression_analysis,
    run_mann_whitney_u_analysis, run_one_way_anova_analysis, run_paired_t_test_analysis,
    run_pearson_correlation_analysis, run_shapiro_wilk_analysis, run_spearman_correlation_analysis,
    run_two_proportion_analysis, run_wilcoxon_signed_rank_analysis,
};
use calcite_rust::state::{load_csv_table, TableViewState};
use calcite_rust::transform::{pivot_dataframe, restructure_dataframe};
use serde::Deserialize;

#[derive(Debug, Deserialize, PartialEq, Eq)]
struct CsvSnapshot {
    headers: Vec<String>,
    rows: Vec<Vec<String>>,
}

#[derive(Debug, Deserialize)]
struct PearsonSnapshot {
    r: f64,
    p_value: f64,
    sample_size: usize,
}

#[derive(Debug, Deserialize)]
struct SpearmanSnapshot {
    rho: f64,
    p_value: f64,
    sample_size: usize,
}

#[derive(Debug, Deserialize)]
struct IndependentTTestSnapshot {
    t_statistic: f64,
    p_value: f64,
    degrees_of_freedom: f64,
    sample_size1: usize,
    sample_size2: usize,
    mean1: f64,
    mean2: f64,
}

#[derive(Debug, Deserialize)]
struct PairedTTestSnapshot {
    t_statistic: f64,
    p_value: f64,
    degrees_of_freedom: f64,
    sample_size: usize,
    mean1: f64,
    mean2: f64,
    mean_difference: f64,
}

#[derive(Debug, Deserialize)]
struct MannWhitneySnapshot {
    u_statistic: f64,
    p_value: f64,
    sample_size1: usize,
    sample_size2: usize,
    mean_rank1: f64,
    mean_rank2: f64,
}

#[derive(Debug, Deserialize)]
struct WilcoxonSnapshot {
    w_statistic: f64,
    p_value: f64,
    sample_size: usize,
    nonzero_difference_count: usize,
    positive_rank_sum: f64,
    negative_rank_sum: f64,
}

#[derive(Debug, Deserialize)]
struct LinearRegressionSnapshot {
    slope: f64,
    intercept: f64,
    r_squared: f64,
    p_value: f64,
    sample_size: usize,
}

#[derive(Debug, Deserialize)]
struct AnovaGroupSnapshot {
    label: String,
    sample_size: usize,
    mean: f64,
}

#[derive(Debug, Deserialize)]
struct AnovaSnapshot {
    groups: Vec<AnovaGroupSnapshot>,
    f_statistic: f64,
    p_value: f64,
    between_group_df: usize,
    within_group_df: usize,
}

#[derive(Debug, Deserialize)]
struct ShapiroGroupSnapshot {
    group_name: String,
    sample_size: usize,
    statistic: Option<f64>,
    skipped: bool,
}

#[derive(Debug, Deserialize)]
struct ShapiroSnapshot {
    value_col: String,
    group_col: String,
    groups: Vec<ShapiroGroupSnapshot>,
}

#[derive(Debug, Deserialize)]
struct ChiSquaredSnapshot {
    rows_col: String,
    cols_col: String,
    contingency_table: Vec<Vec<usize>>,
    row_labels: Vec<String>,
    column_labels: Vec<String>,
    expected_table: Vec<Vec<f64>>,
    standardized_residuals: Vec<Vec<f64>>,
    contribution_table: Vec<Vec<f64>>,
    chi2: f64,
    p_value: f64,
    degrees_of_freedom: usize,
    cramers_v: f64,
}

#[derive(Debug, Deserialize)]
struct TwoProportionSnapshot {
    rows_col: String,
    cols_col: String,
    group1_label: String,
    group2_label: String,
    success_label: String,
    success_count_group1: usize,
    success_count_group2: usize,
    total_group1: usize,
    total_group2: usize,
    proportion_group1: f64,
    proportion_group2: f64,
    ci_low_group1: f64,
    ci_high_group1: f64,
    ci_low_group2: f64,
    ci_high_group2: f64,
    difference_in_proportions: f64,
    ci_low_difference: f64,
    ci_high_difference: f64,
    z_statistic: f64,
    p_value: f64,
}

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("workspace root")
        .to_path_buf()
}

fn sample_data_path(name: &str) -> PathBuf {
    repo_root().join("sample_data").join(name)
}

fn run_python_json(script: &str) -> serde_json::Value {
    let output = Command::new("uv")
        .current_dir(repo_root())
        .env("UV_CACHE_DIR", "/private/tmp/uv-cache")
        .args(["run", "python", "-c", script])
        .output()
        .expect("run python reference");

    if !output.status.success() {
        panic!(
            "python reference failed\nstdout:\n{}\nstderr:\n{}",
            String::from_utf8_lossy(&output.stdout),
            String::from_utf8_lossy(&output.stderr)
        );
    }

    serde_json::from_slice(&output.stdout).expect("parse python json")
}

fn assert_close(actual: f64, expected: f64, tolerance: f64, label: &str) {
    assert!(
        (actual - expected).abs() <= tolerance,
        "{label} mismatch: actual={actual}, expected={expected}, tolerance={tolerance}"
    );
}

fn assert_matrix_close(actual: &[Vec<f64>], expected: &[Vec<f64>], tolerance: f64, label: &str) {
    assert_eq!(actual.len(), expected.len(), "{label} row count mismatch");
    for (row_index, (actual_row, expected_row)) in actual.iter().zip(expected.iter()).enumerate() {
        assert_eq!(
            actual_row.len(),
            expected_row.len(),
            "{label} column count mismatch at row {row_index}"
        );
        for (col_index, (actual_value, expected_value)) in actual_row.iter().zip(expected_row.iter()).enumerate() {
            assert_close(
                *actual_value,
                *expected_value,
                tolerance,
                &format!("{label}[{row_index}][{col_index}]"),
            );
        }
    }
}

fn assert_matrix_usize(actual: &[Vec<usize>], expected: &[Vec<usize>], label: &str) {
    assert_eq!(actual, expected, "{label} mismatch");
}

#[test]
fn csv_loading_matches_python_reference() {
    let path = sample_data_path("for_correlation.csv");
    let rust_table = load_csv_table(&path).expect("load csv");

    let python = run_python_json(&format!(
        r#"
import json
import pandas as pd

df = pd.read_csv(r"{path}")
snapshot = {{
    "headers": df.columns.tolist(),
    "rows": df.astype(str).values.tolist(),
}}
print(json.dumps(snapshot))
"#,
        path = path.display()
    ));
    let python_snapshot: CsvSnapshot = serde_json::from_value(python).expect("python snapshot");

    assert_eq!(rust_table.headers, python_snapshot.headers);
    assert_eq!(rust_table.rows, python_snapshot.rows);
}

#[test]
fn restructure_dataframe_matches_python_reference() {
    let path = sample_data_path("for_paired_ttest.csv");
    let rust_table = load_csv_table(&path).expect("load csv");
    let rust_result = restructure_dataframe(
        &rust_table,
        &[String::from("condition")],
        &[String::from("before"), String::from("after")],
        "time",
        "score",
    )
    .expect("restructure");

    let python = run_python_json(&format!(
        r#"
import json
import pandas as pd
from calcite.services.data_service import restructure_dataframe

df = pd.read_csv(r"{path}")
snapshot = restructure_dataframe(
    df,
    {{
        "id_vars": ["condition"],
        "value_vars": ["before", "after"],
        "var_name": "time",
        "value_name": "score",
    }},
)
print(json.dumps({{
    "headers": snapshot.columns.tolist(),
    "rows": snapshot.astype(str).values.tolist(),
}}))
"#,
        path = path.display()
    ));
    let python_snapshot: CsvSnapshot = serde_json::from_value(python).expect("python snapshot");

    assert_eq!(rust_result.headers, python_snapshot.headers);
    assert_eq!(rust_result.rows.len(), python_snapshot.rows.len());
    for (row_index, (rust_row, python_row)) in rust_result
        .rows
        .iter()
        .zip(python_snapshot.rows.iter())
        .enumerate()
    {
        assert_eq!(
            rust_row[0], python_row[0],
            "restructure row label mismatch at row {row_index}"
        );
        assert_eq!(rust_row.len(), python_row.len());
        for (col_index, (rust_cell, python_cell)) in
            rust_row.iter().zip(python_row.iter()).enumerate().skip(1)
        {
            assert_eq!(
                rust_cell, python_cell,
                "restructure cell mismatch at row {row_index}, column {col_index}"
            );
        }
    }
}

#[test]
fn pivot_dataframe_matches_python_reference() {
    let path = sample_data_path("for_4pl_regression.csv");
    let rust_table = load_csv_table(&path).expect("load csv");
    let rust_result =
        pivot_dataframe(&rust_table, &[String::from("group")], "dose", "response").expect("pivot");

    let python = run_python_json(&format!(
        r#"
import json
import pandas as pd
from calcite.services.data_service import pivot_dataframe

def format_number(value):
    if pd.isna(value):
        return ""
    if isinstance(value, str):
        return value
    if abs(value - round(value)) < 1e-12:
        return str(int(round(value)))
    text = f"{{value}}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text

df = pd.read_csv(r"{path}", dtype={{"group": str, "dose": str, "response": float}})
df["group"] = pd.Categorical(df["group"], categories=pd.unique(df["group"]), ordered=True)
df["dose"] = pd.Categorical(df["dose"], categories=pd.unique(df["dose"]), ordered=True)
snapshot = pivot_dataframe(
    df,
    {{
        "id_vars": ["group"],
        "var_name": "dose",
        "value_name": "response",
    }},
)
print(json.dumps({{
    "headers": snapshot.columns.tolist(),
    "rows": [[format_number(value) for value in row] for row in snapshot.itertuples(index=False, name=None)],
}}))
"#,
        path = path.display()
    ));
    let python_snapshot: CsvSnapshot = serde_json::from_value(python).expect("python snapshot");

    assert_eq!(rust_result.headers, python_snapshot.headers);
    assert_eq!(rust_result.rows.len(), python_snapshot.rows.len());
    for (row_index, (rust_row, python_row)) in rust_result
        .rows
        .iter()
        .zip(python_snapshot.rows.iter())
        .enumerate()
    {
        assert_eq!(
            rust_row[0], python_row[0],
            "pivot row label mismatch at row {row_index}"
        );
        assert_eq!(rust_row.len(), python_row.len());
        for (col_index, (rust_cell, python_cell)) in
            rust_row.iter().zip(python_row.iter()).enumerate().skip(1)
        {
            let rust_value: f64 = rust_cell.parse().expect("rust pivot float");
            let python_value: f64 = python_cell.parse().expect("python pivot float");
            assert_close(
                rust_value,
                python_value,
                1e-8,
                &format!("pivot cell [{row_index}][{col_index}]"),
            );
        }
    }
}

#[test]
fn analysis_results_match_python_reference() {
    let correlation_path = sample_data_path("for_correlation.csv");
    let contingency_path = sample_data_path("for_contingency.csv");
    let ttest_path = sample_data_path("for_paired_ttest.csv");
    let anova_path = sample_data_path("for_anova.csv");

    let correlation_table = load_csv_table(&correlation_path).expect("load correlation csv");
    let contingency_table = load_csv_table(&contingency_path).expect("load contingency csv");
    let ttest_table = load_csv_table(&ttest_path).expect("load ttest csv");
    let anova_table = load_csv_table(&anova_path).expect("load anova csv");
    let contingency_sig_rows: Vec<usize> = contingency_table
        .rows
        .iter()
        .enumerate()
        .filter_map(|(index, row)| match row.first() {
            Some(label) if label.ends_with("_sig") => Some(index),
            _ => None,
        })
        .collect();
    let contingency_sig_table = calcite_rust::transform::subset_rows(&contingency_table, &contingency_sig_rows);

    let rust_pearson = run_pearson_correlation_analysis(
        &correlation_table,
        &TableViewState::default(),
        "x_significant",
        "y_significant",
    )
    .expect("pearson");
    let rust_spearman = run_spearman_correlation_analysis(
        &correlation_table,
        &TableViewState::default(),
        "x_significant",
        "y_significant",
    )
    .expect("spearman");
    let rust_chi_squared = run_chi_squared_analysis(
        &contingency_sig_table,
        &TableViewState::default(),
        "group",
        "preference",
    )
    .expect("chi squared");
    let rust_two_proportion = run_two_proportion_analysis(
        &contingency_sig_table,
        &TableViewState::default(),
        "group",
        "preference",
    )
    .expect("two proportion");
    let rust_linear = run_linear_regression_analysis(
        &correlation_table,
        &TableViewState::default(),
        "x_significant",
        "y_significant",
    )
    .expect("linear regression");
    let rust_anova = run_one_way_anova_analysis(
        &anova_table,
        &TableViewState::default(),
        "group",
        "value",
    )
    .expect("anova");
    let rust_independent_t = run_independent_t_test_analysis(
        &ttest_table,
        &TableViewState::default(),
        "before",
        "after",
    )
    .expect("independent t-test");
    let rust_paired_t = run_paired_t_test_analysis(
        &ttest_table,
        &TableViewState::default(),
        "before",
        "after",
    )
    .expect("paired t-test");
    let rust_mann_whitney = run_mann_whitney_u_analysis(
        &ttest_table,
        &TableViewState::default(),
        "before",
        "after",
    )
    .expect("mann-whitney");
    let rust_wilcoxon = run_wilcoxon_signed_rank_analysis(
        &ttest_table,
        &TableViewState::default(),
        "before",
        "after",
    )
    .expect("wilcoxon");
    let rust_shapiro = run_shapiro_wilk_analysis(
        &anova_table,
        &TableViewState::default(),
        "group",
        "value",
    )
    .expect("shapiro");

    let python = run_python_json(&format!(
        r#"
import json
import pandas as pd
from calcite.application.statistics_use_cases import (
    RunChiSquaredAnalysisUseCase,
    RunPearsonCorrelationUseCase,
    RunSpearmanCorrelationUseCase,
    RunTwoProportionAnalysisUseCase,
)
from scipy.stats import f_oneway, linregress, mannwhitneyu, shapiro, ttest_ind, ttest_rel, wilcoxon

correlation_df = pd.read_csv(r"{correlation_path}")
pearson = RunPearsonCorrelationUseCase().execute(correlation_df, "x_significant", "y_significant")
spearman = RunSpearmanCorrelationUseCase().execute(correlation_df, "x_significant", "y_significant")
linreg = linregress(correlation_df["x_significant"], correlation_df["y_significant"])

contingency_df = pd.read_csv(r"{contingency_path}")
contingency_df = contingency_df[contingency_df["group"].str.endswith("_sig")].copy()
contingency_df["group"] = pd.Categorical(contingency_df["group"], categories=pd.unique(contingency_df["group"]), ordered=True)
contingency_df["preference"] = pd.Categorical(contingency_df["preference"], categories=pd.unique(contingency_df["preference"]), ordered=True)
chi = RunChiSquaredAnalysisUseCase().execute(contingency_df, "group", "preference")
two_prop = RunTwoProportionAnalysisUseCase().execute(contingency_df, "group", "preference")

ttest_df = pd.read_csv(r"{ttest_path}")
independent = ttest_ind(ttest_df["before"], ttest_df["after"])
paired = ttest_rel(ttest_df["before"], ttest_df["after"])
mann_whitney = mannwhitneyu(ttest_df["before"], ttest_df["after"], alternative="two-sided", method="asymptotic")
wilcoxon_result = wilcoxon(ttest_df["before"], ttest_df["after"], alternative="two-sided", zero_method="wilcox", correction=False)
mw_combined = pd.DataFrame(
    {{
        "value": pd.concat([ttest_df["before"], ttest_df["after"]], ignore_index=True),
        "group": [0] * len(ttest_df["before"]) + [1] * len(ttest_df["after"]),
    }}
)
mw_combined["rank"] = mw_combined["value"].rank(method="average")
mw_rank_sum1 = float(mw_combined.loc[mw_combined["group"] == 0, "rank"].sum())
mw_rank_sum2 = float(mw_combined.loc[mw_combined["group"] == 1, "rank"].sum())
mw_mean_rank1 = mw_rank_sum1 / len(ttest_df["before"])
mw_mean_rank2 = mw_rank_sum2 / len(ttest_df["after"])
wx_differences = (ttest_df["before"] - ttest_df["after"]).loc[lambda s: s.abs() > 0]
wx_abs_ranks = wx_differences.abs().rank(method="average")
wx_positive_rank_sum = float(wx_abs_ranks[wx_differences > 0].sum())
wx_negative_rank_sum = float(wx_abs_ranks[wx_differences < 0].sum())

anova_df = pd.read_csv(r"{anova_path}")
anova_groups = [group for group in pd.unique(anova_df["group"])]
anova_samples = [anova_df.loc[anova_df["group"] == group, "value"] for group in anova_groups]
anova_f, anova_p = f_oneway(*anova_samples)
shapiro_groups = []
for group in anova_groups:
    data = anova_df.loc[anova_df["group"] == group, "value"]
    statistic, p_value = shapiro(data)
    shapiro_groups.append({{
        "group_name": str(group),
        "sample_size": int(len(data)),
        "statistic": float(statistic),
        "p_value": float(p_value),
        "skipped": False,
    }})

snapshot = {{
    "pearson": {{
        "r": float(pearson.r),
        "p_value": float(pearson.p_value),
        "sample_size": pearson.sample_size,
    }},
    "spearman": {{
        "rho": float(spearman.rho),
        "p_value": float(spearman.p_value),
        "sample_size": spearman.sample_size,
    }},
    "chi_squared": {{
        "rows_col": "group",
        "cols_col": "preference",
        "contingency_table": chi.contingency_table.astype(int).values.tolist(),
        "row_labels": chi.contingency_table.index.astype(str).tolist(),
        "column_labels": chi.contingency_table.columns.astype(str).tolist(),
        "expected_table": chi.expected_table.astype(float).values.tolist(),
        "standardized_residuals": chi.standardized_residuals.astype(float).values.tolist(),
        "contribution_table": chi.contribution_table.astype(float).values.tolist(),
        "chi2": float(chi.chi2),
        "p_value": float(chi.p_value),
        "degrees_of_freedom": int(chi.degrees_of_freedom),
        "cramers_v": float(chi.cramers_v),
    }},
    "two_proportion": {{
        "rows_col": "group",
        "cols_col": "preference",
        "group1_label": two_prop.group1_label,
        "group2_label": two_prop.group2_label,
        "success_label": two_prop.success_label,
        "success_count_group1": two_prop.success_count_group1,
        "success_count_group2": two_prop.success_count_group2,
        "total_group1": two_prop.total_group1,
        "total_group2": two_prop.total_group2,
        "proportion_group1": float(two_prop.proportion_group1),
        "proportion_group2": float(two_prop.proportion_group2),
        "ci_low_group1": float(two_prop.ci_low_group1),
        "ci_high_group1": float(two_prop.ci_high_group1),
        "ci_low_group2": float(two_prop.ci_low_group2),
        "ci_high_group2": float(two_prop.ci_high_group2),
        "difference_in_proportions": float(two_prop.difference_in_proportions),
        "ci_low_difference": float(two_prop.ci_low_difference),
        "ci_high_difference": float(two_prop.ci_high_difference),
        "z_statistic": float(two_prop.z_statistic),
        "p_value": float(two_prop.p_value),
    }},
    "linear_regression": {{
        "slope": float(linreg.slope),
        "intercept": float(linreg.intercept),
        "r_squared": float(linreg.rvalue ** 2),
        "p_value": float(linreg.pvalue),
        "sample_size": int(len(correlation_df)),
    }},
    "anova": {{
        "groups": [
            {{
                "label": str(group),
                "sample_size": int(len(sample)),
                "mean": float(sample.mean()),
            }}
            for group, sample in zip(anova_groups, anova_samples)
        ],
        "f_statistic": float(anova_f),
        "p_value": float(anova_p),
        "between_group_df": int(len(anova_groups) - 1),
        "within_group_df": int(sum(len(sample) for sample in anova_samples) - len(anova_groups)),
    }},
    "independent_t_test": {{
        "t_statistic": float(independent.statistic),
        "p_value": float(independent.pvalue),
        "degrees_of_freedom": float(independent.df),
        "sample_size1": int(len(ttest_df["before"])),
        "sample_size2": int(len(ttest_df["after"])),
        "mean1": float(ttest_df["before"].mean()),
        "mean2": float(ttest_df["after"].mean()),
    }},
    "paired_t_test": {{
        "t_statistic": float(paired.statistic),
        "p_value": float(paired.pvalue),
        "degrees_of_freedom": float(paired.df),
        "sample_size": int(len(ttest_df)),
        "mean1": float(ttest_df["before"].mean()),
        "mean2": float(ttest_df["after"].mean()),
        "mean_difference": float((ttest_df["before"] - ttest_df["after"]).mean()),
    }},
    "mann_whitney": {{
        "u_statistic": float(mann_whitney.statistic),
        "p_value": float(mann_whitney.pvalue),
        "sample_size1": int(len(ttest_df["before"])),
        "sample_size2": int(len(ttest_df["after"])),
        "mean_rank1": float(mw_mean_rank1),
        "mean_rank2": float(mw_mean_rank2),
    }},
    "wilcoxon": {{
        "w_statistic": float(wilcoxon_result.statistic),
        "p_value": float(wilcoxon_result.pvalue),
        "sample_size": int(len(ttest_df)),
        "nonzero_difference_count": int((ttest_df["before"] - ttest_df["after"]).abs().gt(0).sum()),
        "positive_rank_sum": float(wx_positive_rank_sum),
        "negative_rank_sum": float(wx_negative_rank_sum),
    }},
    "shapiro": {{
        "value_col": "value",
        "group_col": "group",
        "groups": shapiro_groups,
    }},
}}
print(json.dumps(snapshot))
"#,
        correlation_path = correlation_path.display(),
        contingency_path = contingency_path.display(),
        ttest_path = ttest_path.display(),
        anova_path = anova_path.display(),
    ));

    let python_json: serde_json::Value = python;
    let python_pearson: PearsonSnapshot =
        serde_json::from_value(python_json["pearson"].clone()).expect("pearson snapshot");
    let python_spearman: SpearmanSnapshot =
        serde_json::from_value(python_json["spearman"].clone()).expect("spearman snapshot");
    let python_chi: ChiSquaredSnapshot =
        serde_json::from_value(python_json["chi_squared"].clone()).expect("chi snapshot");
    let python_two: TwoProportionSnapshot =
        serde_json::from_value(python_json["two_proportion"].clone()).expect("two proportion snapshot");
    let python_linear: LinearRegressionSnapshot =
        serde_json::from_value(python_json["linear_regression"].clone()).expect("linear regression snapshot");
    let python_anova: AnovaSnapshot =
        serde_json::from_value(python_json["anova"].clone()).expect("anova snapshot");
    let python_independent: IndependentTTestSnapshot = serde_json::from_value(
        python_json["independent_t_test"].clone(),
    )
    .expect("independent t-test snapshot");
    let python_paired: PairedTTestSnapshot =
        serde_json::from_value(python_json["paired_t_test"].clone()).expect("paired t-test snapshot");
    let python_mann_whitney: MannWhitneySnapshot = serde_json::from_value(
        python_json["mann_whitney"].clone(),
    )
    .expect("mann-whitney snapshot");
    let python_wilcoxon: WilcoxonSnapshot =
        serde_json::from_value(python_json["wilcoxon"].clone()).expect("wilcoxon snapshot");
    let python_shapiro: ShapiroSnapshot =
        serde_json::from_value(python_json["shapiro"].clone()).expect("shapiro snapshot");

    assert_eq!(rust_pearson.sample_size, python_pearson.sample_size);
    assert_close(rust_pearson.r, python_pearson.r, 1e-8, "pearson r");
    assert_close(rust_pearson.p_value, python_pearson.p_value, 1e-8, "pearson p_value");
    assert_eq!(rust_spearman.sample_size, python_spearman.sample_size);
    assert_close(rust_spearman.rho, python_spearman.rho, 1e-8, "spearman rho");
    assert_close(rust_spearman.p_value, python_spearman.p_value, 1e-8, "spearman p_value");

    assert_eq!(rust_chi_squared.rows_col, python_chi.rows_col);
    assert_eq!(rust_chi_squared.cols_col, python_chi.cols_col);
    assert_matrix_usize(
        &rust_chi_squared.contingency_table,
        &python_chi.contingency_table,
        "chi-squared contingency table",
    );
    assert_eq!(rust_chi_squared.row_labels, python_chi.row_labels);
    assert_eq!(rust_chi_squared.column_labels, python_chi.column_labels);
    assert_matrix_close(
        &rust_chi_squared.expected_table,
        &python_chi.expected_table,
        1e-8,
        "chi-squared expected table",
    );
    assert_matrix_close(
        &rust_chi_squared.standardized_residuals,
        &python_chi.standardized_residuals,
        1e-8,
        "chi-squared standardized residuals",
    );
    assert_matrix_close(
        &rust_chi_squared.contribution_table,
        &python_chi.contribution_table,
        1e-8,
        "chi-squared contribution table",
    );
    assert_close(rust_chi_squared.chi2, python_chi.chi2, 1e-8, "chi-squared chi2");
    assert_close(
        rust_chi_squared.p_value,
        python_chi.p_value,
        1e-8,
        "chi-squared p_value",
    );
    assert_eq!(
        rust_chi_squared.degrees_of_freedom,
        python_chi.degrees_of_freedom
    );
    assert_close(
        rust_chi_squared.cramers_v,
        python_chi.cramers_v,
        1e-8,
        "chi-squared cramers_v",
    );

    assert_eq!(rust_two_proportion.rows_col, python_two.rows_col);
    assert_eq!(rust_two_proportion.cols_col, python_two.cols_col);
    assert_eq!(rust_two_proportion.group1_label, python_two.group1_label);
    assert_eq!(rust_two_proportion.group2_label, python_two.group2_label);
    assert_eq!(rust_two_proportion.success_label, python_two.success_label);
    assert_eq!(
        rust_two_proportion.success_count_group1,
        python_two.success_count_group1
    );
    assert_eq!(
        rust_two_proportion.success_count_group2,
        python_two.success_count_group2
    );
    assert_eq!(rust_two_proportion.total_group1, python_two.total_group1);
    assert_eq!(rust_two_proportion.total_group2, python_two.total_group2);
    assert_close(
        rust_two_proportion.proportion_group1,
        python_two.proportion_group1,
        1e-8,
        "two-proportion proportion_group1",
    );
    assert_close(
        rust_two_proportion.proportion_group2,
        python_two.proportion_group2,
        1e-8,
        "two-proportion proportion_group2",
    );
    assert_close(
        rust_two_proportion.ci_low_group1,
        python_two.ci_low_group1,
        1e-8,
        "two-proportion ci_low_group1",
    );
    assert_close(
        rust_two_proportion.ci_high_group1,
        python_two.ci_high_group1,
        1e-8,
        "two-proportion ci_high_group1",
    );
    assert_close(
        rust_two_proportion.ci_low_group2,
        python_two.ci_low_group2,
        1e-8,
        "two-proportion ci_low_group2",
    );
    assert_close(
        rust_two_proportion.ci_high_group2,
        python_two.ci_high_group2,
        1e-8,
        "two-proportion ci_high_group2",
    );
    assert_close(
        rust_two_proportion.difference_in_proportions,
        python_two.difference_in_proportions,
        1e-8,
        "two-proportion difference_in_proportions",
    );
    assert_close(
        rust_two_proportion.ci_low_difference,
        python_two.ci_low_difference,
        1e-8,
        "two-proportion ci_low_difference",
    );
    assert_close(
        rust_two_proportion.ci_high_difference,
        python_two.ci_high_difference,
        1e-8,
        "two-proportion ci_high_difference",
    );
    assert_close(
        rust_two_proportion.z_statistic,
        python_two.z_statistic,
        1e-8,
        "two-proportion z_statistic",
    );
    assert_close(
        rust_two_proportion.p_value,
        python_two.p_value,
        1e-6,
        "two-proportion p_value",
    );

    assert_eq!(rust_linear.sample_size, python_linear.sample_size);
    assert_close(rust_linear.slope, python_linear.slope, 1e-8, "linear slope");
    assert_close(
        rust_linear.intercept,
        python_linear.intercept,
        1e-8,
        "linear intercept",
    );
    assert_close(
        rust_linear.r_squared,
        python_linear.r_squared,
        1e-8,
        "linear r_squared",
    );
    assert_close(
        rust_linear.p_value,
        python_linear.p_value,
        1e-8,
        "linear p_value",
    );

    assert_eq!(rust_anova.between_group_df, python_anova.between_group_df);
    assert_eq!(rust_anova.within_group_df, python_anova.within_group_df);
    assert_close(
        rust_anova.f_statistic,
        python_anova.f_statistic,
        1e-8,
        "anova f_statistic",
    );
    assert_close(
        rust_anova.p_value,
        python_anova.p_value,
        1e-8,
        "anova p_value",
    );
    assert_eq!(rust_anova.groups.len(), python_anova.groups.len());
    for (rust_group, python_group) in rust_anova.groups.iter().zip(python_anova.groups.iter()) {
        assert_eq!(rust_group.label, python_group.label);
        assert_eq!(rust_group.sample_size, python_group.sample_size);
        assert_close(rust_group.mean, python_group.mean, 1e-8, "anova group mean");
    }

    assert_eq!(rust_independent_t.sample_size1, python_independent.sample_size1);
    assert_eq!(rust_independent_t.sample_size2, python_independent.sample_size2);
    assert_close(
        rust_independent_t.mean1,
        python_independent.mean1,
        1e-8,
        "independent mean1",
    );
    assert_close(
        rust_independent_t.mean2,
        python_independent.mean2,
        1e-8,
        "independent mean2",
    );
    assert_close(
        rust_independent_t.t_statistic,
        python_independent.t_statistic,
        1e-8,
        "independent t_statistic",
    );
    assert_close(
        rust_independent_t.degrees_of_freedom,
        python_independent.degrees_of_freedom,
        1e-8,
        "independent degrees_of_freedom",
    );
    assert_close(
        rust_independent_t.p_value,
        python_independent.p_value,
        1e-8,
        "independent p_value",
    );

    assert_eq!(rust_paired_t.sample_size, python_paired.sample_size);
    assert_close(rust_paired_t.mean1, python_paired.mean1, 1e-8, "paired mean1");
    assert_close(rust_paired_t.mean2, python_paired.mean2, 1e-8, "paired mean2");
    assert_close(
        rust_paired_t.mean_difference,
        python_paired.mean_difference,
        1e-8,
        "paired mean_difference",
    );
    assert_close(
        rust_paired_t.t_statistic,
        python_paired.t_statistic,
        1e-8,
        "paired t_statistic",
    );
    assert_close(
        rust_paired_t.degrees_of_freedom,
        python_paired.degrees_of_freedom,
        1e-8,
        "paired degrees_of_freedom",
    );
    assert_close(
        rust_paired_t.p_value,
        python_paired.p_value,
        1e-8,
        "paired p_value",
    );

    assert_eq!(rust_mann_whitney.sample_size1, python_mann_whitney.sample_size1);
    assert_eq!(rust_mann_whitney.sample_size2, python_mann_whitney.sample_size2);
    assert_close(
        rust_mann_whitney.u_statistic,
        python_mann_whitney.u_statistic,
        1e-8,
        "mann-whitney u_statistic",
    );
    assert_close(
        rust_mann_whitney.mean_rank1,
        python_mann_whitney.mean_rank1,
        1e-8,
        "mann-whitney mean_rank1",
    );
    assert_close(
        rust_mann_whitney.mean_rank2,
        python_mann_whitney.mean_rank2,
        1e-8,
        "mann-whitney mean_rank2",
    );
    assert_close(
        rust_mann_whitney.p_value,
        python_mann_whitney.p_value,
        5e-2,
        "mann-whitney p_value",
    );

    assert_eq!(rust_wilcoxon.sample_size, python_wilcoxon.sample_size);
    assert_eq!(
        rust_wilcoxon.nonzero_difference_count,
        python_wilcoxon.nonzero_difference_count
    );
    assert_close(
        rust_wilcoxon.w_statistic,
        python_wilcoxon.w_statistic,
        1e-8,
        "wilcoxon w_statistic",
    );
    assert_close(
        rust_wilcoxon.positive_rank_sum,
        python_wilcoxon.positive_rank_sum,
        1e-8,
        "wilcoxon positive_rank_sum",
    );
    assert_close(
        rust_wilcoxon.negative_rank_sum,
        python_wilcoxon.negative_rank_sum,
        1e-8,
        "wilcoxon negative_rank_sum",
    );
    assert_close(
        rust_wilcoxon.p_value,
        python_wilcoxon.p_value,
        5e-2,
        "wilcoxon p_value",
    );

    assert_eq!(rust_shapiro.value_col, python_shapiro.value_col);
    assert_eq!(rust_shapiro.group_col, python_shapiro.group_col);
    assert_eq!(rust_shapiro.groups.len(), python_shapiro.groups.len());
    for (rust_group, python_group) in rust_shapiro.groups.iter().zip(python_shapiro.groups.iter()) {
        assert_eq!(rust_group.group_name, python_group.group_name);
        assert_eq!(rust_group.sample_size, python_group.sample_size);
        assert_eq!(rust_group.skipped, python_group.skipped);
        if let (Some(rust_statistic), Some(python_statistic)) =
            (rust_group.statistic, python_group.statistic)
        {
            assert!(rust_statistic.is_finite(), "rust shapiro statistic should be finite");
            assert!(python_statistic.is_finite(), "python shapiro statistic should be finite");
            assert!(
                (rust_statistic - python_statistic).abs() < 0.5,
                "shapiro statistic diverged too much: rust={rust_statistic}, python={python_statistic}"
            );
        }
    }
}
