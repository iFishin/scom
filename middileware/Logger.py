import logging
import os
import sys
import traceback
import threading
import time
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional, Union, Dict, Any
from functools import wraps

try:
    from PySide6.QtCore import QObject, Signal, QTimer, QThread
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False

class Logger:
    """
    高级日志中间件 - 专为PySide6应用优化
    功能：
    1. 多组件日志区分
    2. 文件日志轮转
    3. GUI实时显示支持
    4. 异常自动捕获
    5. 日志分级控制
    6. PySide6 UI错误专项跟踪
    7. 线程安全的Qt信号处理
    8. UI性能监控
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
        enable_ui_monitoring: bool = True,
    ):
        if hasattr(self, '_initialized'):  # 确保单例只初始化一次
            return
            
        self.app_name = app_name
        self.log_dir = log_dir
        self.gui_signal = gui_signal
        self.enable_ui_monitoring = enable_ui_monitoring
        
        # UI错误统计
        self.ui_error_stats = {
            'widget_errors': 0,
            'signal_errors': 0,
            'layout_errors': 0,
            'style_errors': 0,
            'resource_errors': 0,
            'thread_errors': 0,
        }
        
        # 性能监控数据
        self.performance_data = {
            'ui_operations': [],
            'memory_usage': [],
            'response_times': [],
        }
        
        # 创建日志目录
        os.makedirs(log_dir, exist_ok=True)
        
        # 主日志格式
        self.formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        )
        
        # UI专用格式
        self.ui_formatter = logging.Formatter(
            '%(asctime)s - UI-%(levelname)s - %(message)s - [Thread:%(thread)d]'
        )
        
        # 初始化根logger
        self.root_logger = logging.getLogger()
        self.root_logger.setLevel(logging.DEBUG)
        
        # 添加文件处理器
        self._setup_file_handler(max_bytes, backup_count)
        
        # 添加控制台处理器
        self._setup_console_handler()
        
        # 添加UI专用处理器
        self._setup_ui_handlers()
        
        # 添加GUI处理器（如果提供信号）
        if gui_signal:
            self._setup_gui_handler()
            
        # 捕获未处理异常
        self._setup_exception_handler()
        
        # 初始化UI监控
        if enable_ui_monitoring and PYSIDE6_AVAILABLE:
            self._setup_ui_monitoring()
            
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
    
    def _setup_ui_handlers(self):
        """配置UI专用日志处理器"""
        # UI错误专用文件
        ui_error_handler = RotatingFileHandler(
            filename=os.path.join(self.log_dir, f"{self.app_name}_ui_errors.log"),
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        ui_error_handler.setFormatter(self.ui_formatter)
        ui_error_handler.setLevel(logging.ERROR)
        
        # 添加过滤器，只处理UI相关错误
        class UIErrorFilter(logging.Filter):
            def filter(self, record):
                ui_keywords = ['widget', 'signal', 'slot', 'layout', 'style', 'qss', 'pyside', 'qt']
                message = record.getMessage().lower()
                return any(keyword in message for keyword in ui_keywords)
        
        ui_error_handler.addFilter(UIErrorFilter())
        self.root_logger.addHandler(ui_error_handler)
        
        # 性能监控日志
        if self.enable_ui_monitoring:
            perf_handler = logging.FileHandler(
                os.path.join(self.log_dir, f"{self.app_name}_performance.log"),
                encoding='utf-8'
            )
            perf_formatter = logging.Formatter(
                '%(asctime)s - PERF - %(message)s'
            )
            perf_handler.setFormatter(perf_formatter)
            perf_handler.setLevel(logging.INFO)
            
            # 性能专用logger
            self.perf_logger = logging.getLogger('performance')
            self.perf_logger.addHandler(perf_handler)
            self.perf_logger.setLevel(logging.INFO)
            self.perf_logger.propagate = False
    
    def _setup_ui_monitoring(self):
        """设置UI性能监控"""
        if not PYSIDE6_AVAILABLE:
            return
            
        # 创建监控定时器
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._collect_performance_data)
        self.monitor_timer.start(5000)  # 每5秒收集一次数据
    
    def _collect_performance_data(self):
        """收集性能数据"""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            self.performance_data['memory_usage'].append({
                'timestamp': datetime.now(),
                'memory_mb': memory_mb
            })
            
            # 保持最近100条记录
            if len(self.performance_data['memory_usage']) > 100:
                self.performance_data['memory_usage'].pop(0)
                
            # 记录到性能日志
            if hasattr(self, 'perf_logger'):
                self.perf_logger.info(f"Memory: {memory_mb:.2f}MB")
                
        except ImportError:
            pass  # psutil未安装时跳过
        except Exception as e:
            self.root_logger.warning(f"性能数据收集失败: {e}")
    
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

    # PySide6 专用日志方法
    def log_ui_error(self, error_type: str, widget_name: str, error_msg: str, exc_info=None):
        """记录UI错误的专用方法"""
        self.ui_error_stats[f'{error_type}_errors'] = self.ui_error_stats.get(f'{error_type}_errors', 0) + 1
        
        message = f"UI-{error_type.upper()}: Widget[{widget_name}] - {error_msg}"
        if exc_info:
            self.root_logger.error(message, exc_info=exc_info)
        else:
            self.root_logger.error(message)
    
    def log_widget_operation(self, widget_name: str, operation: str, duration_ms: float = None):
        """记录UI组件操作"""
        if hasattr(self, 'perf_logger'):
            msg = f"Widget[{widget_name}] {operation}"
            if duration_ms is not None:
                msg += f" - {duration_ms:.2f}ms"
            self.perf_logger.info(msg)
    
    def log_signal_error(self, signal_name: str, slot_name: str, error_msg: str):
        """记录信号槽错误"""
        self.log_ui_error('signal', f'{signal_name}->{slot_name}', error_msg)
    
    def log_style_error(self, widget_name: str, style_property: str, error_msg: str):
        """记录样式错误"""
        self.log_ui_error('style', f'{widget_name}.{style_property}', error_msg)
    
    def log_resource_error(self, resource_path: str, error_msg: str):
        """记录资源加载错误"""
        self.log_ui_error('resource', resource_path, error_msg)
    
    def log_thread_violation(self, operation: str, widget_name: str):
        """记录跨线程UI操作违规"""
        current_thread = threading.current_thread().name
        message = f"Thread violation: {operation} on Widget[{widget_name}] from thread[{current_thread}]"
        self.log_ui_error('thread', widget_name, message)
    
    def get_ui_error_stats(self) -> Dict[str, int]:
        """获取UI错误统计"""
        return self.ui_error_stats.copy()
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        if not self.performance_data['memory_usage']:
            return {}
            
        memory_values = [item['memory_mb'] for item in self.performance_data['memory_usage']]
        return {
            'avg_memory_mb': sum(memory_values) / len(memory_values),
            'max_memory_mb': max(memory_values),
            'min_memory_mb': min(memory_values),
            'total_ui_errors': sum(self.ui_error_stats.values()),
            'error_breakdown': self.ui_error_stats.copy()
        }

# 装饰器：自动记录UI操作性能
def log_ui_operation(widget_name: str = None, operation: str = None):
    """装饰器：自动记录UI操作的执行时间"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                # 尝试获取Logger实例
                if Logger._instance:
                    name = widget_name or getattr(args[0], 'objectName', lambda: 'Unknown')()
                    op = operation or func.__name__
                    Logger._instance.log_widget_operation(name, op, duration_ms)
                
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                if Logger._instance:
                    name = widget_name or getattr(args[0], 'objectName', lambda: 'Unknown')()
                    Logger._instance.log_ui_error('operation', name, f"{func.__name__} failed: {str(e)}", exc_info=True)
                raise
        return wrapper
    return decorator

# 装饰器：自动捕获UI异常
def catch_ui_exceptions(widget_name: str = None):
    """装饰器：自动捕获并记录UI相关异常"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if Logger._instance:
                    name = widget_name or getattr(args[0], 'objectName', lambda: 'Unknown')()
                    Logger._instance.log_ui_error('exception', name, f"{func.__name__}: {str(e)}", exc_info=True)
                raise
        return wrapper
    return decorator

# 快捷访问方法（可选）
def init_logging(*args, **kwargs):
    """初始化日志中间件（快捷方式）"""
    return Logger(*args, **kwargs)

def get_logger(name: str):
    """获取logger（快捷方式）"""
    return Logger.get_logger(name)