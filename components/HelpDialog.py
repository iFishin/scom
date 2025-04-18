import sys
import os
import markdown
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QPushButton,
    QHBoxLayout,
)
from PySide6.QtCore import Qt, QUrl, QSize
from PySide6.QtGui import QFont
from PySide6.QtWebEngineWidgets import QWebEngineView


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("helpDialog")  # 设置对象名称以应用特定样式
        self.setWindowTitle("帮助")
        self.setFixedSize(800, 700)
        self.setWindowFlag(Qt.FramelessWindowHint)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        md_file_path = "./res/Help.md"
        self.web_view = QWebEngineView()
        if os.path.exists(md_file_path):
            with open(md_file_path, "r", encoding="utf-8") as f:
                content = f.read()
                res_dir = os.path.abspath(os.path.dirname(md_file_path))
                dialog_width = self.width()
                image_width = int(dialog_width * 0.9)
                
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
                
                html_template = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <style>
                        body {{
                            font-family: "Microsoft YaHei", "SimSun", "Consolas", "Courier New", monospace;
                            font-size: 15px;
                            line-height: 1.8;
                            padding: 20px;
                            background-color: white;
                            color: #333;
                        }}
                        img {{
                            max-width: 100%;
                            width: {image_width}px;
                            height: auto;
                            margin: 15px auto;
                            border-radius: 8px;
                            display: block;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        }}
                        code {{
                            background-color: #f8f9fa;
                            padding: 3px 6px;
                            border-radius: 4px;
                            font-family: "Consolas", "Courier New", monospace;
                            color: #e83e8c;
                        }}
                        pre {{
                            background-color: #f8f9fa;
                            padding: 15px;
                            border-radius: 8px;
                            margin: 15px 0;
                            overflow-x: auto;
                            border: 1px solid #e9ecef;
                        }}
                        h1, h2, h3, h4, h5, h6 {{
                            color: #2c3e50;
                            margin-top: 25px;
                            margin-bottom: 15px;
                            font-weight: 600;
                        }}
                        p {{
                            margin: 12px 0;
                        }}
                        a {{
                            color: #007bff;
                            text-decoration: none;
                        }}
                        a:hover {{
                            text-decoration: underline;
                        }}
                    </style>
                </head>
                <body>
                    {html_content}
                </body>
                </html>
                """
                
                self.web_view.setHtml(html_template, QUrl.fromLocalFile(res_dir + "/"))
        else:
            self.web_view.setHtml("<h1>帮助文件未找到</h1>")
            
        layout.addWidget(self.web_view)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_button = QPushButton("Close")
        close_button.setObjectName("closeButton")  # 设置对象名称以应用特定样式
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.setStyleSheet(
            """
            QDialog {
                border-radius: 12px;
                border: 1px solid #e0e0e0;
                background-color: white;
            }
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                padding: 8px 16px;
                text-align: center;
                font-size: 14px;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:pressed {
                background-color: #2d6da3;
            }
            """
        )
