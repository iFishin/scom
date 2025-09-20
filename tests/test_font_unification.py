#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试字体统一效果
"""

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, 
    QCheckBox, QRadioButton, QGroupBox, QListWidget, QTableWidget,
    QTabWidget, QProgressBar, QSlider, QTableWidgetItem
)
from PySide6.QtCore import Qt
from components.QSSLoader import QSSLoader


class FontTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("字体统一效果测试 - Font Unification Test")
        self.setGeometry(100, 100, 800, 700)
        
        # 应用统一后的样式
        qss_loader = QSSLoader()
        stylesheet = qss_loader.load_stylesheet("styles/fish.qss")
        self.setStyleSheet(stylesheet)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 标题
        title = QLabel("字体统一效果测试")
        title.setProperty("labelStyle", "title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 基本控件测试
        self.create_basic_controls_section(layout)
        
        # 输入控件测试
        self.create_input_controls_section(layout)
        
        # 复杂控件测试
        self.create_complex_controls_section(layout)
        
        # 样式效果测试
        self.create_style_effects_section(layout)
    
    def create_basic_controls_section(self, layout):
        """基本控件测试"""
        group = QGroupBox("基本控件 - Basic Controls")
        group_layout = QVBoxLayout(group)
        
        # 标签
        label = QLabel("标准标签 (QLabel) - Standard Label")
        group_layout.addWidget(label)
        
        subtitle = QLabel("副标题标签 (Subtitle)")
        subtitle.setProperty("labelStyle", "subtitle")
        group_layout.addWidget(subtitle)
        
        caption = QLabel("说明文字 (Caption)")
        caption.setProperty("labelStyle", "caption")
        group_layout.addWidget(caption)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn1 = QPushButton("标准按钮")
        btn2 = QPushButton("危险按钮")
        btn2.setProperty("buttonStyle", "danger")
        btn3 = QPushButton("次要按钮")
        btn3.setProperty("buttonStyle", "secondary")
        
        btn_layout.addWidget(btn1)
        btn_layout.addWidget(btn2)
        btn_layout.addWidget(btn3)
        group_layout.addLayout(btn_layout)
        
        # 复选框和单选按钮
        checkbox_layout = QHBoxLayout()
        checkbox1 = QCheckBox("复选框选项 1")
        checkbox2 = QCheckBox("复选框选项 2")
        radio1 = QRadioButton("单选按钮选项 1")
        radio2 = QRadioButton("单选按钮选项 2")
        
        checkbox_layout.addWidget(checkbox1)
        checkbox_layout.addWidget(checkbox2)
        checkbox_layout.addWidget(radio1)
        checkbox_layout.addWidget(radio2)
        group_layout.addLayout(checkbox_layout)
        
        layout.addWidget(group)
    
    def create_input_controls_section(self, layout):
        """输入控件测试"""
        group = QGroupBox("输入控件 - Input Controls")
        group_layout = QVBoxLayout(group)
        
        # 单行输入
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("单行输入:"))
        line_edit = QLineEdit("这是一个测试文本")
        input_layout.addWidget(line_edit)
        group_layout.addLayout(input_layout)
        
        # 下拉框
        combo_layout = QHBoxLayout()
        combo_layout.addWidget(QLabel("下拉框:"))
        combo = QComboBox()
        combo.addItems(["选项 1", "选项 2", "选项 3", "Microsoft YaHei 字体测试"])
        combo_layout.addWidget(combo)
        group_layout.addLayout(combo_layout)
        
        # 多行文本
        text_edit = QTextEdit()
        text_edit.setPlainText("""这是多行文本编辑器测试
        
字体应该统一为: Microsoft YaHei, SimSun, Segoe UI, Roboto, sans-serif
字体大小应该为: 14px (UI_FONT_SIZE_MEDIUM)

测试中文显示效果
测试英文显示效果 - English Font Test
测试数字显示效果 - 1234567890""")
        text_edit.setMaximumHeight(120)
        group_layout.addWidget(text_edit)
        
        layout.addWidget(group)
    
    def create_complex_controls_section(self, layout):
        """复杂控件测试"""
        group = QGroupBox("复杂控件 - Complex Controls")
        group_layout = QVBoxLayout(group)
        
        # 选项卡
        tab_widget = QTabWidget()
        
        # 列表页面
        list_widget = QListWidget()
        list_widget.addItems([
            "列表项目 1 - List Item 1",
            "列表项目 2 - List Item 2", 
            "字体测试项目 - Font Test Item",
            "Microsoft YaHei 显示测试"
        ])
        tab_widget.addTab(list_widget, "列表控件")
        
        # 表格页面
        table = QTableWidget(3, 3)
        table.setHorizontalHeaderLabels(["列 1", "列 2", "列 3"])
        for i in range(3):
            for j in range(3):
                table.setItem(i, j, QTableWidgetItem(f"单元格 {i+1},{j+1}"))
        tab_widget.addTab(table, "表格控件")
        
        group_layout.addWidget(tab_widget)
        
        layout.addWidget(group)
    
    def create_style_effects_section(self, layout):
        """样式效果测试"""
        group = QGroupBox("样式效果 - Style Effects")
        group_layout = QVBoxLayout(group)
        
        # 进度条
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("进度条:"))
        progress = QProgressBar()
        progress.setValue(65)
        progress_layout.addWidget(progress)
        group_layout.addLayout(progress_layout)
        
        # 滑块
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(QLabel("滑块:"))
        slider = QSlider(Qt.Horizontal)
        slider.setValue(50)
        slider_layout.addWidget(slider)
        group_layout.addLayout(slider_layout)
        
        # 状态标签
        status_layout = QHBoxLayout()
        success_label = QLabel("成功状态")
        success_label.setProperty("labelStyle", "success")
        
        danger_label = QLabel("危险状态")
        danger_label.setProperty("labelStyle", "danger")
        
        warning_label = QLabel("警告状态")
        warning_label.setProperty("labelStyle", "warning")
        
        info_label = QLabel("信息状态")
        info_label.setProperty("labelStyle", "info")
        
        status_layout.addWidget(success_label)
        status_layout.addWidget(danger_label)
        status_layout.addWidget(warning_label)
        status_layout.addWidget(info_label)
        group_layout.addLayout(status_layout)
        
        layout.addWidget(group)


def main():
    app = QApplication(sys.argv)
    
    window = FontTestWindow()
    window.show()
    
    # 输出字体信息
    print("📝 Font Unification Test Window")
    print("=" * 40)
    print("✅ Applied unified font styles")
    print("🎨 UI Font: Microsoft YaHei, SimSun, Segoe UI, Roboto")
    print("💻 Code Font: JetBrains Mono, Consolas, Courier New")
    print("📏 Standard sizes: 11px, 13px, 14px, 15px, 16px")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
