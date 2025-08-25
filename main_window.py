# main_window.py

from PySide6.QtWidgets import (
    QMainWindow, QSplitter, QTableView, QMessageBox, QToolBar,
    QMenu, QLineEdit, QApplication
)
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtCore import Qt

# --- Local Imports ---
from graph_widget import GraphWidget
from properties_widget import PropertiesWidget
from results_widget import ResultsWidget
from pandas_model import PandasModel

# --- Handlers ---
from handlers.action_handler import ActionHandler
from handlers.graph_manager import GraphManager

import pandas as pd

class MainWindow(QMainWindow):
    """
    アプリケーションのメインウィンドウ。
    UIの配置と、各ハンドラーへの処理の委譲を担当する。
    """
    def __init__(self, data=None):
        super().__init__()
        self.setWindowTitle("demo")
        self.setGeometry(100, 100, 1000, 650)
        
        self.model = None
        self.current_graph_type = 'scatter'
        self.header_editor = None
        self.regression_line_params = None
        self.fit_params = None
        self.statistical_annotations = []
        self.paired_annotations = []
        
        self.action_handler = ActionHandler(self)
        self.graph_manager = GraphManager(self)

        self._setup_ui()
        self._create_menu_bar()
        self._create_toolbar()
        self._connect_signals()
        
        if data is not None:
            self.load_dataframe(data)

    def load_dataframe(self, df):
        """
        指定されたPandas DataFrameをアプリケーションに読み込む
        """
        if not isinstance(df, pd.DataFrame):
            QMessageBox.critical(self, "Error", "Invalid data type. A Pandas DataFrame is required.")
            return

        try:
            self.model = PandasModel(df)
            self.table_view.setModel(self.model)
            self.properties_panel.set_columns(df.columns)
            self.results_widget.clear_results()

            # グラフ更新のためのシグナルを接続
            self.table_view.selectionModel().selectionChanged.connect(self.graph_manager.update_graph)
            self.model.dataChanged.connect(self.graph_manager.update_graph)
            self.model.headerDataChanged.connect(self.graph_manager.update_graph)
            
            # 初期グラフを描画
            self.graph_manager.update_graph()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading DataFrame: {e}")

    def _setup_ui(self):
        # メインの分割を水平（左右）にする
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(main_splitter)

        # --- 左カラム ---
        self.table_view = QTableView()
        main_splitter.addWidget(self.table_view)

        # --- 右カラム（ここは垂直に分割）---
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # --- 右カラムの上段（ここは水平に分割）---
        top_right_splitter = QSplitter(Qt.Orientation.Horizontal)

        self.properties_panel = PropertiesWidget()
        top_right_splitter.addWidget(self.properties_panel)

        self.results_widget = ResultsWidget()
        top_right_splitter.addWidget(self.results_widget)
        
        top_right_splitter.setSizes([400, 250])

        right_splitter.addWidget(top_right_splitter)

        # --- 右カラムの下段 ---
        self.graph_widget = GraphWidget()
        right_splitter.addWidget(self.graph_widget)

        right_splitter.setSizes([200, 450])
        main_splitter.addWidget(right_splitter)
        main_splitter.setSizes([400, 800])

    def _connect_signals(self):
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.show_table_context_menu)
        self.table_view.horizontalHeader().sectionClicked.connect(self.sort_table)
        self.table_view.horizontalHeader().sectionDoubleClicked.connect(self.edit_header)
        
        self.properties_panel.propertiesChanged.connect(self.graph_manager.update_graph)
        self.properties_panel.graphUpdateRequest.connect(self.graph_manager.update_graph)
        self.properties_panel.subgroupColumnChanged.connect(self.on_subgroup_column_changed)
        
    def sort_table(self, logicalIndex):
        """テーブルを指定された列でソートする"""
        if hasattr(self, 'model') and self.model is not None:
            order = self.table_view.horizontalHeader().sortIndicatorOrder()
            self.model.sort(logicalIndex, order)

    def _create_menu_bar(self):
        menu_bar = self.menuBar()
        # File Menu
        file_menu = menu_bar.addMenu("&File")
        open_action = QAction("&Open CSV...", self)
        open_action.triggered.connect(self.action_handler.open_csv_file)
        file_menu.addAction(open_action)
        save_table_action = QAction("&Save Table As...", self)
        save_table_action.triggered.connect(self.action_handler.save_table_as_csv)
        file_menu.addAction(save_table_action)
        file_menu.addSeparator()
        save_graph_action = QAction("&Save Graph As...", self)
        save_graph_action.triggered.connect(self.graph_manager.save_graph)
        file_menu.addAction(save_graph_action)
        # Edit Menu
        edit_menu = menu_bar.addMenu("&Edit")
        paste_action = QAction("&Paste", self)
        paste_action.triggered.connect(self.action_handler.paste_from_clipboard)
        edit_menu.addAction(paste_action)
        clear_annotations_action = QAction("Clear Annotations", self)
        clear_annotations_action.triggered.connect(self.graph_manager.clear_annotations)
        edit_menu.addAction(clear_annotations_action)
        # Data Menu
        data_menu = menu_bar.addMenu("&Data")
        restructure_action = QAction("&Restructure (Wide to Long)...", self)
        restructure_action.triggered.connect(self.action_handler.show_restructure_dialog)
        data_menu.addAction(restructure_action)
        pivot_action = QAction("Pivot (Long to Wide)...", self)
        pivot_action.triggered.connect(self.action_handler.show_pivot_dialog)
        data_menu.addAction(pivot_action)
        filter_action = QAction("&Filter...", self)
        filter_action.triggered.connect(self.action_handler.show_advanced_filter_dialog)
        data_menu.addAction(filter_action)
        calculate_action = QAction("&Calculate New Column...", self)
        calculate_action.triggered.connect(self.action_handler.show_calculate_dialog)
        data_menu.addAction(calculate_action)
        # Analysis Menu
        analysis_menu = menu_bar.addMenu("&Analysis")
        ttest_action = QAction("&Independent t-test...", self)
        ttest_action.triggered.connect(self.action_handler.perform_t_test)
        analysis_menu.addAction(ttest_action)
        paired_ttest_action = QAction("&Paired t-test...", self)
        paired_ttest_action.triggered.connect(self.action_handler.perform_paired_t_test)
        analysis_menu.addAction(paired_ttest_action)
        anova_action = QAction("&One-way ANOVA...", self)
        anova_action.triggered.connect(self.action_handler.perform_one_way_anova)
        analysis_menu.addAction(anova_action)
        analysis_menu.addSeparator()

        # --- Non-parametric Tests ---
        analysis_menu.addSection("Non-parametric Tests")
        mannwhitney_action = QAction("&Mann-Whitney U test...", self)
        mannwhitney_action.triggered.connect(self.action_handler.perform_mannwhitney_test)
        analysis_menu.addAction(mannwhitney_action)
        wilcoxon_action = QAction("&Wilcoxon signed-rank test...", self)
        wilcoxon_action.triggered.connect(self.action_handler.perform_wilcoxon_test)
        analysis_menu.addAction(wilcoxon_action)
        kruskal_action = QAction("&Kruskal-Wallis test...", self)
        kruskal_action.triggered.connect(self.action_handler.perform_kruskal_test)
        analysis_menu.addAction(kruskal_action)

        shapiro_test_action = QAction("&Shapiro-Wilk...", self)
        shapiro_test_action.triggered.connect(self.action_handler.perform_shapiro_test)
        analysis_menu.addAction(shapiro_test_action)
        analysis_menu.addSeparator()
        chi_squared_action = QAction("&Chi-squared Test...", self)
        chi_squared_action.triggered.connect(self.action_handler.perform_chi_squared_test)
        analysis_menu.addAction(chi_squared_action)
        analysis_menu.addSeparator()
        spearman_action = QAction("&Spearman...", self)
        spearman_action.triggered.connect(self.action_handler.perform_spearman_correlation)
        analysis_menu.addAction(spearman_action)
        regression_action = QAction("&Regression...", self)
        regression_action.triggered.connect(self.action_handler.perform_regression)
        analysis_menu.addAction(regression_action)

    def _create_toolbar(self):
        toolbar = QToolBar("Graph Type")
        self.addToolBar(toolbar)
        action_group = QActionGroup(self)
        action_group.setExclusive(True)
        
        scatter_action = QAction("Scatter Plot", self)
        scatter_action.setCheckable(True); scatter_action.setChecked(True)
        scatter_action.triggered.connect(lambda: self.set_graph_type('scatter'))
        toolbar.addAction(scatter_action); action_group.addAction(scatter_action)
        
        bar_action = QAction("Bar Chart", self)
        bar_action.setCheckable(True)
        bar_action.triggered.connect(lambda: self.set_graph_type('bar'))
        toolbar.addAction(bar_action); action_group.addAction(bar_action)
        
        box_action = QAction("Box Plot", self)
        box_action.setCheckable(True)
        box_action.triggered.connect(lambda: self.set_graph_type('boxplot'))
        toolbar.addAction(box_action); action_group.addAction(box_action)

        violin_action = QAction("Violin Plot", self)
        violin_action.setCheckable(True)
        violin_action.triggered.connect(lambda: self.set_graph_type('violin'))
        toolbar.addAction(violin_action); action_group.addAction(violin_action)
        
        line_action = QAction("Line Plot", self)
        line_action.setCheckable(True)
        line_action.triggered.connect(lambda: self.set_graph_type('lineplot'))
        toolbar.addAction(line_action); action_group.addAction(line_action)
        
        point_action = QAction("Point Plot", self)
        point_action.setCheckable(True)
        point_action.triggered.connect(lambda: self.set_graph_type('pointplot'))
        toolbar.addAction(point_action); action_group.addAction(point_action)
        
        paired_scatter_action = QAction("Paired Scatter", self)
        paired_scatter_action.setCheckable(True)
        paired_scatter_action.triggered.connect(lambda: self.set_graph_type('paired_scatter'))
        toolbar.addAction(paired_scatter_action); action_group.addAction(paired_scatter_action)

        histogram_action = QAction("Histogram", self)
        histogram_action.setCheckable(True)
        histogram_action.triggered.connect(lambda: self.set_graph_type('histogram'))
        toolbar.addAction(histogram_action); action_group.addAction(histogram_action)

    def set_graph_type(self, graph_type):
        try:
            self.properties_panel.propertiesChanged.disconnect(self.graph_manager.update_graph)
        except (RuntimeError, TypeError):
            pass

        self.current_graph_type = graph_type
        self.properties_panel.data_tab.set_graph_type(graph_type)
        self.properties_panel.text_tab.update_paired_labels_visibility(graph_type == 'paired_scatter')
        
        self.properties_panel.propertiesChanged.connect(self.graph_manager.update_graph)
        
        self.graph_manager.update_graph()

    def edit_header(self, logicalIndex):
        if self.header_editor: self.header_editor.close()
        header = self.table_view.horizontalHeader()
        model = self.table_view.model()
        self.header_editor = QLineEdit(parent=header)
        self.header_editor.setText(model.headerData(logicalIndex, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole))
        self.header_editor.setGeometry(header.sectionViewportPosition(logicalIndex), 0, header.sectionSize(logicalIndex), header.height())
        self.header_editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_editor.editingFinished.connect(lambda: self.finish_header_edit(logicalIndex))
        self.header_editor.show(); self.header_editor.setFocus()

    def finish_header_edit(self, logicalIndex):
        if self.header_editor:
            new_text = self.header_editor.text()
            model = self.table_view.model()
            model.setHeaderData(logicalIndex, Qt.Orientation.Horizontal, new_text, Qt.ItemDataRole.EditRole)
            self.properties_panel.set_columns(model._data.columns)
            self.header_editor.close(); self.header_editor = None
        
    def show_table_context_menu(self, position):
        if not hasattr(self, 'model'): return
        menu = QMenu()
        insert_row_action = QAction("Insert Row Above", self); insert_row_action.triggered.connect(self.insert_row)
        remove_row_action = QAction("Remove Selected Row(s)", self); remove_row_action.triggered.connect(self.remove_row)
        insert_col_action = QAction("Insert Column Left", self); insert_col_action.triggered.connect(self.insert_col)
        remove_col_action = QAction("Remove Selected Column(s)", self); remove_col_action.triggered.connect(self.remove_col)
        menu.addAction(insert_row_action); menu.addAction(remove_row_action)
        menu.addSeparator()
        menu.addAction(insert_col_action); menu.addAction(remove_col_action)
        menu.exec(self.table_view.viewport().mapToGlobal(position))

    def on_subgroup_column_changed(self, column_name):
        if not hasattr(self, 'model') or not column_name:
            self.properties_panel.format_tab.update_subgroup_color_ui([])
            return
        try:
            unique_categories = self.model._data[column_name].unique()
            self.properties_panel.format_tab.update_subgroup_color_ui(sorted(unique_categories))
        except KeyError:
            self.properties_panel.format_tab.update_subgroup_color_ui([])
            
    def insert_row(self):
        if hasattr(self, 'model'):
            selected_index = self.table_view.currentIndex()
            row = selected_index.row() if selected_index.isValid() else self.model.rowCount()
            self.model.insertRows(row, 1)

    def remove_row(self):
        if hasattr(self, 'model'):
            selected_rows = sorted(list(set(index.row() for index in self.table_view.selectionModel().selectedRows())))
            for row in reversed(selected_rows): self.model.removeRows(row, 1)

    def insert_col(self):
        if hasattr(self, 'model'):
            selected_index = self.table_view.currentIndex()
            col = selected_index.column() if selected_index.isValid() else self.model.columnCount()
            self.model.insertColumns(col, 1)

    def remove_col(self):
        if hasattr(self, 'model'):
            selected_cols = sorted(list(set(index.column() for index in self.table_view.selectionModel().selectedColumns())))
            for col in reversed(selected_cols): self.model.removeColumns(col, 1)