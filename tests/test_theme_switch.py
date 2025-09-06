#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试 MoreSettingsDialog 主题切换功能
"""

import sys
from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget
from components.MoreSettingsDialog import MoreSettingsDialog
from components.QSSLoader import QSSLoader

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("测试 MoreSettings 主题切换")
        self.setFixedSize(300, 200)
        
        layout = QVBoxLayout()
        
        settings_button = QPushButton("打开 More Settings")
        settings_button.clicked.connect(self.show_settings_dialog)
        layout.addWidget(settings_button)
        
        self.setLayout(layout)
        
    def show_settings_dialog(self):
        dialog = MoreSettingsDialog(self)
        dialog.exec()

def main():
    app = QApplication(sys.argv)
    
    # 加载样式
    qss_loader = QSSLoader()
    stylesheet = qss_loader.load_stylesheet("styles/fish.qss")
    app.setStyleSheet(stylesheet)
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
