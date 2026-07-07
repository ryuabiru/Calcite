from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PlotRequest:
    graph_type: str
    x_col: str = ""
    y_col: str = ""
    subgroup_col: str = ""
    facet_col: str = ""
    properties: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_sources(
        cls,
        graph_type: str,
        data_settings: dict[str, Any],
        properties: dict[str, Any],
    ) -> "PlotRequest":
        return cls(
            graph_type=graph_type,
            x_col=data_settings.get("x_col", ""),
            y_col=data_settings.get("y_col", ""),
            subgroup_col=data_settings.get("subgroup_col", ""),
            facet_col=data_settings.get("facet_col", ""),
            properties={**properties, **data_settings},
        )


@dataclass(frozen=True)
class AnalysisRequest:
    value_col: str = ""
    group_col: str = ""
    subgroup_col: str = ""
    facet_col: str = ""

    @classmethod
    def from_settings(cls, data_settings: dict[str, Any]) -> "AnalysisRequest":
        return cls(
            value_col=data_settings.get("y_col", ""),
            group_col=data_settings.get("x_col", ""),
            subgroup_col=data_settings.get("subgroup_col", ""),
            facet_col=data_settings.get("facet_col", ""),
        )
