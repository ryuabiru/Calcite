from __future__ import annotations


def build_application_stylesheet() -> str:
    return """
    QMainWindow {
        background: #f4efe6;
        color: #1f1a17;
    }

    QWidget {
        font-family: "Avenir Next", "Helvetica Neue", "Segoe UI", sans-serif;
        font-size: 13px;
        color: #1f1a17;
    }

    QToolBar {
        background: #e8dcc7;
        border: none;
        border-bottom: 1px solid #d4c2aa;
        spacing: 8px;
        padding: 8px 10px;
    }

    QToolBar QToolButton {
        background: transparent;
        border: 1px solid transparent;
        border-radius: 10px;
        padding: 8px 12px;
        margin: 0 2px;
        font-weight: 600;
    }

    QToolBar QToolButton:hover {
        background: #f6efe3;
        border-color: #d7c6b0;
    }

    QToolBar QToolButton:checked {
        background: #1f1a17;
        color: #f8f2e8;
        border-color: #1f1a17;
    }

    QMenuBar {
        background: #f4efe6;
        border-bottom: 1px solid #ddcfbc;
    }

    QMenuBar::item {
        padding: 6px 10px;
        border-radius: 6px;
        background: transparent;
    }

    QMenuBar::item:selected {
        background: #e8dcc7;
    }

    QMenu {
        background: #fbf7f0;
        border: 1px solid #d7c6b0;
        padding: 6px;
    }

    QMenu::item {
        padding: 7px 20px 7px 12px;
        border-radius: 6px;
    }

    QMenu::item:selected {
        background: #e8dcc7;
    }

    QTabWidget::pane {
        border: 1px solid #d7c6b0;
        border-radius: 14px;
        background: #fbf7f0;
        top: -1px;
    }

    QTabBar::tab {
        background: #e9decd;
        border: 1px solid #d7c6b0;
        border-bottom: none;
        padding: 10px 16px;
        margin-right: 6px;
        border-top-left-radius: 12px;
        border-top-right-radius: 12px;
        font-weight: 600;
    }

    QTabBar::tab:selected {
        background: #fbf7f0;
    }

    QSplitter::handle {
        background: #decdb7;
    }

    QSplitter::handle:horizontal {
        width: 6px;
    }

    QSplitter::handle:vertical {
        height: 6px;
    }

    QGroupBox {
        background: #fffaf3;
        border: 1px solid #e0d2c0;
        border-radius: 14px;
        margin-top: 14px;
        padding: 14px 12px 12px 12px;
        font-weight: 700;
    }

    QGroupBox::title {
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
        color: #7f4f24;
    }

    QLineEdit,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QTextEdit,
    QTableView {
        background: #fffdf9;
        border: 1px solid #d8c8b2;
        border-radius: 10px;
        padding: 6px 8px;
        selection-background-color: #d98f3d;
        selection-color: #fffaf3;
    }

    QComboBox::drop-down {
        border: none;
        width: 26px;
    }

    QComboBox QAbstractItemView {
        background: #fffdf9;
        border: 1px solid #d8c8b2;
        selection-background-color: #d98f3d;
        selection-color: #fffaf3;
    }

    QPushButton {
        background: #ede2d3;
        border: 1px solid #d5c1a7;
        border-radius: 11px;
        padding: 8px 14px;
        font-weight: 700;
    }

    QPushButton:hover {
        background: #f5ecdf;
    }

    QPushButton:pressed {
        background: #dfcfbb;
    }

    QPushButton#primaryButton {
        background: #a44a1b;
        color: #fff9f1;
        border-color: #8c3f16;
        padding: 10px 14px;
    }

    QPushButton#primaryButton:hover {
        background: #b65420;
    }

    QLabel#sectionTitle {
        font-size: 14px;
        font-weight: 800;
        letter-spacing: 0.3px;
        color: #7f4f24;
        padding-bottom: 4px;
    }

    QWidget#panelSurface {
        background: #fbf7f0;
        border: 1px solid #dccab3;
        border-radius: 16px;
    }

    QFrame#retirementBanner {
        background: #fff2e2;
        border: 1px solid #e0a86f;
        border-radius: 14px;
    }

    QFrame#retirementBanner QLabel {
        background: transparent;
    }

    QTextEdit {
        padding: 10px 12px;
    }

    QHeaderView::section {
        background: #ede2d3;
        color: #3b2a1f;
        border: none;
        border-right: 1px solid #d9c7af;
        border-bottom: 1px solid #d9c7af;
        padding: 7px 8px;
        font-weight: 700;
    }

    QScrollBar:vertical,
    QScrollBar:horizontal {
        background: transparent;
        border: none;
        margin: 4px;
    }

    QScrollBar::handle:vertical,
    QScrollBar::handle:horizontal {
        background: #d0b89c;
        border-radius: 6px;
        min-height: 28px;
        min-width: 28px;
    }

    QScrollBar::add-line,
    QScrollBar::sub-line,
    QScrollBar::add-page,
    QScrollBar::sub-page {
        background: transparent;
        border: none;
    }
    """
