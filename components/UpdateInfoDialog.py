import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import requests

from PySide6.QtWidgets import (
    QTextEdit,
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
)


class UpdateInfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.url_update_info = "https:1//ifishin.xyz/UpdateInfo.txt"
        
        self.setWindowTitle("Update Information")
        self.setFixedSize(600, 400)
        self.setWindowFlag(Qt.FramelessWindowHint)

        layout = QVBoxLayout()

        title_label = QLabel("Update Information")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.setStyleSheet(
            """
            QDialog {
            border-radius: 10px;
            border: 2px solid #888;
            }
            QLabel {
            color: #444;
            }
            QTextEdit {
            border: 1px dashed #888;
            background-color: white;
            padding: 10px;
            border-radius: 10px;
            font-size: 14px;
            font-family: "Microsoft YaHei", "SimSun", "Consolas", "Courier New", monospace;
            font-weight: bold;
            }
            QPushButton {
            background-color: #6699cc;
            color: white;
            border: none;
            padding: 10px 20px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            border-radius: 5px;
            }
            QPushButton:hover {
            background-color: #5588bb;
            }
        """
        )
        try:
            response = requests.get(self.url_update_info)
            response.raise_for_status()
            response.encoding = 'utf-8'
            content = response.text
        except requests.RequestException as e:
            self.text_edit.setPlainText(f"Failed to retrieve update information: {e}")
            return

        self.text_edit.setPlainText(content)

        if not os.path.exists("CHANGELOG.md"):
            with open("CHANGELOG.md", "w", encoding="utf-8") as f:
                f.write(content)
                self.show()
        else:
            with open("CHANGELOG.md", "r", encoding="utf-8") as f:
                old_content = f.read()
                if content != old_content:
                    with open("CHANGELOG.md", "w", encoding="utf-8") as f:
                        f.write(content)
                        self.show()
