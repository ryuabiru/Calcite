from __future__ import annotations
import warnings

warnings.warn(
    "calcite.handlers.action_base is part of the legacy Python UI and will be retired after the Rust migration.",
    DeprecationWarning,
    stacklevel=2,
)


class ActionHandlerBase:
    def __init__(self, main_window):
        self.main = main_window
