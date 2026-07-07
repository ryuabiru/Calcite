# main_window.py

from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QSplitter,
    QTabWidget,
    QTableView,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt
import warnings

# --- Local Imports ---
from .graph_widget import GraphWidget
from .properties_widget import PropertiesWidget
from .results_widget import ResultsWidget
from .pandas_model import PandasModel
from .data_widget import DataWidget
from .main_window_builders import build_graph_toolbar, build_menu_bar, build_table_context_menu
from .main_window_history import DataframeHistoryManager
from .main_window_persistence import MainWindowPersistence
from .main_window_table_interaction import MainWindowTableInteraction

# --- Handlers ---
from .handlers.action_handler import ActionHandler
from .handlers.graph_manager import GraphManager
from .application import AppState, MainWindowController, TableController

import pandas as pd

from .services.project_service import ProjectState

class MainWindow(QMainWindow):
    """
    アプリケーションのメインウィンドウ。
    UIの配置と、各ハンドラーへの処理の委譲を担当する。
    """
    def __init__(self, data=None):
        warnings.warn(
            "calcite.main_window is legacy Python UI scaffolding kept for parity checks.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__()
        self.setWindowTitle("Calcite")
        self.resize(1380, 920)
        self.setMinimumSize(1180, 760)
        
        self.model = None
        self.app_state = AppState()
        self.controller = MainWindowController(self.app_state)
        self.table_controller = TableController()
        self.history = DataframeHistoryManager(on_change=self._update_history_actions)
        self.persistence = MainWindowPersistence()
        self.table_interaction = MainWindowTableInteraction(self)
        
        self.action_handler = ActionHandler(self)
        self.graph_manager = GraphManager(self)
        
        self._setup_ui()
        self._create_menu_bar()
        self._create_toolbar()
        self._connect_signals()
        self.statusBar().showMessage(
            "Legacy Python GUI: use Rust/Tauri for primary development.",
            10000,
        )
        
        self.table_view.installEventFilter(self)
        
        if data is not None:
            self.load_dataframe(data)

        self.restore_settings()
        self._update_history_actions(False, False)

    def restore_settings(self):
        self.persistence.restore_geometry(self)

    def closeEvent(self, event):
        self.persistence.save_geometry(self)
        super().closeEvent(event)

    def load_dataframe(self, df):
        """
        指定されたPandas DataFrameをアプリケーションに読み込む
        """
        if not isinstance(df, pd.DataFrame):
            QMessageBox.critical(self, "Error", "Invalid data type. A Pandas DataFrame is required.")
            return
        
        try:
            self.model = PandasModel(
                df,
                on_before_change=self._on_model_before_change,
                on_after_change=self._on_model_after_change,
            )
            self.table_view.setModel(self.model)
            self.data_widget.set_columns(df.columns)
            self.results_widget.clear_results()
            self._connect_model_signals()
            self.history.reset(df)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading DataFrame: {e}")

    def _connect_model_signals(self):
        if self.model is None:
            return
        selection_model = self.table_view.selectionModel()
        if selection_model is not None:
            selection_model.selectionChanged.connect(self.graph_manager.update_graph)
        self.model.dataChanged.connect(self.graph_manager.update_graph)
        self.model.headerDataChanged.connect(self.graph_manager.update_graph)

    def _on_model_before_change(self, dataframe):
        self.history.begin_change(dataframe)

    def _on_model_after_change(self, dataframe):
        self.history.end_change(dataframe)

    def get_project_state(self):
        dataframe = self.model._data if self.model is not None else None
        return ProjectState(
            dataframe=dataframe,
            settings=self.properties_widget.get_properties(),
            statistical_annotations=self.app_state.statistical_annotations,
            regression_line_params=self.app_state.regression_line_params,
            fit_params=self.app_state.fit_params,
        )

    def apply_project_state(self, state: ProjectState):
        if state.dataframe is not None:
            self.load_dataframe(state.dataframe)
        if state.settings:
            self.properties_widget.set_properties(state.settings)
        self.app_state.statistical_annotations = state.statistical_annotations
        self.app_state.regression_line_params = state.regression_line_params
        self.app_state.fit_params = state.fit_params
        self.graph_manager.update_graph()


    def _setup_ui(self):
        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)
        central_layout.setContentsMargins(12, 12, 12, 12)
        central_layout.setSpacing(10)

        retirement_banner = QFrame()
        retirement_banner.setObjectName("retirementBanner")
        retirement_layout = QVBoxLayout(retirement_banner)
        retirement_layout.setContentsMargins(16, 12, 16, 12)
        retirement_layout.setSpacing(4)

        banner_title = QLabel("Legacy Python GUI")
        banner_title.setObjectName("sectionTitle")
        banner_message = QLabel(
            "Rust/Tauri is now the primary development target. Use this window for parity checks and migration support."
        )
        banner_message.setWordWrap(True)
        retirement_layout.addWidget(banner_title)
        retirement_layout.addWidget(banner_message)
        central_layout.addWidget(retirement_banner)

        # メインの分割を水平（左右）にする
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        central_layout.addWidget(main_splitter)
        self.setCentralWidget(central_widget)

        # --- 左カラム（タブ形式） ---
        left_tab_widget = QTabWidget()
        left_tab_widget.setDocumentMode(True)
        
        # データフレームタブ
        self.table_view = QTableView()
        self.table_view.setAlternatingRowColors(True)
        left_tab_widget.addTab(self.table_view, "データフレーム")
        
        # プロパティタブ
        self.properties_widget = PropertiesWidget()
        properties_scroll_area = QScrollArea()
        properties_scroll_area.setWidgetResizable(True)
        properties_scroll_area.setWidget(self.properties_widget)
        left_tab_widget.addTab(properties_scroll_area, "プロパティ")
        
        main_splitter.addWidget(left_tab_widget)
        
        # --- 右カラム（ここは垂直に分割）---
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # --- 右カラムの上段（ここは水平に分割）---
        top_right_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.data_widget = DataWidget()
        top_right_splitter.addWidget(self.data_widget)
        
        self.results_widget = ResultsWidget()
        top_right_splitter.addWidget(self.results_widget)
        
        top_right_splitter.setSizes([250, 350])
        
        right_splitter.addWidget(top_right_splitter)
        
        # --- 右カラムの下段 ---
        self.graph_widget = GraphWidget()
        right_splitter.addWidget(self.graph_widget)
        
        right_splitter.setSizes([200, 450])
        main_splitter.addWidget(right_splitter)
        main_splitter.setSizes([400, 600])


    def _connect_signals(self):
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.show_table_context_menu)
        self.table_view.horizontalHeader().sectionClicked.connect(self.sort_table)
        self.table_view.horizontalHeader().sectionDoubleClicked.connect(self.edit_header)
        
        # self.properties_widget.propertiesChanged.connect(self.graph_manager.update_graph)
        self.data_widget.graphUpdateRequest.connect(self.graph_manager.update_graph)
        self.data_widget.subgroupColumnChanged.connect(self.on_subgroup_column_changed)


    def sort_table(self, logicalIndex):
        """テーブルを指定された列でソートする"""
        if hasattr(self, 'model') and self.model is not None:
            order = self.table_view.horizontalHeader().sortIndicatorOrder()
            self.model.sort(logicalIndex, order)

    def undo(self):
        if self.model is None:
            return
        previous = self.history.undo(self.model._data)
        if previous is None:
            return
        self._restore_history_dataframe(previous)

    def redo(self):
        if self.model is None:
            return
        next_df = self.history.redo(self.model._data)
        if next_df is None:
            return
        self._restore_history_dataframe(next_df)

    def _restore_history_dataframe(self, dataframe):
        self.model = PandasModel(
            dataframe,
            on_before_change=self._on_model_before_change,
            on_after_change=self._on_model_after_change,
        )
        self.table_view.setModel(self.model)
        self.data_widget.set_columns(dataframe.columns)
        self._connect_model_signals()
        self.graph_manager.update_graph()

    def _update_history_actions(self, can_undo, can_redo):
        if hasattr(self, "undo_action"):
            self.undo_action.setEnabled(can_undo)
        if hasattr(self, "redo_action"):
            self.redo_action.setEnabled(can_redo)


    def _create_menu_bar(self):
        build_menu_bar(self)

    def _create_toolbar(self):
        build_graph_toolbar(self)


    def set_graph_type(self, graph_type):
        self.controller.set_graph_type(graph_type, self.data_widget, self.properties_widget)


    def edit_header(self, logicalIndex):
        self.table_interaction.edit_header(logicalIndex)


    def finish_header_edit(self, logicalIndex):
        self.table_interaction.finish_header_edit(logicalIndex)


    def eventFilter(self, source, event):
        if self.table_interaction.handle_event_filter(source, event):
            return True
        return super().eventFilter(source, event)

    def fill_down(self):
        self.table_interaction.fill_down()

    def copy_selection(self):
        self.table_interaction.copy_selection()

    def paste_selection(self):
        self.table_interaction.paste_selection()


    def show_table_context_menu(self, position):
        menu = build_table_context_menu(self)
        if menu is None:
            return
        menu.exec(self.table_view.viewport().mapToGlobal(position))


    def on_subgroup_column_changed(self, column_name):
        self.table_interaction.on_subgroup_column_changed(column_name)


    def insert_row(self):
        self.table_interaction.insert_row()


    def remove_row(self):
        self.table_interaction.remove_row()


    def insert_col(self, left=False):
        self.table_interaction.insert_col(left=left)


    def remove_col(self):
        self.table_interaction.remove_col()
