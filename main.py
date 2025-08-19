# main.py

import sys
# from PyQt6.QtWidgets import QApplication
from PySide6.QtWidgets import QApplication # ← 変更
from main_window import MainWindow
# ... (以降は変更なし)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())