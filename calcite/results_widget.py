# results_widget.py (新規作成)

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel
from PySide6.QtGui import QFont

class ResultsWidget(QWidget):
    """
    統計解析の結果を表示するためのウィジェット。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5) # 少し余白を持たせる

        title_label = QLabel("<b>Analysis Results</b>")
        
        self.results_text_edit = QTextEdit()
        self.results_text_edit.setReadOnly(True) # 編集不可にする
        
        # 論文などで使われる等幅フォントに設定
        font = QFont("Courier New")
        self.results_text_edit.setFont(font)

        main_layout.addWidget(title_label)
        main_layout.addWidget(self.results_text_edit)

    def set_results_text(self, text):
        """
        パネルのテキストを更新する。
        """
        self.results_text_edit.setText(text)

    def clear_results(self):
        """
        パネルのテキストをクリアする。
        """
        self.results_text_edit.clear()