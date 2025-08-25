# main.py

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QCoreApplication
from main_window import MainWindow
import seaborn as sns
import pandas as pd

# ▼▼▼ アプリケーション起動ロジックを関数化 ▼▼▼
def main(data=None):
    """
    Calciteアプリケーションを起動します。

    Args:
        data (pd.DataFrame, optional): 初期表示するDataFrame。
                                       Noneの場合は空のウィンドウで起動します。
    """
    # QApplication.instance()は、既にインスタンスがあればそれを返し、なければNoneを返す
    # これにより、Jupyter Notebookなどから複数回呼び出してもエラーにならない
    app = QApplication.instance() or QApplication(sys.argv)
    
    sns.set_theme(style="ticks")
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    # MainWindowにDataFrameを渡してインスタンス化
    window = MainWindow(data=data)
    window.show()
    
    # app.exec()はイベントループを開始し、ウィンドウが閉じるまで待機する
    # スクリプトとして実行された場合のみ、sys.exit()で終了コードを返す
    if __name__ == "__main__":
        sys.exit(app.exec())
    else:
        app.exec()

# ▼▼▼ 直接実行された場合は、引数なしでmain()を呼び出す ▼▼▼
if __name__ == "__main__":
    main()