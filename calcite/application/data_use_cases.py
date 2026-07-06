from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ..services.data_service import (
    filter_dataframe,
    pivot_dataframe,
    restructure_dataframe,
    subset_rows,
)


@dataclass(frozen=True)
class FilterDataResult:
    dataframe: pd.DataFrame
    query: str


class RestructureDataUseCase:
    def execute(self, dataframe: pd.DataFrame, settings: dict) -> pd.DataFrame:
        return restructure_dataframe(dataframe, settings)


class PivotDataUseCase:
    def execute(self, dataframe: pd.DataFrame, settings: dict) -> pd.DataFrame:
        return pivot_dataframe(dataframe, settings)


class ApplyAdvancedFilterUseCase:
    def execute(self, dataframe: pd.DataFrame, settings: list[dict]) -> FilterDataResult:
        filtered_df, query = filter_dataframe(dataframe, settings)
        return FilterDataResult(dataframe=filtered_df, query=query)


class CreateSubsetUseCase:
    def execute(self, dataframe: pd.DataFrame, row_indices: list[int]) -> pd.DataFrame:
        return subset_rows(dataframe, row_indices)
