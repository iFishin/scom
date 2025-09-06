#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
专门测试主应用实时主题切换的脚本
"""

import sys
import os
from PySide6.QtWidgets import (QApplication, QVBoxLayout, QWidget, QLabel, 
                              QPushButton, QHBoxLayout, QMessageBox)
from PySide6.QtCore import Qt, QTimer

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from components.MoreSettingsDialog import MoreSettingsDialog
from components.QSSLoader import QSSLoader

class MainAppThemeTest(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("主应用主题切换测试")
        self.setFixedSize(500, 300)
        
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel("主应用主题切换测试")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 15px;")
        layout.addWidget(title)
        
        # 说明
        info = QLabel("这个测试模拟主应用的情况：\n1. 样式通过 widget.setStyleSheet() 应用\n2. 测试实时主题切换是否生效")
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("font-size: 12px; margin: 10px; line-height: 1.4;")
        layout.addWidget(info)
        
        # 测试控件
        test_label = QLabel("观察这些控件的颜色变化：")
        test_label.setStyleSheet("font-weight: bold; margin: 10px 0;")
        layout.addWidget(test_label)
        
        from PySide6.QtWidgets import QLineEdit, QTextEdit, QComboBox
        
        # 输入框
        self.test_input = QLineEdit()
        self.test_input.setPlaceholderText("测试输入框")
        layout.addWidget(self.test_input)
        
        # 下拉框
        self.test_combo = QComboBox()
        self.test_combo.addItems(["选项1", "选项2", "选项3"])
        layout.addWidget(self.test_combo)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 打开More Settings对话框
        settings_button = QPushButton("打开 More Settings (测试主题切换)")
        settings_button.clicked.connect(self.open_more_settings)
        
        # 关闭按钮
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.close)
        
        button_layout.addWidget(settings_button)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        
        # 状态信息
        self.status_label = QLabel("💡 打开 More Settings，切换主题开关，观察这个窗口是否立即变色")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 11px; color: #666; margin: 15px; line-height: 1.3;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        # 定时器用于检测样式变化
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_style_change)
        self.timer.start(1000)  # 每秒检查一次
        self.last_bg_color = None
        
    def open_more_settings(self):
        """打开More Settings对话框"""
        dialog = MoreSettingsDialog(self)
        dialog.exec()
    
    def check_style_change(self):
        """检测样式变化"""
        try:
            # 获取当前的背景色
            current_bg = self.palette().window().color().name()
            if self.last_bg_color is None:
                self.last_bg_color = current_bg
            elif self.last_bg_color != current_bg:
                self.status_label.setText(f"✅ 检测到样式变化！背景色从 {self.last_bg_color} 变为 {current_bg}")
                self.last_bg_color = current_bg
                # 3秒后恢复原文字
                QTimer.singleShot(3000, lambda: self.status_label.setText("💡 打开 More Settings，切换主题开关，观察这个窗口是否立即变色"))
        except Exception:
            pass

def main():
    app = QApplication(sys.argv)
    
    # 模拟主应用的样式加载方式
    qss_loader = QSSLoader()
    stylesheet = qss_loader.load_stylesheet("styles/fish.qss")
    
    # 创建主窗口
    window = MainAppThemeTest()
    
    # 重要：这里使用widget.setStyleSheet()而不是app.setStyleSheet()
    # 模拟主应用的样式应用方式
    window.setStyleSheet(stylesheet)
    
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
