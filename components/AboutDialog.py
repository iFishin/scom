from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QTextBrowser
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtCore import Qt
import os
from dotenv import load_dotenv

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About SCOM")
        self.setFixedSize(500, 600)
        self.setWindowFlag(Qt.FramelessWindowHint)

        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)  # Add margins

        # Title
        title_label = QLabel("About SCOM👋")
        title_font = QFont()
        title_font.setPointSize(32)  # Increase title font size
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Logo
        image_label = QLabel()
        pixmap = QPixmap("favicon.ico").scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(image_label)

        # Version information
        version_label = QLabel()
        version_font = QFont()
        version_font.setPointSize(16)
        version_font.setBold(True)
        version_label.setFont(version_font)
        version_label.setAlignment(Qt.AlignCenter)
        load_dotenv()
        version = os.getenv('VERSION', 'Unknown')
        version_label.setText(f"Version {version}")
        layout.addWidget(version_label)

        # Description
        text_browser = QTextBrowser()
        text_browser.setHtml(f"""
            <div style='text-align: center;'>
            <p style='font-size: 14px; margin: 10px 0;'>A Professional Serial Communication Tool</p>
            <p style='font-size: 14px; margin: 10px 0;'>Created by iFishin</p>
            <p style='font-size: 14px; margin: 10px 0;'>Developed by enthusiastic developers</p>
            <p style='font-size: 14px; margin: 10px 0;'>
            <a href='https://github.com/ifishin/SCOM' style='color: #6699cc; text-decoration: none;'>
            GitHub Repository
            </a>
            </p>
            </div>
        """)
        text_browser.setReadOnly(True)
        text_browser.setOpenExternalLinks(True)
        text_browser.setMinimumHeight(120)  # 设置最小高度避免出现滚动条
        text_browser.setMaximumHeight(150)  # 设置最大高度保持界面整洁
        layout.addWidget(text_browser)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_button = QPushButton("Close")
        close_button.setFixedWidth(120)
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)
