from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QTextBrowser
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtCore import Qt

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About SCOM")
        self.setFixedSize(600, 400)
        self.setWindowFlag(Qt.FramelessWindowHint)

        layout = QVBoxLayout()

        title_label = QLabel("About SCOM👋")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        image_label = QLabel()
        pixmap = QPixmap("favicon.ico").scaled(125, 125)
        image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(image_label)

        text_browser = QTextBrowser()
        text_browser.setHtml("""
            <p>Version: 1.0</p>
            <p>Description: Serial Communication Tool</p>
            <p>Repository: <a href="https://github.com/ifishin/SCOM">https://github.com/ifishin/SCOM</a></p>
        """)
        text_browser.setReadOnly(True)
        layout.addWidget(text_browser)

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
            QTextBrowser {
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
        """)
