from __future__ import annotations


def format_binary_test_result(
    title: str,
    value_col: str,
    group_1_label: str,
    group_1_n: int,
    group_2_label: str,
    group_2_n: int,
    statistic_label: str,
    statistic_value: float,
    p_value: float,
    group_1_mean: float | None = None,
    group_2_mean: float | None = None,
) -> str:
    group_1_suffix = f", Mean: {group_1_mean:.3f}" if group_1_mean is not None else ""
    group_2_suffix = f", Mean: {group_2_mean:.3f}" if group_2_mean is not None else ""
    result_text = (
        f"{title}\n"
        f"============================================\n\n"
        f"Comparing '{value_col}' between:\n"
        f"- Group 1: {group_1_label} (n={group_1_n}{group_1_suffix})\n"
        f"- Group 2: {group_2_label} (n={group_2_n}{group_2_suffix})\n\n"
        f"---\n"
        f"{statistic_label}: {statistic_value:.4f}\n"
        f"p-value: {p_value:.4f}\n\n"
    )
    if p_value < 0.05:
        return result_text + "Conclusion: The difference is statistically significant (p < 0.05)."
    return result_text + "Conclusion: The difference is not statistically significant (p >= 0.05)."


def format_paired_test_result(
    title: str,
    col1: str,
    col2: str,
    statistic_label: str,
    statistic_value: float,
    p_value: float,
    col1_mean: float | None = None,
    col2_mean: float | None = None,
    note: str = "",
) -> str:
    mean_line_1 = f" (Mean: {col1_mean:.3f})" if col1_mean is not None else ""
    mean_line_2 = f" (Mean: {col2_mean:.3f})" if col2_mean is not None else ""
    note_block = f"\n{note}\n" if note else "\n"
    result_text = (
        f"{title}\n=====================\n\nComparing:\n"
        f"- Column 1: '{col1}'{mean_line_1}\n"
        f"- Column 2: '{col2}'{mean_line_2}"
        f"{note_block}\n---\n"
        f"{statistic_label}: {statistic_value:.4f}\n"
        f"p-value: {p_value:.4f}\n\n"
    )
    if p_value < 0.05:
        return result_text + "Conclusion: The difference is statistically significant (p < 0.05)."
    return result_text + "Conclusion: The difference is not statistically significant (p >= 0.05)."


def format_regression_summary(model: str, summary_lines: list[str]) -> str:
    header = "Linear Regression Results" if model == "linear" else "Non-linear Regression (4PL) Results"
    return f"{header}\n=========================\n" + "\n".join(summary_lines)


def format_chi_squared_result(result, rows_col: str, cols_col: str) -> str:
    text = "Chi-squared Test Results\n==========================\n\nObserved Frequencies:\n"
    text += f"{result.contingency_table.to_string()}\n\nExpected Frequencies:\n"
    text += f"{result.expected_table.round(2).to_string()}\n\nStandardized Residuals:\n"
    text += f"{result.standardized_residuals.round(2).to_string()}\n\nCell Contributions to Chi-squared:\n"
    text += f"{result.contribution_table.round(2).to_string()}\n\n---\n"
    text += (
        f"Chi-squared statistic: {result.chi2:.4f}\n"
        f"Degrees of Freedom: {result.degrees_of_freedom}\n"
        f"Cramer's V: {result.cramers_v:.4f}\n"
        f"p-value: {result.p_value:.4f}\n\n"
    )
    if result.p_value < 0.05:
        return text + f"Conclusion: There is a statistically significant association between '{rows_col}' and '{cols_col}' (p < 0.05)."
    return text + f"Conclusion: There is no statistically significant association between '{rows_col}' and '{cols_col}' (p >= 0.05)."


def format_spearman_correlation_result(result, col1: str, col2: str) -> str:
    text = (
        "Spearman's Rank Correlation Results\n"
        "====================================\n\n"
        f"Comparing:\n- Variable 1: '{col1}'\n- Variable 2: '{col2}'\n"
        f"(n={result.sample_size})\n\n"
        "---\n"
        f"Spearman's rho: {result.rho:.4f}\n"
        f"p-value: {result.p_value:.4f}\n\n"
    )
    if result.p_value < 0.05:
        return text + "Conclusion: There is a statistically significant correlation."
    return text + "Conclusion: There is no statistically significant correlation."


def format_pearson_correlation_result(result, col1: str, col2: str) -> str:
    text = (
        "Pearson Correlation Results\n"
        "===========================\n\n"
        f"Comparing:\n- Variable 1: '{col1}'\n- Variable 2: '{col2}'\n"
        f"(n={result.sample_size})\n\n"
        "---\n"
        f"Pearson's r: {result.r:.4f}\n"
        f"p-value: {result.p_value:.4f}\n\n"
    )
    if result.p_value < 0.05:
        return text + "Conclusion: There is a statistically significant linear correlation."
    return text + "Conclusion: There is no statistically significant linear correlation."


def format_two_proportion_result(result, rows_col: str, cols_col: str) -> str:
    text = (
        "2-Proportion z-test Results\n"
        "============================\n\n"
        f"Comparing success rate for '{result.success_label}' across '{rows_col}'.\n"
        f"Reference categorical column: '{cols_col}'\n\n"
        f"- Group 1: {result.group1_label} ({result.success_count_group1}/{result.total_group1}, "
        f"{result.proportion_group1:.3f}, 95% CI [{result.ci_low_group1:.3f}, {result.ci_high_group1:.3f}])\n"
        f"- Group 2: {result.group2_label} ({result.success_count_group2}/{result.total_group2}, "
        f"{result.proportion_group2:.3f}, 95% CI [{result.ci_low_group2:.3f}, {result.ci_high_group2:.3f}])\n\n"
        "---\n"
        f"Difference in proportions: {result.difference_in_proportions:.3f}\n"
        f"95% CI for difference: [{result.ci_low_difference:.3f}, {result.ci_high_difference:.3f}]\n"
        f"z-statistic: {result.z_statistic:.4f}\n"
        f"p-value: {result.p_value:.4f}\n\n"
    )
    if result.p_value < 0.05:
        return text + "Conclusion: The difference in proportions is statistically significant (p < 0.05)."
    return text + "Conclusion: The difference in proportions is not statistically significant (p >= 0.05)."


def format_shapiro_result(result) -> str:
    text = (
        "Shapiro-Wilk Normality Test Results\n"
        "=========================================\n\n"
        f"Value Column: {result.value_col}\n"
        f"Grouping by: {result.group_name}\n\n"
        "p > 0.05 suggests that the data is normally distributed.\n\n"
        "-----------------------------------------"
    )
    for group in result.groups:
        text += f"\nGroup: {group.group_name} (n={group.sample_size})\n"
        if group.skipped:
            text += "  -> Skipped (sample size < 3)\n"
        else:
            text += f"  - W-statistic: {group.statistic:.4f}\n"
            text += f"  - p-value: {group.p_value:.4f}\n"
            if group.p_value > 0.05:
                text += "  - Conclusion: Data likely follows a normal distribution.\n"
            else:
                text += "  - Conclusion: Data likely does not follow a normal distribution.\n"
        text += "-----------------------------------------"
    return text
