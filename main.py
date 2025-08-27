# main.py

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QCoreApplication
from main_window import MainWindow
import seaborn as sns
import pandas as pd

def main(data=None):
    """
    Calciteアプリケーションを起動します。
    """
    # ▼▼▼ 警告を解消するため、インスタンス作成前に設定を移動 ▼▼▼
    # PySide6のバージョンによっては、これらの設定が起動時に必要
    if not QApplication.instance():
        QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    sns.set_theme(style="ticks")
    
    window = MainWindow(data=data)
    window.show()
    
    if __name__ == "__main__":
        sys.exit(app.exec())
    else:
        app.exec()

if __name__ == "__main__":
    main()