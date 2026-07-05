from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import scikit_posthocs as sp
from scipy.stats import f_oneway, kruskal
from statsmodels.stats.multicomp import pairwise_tukeyhsd

from calcite.models import AnalysisRequest

UNIQUE_SEPARATOR = "_#%%%_"


def normalize_analysis_request(request: AnalysisRequest) -> AnalysisRequest:
    subgroup_col = request.subgroup_col
    if subgroup_col == request.group_col:
        subgroup_col = ""

    return AnalysisRequest(
        value_col=request.value_col,
        group_col=request.group_col,
        subgroup_col=subgroup_col,
        facet_col=request.facet_col,
    )


def prepare_analysis_dataframe(
    df: pd.DataFrame,
    request: AnalysisRequest,
) -> tuple[pd.DataFrame, AnalysisRequest]:
    normalized_request = normalize_analysis_request(request)
    prepared_df = df.copy()

    if normalized_request.group_col:
        prepared_df[normalized_request.group_col] = prepared_df[normalized_request.group_col].astype(str)
    if normalized_request.subgroup_col and normalized_request.subgroup_col in prepared_df.columns:
        prepared_df[normalized_request.subgroup_col] = prepared_df[normalized_request.subgroup_col].astype(str)

    return prepared_df, normalized_request


def build_effective_groups(
    df: pd.DataFrame,
    group_col: str,
    subgroup_col: str,
) -> tuple[pd.Series, str]:
    if subgroup_col and subgroup_col in df.columns:
        interaction_col_name = f"{group_col}_{subgroup_col}_interaction"
        effective_groups = df[group_col].astype(str) + UNIQUE_SEPARATOR + df[subgroup_col].astype(str)
        return effective_groups, interaction_col_name
    return df[group_col].astype(str), group_col


def format_annotation_pair(pair: tuple[str, str], subgroup_col: str):
    if not subgroup_col:
        return pair

    try:
        group1 = tuple(pair[0].split(UNIQUE_SEPARATOR))
        group2 = tuple(pair[1].split(UNIQUE_SEPARATOR))
        return (group1, group2)
    except Exception:
        return pair


@dataclass(frozen=True)
class OmnibusTestResult:
    summary_lines: list[str]
    annotations: list[dict]
    has_valid_samples: bool


def _build_annotation(
    value_col: str,
    group_col: str,
    subgroup_col: str,
    facet_col: str | None,
    facet_value: object,
    pair: tuple[str, str],
    p_value: float,
) -> dict:
    return {
        "value_col": value_col,
        "group_col": group_col,
        "hue_col": subgroup_col or None,
        "facet_col": facet_col,
        "facet_value": facet_value,
        "box_pair": format_annotation_pair(pair, subgroup_col),
        "p_value": p_value,
    }


def run_anova(
    df: pd.DataFrame,
    *,
    value_col: str,
    group_col: str,
    subgroup_col: str,
    facet_col: str,
    selected_groups: list[str],
) -> OmnibusTestResult:
    effective_groups, _ = build_effective_groups(df, group_col, subgroup_col)
    results_summary: list[str] = []
    annotations: list[dict] = []
    has_valid_samples = False

    if facet_col and facet_col in df.columns:
        for category in df[facet_col].dropna().unique():
            subset_df = df[df[facet_col] == category].copy()
            current_facet_groups, _ = build_effective_groups(subset_df, group_col, subgroup_col)
            samples = [subset_df.loc[current_facet_groups == g, value_col].dropna() for g in selected_groups]
            samples = [s for s in samples if not s.empty]

            if len(samples) < 2:
                continue

            has_valid_samples = True
            f_stat, p_value = f_oneway(*samples)
            results_summary.append(f"--- Facet: {facet_col} = {category} ---")
            results_summary.append(f"F-statistic: {f_stat:.4f}, p-value: {p_value:.4f}")

            if p_value < 0.05:
                selected_data_indices = current_facet_groups.isin(selected_groups)
                all_data = subset_df.loc[selected_data_indices, value_col].dropna()
                group_labels = current_facet_groups[selected_data_indices].dropna()
                tukey_result = pairwise_tukeyhsd(endog=all_data, groups=group_labels, alpha=0.05)
                df_tukey = pd.DataFrame(
                    data=tukey_result._results_table.data[1:],
                    columns=tukey_result._results_table.data[0],
                )
                results_summary.append(str(tukey_result))

                for _, row in df_tukey.iterrows():
                    if row["p-adj"] < 0.05:
                        annotations.append(
                            _build_annotation(
                                value_col,
                                group_col,
                                subgroup_col,
                                facet_col,
                                category,
                                (str(row["group1"]), str(row["group2"])),
                                row["p-adj"],
                            )
                        )
    else:
        samples = [df.loc[effective_groups == g, value_col].dropna() for g in selected_groups]
        samples = [s for s in samples if not s.empty]

        if len(samples) >= 2:
            has_valid_samples = True
            f_stat, p_value = f_oneway(*samples)
            results_summary.append(f"F-statistic: {f_stat:.4f}")
            results_summary.append(f"p-value: {p_value:.4f}")

            if p_value < 0.05:
                selected_data_indices = effective_groups.isin(selected_groups)
                all_data = df.loc[selected_data_indices, value_col].dropna()
                group_labels = effective_groups[selected_data_indices].dropna()
                tukey_result = pairwise_tukeyhsd(endog=all_data, groups=group_labels, alpha=0.05)
                df_tukey = pd.DataFrame(
                    data=tukey_result._results_table.data[1:],
                    columns=tukey_result._results_table.data[0],
                )
                results_summary.append("")
                results_summary.append("Post-hoc test (Tukey's HSD):")
                results_summary.append(str(tukey_result))

                for _, row in df_tukey.iterrows():
                    if row["p-adj"] < 0.05:
                        annotations.append(
                            _build_annotation(
                                value_col,
                                group_col,
                                subgroup_col,
                                None,
                                None,
                                (str(row["group1"]), str(row["group2"])),
                                row["p-adj"],
                            )
                        )

    return OmnibusTestResult(
        summary_lines=results_summary,
        annotations=annotations,
        has_valid_samples=has_valid_samples,
    )


