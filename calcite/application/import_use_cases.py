from __future__ import annotations

import pandas as pd

from ..services.project_service import dataframe_from_clipboard_text, optimize_imported_dataframe


class OpenCsvUseCase:
    def execute(self, file_path: str) -> pd.DataFrame:
        return optimize_imported_dataframe(pd.read_csv(file_path))


class PasteClipboardUseCase:
    def execute(self, clipboard_text: str) -> pd.DataFrame:
        return dataframe_from_clipboard_text(clipboard_text)
