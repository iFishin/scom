#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试对话框样式一致性
"""

import sys
from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, 
                              QLabel, QPushButton, QLineEdit, QTextEdit, 
                              QComboBox, QSpinBox, QGroupBox, QListWidget)
from PySide6.QtCore import Qt
from components.QSSLoader import QSSLoader

class TestDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("对话框样式测试")
        self.setModal(True)
        self.setMinimumSize(500, 400)
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 标签测试
        label1 = QLabel("这是一个普通标签")
        layout.addWidget(label1)
        
        # 输入框测试
        line_edit = QLineEdit()
        line_edit.setPlaceholderText("请输入文本")
        layout.addWidget(line_edit)
        
        # 文本编辑器测试
        text_edit = QTextEdit()
        text_edit.setPlaceholderText("这是文本编辑器")
        text_edit.setMaximumHeight(100)
        layout.addWidget(text_edit)
        
        # 下拉框测试
        combo_box = QComboBox()
        combo_box.addItems(["选项1", "选项2", "选项3"])
        layout.addWidget(combo_box)
        
        # 数字输入框测试
        spin_box = QSpinBox()
        spin_box.setMinimum(0)
        spin_box.setMaximum(100)
        spin_box.setValue(50)
        layout.addWidget(spin_box)
        
        # 分组框测试
        group_box = QGroupBox("分组框测试")
        group_layout = QVBoxLayout()
        group_label = QLabel("分组框内的标签")
        group_layout.addWidget(group_label)
        group_box.setLayout(group_layout)
        layout.addWidget(group_box)
        
        # 列表测试
        list_widget = QListWidget()
        list_widget.addItems(["项目1", "项目2", "项目3"])
        list_widget.setMaximumHeight(80)
        layout.addWidget(list_widget)
        
        # 按钮
        button_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        cancel_button = QPushButton("取消")
        cancel_button.setProperty("buttonRole", "cancel")
        
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

def main():
    app = QApplication(sys.argv)
    
    # 加载样式
    qss_loader = QSSLoader()
    stylesheet = qss_loader.load_stylesheet("styles/fish.qss")
    app.setStyleSheet(stylesheet)
    
    # 创建对话框
    dialog = TestDialog()
    dialog.exec()
    
    sys.exit(app.exit_code if hasattr(app, 'exit_code') else 0)

if __name__ == "__main__":
    main()
