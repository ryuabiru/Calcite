from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.stats import chi2_contingency, linregress, norm, pearsonr, shapiro, spearmanr
from statsmodels.stats.proportion import proportion_confint


@dataclass(frozen=True)
class RegressionAnalysisResult:
    regression_line_params: dict | None
    fit_params: dict | None
    summary_lines: list[str]


@dataclass(frozen=True)
class ChiSquaredAnalysisResult:
    contingency_table: pd.DataFrame
    expected_table: pd.DataFrame
    standardized_residuals: pd.DataFrame
    contribution_table: pd.DataFrame
    chi2: float
    p_value: float
    degrees_of_freedom: int
    cramers_v: float


@dataclass(frozen=True)
class SpearmanCorrelationResult:
    rho: float
    p_value: float
    sample_size: int


@dataclass(frozen=True)
class PearsonCorrelationResult:
    r: float
    p_value: float
    sample_size: int


@dataclass(frozen=True)
class TwoProportionTestResult:
    group1_label: str
    group2_label: str
    success_label: str
    success_count_group1: int
    success_count_group2: int
    total_group1: int
    total_group2: int
    proportion_group1: float
    proportion_group2: float
    ci_low_group1: float
    ci_high_group1: float
    ci_low_group2: float
    ci_high_group2: float
    difference_in_proportions: float
    ci_low_difference: float
    ci_high_difference: float
    z_statistic: float
    p_value: float


@dataclass(frozen=True)
class ShapiroGroupResult:
    group_name: str
    sample_size: int
    statistic: float | None
    p_value: float | None
    skipped: bool


@dataclass(frozen=True)
class ShapiroAnalysisResult:
    value_col: str
    group_name: str
    groups: list[ShapiroGroupResult]


def sigmoid_4pl(x, bottom, top, hill_slope, log_ec50):
    return bottom + (top - bottom) / (1 + 10 ** ((log_ec50 - x) * hill_slope))


class RunRegressionAnalysisUseCase:
    def execute(
        self,
        dataframe: pd.DataFrame,
        x_col: str,
        y_col: str,
        model: str,
        subgroup_col: str | None = None,
    ) -> RegressionAnalysisResult:
        regression_line_params: dict | None = {}
        fit_params: dict | None = {}
        summary_lines: list[str] = []

        groups_to_fit = [None]
        if subgroup_col and subgroup_col in dataframe.columns:
            groups_to_fit = sorted(dataframe[subgroup_col].dropna().unique())

        for group in groups_to_fit:
            subset_df = dataframe if group is None else dataframe[dataframe[subgroup_col] == group]
            if group is not None:
                summary_lines.append(f"\n--- Sub-group: {group} ---")

            if model == "linear":
                line_result, summary_line = _run_linear_regression(subset_df, x_col, y_col)
                if line_result is None:
                    continue
                if group is not None:
                    regression_line_params[group] = line_result
                else:
                    regression_line_params = line_result
                summary_lines.append(summary_line)

            elif model == "4pl":
                fit_result, summary_line = _run_four_pl_regression(subset_df, x_col, y_col)
                if fit_result is None:
                    continue
                if group is not None:
                    fit_params[group] = fit_result
                else:
                    fit_params = fit_result
                summary_lines.append(summary_line)

        if model == "linear":
            fit_params = None
            if regression_line_params == {}:
                regression_line_params = None
        else:
            regression_line_params = None
            if fit_params == {}:
                fit_params = None

        return RegressionAnalysisResult(
            regression_line_params=regression_line_params,
            fit_params=fit_params,
            summary_lines=summary_lines,
        )


