#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试更新检测对话框
"""

from components.SafeUpdateChecker import SafeUpdateDialog
import sys
from PySide6.QtWidgets import QApplication

def main():
    app = QApplication(sys.argv)
    dialog = SafeUpdateDialog()
    dialog.show()
    
    print('更新对话框已打开，现在你可以测试手动检查功能')
    print('点击"手动检查"按钮来测试更新检测')
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
