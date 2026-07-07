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


def subset_rows(df: pd.DataFrame, row_indices: list[int]) -> pd.DataFrame:
    return df.iloc[row_indices].copy().reset_index(drop=True)
