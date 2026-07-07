from __future__ import annotations

import warnings

import pandas as pd

warnings.warn(
    "calcite.main_window_history is legacy Python UI scaffolding kept for parity checks.",
    DeprecationWarning,
    stacklevel=2,
)


class DataframeHistoryManager:
    def __init__(self, on_change=None):
        self._undo_stack: list[pd.DataFrame] = []
        self._redo_stack: list[pd.DataFrame] = []
        self._pending_snapshot: pd.DataFrame | None = None
        self._group_depth = 0
        self._on_change = on_change

    def reset(self, dataframe: pd.DataFrame | None = None):
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._pending_snapshot = dataframe.copy(deep=True) if dataframe is not None else None
        self._group_depth = 0
        self._emit_change()

    def begin_change(self, dataframe: pd.DataFrame):
        if self._group_depth == 0:
            self._pending_snapshot = dataframe.copy(deep=True)
        self._group_depth += 1

    def end_change(self, dataframe: pd.DataFrame):
        if self._group_depth == 0:
            return
        self._group_depth -= 1
        if self._group_depth != 0:
            return
        self._commit_pending_snapshot(dataframe)

    def record_change(self, before_df: pd.DataFrame, after_df: pd.DataFrame):
        self._pending_snapshot = before_df.copy(deep=True)
        self._commit_pending_snapshot(after_df)

    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    def can_redo(self) -> bool:
        return bool(self._redo_stack)

    def undo(self, current_df: pd.DataFrame) -> pd.DataFrame | None:
        if not self._undo_stack:
            return None
        previous = self._undo_stack.pop()
        self._redo_stack.append(current_df.copy(deep=True))
        self._pending_snapshot = previous.copy(deep=True)
        self._emit_change()
        return previous.copy(deep=True)

    def redo(self, current_df: pd.DataFrame) -> pd.DataFrame | None:
        if not self._redo_stack:
            return None
        next_df = self._redo_stack.pop()
        self._undo_stack.append(current_df.copy(deep=True))
        self._pending_snapshot = next_df.copy(deep=True)
        self._emit_change()
        return next_df.copy(deep=True)

    def _commit_pending_snapshot(self, after_df: pd.DataFrame):
        if self._pending_snapshot is None:
            return
        if self._pending_snapshot.equals(after_df):
            self._pending_snapshot = None
            return
        self._undo_stack.append(self._pending_snapshot.copy(deep=True))
        self._redo_stack.clear()
        self._pending_snapshot = after_df.copy(deep=True)
        self._emit_change()

    def _emit_change(self):
        if self._on_change is not None:
            self._on_change(self.can_undo(), self.can_redo())
