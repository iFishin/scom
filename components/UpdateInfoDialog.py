import os
from PySide6.QtCore import Qt
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
    QTextBrowser,
)


class UpdateInfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.url_update_info = "https://raw.githubusercontent.com/iFishin/scom/refs/heads/main/CHANGELOG.md"
        self.proxy_list = [
            "https://gh-proxy.com/",
            "https://gh-proxy.ygxz.in/",
            "https://goppx.com/"
        ]
        self.setWindowTitle("Update Information")
        self.setFixedSize(600, 400)
        self.setWindowFlag(Qt.FramelessWindowHint)


        title_label = QLabel("Update Information")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)
        layout.addWidget(self.text_browser)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # 尝试获取更新信息
        content = None
        max_retries = 3
        
        # 首先尝试直接访问
        custom_print("尝试直接访问GitHub...")
        for attempt in range(max_retries):
            try:
                response = requests.get(self.url_update_info, timeout=5)
                response.raise_for_status()
                response.encoding = 'utf-8'
                content = response.text
                custom_print("直接访问GitHub成功")
                break
            except requests.RequestException as e:
                custom_print(f"直接访问尝试 {attempt + 1} 失败: {e}")
                
                # 最后一次尝试失败后，不要立即返回，继续尝试代理
                if attempt == max_retries - 1:
                    custom_print("直接访问GitHub失败，尝试使用代理...")
        
        # 如果直接访问失败，依次尝试代理
        if content is None:
            for proxy in self.proxy_list:
                proxy_url = f"{proxy}{self.url_update_info}"
                custom_print(f"尝试使用代理: {proxy}")
                
                for attempt in range(max_retries):
                    try:
                        response = requests.get(proxy_url, timeout=8)  # 代理可能较慢，增加超时时间
                        response.raise_for_status()
                        response.encoding = 'utf-8'
                        content = response.text
                        custom_print(f"使用代理 {proxy} 访问成功")
                        break
                    except requests.RequestException as e:
                        custom_print(f"代理 {proxy} 尝试 {attempt + 1} 失败: {e}")
                        
                        # 当前代理的所有尝试都失败
                        if attempt == max_retries - 1:
                            custom_print(f"代理 {proxy} 访问失败，尝试下一个代理...")
                
                # 如果此代理成功获取内容，不再尝试其他代理
                if content is not None:
                    break
        
        # 如果所有方法都失败
        if content is None:
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
                <h1>无法获取更新信息</h1>
                <p>所有访问方式均失败，请检查网络连接或稍后再试。</p>
            </body>
            </html>
            """
            self.text_browser.setHtml(error_html)
            custom_print("所有访问方式均失败，无法获取更新信息")
            return

        # 处理成功获取的内容
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
        
        self.text_browser.setHtml(html_template)

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
