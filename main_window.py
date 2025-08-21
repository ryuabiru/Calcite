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
from dialogs.paired_plot_dialog import PairedPlotDialog
# --- Handlers ---
from handlers.action_handler import ActionHandler
from handlers.graph_manager import GraphManager

class MainWindow(QMainWindow):
    """
    アプリケーションのメインウィンドウ。
    UIの配置と、各ハンドラーへの処理の委譲を担当する。
    """
    def __init__(self):
        """
        MainWindowの初期化。UIのセットアップ、ハンドラーの初期化、シグナルとスロットの接続を行う。
        """
        super().__init__()
        self.setWindowTitle("Calcite")
        self.setGeometry(100, 100, 1000, 650)
        
        # モデルやグラフの状態を保持する変数
        self.model = None
        self.current_graph_type = 'scatter'
        self.header_editor = None
        self.regression_line_params = None
        self.fit_params = None
        self.statistical_annotations = []
        
        # ハンドラークラスを初期化
        self.action_handler = ActionHandler(self)
        self.graph_manager = GraphManager(self)

        # UIウィジェットの作成と配置
        self._setup_ui()

        # メニューバーとツールバーの作成
        self._create_menu_bar()
        self._create_toolbar()
        
        # シグナルとスロットの接続
        self._connect_signals()

    def _setup_ui(self):
        """メインウィンドウのUIウィジェットを作成し、レイアウトする。"""
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        top_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.table_view = QTableView()
        top_splitter.addWidget(self.table_view)
        
        self.graph_widget = GraphWidget()
        top_splitter.addWidget(self.graph_widget)
        
        top_splitter.setSizes([550, 450])

        self.properties_panel = PropertiesWidget()

        main_splitter.addWidget(top_splitter)
        main_splitter.addWidget(self.properties_panel)
        main_splitter.setSizes([550, 250])

        self.setCentralWidget(main_splitter)

    def _connect_signals(self):
        """UIウィジェットのシグナルを適切なハンドラーのスロットに接続する。"""
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.show_table_context_menu)
        self.table_view.horizontalHeader().sectionDoubleClicked.connect(self.edit_header)
        
        # PropertiesPanelの変更はGraphManagerに通知
        self.properties_panel.propertiesChanged.connect(self.graph_manager.update_graph)
        self.properties_panel.graphUpdateRequest.connect(self.graph_manager.update_graph)
        self.properties_panel.subgroupColumnChanged.connect(self.on_subgroup_column_changed)

    def _create_menu_bar(self):
        """メニューバーを作成し、各アクションを適切なハンドラーに接続する。"""
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("&File")
        open_action = QAction("&Open CSV...", self)
        open_action.triggered.connect(self.action_handler.open_csv_file)
        file_menu.addAction(open_action)
        
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

        # Data & Analysis Menus (ActionHandlerに接続)
        data_menu = menu_bar.addMenu("&Data")
        restructure_action = QAction("&Restructure (Wide to Long)...", self)
        restructure_action.triggered.connect(self.action_handler.show_restructure_dialog)
        data_menu.addAction(restructure_action)
        # ... 他のData, Analysisメニューも同様にaction_handlerに接続 ...

    def _create_toolbar(self):
        """グラフタイプを選択するためのツールバーを作成する。"""
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
        
        paired_scatter_action = QAction("Paired Scatter", self)
        paired_scatter_action.setCheckable(True)
        paired_scatter_action.triggered.connect(self.show_paired_plot_dialog)
        toolbar.addAction(paired_scatter_action); action_group.addAction(paired_scatter_action)

    # --- MainWindowに残るUI関連のメソッド ---

    def set_graph_type(self, graph_type):
        self.current_graph_type = graph_type
        self.graph_manager.update_graph()

    def show_paired_plot_dialog(self):
        if not hasattr(self, 'model'): return
        dialog = PairedPlotDialog(self.model._data.columns, self)
        if dialog.exec():
            settings = dialog.get_settings()
            if not all(settings.values()): return
            self.current_graph_type = 'paired_scatter'
            self.paired_plot_cols = {'col1': settings['col1'], 'col2': settings['col2']}
            self.graph_manager.update_graph()

    def edit_header(self, logicalIndex):
        # ... (変更なし) ...
        pass

    def finish_header_edit(self, logicalIndex):
        # ... (変更なし) ...
        pass
        
    def show_table_context_menu(self, position):
        # ... (変更なし) ...
        pass

    def on_subgroup_column_changed(self, column_name):
        if not hasattr(self, 'model') or not column_name:
            self.properties_panel.update_subgroup_color_ui([])
            return
        try:
            unique_categories = self.model._data[column_name].unique()
            self.properties_panel.update_subgroup_color_ui(sorted(unique_categories))
        except KeyError:
            self.properties_panel.update_subgroup_color_ui([])
            
    # --- PandasModelの行・列操作メソッド ---
    def insert_row(self):
        if hasattr(self, 'model'):
            # ... (変更なし) ...
            pass
    # ... (remove_row, insert_col, remove_colも同様) ...