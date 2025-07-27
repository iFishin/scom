import os
from PySide6.QtCore import Qt, QObject, Signal, QUrl, QTimer
from PySide6.QtGui import QFont
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from middileware.Logger import Logger, init_logging
import markdown
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QTextBrowser,
)

logger = init_logging().get_logger("UpdateChecker")


class UpdateChecker(QObject):
    """更新检查器 - 在主线程中运行"""
    finished = Signal(bool, bool)  # 完成信号，传递是否成功加载和是否需要显示对话框
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.network_manager = QNetworkAccessManager(self)
        self.url_update_info = "https://raw.githubusercontent.com/iFishin/scom/refs/heads/main/CHANGELOG.md"
        self.proxy_list = [
            "https://gh-proxy.com/",
            "https://gh-proxy.ygxz.in/",
            "https://goppx.com/"
        ]
        self.current_urls = []
        self.current_url_index = 0
        self.current_reply = None  # 保存当前的回复对象
        self.timeout_timer = None  # 保存超时定时器
        
    def start_check(self):
        """开始检查更新"""
        # 准备所有要尝试的URL
        self.current_urls = [self.url_update_info]
        for proxy in self.proxy_list:
            self.current_urls.append(f"{proxy}{self.url_update_info}")
        
        self.current_url_index = 0
        self._try_next_url()
    
    def _try_next_url(self):
        """尝试下一个URL"""
        # 清理之前的请求
        self._cleanup_current_request()
        
        if self.current_url_index >= len(self.current_urls):
            logger.error("所有访问方式均失败，无法获取更新信息")
            self.finished.emit(False, False)
            return
            
        url = self.current_urls[self.current_url_index]
        logger.info(f"尝试访问: {url}")
        
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader(b"User-Agent", b"SCOM-App/1.0")
        
        self.current_reply = self.network_manager.get(request)
        self.current_reply.finished.connect(self._handle_reply)
        
        # 创建超时定时器
        self.timeout_timer = QTimer(self)
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self._handle_timeout)
        self.timeout_timer.start(5000)
    
    def _cleanup_current_request(self):
        """清理当前的请求和定时器"""
        if self.timeout_timer:
            self.timeout_timer.stop()
            self.timeout_timer.deleteLater()
            self.timeout_timer = None
            
        if self.current_reply:
            if self.current_reply.isRunning():
                self.current_reply.abort()
            self.current_reply.deleteLater()
            self.current_reply = None
    
    def _handle_reply(self):
        """处理网络响应"""
        if not self.current_reply:
            return
            
        # 停止超时定时器
        if self.timeout_timer:
            self.timeout_timer.stop()
            
        if self.current_reply.error() == QNetworkReply.NetworkError.NoError:
            content = self.current_reply.readAll().data().decode('utf-8')
            logger.info("网络请求成功")
            self._cleanup_current_request()
            self._process_content(content)
        else:
            error_msg = self.current_reply.errorString()
            logger.error(f"网络请求失败: {error_msg}")
            self._cleanup_current_request()
            # 尝试下一个URL
            self.current_url_index += 1
            self._try_next_url()
    
    def _handle_timeout(self):
        """处理超时"""
        logger.error("网络请求超时")
        if self.current_reply and self.current_reply.isRunning():
            self.current_reply.abort()
        
        self._cleanup_current_request()
        # 尝试下一个URL
        self.current_url_index += 1
        self._try_next_url()
    
    def _process_content(self, content):
        """处理获取到的内容"""
        try:
            should_show_dialog = False
            if not os.path.exists("CHANGELOG.md"):
                with open("CHANGELOG.md", "w", encoding="utf-8") as f:
                    f.write(content)
                should_show_dialog = True
            else:
                with open("CHANGELOG.md", "r", encoding="utf-8") as f:
                    old_content = f.read()
                    if content != old_content:
                        with open("CHANGELOG.md", "w", encoding="utf-8") as f:
                            f.write(content)
                        should_show_dialog = True
            
            logger.info(f"更新信息处理完成，需要显示对话框: {should_show_dialog}")
            self.finished.emit(True, should_show_dialog)
        except Exception as e:
            logger.error(f"处理更新内容失败: {e}")
            self.finished.emit(False, False)
    
class UpdateInfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.url_update_info = "https://raw.githubusercontent.com/iFishin/scom/refs/heads/main/CHANGELOG.md"
        self.proxy_list = [
            "https://gh-proxy.com/",
            "https://gh-proxy.ygxz.in/",
            "https://goppx.com/"
        ]
        self.network_manager = QNetworkAccessManager()
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

        # 同步加载更新信息（保持原有逻辑）
        self._load_update_info()
    
    @staticmethod
    def load_update_info_async():
        """静态方法：异步加载更新信息，返回检查器对象"""
        checker = UpdateChecker()
        return checker
    
    def _load_update_info(self):
        """同步加载更新信息的内部方法"""
        # 创建一个简单的网络管理器来同步获取内容
        checker = UpdateChecker(self)
        
        def on_content_received(success, should_show):
            if success:
                # 读取本地文件并显示
                try:
                    if os.path.exists("CHANGELOG.md"):
                        with open("CHANGELOG.md", "r", encoding="utf-8") as f:
                            content = f.read()
                        self._display_content(content)
                    else:
                        self._display_error("无法找到更新信息文件")
                except Exception as e:
                    self._display_error(f"读取更新信息失败: {e}")
            else:
                self._display_error("无法获取更新信息")
        
        checker.finished.connect(on_content_received)
        checker.start_check()
    
    def _display_content(self, content):
        """显示内容"""
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
    
    def _display_error(self, error_msg):
        """显示错误信息"""
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
            <p>{error_msg}</p>
            <p>请检查网络连接或稍后再试。</p>
        </body>
        </html>
        """
        self.text_browser.setHtml(error_html)
