import sys
import os
import markdown
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
)
from PySide6.QtCore import Qt, QUrl, QSize
from PySide6.QtGui import QFont
from PySide6.QtWebEngineWidgets import QWebEngineView


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help❓")
        self.setFixedSize(600, 600)
        self.setWindowFlag(Qt.FramelessWindowHint)

        layout = QVBoxLayout()

        title_label = QLabel("Help❓")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        md_file_path = "./res/Help.md"
        self.web_view = QWebEngineView()
        if os.path.exists(md_file_path):
            with open(md_file_path, "r", encoding="utf-8") as f:
                content = f.read()
                # Get absolute path of res directory
                res_dir = os.path.abspath(os.path.dirname(md_file_path))
                
                # Calculate image width (90% of dialog width)
                dialog_width = self.width()
                image_width = int(dialog_width * 0.9)
                
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
                        img {{
                            max-width: 100%;
                            width: {image_width}px;
                            height: auto;
                            margin: 10px auto;
                            border-radius: 5px;
                            display: block;
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
                
                # Set HTML content
                self.web_view.setHtml(html_template, QUrl.fromLocalFile(res_dir + "/"))
        else:
            self.web_view.setHtml("<h1>Help file not found.</h1>")
            
        layout.addWidget(self.web_view)

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
