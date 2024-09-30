import os
from PySide6.QtCore import *
from PySide6 import QtWidgets
from utils import common

class FileSender(QThread):
    # 定义一个进度信号
    progressUpdated = Signal(int)

    def __init__(self, file_path, serial_port):
        super().__init__()
        self.file_path = file_path
        self.serial_port = serial_port

    def run(self):
        try:
            with open(self.file_path, "r", encoding='utf-8') as f:
                file_size = os.path.getsize(self.file_path)
                sent_bytes = 0
                chunk_size = 4096
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    common.port_write(chunk, self.serial_port, False)
                    sent_bytes += len(chunk)
                    # 发送进度信号
                    self.progressUpdated.emit(int(sent_bytes / file_size * 100))
        except FileNotFoundError:
            QtWidgets.QMessageBox.warning(self, "Warning", "File not found.")
        except PermissionError:
            QtWidgets.QMessageBox.warning(self, "Warning", "Permission denied to open the file.")