import sys
import os
from PySide6.QtWidgets import (
    QTextEdit,
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help❓")
        self.setFixedSize(600, 400)
        self.setWindowFlag(Qt.FramelessWindowHint)

        layout = QVBoxLayout()

        title_label = QLabel("Help❓")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        txt_file_path = "./res/HELP.txt"
        self.text_edit = QTextEdit()
        if os.path.exists(txt_file_path):
            with open(txt_file_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.text_edit.setPlainText(content)
        else:
            self.text_edit.setPlainText("Help file not found.")
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
