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
        """获取当前版本号 - 简化版"""
        version_sources = [
            (".env", lambda f: next((line.split("=", 1)[1].strip().strip('"').strip("'")
                                   for line in f if line.startswith("VERSION=")), None)),
            ("version.txt", lambda f: f.read().strip().strip('"').strip("'")),
            ("setup.py", lambda f: self._extract_version_from_setup(f.read())),
            ("package.json", lambda f: json.load(f).get("version"))
        ]

        for file_path, extractor in version_sources:
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        version = extractor(f)
                        if version:
                            # 确保版本字符串是干净的
                            clean_version = str(version).strip().strip('"').strip("'")
                            logger.info(f"Version from {file_path}: {clean_version}")
                            return clean_version
                except Exception as e:
                    logger.warning(f"Failed to read version from {file_path}: {e}")

        logger.warning("Using default version 0.9.0")
        return "0.9.0"

    def _extract_version_from_setup(self, content):
        """从setup.py提取版本号"""
        import re
        patterns = [
            r'version\s*=\s*["\']([^"\']+)["\']',
            r'__version__\s*=\s*["\']([^"\']+)["\']'
        ]
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        return None
    
    def check_for_updates(self, user_initiated=True):
        """检查更新"""
        if not user_initiated and not self._should_auto_check():
            logger.info("Auto-check skipped due to policy restrictions")
            return

        logger.info(f"Starting update check - User initiated: {user_initiated}")

        request = QNetworkRequest(QUrl(self.api_url))
        request.setRawHeader(b"Accept", b"application/vnd.github.v3+json")

        reply = self.network_manager.get(request)
        reply.finished.connect(lambda: self._handle_response(reply, user_initiated))

        # 简化超时处理
        QTimer.singleShot(10000, lambda: self._handle_timeout(reply))
    
    def _handle_timeout(self, reply):
        """处理请求超时"""
        if reply and not reply.isFinished():
            logger.warning("Update check request timed out")
            reply.abort()
            self.check_failed.emit("Request timed out. Please check your network connection.")
    
    def _should_auto_check(self):
        """判断是否应该进行自动检查 - 简化版"""
        config = self._load_config()

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
    
    def _handle_response(self, reply, user_initiated):
        """处理响应 - 简化版"""
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                error_msg = f"Network request failed: {reply.errorString()}"
                logger.error(error_msg)
                # 无论是否用户主动发起，都应该通知UI更新状态
                self.check_failed.emit(error_msg)
                return

            data = json.loads(reply.readAll().data().decode('utf-8'))
            latest_version = data.get("tag_name", "").lstrip("v")
            release_notes = data.get("body", "")

            if self._is_newer_version(latest_version):
                logger.info(f"New version found: {latest_version}")
                self.update_available.emit(latest_version, release_notes)
            else:
                # 无论是否用户主动发起，都应该通知UI当前是最新版本
                self.check_failed.emit("Currently the latest version")

        except Exception as e:
            error_msg = f"Failed to parse update information: {e}"
            logger.error(error_msg)
            # 无论是否用户主动发起，都应该通知UI错误状态
            self.check_failed.emit(error_msg)
        finally:
            reply.deleteLater()
            self._update_check_time()
    

    def _is_newer_version(self, latest_version):
        """比较版本号 - 简化版"""
        try:
            def version_tuple(v):
                # 清理版本字符串
                v = str(v).strip().strip('"').strip("'").lstrip('v')
                parts = v.split('-')[0].split('.')
                # 只取前3个部分，转换为整数
                version_parts = []
                for part in parts[:3]:
                    try:
                        version_parts.append(int(part))
                    except ValueError:
                        version_parts.append(0)
                # 补齐到3个部分
                while len(version_parts) < 3:
                    version_parts.append(0)
                return tuple(version_parts)

            current_tuple = version_tuple(self.current_version)
            latest_tuple = version_tuple(latest_version)

            logger.info(f"Version comparison: {current_tuple} vs {latest_tuple}")
            return latest_tuple > current_tuple

        except Exception as e:
            logger.error(f"Version comparison failed: {e}")
            return True
    
    def _load_config(self):
        """加载配置"""
        try:
            if os.path.exists("update_config.json"):
                with open("update_config.json", "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
        return {}

    def _save_config(self, config):
        """保存配置"""
        try:
            existing = self._load_config()
            existing.update(config)
            with open("update_config.json", "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def _update_check_time(self):
        """更新检查时间 - 简化版"""
        import datetime
        self._save_config({"last_check_time": datetime.datetime.now().isoformat()})
    
    @staticmethod
    def check_updates_on_startup():
        """启动时检查更新（静态方法）- 检查用户设置"""
        try:
            # 使用update_config.json中的设置
            checker = SafeUpdateChecker()
            config = checker._load_config()
            
            # 获取启动时检查更新的设置，默认值为True
            check_on_startup = config.get("check_on_startup_enabled", True)

            if not check_on_startup:
                logger.info("Update check on startup is disabled by user setting")
                return None

            logger.info("Update check on startup is enabled, starting check...")
            checker.check_for_updates(user_initiated=False)
            return checker

        except Exception as e:
            logger.warning(f"Failed to read startup update check setting: {e}")
            # 如果读取失败，默认执行检查
            logger.info("Defaulting to check updates on startup due to config read error")
            checker = SafeUpdateChecker()
            checker.check_for_updates(user_initiated=False)
            return checker


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
        
        # 对话框打开时自动开始检查
        QTimer.singleShot(500, self._auto_check_on_open)
    
    def _auto_check_on_open(self):
        """对话框打开时自动检查更新"""
        logger.info("Auto-checking for updates when dialog opens")
        
        # 首先显示正在检查的状态
        self.content_area.setHtml("""
        <div style='text-align: center; padding: 20px;'>
            <h3>Checking for updates...</h3>
            <p>Please wait while we check for the latest version</p>
        </div>
        """)
        
        self.check_button.setText("Checking...")
        self.check_button.setEnabled(False)
        
        # 对话框打开时的检查应该被视为用户主动操作，不受时间限制
        self.checker.check_for_updates(user_initiated=True)
    
    def _init_ui(self):
        """初始化UI - 简化版"""
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
            <h3>Initializing...</h3>
            <p>Preparing update check</p>
        </div>
        """)
        layout.addWidget(self.content_area)

        # 按钮区域 - 分为两行
        button_section = QVBoxLayout()
        
        # 第一行：操作按钮
        action_layout = QHBoxLayout()
        
        self.check_button = QPushButton("Manual Check")
        self.check_button.clicked.connect(self._manual_check)
        action_layout.addWidget(self.check_button)
        
        action_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        action_layout.addWidget(close_button)
        
        # 第二行：设置选项
        settings_layout = QHBoxLayout()
        
        # 启动时检查设置 - 简化标签
        self.startup_check_box = QCheckBox("Check on startup")
        self.startup_check_box.setChecked(self._get_startup_check_setting())
        self.startup_check_box.toggled.connect(self._save_startup_check_setting)
        self.startup_check_box.setToolTip("Enable automatic update check when application starts")
        settings_layout.addWidget(self.startup_check_box)

        settings_layout.addStretch()

        # 自动检查设置 - 简化标签
        self.auto_check_box = QCheckBox("Auto check")
        self.auto_check_box.setChecked(self._get_auto_check_setting())
        self.auto_check_box.toggled.connect(self._save_auto_check_setting)
        self.auto_check_box.setToolTip("Enable automatic periodic update checks")
        settings_layout.addWidget(self.auto_check_box)

        # 组装按钮区域
        button_section.addLayout(action_layout)
        button_section.addLayout(settings_layout)
        
        layout.addLayout(button_section)
        self.setLayout(layout)
    
    def _manual_check(self):
        """手动检查更新 - 简化版"""
        self.content_area.setHtml("""
        <div style='text-align: center; padding: 20px;'>
            <h3>Checking for updates...</h3>
            <p>Please wait</p>
        </div>
        """)

        self.check_button.setText("Checking...")
        self.check_button.setEnabled(False)

        # 使用现有的checker实例进行用户主动检查
        self.checker.check_for_updates(user_initiated=True)
    
    def _show_update_available(self, version, notes):
        """显示有可用更新 - 简化版"""
        # 重置按钮状态
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

        # 将手动检查按钮替换为下载按钮
        download_button = QPushButton("🌐 Open Download Page")
        download_button.clicked.connect(self._open_download_page)

        # 找到按钮布局并替换
        button_section = self.layout().itemAt(2).layout()  # 获取按钮区域
        action_layout = button_section.itemAt(0).layout()  # 获取第一行（操作按钮）
        action_layout.replaceWidget(self.check_button, download_button)
        self.check_button.deleteLater()
        self.check_button = download_button
    
    def _show_check_failed(self, error_msg):
        """显示检查失败 - 简化版"""
        # 重置按钮状态
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
            # 对于最新版本，将按钮改为"Check Again"
            self.check_button.setText("Check Again")
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
        """获取自动检查设置 - 简化版"""
        return self.checker._load_config().get("auto_check_enabled", True)

    def _save_auto_check_setting(self, enabled):
        """保存自动检查设置 - 简化版"""
        self.checker._save_config({"auto_check_enabled": enabled})
        logger.info(f"Automatic update check {'enabled' if enabled else 'disabled'}")

    def _get_startup_check_setting(self):
        """获取启动时检查设置"""
        return self.checker._load_config().get("check_on_startup_enabled", True)

    def _save_startup_check_setting(self, enabled):
        """保存启动时检查设置"""
        self.checker._save_config({"check_on_startup_enabled": enabled})
        logger.info(f"Startup update check {'enabled' if enabled else 'disabled'}")


# 向后兼容的类名
UpdateInfoDialog = SafeUpdateDialog
UpdateChecker = SafeUpdateChecker
