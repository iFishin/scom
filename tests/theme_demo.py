#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主题切换功能演示
"""

import sys
import os
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from components.MoreSettingsDialog import ThemeToggleSwitch
from components.QSSLoader import QSSLoader

class ThemeDemo(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("主题切换演示")
        self.setFixedSize(400, 200)
        
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel("SCOM 主题切换演示")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)
        
        # 主题切换区域
        theme_layout = QHBoxLayout()
        
        theme_label = QLabel("选择主题：")
        theme_label.setStyleSheet("font-size: 14px;")
        
        self.status_label = QLabel("☀️ 亮色主题")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        self.theme_switch = ThemeToggleSwitch()
        
        # 连接主题切换事件
        original_theme_changed = self.theme_switch.theme_changed
        def enhanced_theme_changed():
            original_theme_changed()
            self.update_status()
        self.theme_switch.theme_changed = enhanced_theme_changed
        
        theme_layout.addWidget(theme_label)
        theme_layout.addStretch()
        theme_layout.addWidget(self.status_label)
        theme_layout.addWidget(self.theme_switch)
        
        layout.addLayout(theme_layout)
        
        # 说明文字
        description = QLabel("点击开关切换主题，变更将立即应用到样式文件")
        description.setAlignment(Qt.AlignCenter)
        description.setStyleSheet("font-size: 12px; color: #666; margin: 20px;")
        layout.addWidget(description)
        
        # 关闭按钮
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.close)
        close_button.setFixedWidth(100)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def update_status(self):
        """更新状态标签"""
        if self.theme_switch.is_dark_theme():
            self.status_label.setText("🌙 暗色主题")
        else:
            self.status_label.setText("☀️ 亮色主题")

def main():
    app = QApplication(sys.argv)
    
    # 加载样式
    qss_loader = QSSLoader()
    stylesheet = qss_loader.load_stylesheet("styles/fish.qss")
    app.setStyleSheet(stylesheet)
    
    # 创建演示窗口
    demo = ThemeDemo()
    demo.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
