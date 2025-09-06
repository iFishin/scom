#!/usr/bin/env python3
"""
测试状态标签样式优化
验证QSS样式是否正确应用
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PySide6.QtCore import Qt

class StatusLabelTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Status Label Style Test")
        self.setGeometry(100, 100, 400, 300)
        
        # 创建中央widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 创建状态标签
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setObjectName("status_label")
        layout.addWidget(self.status_label)
        
        # 创建测试按钮
        buttons_data = [
            ("Connected", "#00a86b"),
            ("Open", "#198754"),
            ("Disconnected", "#6c757d"),
            ("Failed", "#dc3545"),
            ("Warning", "#ffc107"),
            ("Info", "#17a2b8")
        ]
        
        for text, color in buttons_data:
            btn = QPushButton(f"Set {text}")
            btn.clicked.connect(lambda checked, t=text, c=color: self.set_status_label(t, c))
            layout.addWidget(btn)
        
        # 加载样式表
        self.load_stylesheet()
    
    def load_stylesheet(self):
        """加载优化后的样式表"""
        try:
            qss_path = os.path.join(os.path.dirname(__file__), "..", "styles", "fish_optimized.qss")
            with open(qss_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
            print("✅ 样式表加载成功")
        except FileNotFoundError:
            print("❌ 样式表文件未找到")
        except Exception as e:
            print(f"❌ 加载样式表时出错: {e}")
    
    def set_status_label(self, text, color):
        """设置状态标签 - 使用QSS样式而不是内联样式"""
        self.status_label.setText(text)
        
        # 根据颜色设置状态属性，使用QSS中定义的样式
        color_to_status = {
            "#00a86b": "connected",   # 绿色 - 已连接
            "#198754": "connected",   # 另一种绿色 - 已连接
            "#6c757d": "disconnected", # 灰色 - 已断开
            "#dc3545": "error",       # 红色 - 错误状态
            "#ffc107": "warning",     # 黄色 - 警告状态
            "#17a2b8": "info"         # 青色 - 信息状态
        }
        
        status = color_to_status.get(color, "disconnected")
        self.status_label.setProperty("status", status)
        
        # 强制刷新样式
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        
        print(f"状态已设置: {text} ({color}) -> {status}")

def main():
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    window = StatusLabelTest()
    window.show()
    
    print("🧪 状态标签样式测试程序")
    print("点击按钮测试不同状态的样式效果")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
