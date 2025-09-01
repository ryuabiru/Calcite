# main_window.py

from PySide6.QtWidgets import (
    QMainWindow, QSplitter, QTableView, QMessageBox, QToolBar,
    QMenu, QLineEdit, QApplication
)
from PySide6.QtGui import QAction, QActionGroup, QKeySequence
from PySide6.QtCore import Qt, QEvent

# --- Local Imports ---
from .graph_widget import GraphWidget
from .properties_widget import PropertiesWidget
from .results_widget import ResultsWidget
from .pandas_model import PandasModel

# --- Handlers ---
from .handlers.action_handler import ActionHandler
from .handlers.graph_manager import GraphManager

import pandas as pd

class MainWindow(QMainWindow):
    """
    アプリケーションのメインウィンドウ。
    UIの配置と、各ハンドラーへの処理の委譲を担当する。
    """
    def __init__(self, data=None):
        super().__init__()
        self.setWindowTitle("Calcite")
        self.setGeometry(100, 100, 1000, 650)
        
        self.model = None
        self.current_graph_type = 'scatter'
        self.previous_graph_type = 'scatter'
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
        
        self.table_view.installEventFilter(self)
        
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
        file_menu = menu_bar.addMenu("File")
        open_action = QAction("Open CSV...", self)
        open_action.triggered.connect(self.action_handler.open_csv_file)
        file_menu.addAction(open_action)
        save_table_action = QAction("Save Table As...", self)
        save_table_action.triggered.connect(self.action_handler.save_table_as_csv)
        file_menu.addAction(save_table_action)
        file_menu.addSeparator()
        save_graph_action = QAction("Save Graph As...", self)
        save_graph_action.triggered.connect(self.graph_manager.save_graph)
        file_menu.addAction(save_graph_action)
        
        # Edit Menu
        edit_menu = menu_bar.addMenu("Edit")
        paste_action = QAction("Paste from Clipboard", self)
        paste_action.triggered.connect(self.action_handler.paste_from_clipboard)
        edit_menu.addAction(paste_action)
        edit_menu.addSeparator()
        clear_graph_action = QAction("Clear Graph", self)
        clear_graph_action.triggered.connect(self.graph_manager.clear_graph)
        edit_menu.addAction(clear_graph_action)
        clear_annotations_action = QAction("Clear Annotations", self)
        clear_annotations_action.triggered.connect(self.graph_manager.clear_annotations)
        edit_menu.addAction(clear_annotations_action)
        
        # Data Menu
        data_menu = menu_bar.addMenu("Data")
        restructure_action = QAction("Restructure (Wide to Long)...", self)
        restructure_action.triggered.connect(self.action_handler.show_restructure_dialog)
        data_menu.addAction(restructure_action)
        pivot_action = QAction("Pivot (Long to Wide)...", self)
        pivot_action.triggered.connect(self.action_handler.show_pivot_dialog)
        data_menu.addAction(pivot_action)
        filter_action = QAction("Filter...", self)
        filter_action.triggered.connect(self.action_handler.show_advanced_filter_dialog)
        data_menu.addAction(filter_action)
        calculate_action = QAction("Calculate New Column...", self)
        calculate_action.triggered.connect(self.action_handler.show_calculate_dialog)
        data_menu.addAction(calculate_action)
        
        # Analysis Menu (提案に基づき再構成)
        analysis_menu = menu_bar.addMenu("Analysis")
        
        analysis_menu.addSection("Compare Means / Medians")
        ttest_action = QAction("Independent t-test...", self)
        ttest_action.triggered.connect(self.action_handler.statistical_handler.perform_t_test)
        analysis_menu.addAction(ttest_action)
        
        paired_ttest_action = QAction("Paired t-test...", self)
        paired_ttest_action.triggered.connect(self.action_handler.statistical_handler.perform_paired_t_test)
        analysis_menu.addAction(paired_ttest_action)
        
        anova_action = QAction("One-way ANOVA...", self)
        anova_action.triggered.connect(self.action_handler.statistical_handler.perform_one_way_anova)
        analysis_menu.addAction(anova_action)
        
        analysis_menu.addSeparator()
        analysis_menu.addSection("Non-parametric Tests")
        mannwhitney_action = QAction("Mann-Whitney U test...", self)
        mannwhitney_action.triggered.connect(self.action_handler.statistical_handler.perform_mannwhitney_test)
        analysis_menu.addAction(mannwhitney_action)
        
        wilcoxon_action = QAction("Wilcoxon signed-rank test...", self)
        wilcoxon_action.triggered.connect(self.action_handler.statistical_handler.perform_wilcoxon_test)
        analysis_menu.addAction(wilcoxon_action)
        
        kruskal_action = QAction("Kruskal-Wallis test...", self)
        kruskal_action.triggered.connect(self.action_handler.statistical_handler.perform_kruskal_test)
        analysis_menu.addAction(kruskal_action)
        
        analysis_menu.addSeparator()
        analysis_menu.addSection("Assess Associations & Relationships")
        spearman_action = QAction("Correlation (Spearman)...", self)
        spearman_action.triggered.connect(self.action_handler.statistical_handler.perform_spearman_correlation)
        analysis_menu.addAction(spearman_action)

        chi_squared_action = QAction("Chi-squared Test...", self)
        chi_squared_action.triggered.connect(self.action_handler.statistical_handler.perform_chi_squared_test)
        analysis_menu.addAction(chi_squared_action)

        regression_action = QAction("Regression...", self)
        regression_action.triggered.connect(self.action_handler.statistical_handler.perform_regression)
        analysis_menu.addAction(regression_action)

        analysis_menu.addSeparator()
        analysis_menu.addSection("Distribution Tests")
        shapiro_test_action = QAction("Shapiro-Wilk Normality Test...", self)
        shapiro_test_action.triggered.connect(self.action_handler.statistical_handler.perform_shapiro_test)
        analysis_menu.addAction(shapiro_test_action)

        help_menu = menu_bar.addMenu("Help")
        license_action = QAction("Licenses...", self)
        license_action.triggered.connect(self.action_handler.show_license_dialog)
        help_menu.addAction(license_action)

    def _create_toolbar(self):
        toolbar = QToolBar("Graph Type")
        self.addToolBar(toolbar)
        action_group = QActionGroup(self)
        action_group.setExclusive(True)
        
        scatter_action = QAction("Scatter Plot", self)
        scatter_action.setCheckable(True); scatter_action.setChecked(True)
        scatter_action.triggered.connect(lambda: self.set_graph_type('scatter'))
        toolbar.addAction(scatter_action); action_group.addAction(scatter_action)
        
        summary_scatter_action = QAction("Summary Scatter", self)
        summary_scatter_action.setCheckable(True)
        summary_scatter_action.triggered.connect(lambda: self.set_graph_type('summary_scatter'))
        toolbar.addAction(summary_scatter_action)
        action_group.addAction(summary_scatter_action)
        
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
        
        previous_graph_type = self.current_graph_type
        self.current_graph_type = graph_type
        
        self.properties_panel.data_tab.set_graph_type(graph_type)
        self.properties_panel.text_tab.update_paired_labels_visibility(graph_type == 'paired_scatter')
        
        current_legend_setting = self.properties_panel.text_tab.legend_pos_combo.currentData()
        
        if graph_type == 'summary_scatter' and current_legend_setting == 'best':
            hide_index = self.properties_panel.text_tab.legend_pos_combo.fineData('hide')
            if hide_index != -1:
                self.properties_panel.text_tab.legend_pos_combo.setCurrentIndex(hide_index)
        
        elif previous_graph_type == 'summary_scatter' and current_legend_setting == 'hide':
            best_index = self.properties_panel.text_tab.legend_pos_combo.findData('best')
            if best_index != -1:
                self.properties_panel.text_tab.legend_pos_combo.setCurrentIndex(best_index)
        
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


    def eventFilter(self, source, event):
        """
        table_viewのイベントを監視し、特定のキー入力を処理する。
        """
        # イベントがキープレスで、発生源がテーブルビューの場合のみ処理
        if event.type() == QEvent.Type.KeyPress and source is self.table_view:
            # 押されたキーがEnter/Returnキーかチェック
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                
                # 現在選択されているセルのインデックスを取得
                current_index = self.table_view.currentIndex()
                if current_index.isValid():
                    # 1行下のインデックスを作成
                    next_index = current_index.model().index(current_index.row() + 1, current_index.column())
                    
                    # 次の行が存在すれば、そこにカーソルを移動
                    if next_index.isValid():
                        self.table_view.setCurrentIndex(next_index)
                        # イベントが処理されたことを示す
                        return True

            if event.matches(QKeySequence.StandardKey.Copy):
                self.copy_selection()
                return True
            
            if event.matches(QKeySequence.StandardKey.Paste):
                self.paste_selection()
                return True

        # 上記以外のイベントは、通常の処理に任せる
        return super().eventFilter(source, event)

    def fill_down(self):
        """
        選択されたセルのうち、一番上のセルの値で他の選択セルを埋める。
        """
        if not hasattr(self, 'model'): return
        
        selection_model = self.table_view.selectionModel()
        selected_indexes = selection_model.selectedIndexes()
        
        if len(selected_indexes) < 2: return # 2つ以上選択されていないと意味がない
        
        # 選択範囲を(行, 列)のタプルのリストに変換し、行番号でソート
        sorted_indexes = sorted(selected_indexes, key=lambda index: (index.row(), index.column()))
        
        # フィル元の値を取得 (ソート後、最初のインデックスが一番上になる)
        source_index = sorted_indexes[0]
        fill_value = self.model.data(source_index, Qt.ItemDataRole.DisplayRole)
        
        # フィル元以外のインデックスをループして、値をセット
        for target_index in sorted_indexes[1:]:
            self.model.setData(target_index, fill_value, Qt.ItemDataRole.EditRole)

    def copy_selection(self):
        """
        選択されたセル範囲のデータをタブ区切りテキストとしてクリップボードにコピーする。
        """
        selection_model = self.table_view.selectionModel()
        selected_indexes = selection_model.selectedIndexes()

        if not selected_indexes:
            return

        # 行と列の範囲を特定
        rows = sorted(list(set(index.row() for index in selected_indexes)))
        cols = sorted(list(set(index.column() for index in selected_indexes)))
        
        # データを格納する二次元配列を作成
        row_count = len(rows)
        col_count = len(cols)
        data = [["" for _ in range(col_count)] for _ in range(row_count)]

        # 選択されたインデックスのみデータを取得
        row_map = {row: i for i, row in enumerate(rows)}
        col_map = {col: i for i, col in enumerate(cols)}

        for index in selected_indexes:
            r, c = row_map[index.row()], col_map[index.column()]
            data[r][c] = index.data()

        # タブ区切りテキストを作成
        tsv_text = "\n".join(["\t".join(row) for row in data])

        # クリップボードに設定
        QApplication.clipboard().setText(tsv_text)

    def paste_selection(self):
        """
        クリップボードのタブ区切りテキストを、選択されたセルを起点として貼り付ける。
        """
        clipboard_text = QApplication.clipboard().text()
        if not clipboard_text:
            return
            
        start_index = self.table_view.currentIndex()
        if not start_index.isValid():
            return # 貼り付け開始位置がなければ何もしない

        start_row = start_index.row()
        start_col = start_index.column()

        # クリップボードのテキストを行と列に分割
        lines = clipboard_text.strip('\n').split('\n')
        rows_data = [line.split('\t') for line in lines]
        
        # 貼り付け処理
        for r_offset, row_data in enumerate(rows_data):
            for c_offset, cell_value in enumerate(row_data):
                target_row = start_row + r_offset
                target_col = start_col + c_offset
                
                # モデルの範囲内かチェック
                if (target_row < self.model.rowCount() and 
                    target_col < self.model.columnCount()):
                    
                    target_index = self.model.index(target_row, target_col)
                    self.model.setData(target_index, cell_value, Qt.ItemDataRole.EditRole)


    def show_table_context_menu(self, position):
        if not hasattr(self, 'model'): return
        menu = QMenu()
        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(self.copy_selection)
        paste_action = QAction("Paste", self)
        paste_action.triggered.connect(self.paste_selection)
        create_table_action = QAction("Create New Table from Selection", self)
        create_table_action.triggered.connect(self.action_handler.create_table_from_selection)
        insert_row_action = QAction("Insert Row Above", self); insert_row_action.triggered.connect(self.insert_row)
        remove_row_action = QAction("Remove Selected Row(s)", self); remove_row_action.triggered.connect(self.remove_row)
        insert_col_left_action = QAction("Insert Column Left", self)
        insert_col_left_action.triggered.connect(lambda: self.insert_col(left=True))
        insert_col_right_action = QAction("Insert Column Right", self)
        insert_col_right_action.triggered.connect(lambda: self.insert_col(left=False))
        remove_col_action = QAction("Remove Selected Column(s)", self); remove_col_action.triggered.connect(self.remove_col)
        
        fill_down_action = QAction("Fill Down", self)
        fill_down_action.triggered.connect(self.fill_down)
        # 選択されているセルが2つ未満の場合は無効化する
        if len(self.table_view.selectionModel().selectedIndexes()) < 2:
            fill_down_action.setEnabled(False)

        menu.addAction(copy_action)
        menu.addAction(paste_action)
        menu.addSeparator()
        menu.addAction(create_table_action)
        menu.addSeparator()
        menu.addAction(fill_down_action)
        menu.addSeparator()
        menu.addAction(insert_row_action); menu.addAction(remove_row_action)
        menu.addSeparator()
        menu.addAction(insert_col_left_action)
        menu.addAction(insert_col_right_action)
        menu.addAction(remove_col_action)
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


    def insert_col(self, left=False):
        if hasattr(self, 'model'):
            selected_index = self.table_view.currentIndex()
            col = selected_index.column() if selected_index.isValid() else self.model.columnCount()
            if not left and selected_index.isValid():
                col += 1
            self.model.insertColumns(col, 1)


    def remove_col(self):
        if hasattr(self, 'model'):
            selected_cols = sorted(list(set(index.column() for index in self.table_view.selectionModel().selectedColumns())))
            for col in reversed(selected_cols): self.model.removeColumns(col, 1)