import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional, Union

class Logger:
    """
    高级日志中间件
    功能：
    1. 多组件日志区分
    2. 文件日志轮转
    3. GUI实时显示支持
    4. 异常自动捕获
    5. 日志分级控制
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(
        self,
        app_name: str = "App",
        log_dir: str = "logs",
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        gui_signal=None,
    ):
        if hasattr(self, '_initialized'):  # 确保单例只初始化一次
            return
            
        self.app_name = app_name
        self.log_dir = log_dir
        self.gui_signal = gui_signal
        
        # 创建日志目录
        os.makedirs(log_dir, exist_ok=True)
        
        # 主日志格式
        self.formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 初始化根logger
        self.root_logger = logging.getLogger()
        self.root_logger.setLevel(logging.DEBUG)
        
        # 添加文件处理器
        self._setup_file_handler(max_bytes, backup_count)
        
        # 添加控制台处理器
        self._setup_console_handler()
        
        # 添加GUI处理器（如果提供信号）
        if gui_signal:
            self._setup_gui_handler()
            
        # 捕获未处理异常
        self._setup_exception_handler()
        
        self._initialized = True
    
    def _setup_file_handler(self, max_bytes, backup_count):
        """配置文件日志轮转"""
        file_handler = RotatingFileHandler(
            filename=os.path.join(self.log_dir, f"{self.app_name}.log"),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(self.formatter)
        file_handler.flush()  # 强制刷新
        self.root_logger.addHandler(file_handler)
    
    def _setup_console_handler(self):
        """配置控制台日志"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self.formatter)
        self.root_logger.addHandler(console_handler)
    
    def _setup_gui_handler(self):
        """配置GUI日志显示"""
        class GuiLogHandler(logging.Handler):
            def __init__(self, signal):
                super().__init__()
                self.signal = signal
            
            def emit(self, record):
                msg = self.format(record)
                self.signal.emit(msg)
                
        gui_handler = GuiLogHandler(self.gui_signal)
        gui_handler.setFormatter(self.formatter)
        self.root_logger.addHandler(gui_handler)
    
    def _setup_exception_handler(self):
        """捕获未处理异常"""
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
                
            self.root_logger.critical(
                "未捕获的异常",
                exc_info=(exc_type, exc_value, exc_traceback)
            )
            
        sys.excepthook = handle_exception
    
    @classmethod
    def get_logger(cls, name: str, filename: Optional[str] = None, level=logging.DEBUG) -> logging.Logger:
        """获取组件专用logger，支持独立文件处理器"""
        if not cls._instance:
            raise RuntimeError("日志中间件未初始化，请先创建Logger实例")
        
        logger = logging.getLogger(name)
        
        if not logger.hasHandlers():  # 确保不会重复添加处理器
            if filename:
                # 为该实例添加独立的文件处理器
                handler = logging.FileHandler(
                    os.path.join(cls._instance.log_dir, filename),
                    encoding='utf-8'
                )
                handler.setLevel(level)
                handler.setFormatter(cls._instance.formatter)
                logger.addHandler(handler)
            
            logger.setLevel(level)
            logger.propagate = False  # 禁用日志传播
        
        return logger
    
    def set_level(self, level: Union[str, int]):
        """动态设置日志级别"""
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        self.root_logger.setLevel(level)
        
    def add_file_handler(self, filename: str, level=logging.DEBUG):
        """动态添加文件日志"""
        handler = logging.FileHandler(
            os.path.join(self.log_dir, filename),
            encoding='utf-8'
        )
        handler.setLevel(level)
        handler.setFormatter(self.formatter)
        self.root_logger.addHandler(handler)
        return handler

# 快捷访问方法（可选）
def init_logging(*args, **kwargs):
    """初始化日志中间件（快捷方式）"""
    return Logger(*args, **kwargs)

def get_logger(name: str):
    """获取logger（快捷方式）"""
    return Logger.get_logger(name)