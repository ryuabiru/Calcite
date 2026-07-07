from __future__ import annotations

import pandas as pd

from ..services.data_service import (
    pivot_dataframe,
    restructure_dataframe,
    subset_rows,
)


class RestructureDataUseCase:
    def execute(self, dataframe: pd.DataFrame, settings: dict) -> pd.DataFrame:
        return restructure_dataframe(dataframe, settings)


class PivotDataUseCase:
    def execute(self, dataframe: pd.DataFrame, settings: dict) -> pd.DataFrame:
        return pivot_dataframe(dataframe, settings)


class CreateSubsetUseCase:
    def execute(self, dataframe: pd.DataFrame, row_indices: list[int]) -> pd.DataFrame:
        return subset_rows(dataframe, row_indices)
