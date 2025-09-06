import os
import json
from PySide6.QtCore import Qt, QObject, Signal, QUrl, QTimer
from PySide6.QtGui import QFont
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, 
    QTextBrowser, QMessageBox, QCheckBox
)
from middileware.Logger import Logger, init_logging
import markdown

logger = init_logging().get_logger("SafeUpdateChecker")


class SafeUpdateChecker(QObject):
    """安全的更新检查器 - 减少报毒风险"""
    update_available = Signal(str, str)  # 版本号，更新信息
    check_failed = Signal(str)  # 错误信息
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.network_manager = QNetworkAccessManager(self)
        
        # 使用更安全的API端点
        self.api_url = "https://api.github.com/repos/iFishin/scom/releases/latest"
        self.current_version = self._get_current_version()
        
    def _get_current_version(self):
        """获取当前版本号"""
        try:
            # 方法1: 从.env文件读取版本
            if os.path.exists(".env"):
                with open(".env", "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("VERSION="):
                            version = line.split("=", 1)[1].strip().strip('"')
                            logger.info(f"Version obtained from .env file: {version}")
                            return version
            
            # 方法2: 从version.txt文件读取
            if os.path.exists("version.txt"):
                with open("version.txt", "r", encoding="utf-8") as f:
                    version = f.read().strip()
                    logger.info(f"Version obtained from version.txt: {version}")
                    return version
            
            # 方法3: 从setup.py读取版本
            if os.path.exists("setup.py"):
                with open("setup.py", "r", encoding="utf-8") as f:
                    content = f.read()
                    import re
                    # 查找版本号模式
                    version_patterns = [
                        r'version\s*=\s*["\']([^"\']+)["\']',
                        r'__version__\s*=\s*["\']([^"\']+)["\']',
                        r'CURRENT_VERSION\s*=\s*os\.getenv\(["\']VERSION["\'],\s*["\']([^"\']+)["\']',
                    ]
                    for pattern in version_patterns:
                        match = re.search(pattern, content)
                        if match:
                            version = match.group(1)
                            logger.info(f"Version obtained from setup.py: {version}")
                            return version
            
            # 方法4: 从package.json读取（如果有的话）
            if os.path.exists("package.json"):
                import json
                with open("package.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    version = data.get("version")
                    if version:
                        logger.info(f"Version obtained from package.json: {version}")
                        return version
            
            # 默认版本（用于测试）
            logger.warning("Unable to obtain current version, using default version 0.9.0")
            return "0.9.0"  # 设置一个较低的版本号用于测试
            
        except Exception as e:
            logger.warning(f"Unable to obtain current version: {e}")
            return "0.9.0"
    
    def check_for_updates(self, user_initiated=True):
        """检查更新 - 区分用户主动检查和自动检查"""
        if not user_initiated:
            # 自动检查时，添加更多限制
            if not self._should_auto_check():
                return
        
        logger.info(f"Starting update check - User initiated: {user_initiated}")
        
        request = QNetworkRequest(QUrl(self.api_url))
        # 使用标准的User-Agent，避免伪装
        request.setRawHeader(b"Accept", b"application/vnd.github.v3+json")
        
        reply = self.network_manager.get(request)
        reply.finished.connect(lambda: self._handle_response(reply, user_initiated))
        
        # 设置超时 - 使用弱引用避免对象生命周期问题
        import weakref
        reply_ref = weakref.ref(reply)
        QTimer.singleShot(10000, lambda: self._handle_timeout(reply_ref))
    
    def _should_auto_check(self):
        """判断是否应该进行自动检查"""
        try:
            config_file = "update_config.json"
            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    
                # 检查是否禁用了自动更新
                if not config.get("auto_check_enabled", True):
                    return False
                    
                # 检查上次检查时间（避免频繁检查）
                import datetime
                last_check = config.get("last_check_time")
                if last_check:
                    last_time = datetime.datetime.fromisoformat(last_check)
                    if (datetime.datetime.now() - last_time).days < 1:
                        return False
            
            return True
        except Exception as e:
            logger.error(f"Failed to check auto-update configuration: {e}")
            return False
    
    def _handle_response(self, reply, user_initiated):
        """处理响应"""
        try:
            if reply.error() == QNetworkReply.NetworkError.NoError:
                data = reply.readAll().data().decode('utf-8')
                release_info = json.loads(data)
                
                latest_version = release_info.get("tag_name", "").lstrip("v")
                release_notes = release_info.get("body", "")
                
                if self._is_newer_version(latest_version):
                    logger.info(f"New version found: {latest_version}")
                    self.update_available.emit(latest_version, release_notes)
                else:
                    if user_initiated:
                        # 只有用户主动检查时才显示"已是最新版本"
                        self.check_failed.emit("Currently the latest version")
            else:
                error_msg = f"Network request failed: {reply.errorString()}"
                logger.error(error_msg)
                if user_initiated:
                    self.check_failed.emit(error_msg)
        except Exception as e:
            error_msg = f"Failed to parse update information: {e}"
            logger.error(error_msg)
            if user_initiated:
                self.check_failed.emit(error_msg)
        finally:
            reply.deleteLater()
            self._update_check_time()
    
    def _handle_timeout(self, reply_ref):
        """处理超时"""
        reply = reply_ref() if reply_ref else None
        if reply and reply.isRunning():
            logger.warning("Update check timed out, aborting request")
            reply.abort()
        elif reply is None:
            logger.debug("Network request completed, no timeout handling needed")
        else:
            logger.debug("Network request completed, no timeout handling needed")
    
    def _is_newer_version(self, latest_version):
        """比较版本号"""
        try:
            def version_tuple(v):
                # 移除 'v' 前缀并分割版本号
                clean_v = v.lstrip('v').strip()
                # 处理版本号格式：1.0.0, 1.0.0-beta, 1.0.0.1 等
                parts = clean_v.split('-')[0].split('.')
                # 转换为整数元组，不足3位的补0
                return tuple(int(x) for x in parts[:3]) + (0,) * (3 - len(parts))
            
            current_tuple = version_tuple(self.current_version)
            latest_tuple = version_tuple(latest_version)
            
            logger.info(f"Version comparison: Current {self.current_version} ({current_tuple}) vs Latest {latest_version} ({latest_tuple})")
            
            is_newer = latest_tuple > current_tuple
            logger.info(f"Is newer version available: {is_newer}")
            
            return is_newer
            
        except Exception as e:
            logger.error(f"Version comparison failed: {e}")
            # 出错时默认认为有新版本，让用户自己判断
            return True
    
    def _update_check_time(self):
        """更新检查时间"""
        try:
            import datetime
            config = {"last_check_time": datetime.datetime.now().isoformat()}
            
            config_file = "update_config.json"
            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8") as f:
                    existing_config = json.load(f)
                    existing_config.update(config)
                    config = existing_config
            
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to update check time: {e}")


class SafeUpdateDialog(QDialog):
    """安全的更新对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SCOM - Update Check")
        self.setFixedSize(500, 300)
        self.setWindowFlag(Qt.FramelessWindowHint)
        
        self.checker = SafeUpdateChecker(self)
        self.checker.update_available.connect(self._show_update_available)
        self.checker.check_failed.connect(self._show_check_failed)
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("Update Check")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 内容区域
        self.content_area = QTextBrowser()
        self.content_area.setHtml("""
        <div style='text-align: center; padding: 20px;'>
            <h3>Checking for updates...</h3>
            <p>Please wait</p>
        </div>
        """)
        layout.addWidget(self.content_area)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.check_button = QPushButton("Manual Check")
        self.check_button.clicked.connect(self._manual_check)
        button_layout.addWidget(self.check_button)
        
        button_layout.addStretch()
        
        # 自动检查设置
        self.auto_check_box = QCheckBox("Enable automatic update checks")
        self.auto_check_box.setChecked(self._get_auto_check_setting())
        self.auto_check_box.toggled.connect(self._save_auto_check_setting)
        button_layout.addWidget(self.auto_check_box)
        
        button_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def _manual_check(self):
        """手动检查更新"""
        self.content_area.setHtml("""
        <div style='text-align: center; padding: 20px;'>
            <h3>Checking for updates...</h3>
            <p>Please wait</p>
        </div>
        """)
        
        # 重新启用检查按钮的文本
        self.check_button.setText("Checking...")
        self.check_button.setEnabled(False)
        
        # 强制刷新checker实例
        self.checker = SafeUpdateChecker(self)
        self.checker.update_available.connect(self._show_update_available)
        self.checker.check_failed.connect(self._show_check_failed)
        
        # 开始检查
        self.checker.check_for_updates(user_initiated=True)
    
    def _show_update_available(self, version, notes):
        """显示有可用更新"""
        # 重新启用按钮
        self.check_button.setText("Manual Check")
        self.check_button.setEnabled(True)
        
        html_content = f"""
        <div style='padding: 20px;'>
            <h3 style='color: #0066cc;'>🎉 New version available: v{version}</h3>
            <div style='background-color: #f0f8ff; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #0066cc;'>
                <h4 style='margin-top: 0;'>📝 Update notes:</h4>
                <div style='max-height: 200px; overflow-y: auto; background-color: white; padding: 10px; border-radius: 4px;'>
                    <pre style='white-space: pre-wrap; font-family: "Microsoft YaHei", "Consolas", sans-serif; font-size: 12px; line-height: 1.4; margin: 0;'>{notes}</pre>
                </div>
            </div>
            <div style='background-color: #fff3cd; padding: 10px; border-radius: 5px; border: 1px solid #ffeaa7; margin: 10px 0;'>
                <p style='margin: 0;'><strong>🔒 Security note:</strong> Please visit the official GitHub Releases page to manually download the latest version to ensure software security.</p>
            </div>
            <p style='text-align: center;'>
                <a href='https://github.com/iFishin/scom/releases/latest' style='color: #0066cc; text-decoration: none; font-weight: bold;'>
                    🔗 Click to visit download page
                </a>
            </p>
        </div>
        """
        self.content_area.setHtml(html_content)
        
        # 添加下载按钮
        download_button = QPushButton("🌐 Open Download Page")
        download_button.clicked.connect(self._open_download_page)
        
        # 替换检查按钮
        button_layout = self.layout().itemAt(2).layout()
        button_layout.replaceWidget(self.check_button, download_button)
        self.check_button.deleteLater()
        self.check_button = download_button
    
    def _show_check_failed(self, error_msg):
        """显示检查失败"""
        # 重新启用按钮
        self.check_button.setText("Retry Check")
        self.check_button.setEnabled(True)
        
        if "Currently the latest version" in error_msg:
            html_content = f"""
            <div style='text-align: center; padding: 20px;'>
                <h3 style='color: #28a745;'>✅ {error_msg}</h3>
                <div style='background-color: #d4edda; padding: 15px; border-radius: 8px; margin: 15px 0; border: 1px solid #c3e6cb;'>
                    <p style='margin: 0; color: #155724;'>🎉 You are using the latest version, no update needed!</p>
                </div>
                <p style='color: #666; font-size: 14px;'>
                    Current version: <strong>{self.checker.current_version}</strong><br>
                    <small>For development versions, visit: <a href='https://github.com/iFishin/scom' style='color: #0066cc;'>GitHub Project Page</a></small>
                </p>
            </div>
            """
        else:
            html_content = f"""
            <div style='text-align: center; padding: 20px;'>
                <h3 style='color: #dc3545;'>❌ Update check failed</h3>
                <div style='background-color: #f8d7da; padding: 15px; border-radius: 8px; margin: 15px 0; border: 1px solid #f5c6cb;'>
                    <p style='margin: 0; color: #721c24;'><strong>Error message:</strong> {error_msg}</p>
                </div>
                <div style='background-color: #fff3cd; padding: 10px; border-radius: 5px; border: 1px solid #ffeaa7; margin: 10px 0;'>
                    <p style='margin: 0; color: #856404;'><strong>💡 Suggestions:</strong></p>
                    <ul style='text-align: left; margin: 5px 0; color: #856404;'>
                        <li>Check network connection</li>
                        <li>Try again later</li>
                        <li>Manually visit the project page for updates</li>
                    </ul>
                </div>
                <p style='color: #666; font-size: 14px;'>
                    <a href='https://github.com/iFishin/scom/releases' style='color: #0066cc;'>🔗 Visit GitHub Releases</a>
                </p>
            </div>
            """
        self.content_area.setHtml(html_content)
    
    def _open_download_page(self):
        """打开下载页面"""
        from PySide6.QtGui import QDesktopServices
        QDesktopServices.openUrl(QUrl("https://github.com/iFishin/scom/releases"))
    
    def _get_auto_check_setting(self):
        """获取自动检查设置"""
        try:
            if os.path.exists("update_config.json"):
                with open("update_config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)
                    return config.get("auto_check_enabled", True)
            return True
        except Exception:
            return True
    
    def _save_auto_check_setting(self, enabled):
        """保存自动检查设置"""
        try:
            config = {"auto_check_enabled": enabled}
            
            if os.path.exists("update_config.json"):
                with open("update_config.json", "r", encoding="utf-8") as f:
                    existing_config = json.load(f)
                    existing_config.update(config)
                    config = existing_config
            
            with open("update_config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
                
            logger.info(f"Automatic update check {'enabled' if enabled else 'disabled'}")
        except Exception as e:
            logger.error(f"Failed to save automatic check setting: {e}")
    
    @staticmethod
    def check_updates_on_startup():
        """启动时检查更新（静态方法）"""
        checker = SafeUpdateChecker()
        checker.check_for_updates(user_initiated=False)
        return checker


# 向后兼容的类名
UpdateInfoDialog = SafeUpdateDialog
UpdateChecker = SafeUpdateChecker
