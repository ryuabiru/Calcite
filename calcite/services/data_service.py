from __future__ import annotations

import pandas as pd


def restructure_dataframe(df: pd.DataFrame, settings: dict) -> pd.DataFrame:
    return pd.melt(
        df,
        id_vars=settings["id_vars"],
        value_vars=settings["value_vars"],
        var_name=settings["var_name"],
        value_name=settings["value_name"],
    )


def pivot_dataframe(df: pd.DataFrame, settings: dict) -> pd.DataFrame:
    return pd.pivot_table(
        df,
        index=settings["id_vars"],
        columns=settings["var_name"],
        values=settings["value_name"],
    ).reset_index()


def build_advanced_filter_query(settings: list[dict]) -> str:
    query_parts: list[str] = []

    for i, condition in enumerate(settings):
        col = condition["column"]
        op = condition["operator"]
        val = condition["value"]
        query_val = f'"{val}"' if isinstance(val, str) else str(val)

        if op in ["contains", "not contains", "startswith", "endswith"]:
            if op == "not contains":
                part = f'~`{col}`.str.contains({query_val})'
            else:
                part = f'`{col}`.str.{op}({query_val})'
        else:
            part = f"`{col}` {op} {query_val}"

        if i > 0:
            connector = condition["connector"]
            query_parts.append(f" {connector} ({part})")
        else:
            query_parts.append(f"({part})")

    return "".join(query_parts)


def filter_dataframe(df: pd.DataFrame, settings: list[dict]) -> tuple[pd.DataFrame, str]:
    final_query = build_advanced_filter_query(settings)
    filtered_df = df.query(final_query, engine="python").reset_index(drop=True)
    return filtered_df, final_query


def subset_rows(df: pd.DataFrame, row_indices: list[int]) -> pd.DataFrame:
    return df.iloc[row_indices].copy().reset_index(drop=True)
