import sys
import os
import unittest

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from middileware.Logger import Logger, init_logging, log_ui_operation, catch_ui_exceptions

class TestLogger(unittest.TestCase):
    
    def setUp(self):
        """测试前的准备工作"""
        # 清理之前的实例
        Logger._instance = None
        
    def test_init_logging(self):
        """测试日志初始化"""
        logger = init_logging(app_name="TestApp")
        self.assertIsNotNone(logger)
        self.assertIsInstance(logger, Logger)

    def test_logger_singleton(self):
        """测试单例模式"""
        logger1 = Logger(app_name="TestApp1")
        logger2 = Logger(app_name="TestApp2")
        self.assertIs(logger1, logger2)

    def test_get_logger(self):
        """测试获取组件logger"""
        # 先初始化主logger
        main_logger = Logger(app_name="TestApp")
        
        # 获取组件logger
        component_logger = Logger.get_logger("TestComponent")
        self.assertIsNotNone(component_logger)

    def test_ui_error_logging(self):
        """测试UI错误记录"""
        logger = Logger(app_name="TestApp", enable_ui_monitoring=True)
        
        # 记录各种UI错误
        logger.log_ui_error("widget", "test_button", "按钮点击失败")
        logger.log_signal_error("clicked", "on_click", "槽函数异常")
        logger.log_style_error("main_window", "background", "样式加载失败")
        logger.log_resource_error("icon.png", "图标文件未找到")
        logger.log_thread_violation("setText", "label")
        
        # 检查错误统计
        stats = logger.get_ui_error_stats()
        self.assertGreater(stats.get('widget_errors', 0), 0)
        self.assertGreater(stats.get('signal_errors', 0), 0)

    def test_performance_monitoring(self):
        """测试性能监控"""
        logger = Logger(app_name="TestApp", enable_ui_monitoring=True)
        
        # 记录UI操作
        logger.log_widget_operation("test_widget", "click", 25.5)
        
        # 获取性能摘要（可能为空，因为监控需要时间）
        summary = logger.get_performance_summary()
        self.assertIsInstance(summary, dict)

    def test_decorators(self):
        """测试装饰器功能"""
        # 初始化logger
        logger = Logger(app_name="TestApp")
        
        @log_ui_operation(widget_name="test_widget", operation="test_op")
        def test_function():
            return "success"
        
        @catch_ui_exceptions(widget_name="test_widget")
        def error_function():
            raise ValueError("测试异常")
        
        # 测试正常函数
        result = test_function()
        self.assertEqual(result, "success")
        
        # 测试异常捕获
        with self.assertRaises(ValueError):
            error_function()

def run_basic_tests():
    """运行基础测试"""
    print("开始Logger测试...")
    
    # 测试1: 基础初始化
    try:
        logger = init_logging(app_name="BasicTest")
        print("✓ 基础初始化测试通过")
    except Exception as e:
        print(f"✗ 基础初始化测试失败: {e}")
    
    # 测试2: UI错误记录
    try:
        logger.log_ui_error("widget", "test_button", "测试错误")
        logger.log_signal_error("clicked", "slot", "信号错误")
        print("✓ UI错误记录测试通过")
    except Exception as e:
        print(f"✗ UI错误记录测试失败: {e}")
    
    # 测试3: 获取统计信息
    try:
        stats = logger.get_ui_error_stats()
        summary = logger.get_performance_summary()
        print(f"✓ 统计信息获取测试通过 - 错误统计: {stats}")
    except Exception as e:
        print(f"✗ 统计信息获取测试失败: {e}")

if __name__ == "__main__":
    # 运行基础测试
    run_basic_tests()
    
    print("\n" + "="*50)
    print("运行完整单元测试...")
    
    # 运行单元测试
    unittest.main(verbosity=2)