def run_kruskal(
    df: pd.DataFrame,
    *,
    value_col: str,
    group_col: str,
    subgroup_col: str,
    facet_col: str,
    selected_groups: list[str],
) -> OmnibusTestResult:
    effective_groups, interaction_col_name = build_effective_groups(df, group_col, subgroup_col)
    df_with_groups = df.copy()
    df_with_groups[interaction_col_name] = effective_groups
    results_summary: list[str] = []
    annotations: list[dict] = []
    has_valid_samples = False

    if facet_col and facet_col in df_with_groups.columns:
        for category in df_with_groups[facet_col].dropna().unique():
            subset_df = df_with_groups[df_with_groups[facet_col] == category].copy()
            samples = [subset_df.loc[subset_df[interaction_col_name] == g, value_col].dropna() for g in selected_groups]
            samples = [s for s in samples if not s.empty]

            if len(samples) < 2:
                continue

            has_valid_samples = True
            h_stat, p_value = kruskal(*samples)
            results_summary.append(f"--- Facet: {facet_col} = {category} ---")
            results_summary.append(f"Kruskal-Wallis H-statistic: {h_stat:.4f}, p-value: {p_value:.4f}")

            if p_value < 0.05 and len(samples) > 2:
                posthoc_df = sp.posthoc_dunn(subset_df, val_col=value_col, group_col=interaction_col_name)
                results_summary.append("")
                results_summary.append("Dunn's Post-hoc Test (p-values):")
                results_summary.append(posthoc_df.to_string())

                for group1 in posthoc_df.columns:
                    for group2, p_adj in posthoc_df.loc[group1].items():
                        if group1 != group2 and pd.notna(p_adj) and p_adj < 0.05:
                            annotations.append(
                                _build_annotation(
                                    value_col,
                                    group_col,
                                    subgroup_col,
                                    facet_col,
                                    category,
                                    tuple(sorted((str(group1), str(group2)))),
                                    p_adj,
                                )
                            )
            results_summary.append("-" * 20)
    else:
        samples = [df_with_groups.loc[df_with_groups[interaction_col_name] == g, value_col].dropna() for g in selected_groups]
        samples = [s for s in samples if not s.empty]

        if len(samples) >= 2:
            has_valid_samples = True
            h_stat, p_value = kruskal(*samples)
            results_summary.append(f"Kruskal-Wallis H-statistic: {h_stat:.4f}, p-value: {p_value:.4f}")

            if p_value < 0.05 and len(samples) > 2:
                posthoc_df = sp.posthoc_dunn(df_with_groups, val_col=value_col, group_col=interaction_col_name)
                results_summary.append("")
                results_summary.append("Dunn's Post-hoc Test (p-values):")
                results_summary.append(posthoc_df.to_string())

                for group1 in posthoc_df.columns:
                    for group2, p_adj in posthoc_df.loc[group1].items():
                        if group1 != group2 and pd.notna(p_adj) and p_adj < 0.05:
                            annotations.append(
                                _build_annotation(
                                    value_col,
                                    group_col,
                                    subgroup_col,
                                    None,
                                    None,
                                    tuple(sorted((str(group1), str(group2)))),
                                    p_adj,
                                )
                            )

    return OmnibusTestResult(
        summary_lines=results_summary,
        annotations=annotations,
        has_valid_samples=has_valid_samples,
    )
