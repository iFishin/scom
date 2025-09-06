"""
Logger使用示例 - 专为PySide6应用优化的日志使用方法
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout
from PySide6.QtCore import Signal
from middileware.Logger import Logger, log_ui_operation, catch_ui_exceptions

class ExampleWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
        # 初始化Logger
        self.logger = Logger(
            app_name="ExampleApp",
            log_dir="logs",
            enable_ui_monitoring=True
        )
        
        # 获取组件专用logger
        self.ui_logger = Logger.get_logger("UI_Component")
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 创建按钮
        self.test_button = QPushButton("测试按钮")
        self.test_button.setObjectName("test_button")
        self.test_button.clicked.connect(self.on_button_click)
        
        self.error_button = QPushButton("触发错误")
        self.error_button.setObjectName("error_button")
        self.error_button.clicked.connect(self.trigger_error)
        
        layout.addWidget(self.test_button)
        layout.addWidget(self.error_button)
        self.setLayout(layout)
    
    @log_ui_operation(operation="button_click")
    def on_button_click(self):
        """使用装饰器自动记录操作性能"""
        self.ui_logger.info("按钮被点击了")
        
        # 手动记录UI操作
        self.logger.log_widget_operation("test_button", "click", 15.5)
    
    @catch_ui_exceptions()
    def trigger_error(self):
        """使用装饰器自动捕获异常"""
        # 故意触发一个错误
        nonexistent_widget = None
        nonexistent_widget.setText("这会引发异常")
    
    def demonstrate_logging_methods(self):
        """演示各种日志记录方法"""
        
        # 1. 记录UI错误
        self.logger.log_ui_error(
            error_type="widget",
            widget_name="test_input",
            error_msg="输入验证失败"
        )
        
        # 2. 记录信号槽错误
        self.logger.log_signal_error(
            signal_name="textChanged",
            slot_name="validate_input",
            error_msg="槽函数执行失败"
        )
        
        # 3. 记录样式错误
        self.logger.log_style_error(
            widget_name="main_window",
            style_property="background-color",
            error_msg="无效的颜色值"
        )
        
        # 4. 记录资源错误
        self.logger.log_resource_error(
            resource_path="icons/missing_icon.png",
            error_msg="图标文件未找到"
        )
        
        # 5. 记录线程违规
        self.logger.log_thread_violation(
            operation="setText",
            widget_name="status_label"
        )
        
        # 6. 获取错误统计
        stats = self.logger.get_ui_error_stats()
        print("UI错误统计:", stats)
        
        # 7. 获取性能摘要
        perf_summary = self.logger.get_performance_summary()
        print("性能摘要:", perf_summary)

def main():
    app = QApplication(sys.argv)
    
    widget = ExampleWidget()
    widget.show()
    
    # 演示日志记录方法
    widget.demonstrate_logging_methods()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
