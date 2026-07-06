from __future__ import annotations

from PySide6.QtGui import QAction, QActionGroup, QKeySequence
from PySide6.QtWidgets import QMenu, QToolBar


def build_menu_bar(window):
    menu_bar = window.menuBar()
    _build_file_menu(window, menu_bar)
    _build_edit_menu(window, menu_bar)
    _build_data_menu(window, menu_bar)
    _build_analysis_menu(window, menu_bar)
    _build_help_menu(window, menu_bar)


def build_graph_toolbar(window):
    toolbar = QToolBar("Graph Type")
    window.addToolBar(toolbar)
    action_group = QActionGroup(window)
    action_group.setExclusive(True)

    for label, graph_type, checked in [
        ("Scatter Plot", "scatter", True),
        ("Summary Scatter", "summary_scatter", False),
        ("Bar Chart", "bar", False),
        ("Count Plot", "countplot", False),
        ("Stacked Bar", "stacked_bar", False),
        ("100% Stacked Bar", "stacked_bar_100", False),
        ("Proportion Plot", "proportion_plot", False),
        ("Mosaic Plot", "mosaic", False),
        ("Heatmap", "heatmap", False),
        ("Correlation Heatmap", "correlation_heatmap", False),
        ("Box Plot", "boxplot", False),
        ("Violin Plot", "violin", False),
        ("Line Plot", "lineplot", False),
        ("Point Plot", "pointplot", False),
        ("Paired Scatter", "paired_scatter", False),
        ("Histogram", "histogram", False),
    ]:
        action = QAction(label, window)
        action.setCheckable(True)
        action.setChecked(checked)
        action.triggered.connect(lambda _, graph_type=graph_type: window.set_graph_type(graph_type))
        toolbar.addAction(action)
        action_group.addAction(action)


def build_table_context_menu(window):
    if not hasattr(window, "model"):
        return None

    menu = QMenu()
    copy_action = QAction("Copy", window)
    copy_action.triggered.connect(window.copy_selection)
    paste_action = QAction("Paste", window)
    paste_action.triggered.connect(window.paste_selection)
    create_table_action = QAction("Create New Table from Selection", window)
    create_table_action.triggered.connect(window.action_handler.create_table_from_selection)
    insert_row_action = QAction("Insert Row Above", window)
    insert_row_action.triggered.connect(window.insert_row)
    remove_row_action = QAction("Remove Selected Row(s)", window)
    remove_row_action.triggered.connect(window.remove_row)
    insert_col_left_action = QAction("Insert Column Left", window)
    insert_col_left_action.triggered.connect(lambda: window.insert_col(left=True))
    insert_col_right_action = QAction("Insert Column Right", window)
    insert_col_right_action.triggered.connect(lambda: window.insert_col(left=False))
    remove_col_action = QAction("Remove Selected Column(s)", window)
    remove_col_action.triggered.connect(window.remove_col)
    fill_down_action = QAction("Fill Down", window)
    fill_down_action.triggered.connect(window.fill_down)

    selection_model = window.table_view.selectionModel()
    if selection_model is None or len(selection_model.selectedIndexes()) < 2:
        fill_down_action.setEnabled(False)

    menu.addAction(copy_action)
    menu.addAction(paste_action)
    menu.addSeparator()
    menu.addAction(create_table_action)
    menu.addSeparator()
    menu.addAction(fill_down_action)
    menu.addSeparator()
    menu.addAction(insert_row_action)
    menu.addAction(remove_row_action)
    menu.addSeparator()
    menu.addAction(insert_col_left_action)
    menu.addAction(insert_col_right_action)
    menu.addAction(remove_col_action)
    return menu


def _build_file_menu(window, menu_bar):
    file_menu = menu_bar.addMenu("File")
    open_project_action = QAction("Open Project...", window)
    open_project_action.triggered.connect(window.action_handler.open_project)
    file_menu.addAction(open_project_action)

    save_project_action = QAction("Save Project As...", window)
    save_project_action.triggered.connect(window.action_handler.save_project)
    file_menu.addAction(save_project_action)
    file_menu.addSeparator()

    open_action = QAction("Open CSV...", window)
    open_action.triggered.connect(window.action_handler.open_csv_file)
    file_menu.addAction(open_action)

    save_table_action = QAction("Save Table As...", window)
    save_table_action.triggered.connect(window.action_handler.save_table_as_csv)
    file_menu.addAction(save_table_action)
    file_menu.addSeparator()

    save_graph_action = QAction("Save Graph As...", window)
    save_graph_action.triggered.connect(window.graph_manager.save_graph)
    file_menu.addAction(save_graph_action)

    export_results_action = QAction("Export Analysis Results...", window)
    export_results_action.triggered.connect(window.action_handler.export_analysis_results)
    file_menu.addAction(export_results_action)


