# check_env.py

import sys
import matplotlib
import PyQt6
import PySide6

print("--- Pythonの実行パス ---")
print(sys.executable)
print("\n--- ライブラリのバージョン ---")
print(f"Matplotlib: {matplotlib.__version__}")
print(f"PyQt6: {PyQt6.QtCore.PYQT_VERSION_STR}")
print(f"PySide6: {PySide6.__version__}")