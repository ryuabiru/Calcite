from __future__ import annotations

import warnings

from calcite.models import PlotRequest
from calcite.services.plot_service import normalize_plot_request

from .graph_canvas_handler import GraphCanvasHandler
from .graph_renderer import GraphRenderer

warnings.warn(
    "calcite.handlers.graph_manager is legacy Python rendering scaffolding kept for parity checks.",
    DeprecationWarning,
    stacklevel=2,
)


class GraphManager:
    def __init__(self, main_window):
        self.main = main_window
        self.canvas_handler = GraphCanvasHandler(main_window)
        self.renderer = GraphRenderer(main_window)

    def update_graph(self):
        if not hasattr(self.main, "model") or self.main.model is None:
            self.clear_canvas()
            return

        df = self.main.model._data
        request = PlotRequest.from_sources(
            graph_type=self.main.app_state.current_graph_type,
            data_settings=self.main.data_widget.get_current_settings(),
            properties=self.main.properties_widget.get_properties(),
        )
        request = normalize_plot_request(request)

        if request.graph_type == "histogram":
            fig = self.renderer.render_histogram(df, request.properties, request.properties)
        elif request.graph_type in {"stacked_bar", "stacked_bar_100"}:
            fig = self.renderer.render_stacked_bar(df, request)
        elif request.graph_type == "proportion_plot":
            fig = self.renderer.render_proportion_plot(df, request)
        elif request.graph_type == "mosaic":
            fig = self.renderer.render_mosaic(df, request)
        elif request.graph_type == "heatmap":
            fig = self.renderer.render_heatmap(df, request)
        elif request.graph_type == "correlation_heatmap":
            fig = self.renderer.render_correlation_heatmap(df, request.properties)
        else:
            fig = self.renderer.render_categorical_plot(df, request)

        if fig:
            self.canvas_handler.replace_canvas(fig)
            self.renderer.apply_graph_properties(fig, request.properties)

    def clear_canvas(self):
        self.canvas_handler.clear_canvas()

    def save_graph(self):
        self.canvas_handler.save_graph()

    def clear_graph(self):
        self.main.app_state.reset_analysis_results()
        self.clear_canvas()

    def clear_annotations(self):
        self.main.app_state.reset_analysis_results()
        self.update_graph()
