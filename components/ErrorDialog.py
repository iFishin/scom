"""
错误提示框组件
提供统一的错误消息显示界面
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QWidget, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QFont, QPixmap
import utils.common as common
from middileware.Logger import Logger

logger = Logger(
    app_name="ErrorDialog",
    log_dir="logs",
    max_bytes=10 * 1024 * 1024,
    backup_count=3
).get_logger("ErrorDialog")

class ErrorDialog(QDialog):
    """通用错误提示框组件"""
    
    def __init__(self, parent=None, title="错误", message="", details="", error_type="error"):
        """
        初始化错误对话框
        
        Args:
            parent: 父窗口
            title: 对话框标题
            message: 主要错误消息
            details: 详细错误信息（可选）
            error_type: 错误类型 ("error", "warning", "info", "critical")
        """
        super().__init__(parent)
        self.title = title
        self.message = message
        self.details = details
        self.error_type = error_type
        
        self.init_ui()
        self.setup_style()
        
    def init_ui(self):
        """初始化UI界面"""
        self.setWindowTitle(self.title)
        self.setModal(True)
        self.setMinimumSize(400, 200)
        self.setMaximumSize(600, 400)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 顶部消息区域
        message_frame = self.create_message_frame()
        main_layout.addWidget(message_frame)
        
        # 详细信息区域（如果有的话）
        if self.details:
            details_frame = self.create_details_frame()
            main_layout.addWidget(details_frame)
        
        # 按钮区域
        button_frame = self.create_button_frame()
        main_layout.addWidget(button_frame)
        
    def create_message_frame(self):
        """创建消息显示区域"""
        frame = QFrame()
        frame.setObjectName("message_frame")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 图标
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignTop)
        icon_label.setFixedSize(48, 48)
        
        # 根据错误类型设置图标
        icon_path = self.get_icon_path()
        if icon_path:
            icon_label.setPixmap(QPixmap(icon_path).scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        # 消息文本
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignTop)
        message_label.setObjectName("message_label")
        
        # 设置字体
        font = QFont()
        font.setPointSize(10)
        message_label.setFont(font)
        
        layout.addWidget(icon_label)
        layout.addWidget(message_label, 1)
        
        return frame
        
    def create_details_frame(self):
        """创建详细信息区域"""
        frame = QFrame()
        frame.setObjectName("details_frame")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 10, 0, 0)
        
        # 详细信息标签
        details_label = QLabel("详细信息:")
        details_label.setObjectName("details_header")
        layout.addWidget(details_label)
        
        # 详细信息文本框
        self.details_text = QTextEdit()
        self.details_text.setPlainText(self.details)
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(120)
        self.details_text.setObjectName("details_text")
        layout.addWidget(self.details_text)
        
        return frame
        
    def create_button_frame(self):
        """创建按钮区域"""
        frame = QFrame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 10, 0, 0)
        
        # 添加弹性空间
        layout.addStretch()
        
        # 确定按钮
        self.ok_button = QPushButton("OK")
        self.ok_button.setMinimumSize(80, 30)
        self.ok_button.setObjectName("ok_button")
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setDefault(True)
        
        # 如果有详细信息，添加复制按钮
        if self.details:
            self.copy_button = QPushButton("Copy Details")
            self.copy_button.setMinimumSize(80, 30)
            self.copy_button.setObjectName("copy_button")
            self.copy_button.clicked.connect(self.copy_details)
            layout.addWidget(self.copy_button)
        
        layout.addWidget(self.ok_button)
        
        return frame
        
    def get_icon_path(self):
        """根据错误类型获取图标路径"""
        icon_map = {
            "error": "res/error.png",
            "warning": "res/warning.png", 
            "info": "res/info.png",
            "critical": "res/critical.png"
        }
        
        icon_file = icon_map.get(self.error_type, "res/error.png")
        return common.safe_resource_path(icon_file, fallback="")
        
    def setup_style(self):
        """设置样式"""
        style = """
        QDialog {
            background-color: #ffffff;
            border: 1px solid #d0d0d0;
        }
        
        #message_frame {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 10px;
        }
        
        #message_label {
            color: #212529;
            font-size: 11px;
            line-height: 1.4;
        }
        
        #details_frame {
            border-top: 1px solid #e9ecef;
            padding-top: 10px;
        }
        
        #details_header {
            color: #6c757d;
            font-weight: bold;
            font-size: 9px;
        }
        
        #details_text {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            color: #495057;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 9px;
            padding: 8px;
        }
        
        #ok_button, #copy_button {
            background-color: #007bff;
            border: none;
            border-radius: 4px;
            color: white;
            font-size: 10px;
            font-weight: bold;
            padding: 6px 12px;
        }
        
        #ok_button:hover, #copy_button:hover {
            background-color: #0056b3;
        }
        
        #ok_button:pressed, #copy_button:pressed {
            background-color: #004085;
        }
        
        #copy_button {
            background-color: #6c757d;
            margin-right: 10px;
        }
        
        #copy_button:hover {
            background-color: #545b62;
        }
        """
        
        # 根据错误类型调整消息框颜色
        if self.error_type == "error" or self.error_type == "critical":
            style += """
            #message_frame {
                background-color: #f8d7da;
                border-color: #f5c6cb;
            }
            #message_label {
                color: #721c24;
            }
            """
        elif self.error_type == "warning":
            style += """
            #message_frame {
                background-color: #fff3cd;
                border-color: #ffeaa7;
            }
            #message_label {
                color: #856404;
            }
            """
        elif self.error_type == "info":
            style += """
            #message_frame {
                background-color: #d1ecf1;
                border-color: #bee5eb;
            }
            #message_label {
                color: #0c5460;
            }
            """
            
        self.setStyleSheet(style)
        
    def copy_details(self):
        """复制详细信息到剪贴板"""
        try:
            from PySide6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            full_text = f"错误: {self.message}\n\n详细信息:\n{self.details}"
            clipboard.setText(full_text)
            
            # 临时改变按钮文本提示复制成功
            original_text = self.copy_button.text()
            self.copy_button.setText("Copied!")
            
            # 2秒后恢复原文本
            from PySide6.QtCore import QTimer
            QTimer.singleShot(2000, lambda: self.copy_button.setText(original_text))
            
        except Exception as e:
            logger.error(f"Failed to copy details: {e}")

    @staticmethod
    def show_error(parent=None, title="Error", message="", details=""):
        """显示错误对话框的静态方法"""
        dialog = ErrorDialog(parent, title, message, details, "error")
        return dialog.exec()
        
    @staticmethod
    def show_warning(parent=None, title="Warning", message="", details=""):
        """显示警告对话框的静态方法"""
        dialog = ErrorDialog(parent, title, message, details, "warning")
        return dialog.exec()
        
    @staticmethod
    def show_info(parent=None, title="Information", message="", details=""):
        """显示信息对话框的静态方法"""
        dialog = ErrorDialog(parent, title, message, details, "info")
        return dialog.exec()
        
    @staticmethod
    def show_critical(parent=None, title="Critical Error", message="", details=""):
        """显示严重错误对话框的静态方法"""
        dialog = ErrorDialog(parent, title, message, details, "critical")
        return dialog.exec()