class RunChiSquaredAnalysisUseCase:
    def execute(self, dataframe: pd.DataFrame, rows_col: str, cols_col: str) -> ChiSquaredAnalysisResult:
        contingency_table = pd.crosstab(dataframe[rows_col], dataframe[cols_col])
        chi2, p_value, degrees_of_freedom, expected = chi2_contingency(contingency_table)
        expected_table = pd.DataFrame(expected, index=contingency_table.index, columns=contingency_table.columns)
        observed = contingency_table.astype(float)
        standardized_residuals = (observed - expected_table) / np.sqrt(expected_table)
        contribution_table = ((observed - expected_table) ** 2) / expected_table

        sample_size = observed.to_numpy().sum()
        min_dimension = min(observed.shape) - 1
        cramers_v = 0.0
        if sample_size > 0 and min_dimension > 0:
            cramers_v = float(np.sqrt(chi2 / (sample_size * min_dimension)))

        return ChiSquaredAnalysisResult(
            contingency_table=contingency_table,
            expected_table=expected_table,
            standardized_residuals=standardized_residuals,
            contribution_table=contribution_table,
            chi2=chi2,
            p_value=p_value,
            degrees_of_freedom=degrees_of_freedom,
            cramers_v=cramers_v,
        )


class RunSpearmanCorrelationUseCase:
    def execute(self, dataframe: pd.DataFrame, col1: str, col2: str) -> SpearmanCorrelationResult:
        data1 = dataframe[col1].dropna()
        data2 = dataframe[col2].dropna()
        common_indices = data1.index.intersection(data2.index)
        data1 = data1.loc[common_indices]
        data2 = data2.loc[common_indices]
        rho, p_value = spearmanr(data1, data2)
        return SpearmanCorrelationResult(rho=rho, p_value=p_value, sample_size=len(data1))


class RunPearsonCorrelationUseCase:
    def execute(self, dataframe: pd.DataFrame, col1: str, col2: str) -> PearsonCorrelationResult:
        data1 = dataframe[col1].dropna()
        data2 = dataframe[col2].dropna()
        common_indices = data1.index.intersection(data2.index)
        data1 = pd.to_numeric(data1.loc[common_indices], errors="coerce").dropna()
        data2 = pd.to_numeric(data2.loc[common_indices], errors="coerce").dropna()
        common_indices = data1.index.intersection(data2.index)
        data1 = data1.loc[common_indices]
        data2 = data2.loc[common_indices]
        r, p_value = pearsonr(data1, data2)
        return PearsonCorrelationResult(r=r, p_value=p_value, sample_size=len(data1))


class RunTwoProportionAnalysisUseCase:
    def execute(self, dataframe: pd.DataFrame, rows_col: str, cols_col: str) -> TwoProportionTestResult:
        contingency_table = pd.crosstab(dataframe[rows_col], dataframe[cols_col])
        if contingency_table.shape != (2, 2):
            raise ValueError("2-proportion z-test requires a 2x2 contingency table.")

        row_labels = list(contingency_table.index.astype(str))
        col_labels = list(contingency_table.columns.astype(str))
        success_label = col_labels[0]
        counts = contingency_table.to_numpy()
        success_count_group1 = int(counts[0, 0])
        success_count_group2 = int(counts[1, 0])
        total_group1 = int(counts[0].sum())
        total_group2 = int(counts[1].sum())
        proportion_group1 = success_count_group1 / total_group1
        proportion_group2 = success_count_group2 / total_group2
        pooled = (success_count_group1 + success_count_group2) / (total_group1 + total_group2)
        standard_error = np.sqrt(pooled * (1 - pooled) * ((1 / total_group1) + (1 / total_group2)))
        ci_low_group1, ci_high_group1 = proportion_confint(success_count_group1, total_group1, alpha=0.05, method="wilson")
        ci_low_group2, ci_high_group2 = proportion_confint(success_count_group2, total_group2, alpha=0.05, method="wilson")
        difference_in_proportions = proportion_group1 - proportion_group2
        diff_standard_error = np.sqrt(
            (proportion_group1 * (1 - proportion_group1) / total_group1)
            + (proportion_group2 * (1 - proportion_group2) / total_group2)
        )
        diff_margin = 1.96 * diff_standard_error
        z_statistic = 0.0 if standard_error == 0 else (proportion_group1 - proportion_group2) / standard_error
        p_value = float(2 * (1 - norm.cdf(abs(z_statistic))))

        return TwoProportionTestResult(
            group1_label=row_labels[0],
            group2_label=row_labels[1],
            success_label=success_label,
            success_count_group1=success_count_group1,
            success_count_group2=success_count_group2,
            total_group1=total_group1,
            total_group2=total_group2,
            proportion_group1=proportion_group1,
            proportion_group2=proportion_group2,
            ci_low_group1=float(ci_low_group1),
            ci_high_group1=float(ci_high_group1),
            ci_low_group2=float(ci_low_group2),
            ci_high_group2=float(ci_high_group2),
            difference_in_proportions=float(difference_in_proportions),
            ci_low_difference=float(difference_in_proportions - diff_margin),
            ci_high_difference=float(difference_in_proportions + diff_margin),
            z_statistic=float(z_statistic),
            p_value=p_value,
        )


