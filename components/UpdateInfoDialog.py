import os
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QFont
import requests
from utils.common import custom_print
import markdown
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
)
from PySide6.QtWebEngineWidgets import QWebEngineView


class UpdateInfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.url_update_info = "https://raw.githubusercontent.com/iFishin/scom/refs/heads/main/CHANGELOG.md"
        
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

        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(self.url_update_info, timeout=5)
                response.raise_for_status()
                response.encoding = 'utf-8'
                content = response.text
                break
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    error_html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <style>
                            body {{
                                font-family: "Microsoft YaHei", "SimSun", "Consolas", "Courier New", monospace;
                                font-size: 14px;
                                line-height: 1.6;
                                padding: 20px;
                                background-color: white;
                                color: #ff0000;
                            }}
                        </style>
                    </head>
                    <body>
                        <h1>Failed to retrieve update information after {max_retries} attempts: {e}</h1>
                    </body>
                    </html>
                    """
                    self.web_view.setHtml(error_html)
                    custom_print(f"Failed to retrieve update information after {max_retries} attempts: {e}")
                    return
                else:
                    custom_print(f"Attempt {attempt + 1} failed: {e}")

        # Convert Markdown to HTML
        html_content = markdown.markdown(
            content,
            extensions=[
                'fenced_code',
                'tables',
                'attr_list',
                'def_list',
                'nl2br'
            ]
        )
        
        # Add custom styles
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: "Microsoft YaHei", "SimSun", "Consolas", "Courier New", monospace;
                    font-size: 14px;
                    line-height: 1.6;
                    padding: 20px;
                    background-color: white;
                }}
                code {{
                    background-color: #f5f5f5;
                    padding: 2px 4px;
                    border-radius: 3px;
                    font-family: "Consolas", "Courier New", monospace;
                }}
                pre {{
                    background-color: #f5f5f5;
                    padding: 10px;
                    border-radius: 5px;
                    margin: 10px 0;
                    overflow-x: auto;
                }}
                h1, h2, h3, h4, h5, h6 {{
                    color: #444;
                    margin-top: 20px;
                    margin-bottom: 10px;
                }}
                p {{
                    margin: 10px 0;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        self.web_view.setHtml(html_template)

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
