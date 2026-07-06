from __future__ import annotations

from PySide6.QtCore import Qt


def build_clipboard_text(selected_cells: list[tuple[int, int, str]]) -> str:
    if not selected_cells:
        return ""

    rows = sorted({row for row, _, _ in selected_cells})
    cols = sorted({col for _, col, _ in selected_cells})
    row_map = {row: index for index, row in enumerate(rows)}
    col_map = {col: index for index, col in enumerate(cols)}

    grid = [["" for _ in cols] for _ in rows]
    for row, col, value in selected_cells:
        grid[row_map[row]][col_map[col]] = value
    return "\n".join("\t".join(row) for row in grid)


def parse_clipboard_text(text: str) -> list[list[str]]:
    if not text:
        return []
    lines = text.strip("\n").split("\n")
    return [line.split("\t") for line in lines]


class TableController:
    def sync_columns(self, model, data_widget) -> None:
        if model is None:
            return
        data_widget.set_columns(model._data.columns)

    def sync_subgroup_colors(self, model, column_name: str, properties_widget) -> None:
        if model is None or not column_name:
            properties_widget.format_tab.update_subgroup_color_ui([])
            return
        try:
            categories = sorted(model._data[column_name].unique())
        except KeyError:
            categories = []
        properties_widget.format_tab.update_subgroup_color_ui(categories)

    def insert_row(self, model, current_index) -> None:
        if model is None:
            return
        row = current_index.row() if current_index.isValid() else model.rowCount()
        model.insertRows(row, 1)

    def remove_rows(self, model, selected_rows: list[int]) -> None:
        if model is None:
            return
        for row in reversed(sorted(set(selected_rows))):
            model.removeRows(row, 1)

    def insert_column(self, model, current_index, left: bool) -> None:
        if model is None:
            return
        col = current_index.column() if current_index.isValid() else model.columnCount()
        if not left and current_index.isValid():
            col += 1
        model.insertColumns(col, 1)

    def remove_columns(self, model, selected_columns: list[int]) -> None:
        if model is None:
            return
        for col in reversed(sorted(set(selected_columns))):
            model.removeColumns(col, 1)

    def fill_down(self, model, selected_indexes) -> None:
        if model is None or len(selected_indexes) < 2:
            return
        if hasattr(model, "_on_before_change") and model._on_before_change is not None:
            model._on_before_change(model._data)
        sorted_indexes = sorted(selected_indexes, key=lambda index: (index.row(), index.column()))
        source_index = sorted_indexes[0]
        fill_value = model.data(source_index)
        for target_index in sorted_indexes[1:]:
            try:
                original_value = model._data.iloc[target_index.row(), target_index.column()]
                coerced_value = type(original_value)(fill_value)
                model._data.iloc[target_index.row(), target_index.column()] = coerced_value
            except (ValueError, TypeError):
                model._data.iloc[target_index.row(), target_index.column()] = fill_value
            model.dataChanged.emit(target_index, target_index)
        if hasattr(model, "_on_after_change") and model._on_after_change is not None:
            model._on_after_change(model._data)

    def build_selection_clipboard_text(self, selected_indexes) -> str:
        cells = [(index.row(), index.column(), index.data()) for index in selected_indexes]
        return build_clipboard_text(cells)

    def paste_into_model(self, model, start_index, clipboard_text: str) -> None:
        if model is None or not start_index.isValid():
            return
        if hasattr(model, "_on_before_change") and model._on_before_change is not None:
            model._on_before_change(model._data)
        for row_offset, row_data in enumerate(parse_clipboard_text(clipboard_text)):
            for col_offset, cell_value in enumerate(row_data):
                target_row = start_index.row() + row_offset
                target_col = start_index.column() + col_offset
                if target_row < model.rowCount() and target_col < model.columnCount():
                    target_index = model.index(target_row, target_col)
                    try:
                        original_value = model._data.iloc[target_row, target_col]
                        coerced_value = type(original_value)(cell_value)
                        model._data.iloc[target_row, target_col] = coerced_value
                    except (ValueError, TypeError):
                        model._data.iloc[target_row, target_col] = cell_value
                    model.dataChanged.emit(target_index, target_index)
        if hasattr(model, "_on_after_change") and model._on_after_change is not None:
            model._on_after_change(model._data)
