# dialogs/license_dialog.py

from PySide6.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox, QTextBrowser
from PySide6.QtCore import Qt

class LicenseDialog(QDialog):
    """
    サードパーティライブラリのライセンス情報を表示するためのダイアログ。
    """
    def __init__(self, license_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Third-Party Licenses")
        self.setMinimumSize(600, 500)

        main_layout = QVBoxLayout(self)

        text_edit = QTextBrowser()
        text_edit.setReadOnly(True)
        text_edit.setText(license_text)
        
        # テキストのハイパーリンクをクリックで開けるようにする
        text_edit.setOpenExternalLinks(True)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)

        main_layout.addWidget(text_edit)
        main_layout.addWidget(button_box)