def _build_edit_menu(window, menu_bar):
    edit_menu = menu_bar.addMenu("Edit")
    paste_action = QAction("Paste from Clipboard", window)
    paste_action.triggered.connect(window.action_handler.paste_from_clipboard)
    edit_menu.addAction(paste_action)
    edit_menu.addSeparator()

    clear_graph_action = QAction("Clear Graph", window)
    clear_graph_action.triggered.connect(window.graph_manager.clear_graph)
    edit_menu.addAction(clear_graph_action)

    clear_annotations_action = QAction("Clear Annotations", window)
    clear_annotations_action.triggered.connect(window.graph_manager.clear_annotations)
    edit_menu.addAction(clear_annotations_action)
    edit_menu.addSeparator()

    undo_action = QAction("Undo", window)
    undo_action.setShortcut(QKeySequence.StandardKey.Undo)
    undo_action.triggered.connect(window.undo)
    edit_menu.addAction(undo_action)
    window.undo_action = undo_action

    redo_action = QAction("Redo", window)
    redo_action.setShortcut(QKeySequence.StandardKey.Redo)
    redo_action.triggered.connect(window.redo)
    edit_menu.addAction(redo_action)
    window.redo_action = redo_action


def _build_data_menu(window, menu_bar):
    data_menu = menu_bar.addMenu("Data")
    restructure_action = QAction("Restructure (Wide to Long)...", window)
    restructure_action.triggered.connect(window.action_handler.show_restructure_dialog)
    data_menu.addAction(restructure_action)

    pivot_action = QAction("Pivot (Long to Wide)...", window)
    pivot_action.triggered.connect(window.action_handler.show_pivot_dialog)
    data_menu.addAction(pivot_action)

    filter_action = QAction("Filter...", window)
    filter_action.triggered.connect(window.action_handler.show_advanced_filter_dialog)
    data_menu.addAction(filter_action)

    calculate_action = QAction("Calculate New Column...", window)
    calculate_action.triggered.connect(window.action_handler.show_calculate_dialog)
    data_menu.addAction(calculate_action)


def _build_analysis_menu(window, menu_bar):
    analysis_menu = menu_bar.addMenu("Analysis")
    analysis_menu.addSection("Compare Means / Medians")

    for label, callback in [
        ("Independent t-test...", window.action_handler.statistical_handler.perform_t_test),
        ("Paired t-test...", window.action_handler.statistical_handler.perform_paired_t_test),
        ("One-way ANOVA...", window.action_handler.statistical_handler.perform_one_way_anova),
    ]:
        action = QAction(label, window)
        action.triggered.connect(callback)
        analysis_menu.addAction(action)

    analysis_menu.addSeparator()
    analysis_menu.addSection("Non-parametric Tests")
    for label, callback in [
        ("Mann-Whitney U test...", window.action_handler.statistical_handler.perform_mannwhitney_test),
        ("Wilcoxon signed-rank test...", window.action_handler.statistical_handler.perform_wilcoxon_test),
        ("Kruskal-Wallis test...", window.action_handler.statistical_handler.perform_kruskal_test),
    ]:
        action = QAction(label, window)
        action.triggered.connect(callback)
        analysis_menu.addAction(action)

    analysis_menu.addSeparator()
    analysis_menu.addSection("Assess Associations & Relationships")
    for label, callback in [
        ("2-Proportion z-test...", window.action_handler.statistical_handler.perform_two_proportion_test),
        ("Correlation (Pearson)...", window.action_handler.statistical_handler.perform_pearson_correlation),
        ("Correlation (Spearman)...", window.action_handler.statistical_handler.perform_spearman_correlation),
        ("Chi-squared Test...", window.action_handler.statistical_handler.perform_chi_squared_test),
        ("Regression...", window.action_handler.statistical_handler.perform_regression),
    ]:
        action = QAction(label, window)
        action.triggered.connect(callback)
        analysis_menu.addAction(action)

    analysis_menu.addSeparator()
    analysis_menu.addSection("Distribution Tests")
    shapiro_test_action = QAction("Shapiro-Wilk Normality Test...", window)
    shapiro_test_action.triggered.connect(window.action_handler.statistical_handler.perform_shapiro_test)
    analysis_menu.addAction(shapiro_test_action)


def _build_help_menu(window, menu_bar):
    help_menu = menu_bar.addMenu("Help")
    license_action = QAction("Licenses...", window)
    license_action.triggered.connect(window.action_handler.show_license_dialog)
    help_menu.addAction(license_action)
