from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AppState:
    current_graph_type: str = "scatter"
    statistical_annotations: list = field(default_factory=list)
    regression_line_params: dict | None = None
    fit_params: dict | None = None
    chi_squared_highlight: dict | None = None
    two_proportion_highlight: dict | None = None

    def reset_analysis_results(self) -> None:
        self.statistical_annotations.clear()
        self.regression_line_params = None
        self.fit_params = None
        self.chi_squared_highlight = None
        self.two_proportion_highlight = None

    def add_statistical_annotation(self, annotation: dict) -> None:
        if annotation not in self.statistical_annotations:
            self.statistical_annotations.append(annotation)
