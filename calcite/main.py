# main.py

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QCoreApplication
from .main_window import MainWindow
from .ui_theme import build_application_stylesheet
import seaborn as sns
import pandas as pd

def plot(data=None):
    """
    Calciteアプリケーションを起動します。
    """
    if not QApplication.instance():
        QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    QCoreApplication.setOrganizationName("CalciteApp") # 任意の組織名
    QCoreApplication.setApplicationName("Calcite")
    
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(build_application_stylesheet())
    
    sns.set_theme(style="ticks")
    
    window = MainWindow(data=data)
    window.show()
    
    if __name__ == "__main__":
        sys.exit(app.exec())
    else:
        app.exec()

if __name__ == "__main__":
    plot()