class RunShapiroAnalysisUseCase:
    def execute(self, dataframe: pd.DataFrame, value_col: str, effective_groups, group_name: str) -> ShapiroAnalysisResult:
        groups: list[ShapiroGroupResult] = []
        for group in sorted(effective_groups.dropna().unique()):
            data = dataframe[value_col][effective_groups == group].dropna()
            if len(data) < 3:
                groups.append(
                    ShapiroGroupResult(
                        group_name=str(group),
                        sample_size=len(data),
                        statistic=None,
                        p_value=None,
                        skipped=True,
                    )
                )
                continue
            statistic, p_value = shapiro(data)
            groups.append(
                ShapiroGroupResult(
                    group_name=str(group),
                    sample_size=len(data),
                    statistic=statistic,
                    p_value=p_value,
                    skipped=False,
                )
            )
        return ShapiroAnalysisResult(value_col=value_col, group_name=group_name, groups=groups)


def _run_linear_regression(subset_df: pd.DataFrame, x_col: str, y_col: str):
    x_data = subset_df[x_col].dropna()
    y_data = subset_df[y_col].dropna()
    common_indices = x_data.index.intersection(y_data.index)
    x_data = x_data.loc[common_indices]
    y_data = y_data.loc[common_indices]

    if len(x_data) < 2:
        return None, ""

    slope, intercept, r_value, p_value, _ = linregress(x_data, y_data)
    result = {
        "x_line": np.array([x_data.min(), x_data.max()]),
        "y_line": slope * np.array([x_data.min(), x_data.max()]) + intercept,
        "r_squared": r_value**2,
    }
    summary_line = f"Y = {slope:.4f} * X + {intercept:.4f}\nR-squared: {r_value**2:.4f}, p-value: {p_value:.4f}"
    return result, summary_line


def _run_four_pl_regression(subset_df: pd.DataFrame, x_col: str, y_col: str):
    fit_df = subset_df[[x_col, y_col]].dropna().copy()
    if fit_df.empty or (fit_df[x_col] <= 0).any():
        return None, ""

    fit_df["log_x"] = np.log10(fit_df[x_col])
    x_data, y_data = fit_df["log_x"], fit_df[y_col]

    p0 = [y_data.min(), y_data.max(), 1.0, np.median(x_data)]
    params, _ = curve_fit(sigmoid_4pl, x_data, y_data, p0=p0, maxfev=10000)
    y_pred = sigmoid_4pl(x_data, *params)
    r_squared = 1 - (np.sum((y_data - y_pred) ** 2) / np.sum((y_data - np.mean(y_data)) ** 2))

    result = {"params": params, "r_squared": r_squared, "log_x_data": x_data}
    summary_line = (
        f"Top: {params[1]:.4f}, Bottom: {params[0]:.4f}, "
        f"Hill Slope: {params[2]:.4f}, EC50: {10**params[3]:.4f}\nR-squared: {r_squared:.4f}"
    )
    return result, summary_line
