#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试集成后的QSSLoader主题切换功能
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from components.QSSLoader import QSSLoader


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QSSLoader集成测试")
        self.setGeometry(100, 100, 400, 300)
        
        # 创建QSSLoader实例
        self.qss_loader = QSSLoader()
        
        # 中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 状态标签
        self.status_label = QLabel("QSSLoader集成测试")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(self.status_label)
        
        # 功能测试标签
        if self.qss_loader.is_style_manager_available():
            info_text = "✅ 样式管理器已成功集成到QSSLoader"
        else:
            info_text = "❌ 样式管理器集成失败"
        
        info_label = QLabel(info_text)
        info_label.setStyleSheet("font-size: 12px; padding: 5px;")
        layout.addWidget(info_label)
        
        # 暗色主题按钮
        dark_btn = QPushButton("应用暗色主题")
        dark_btn.clicked.connect(self.apply_dark_theme)
        layout.addWidget(dark_btn)
        
        # 亮色主题按钮
        light_btn = QPushButton("应用亮色主题")
        light_btn.clicked.connect(self.apply_light_theme)
        layout.addWidget(light_btn)
        
        # 重新加载样式按钮
        reload_btn = QPushButton("重新加载样式")
        reload_btn.clicked.connect(self.reload_styles)
        layout.addWidget(reload_btn)
        
        # 应用初始样式
        self.load_initial_style()
    
    def load_initial_style(self):
        """加载初始样式"""
        try:
            stylesheet = self.qss_loader.load_stylesheet("styles/fish.qss")
            self.setStyleSheet(stylesheet)
            self.status_label.setText("✅ 初始样式加载成功")
        except Exception as e:
            self.status_label.setText(f"❌ 初始样式加载失败: {e}")
    
    def apply_dark_theme(self):
        """应用暗色主题"""
        if self.qss_loader.is_style_manager_available():
            success = self.qss_loader.apply_dark_theme(create_backup=False)
            if success:
                self.reload_styles()
                self.status_label.setText("🌙 暗色主题已应用")
            else:
                self.status_label.setText("❌ 暗色主题应用失败")
        else:
            self.status_label.setText("❌ 样式管理器不可用")
    
    def apply_light_theme(self):
        """应用亮色主题"""
        if self.qss_loader.is_style_manager_available():
            success = self.qss_loader.apply_light_theme(create_backup=False)
            if success:
                self.reload_styles()
                self.status_label.setText("☀️ 亮色主题已应用")
            else:
                self.status_label.setText("❌ 亮色主题应用失败")
        else:
            self.status_label.setText("❌ 样式管理器不可用")
    
    def reload_styles(self):
        """重新加载样式"""
        try:
            stylesheet = self.qss_loader.load_stylesheet("styles/fish.qss")
            QApplication.instance().setStyleSheet(stylesheet)
            self.repaint()
            print("Styles reloaded successfully")
        except Exception as e:
            print(f"Failed to reload styles: {e}")


def main():
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
