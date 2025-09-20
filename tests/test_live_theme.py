#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试实时主题切换功能
"""

import sys
import os
from PySide6.QtWidgets import (QApplication, QVBoxLayout, QWidget, QLabel, 
                              QPushButton, QHBoxLayout, QLineEdit, QTextEdit)
from PySide6.QtCore import Qt

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from components.MoreSettingsDialog import ThemeToggleSwitch
from components.QSSLoader import QSSLoader

class LiveThemeDemo(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("实时主题切换测试")
        self.setFixedSize(500, 400)
        
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel("实时主题切换测试")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)
        
        # 主题切换区域
        theme_widget = QWidget()
        theme_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
                margin: 10px;
            }
        """)
        
        theme_layout = QHBoxLayout(theme_widget)
        
        theme_info = QLabel("主题切换")
        theme_info.setStyleSheet("font-weight: bold; font-size: 16px;")
        
        self.status_label = QLabel("☀️ 亮色")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        self.theme_switch = ThemeToggleSwitch()
        
        # 连接主题切换事件
        original_theme_changed = self.theme_switch.theme_changed
        def enhanced_theme_changed():
            original_theme_changed()
            self.update_status()
        self.theme_switch.theme_changed = enhanced_theme_changed
        
        theme_layout.addWidget(theme_info)
        theme_layout.addStretch()
        theme_layout.addWidget(self.status_label)
        theme_layout.addWidget(self.theme_switch)
        
        layout.addWidget(theme_widget)
        
        # 测试各种控件
        test_label = QLabel("测试控件（观察主题变化）：")
        test_label.setStyleSheet("font-weight: bold; margin: 10px 0;")
        layout.addWidget(test_label)
        
        # 输入框
        self.test_input = QLineEdit()
        self.test_input.setPlaceholderText("这是一个测试输入框")
        layout.addWidget(self.test_input)
        
        # 文本编辑器
        self.test_text = QTextEdit()
        self.test_text.setPlaceholderText("这是一个测试文本编辑器")
        self.test_text.setMaximumHeight(100)
        layout.addWidget(self.test_text)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        test_button = QPushButton("测试按钮")
        test_button.clicked.connect(lambda: print("按钮被点击"))
        
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.close)
        
        button_layout.addWidget(test_button)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        # 说明
        info_label = QLabel("💡 切换主题开关，观察所有控件的颜色变化\n变化应该立即生效，无需重启应用")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("font-size: 12px; color: #666; margin: 15px; line-height: 1.4;")
        layout.addWidget(info_label)
        
        self.setLayout(layout)
    
    def update_status(self):
        """更新状态标签"""
        if self.theme_switch.is_dark_theme():
            self.status_label.setText("🌙 暗色")
        else:
            self.status_label.setText("☀️ 亮色")

def main():
    app = QApplication(sys.argv)
    
    # 加载初始样式
    qss_loader = QSSLoader()
    stylesheet = qss_loader.load_stylesheet("styles/fish.qss")
    app.setStyleSheet(stylesheet)
    
    # 创建测试窗口
    demo = LiveThemeDemo()
    demo.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
