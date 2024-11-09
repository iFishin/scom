import os
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QMessageBox
from utils import common
import time

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
                print(file_size)
                sent_bytes = 0
                chunk_size = 1024
                while sent_bytes < file_size:
                    chunk = f.read(chunk_size)
                    chunk = repr(chunk).strip("'").replace("\\n", "\r\n")
                    print(chunk)
                    if not chunk:
                        break
                    common.port_write(chunk, self.serial_port, sendWithEnter=False)
                    print(f"####Command sent: {chunk}")
                    sent_bytes += len(chunk)
                    # 发送进度信号
                    self.progressUpdated.emit(int(sent_bytes / file_size * 100))
                    time.sleep(3)
        except FileNotFoundError:
            QMessageBox.warning(self, "Warning", "File not found.")
        except PermissionError:
            QMessageBox.warning(self, "Warning", "Permission denied to open the file.")