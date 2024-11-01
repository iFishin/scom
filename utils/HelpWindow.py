import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QTextEdit
from PySide6.QtCore import QFile, Qt

class HelpWindow(QMainWindow):
    def __init__(self, txt_file_path):
        super().__init__()
        self.setWindowTitle("Help")
        self.setGeometry(100, 100, 800, 600)

        # 创建一个 QTextEdit 用于显示 TXT 内容
        self.text_edit = QTextEdit()
        self.setCentralWidget(self.text_edit)

        # 读取本地 TXT 文件并显示内容
        if os.path.exists(txt_file_path):
            with open(txt_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.text_edit.setPlainText(content)
        else:
            self.text_edit.setText("TXT file not found.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    txt_file_path = "help.txt"
    help_window = HelpWindow(txt_file_path)
    help_window.show()
    sys.exit(app.exec())