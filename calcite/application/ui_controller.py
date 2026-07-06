from __future__ import annotations

from .state import AppState


def resolve_legend_position_for_graph_type(
    previous_graph_type: str,
    next_graph_type: str,
    current_legend_position: str,
) -> str:
    legendless_types = {"summary_scatter", "heatmap", "correlation_heatmap"}
    if next_graph_type in legendless_types and current_legend_position == "best":
        return "hide"
    if previous_graph_type in legendless_types and current_legend_position == "hide":
        return "best"
    return current_legend_position


class MainWindowController:
    def __init__(self, app_state: AppState):
        self.app_state = app_state

    def set_graph_type(self, graph_type: str, data_widget, properties_widget) -> None:
        previous_graph_type = self.app_state.current_graph_type
        self.app_state.current_graph_type = graph_type

        data_widget.set_graph_type(graph_type)
        properties_widget.sync_graph_type(graph_type, previous_graph_type)
