from __future__ import annotations

from PySide6.QtWidgets import QApplication


def build_child_window_title(parent_title: str, suffix: str) -> str:
    return f"{parent_title} [{suffix}]"


def retain_child_window(window) -> None:
    app = QApplication.instance()
    if app is None:
        return
    if not hasattr(app, "main_windows"):
        app.main_windows = []
    app.main_windows.append(window)


class CreateChildWindowUseCase:
    def execute(self, parent_window, dataframe, title_suffix: str):
        new_window = parent_window.__class__(data=dataframe)
        new_window.setWindowTitle(build_child_window_title(parent_window.windowTitle(), title_suffix))
        new_window.show()
        retain_child_window(new_window)
        return new_window
