from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtCore import Qt

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About SCOM")
        self.setFixedSize(400, 300)
        self.setWindowFlag(Qt.FramelessWindowHint)

        layout = QVBoxLayout()

        icon_label = QLabel()
        icon = QPixmap("./favicon.ico").scaled(100, 100, Qt.KeepAspectRatio)
        icon_label.setPixmap(icon)
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        title_label = QLabel("SCOM")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        text_label = QLabel()
        text_font = QFont()
        text_font.setPointSize(14)
        text_label.setFont(text_font)
        text_label.setText("Version: 1.0\nDescription: Serial Communication Tool")
        text_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(text_label)

        repo_label = QLabel()
        repo_label.setText('<a href="https://github.com/ifishin/SCOM">Repository</a>')
        repo_label.setAlignment(Qt.AlignLeft)
        repo_label.setOpenExternalLinks(True)
        layout.addWidget(repo_label)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.setStyleSheet("""
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
                font-family: "Consolas", "Courier New", monospace;
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
        """)