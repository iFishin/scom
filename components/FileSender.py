import os
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QMessageBox
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
            with open(self.file_path, "rb") as f:
                file_content = f.read()
                # 判断文件编码类型
                is_crlf = b'\r\n' in file_content
                is_lf = b'\n' in file_content and not is_crlf
                file_size = len(file_content)
                sent_bytes = 0
                chunk_size = 16
                while sent_bytes < file_size:
                    chunk = file_content[sent_bytes:sent_bytes + chunk_size]
                    if not chunk:
                        break
                    if is_crlf:
                        formatted_chunk = chunk.replace(b'\r\n', b'\n').decode('utf-8')
                        formatted_chunk = formatted_chunk.replace('\n', '\r\n')
                    elif is_lf:
                        formatted_chunk = chunk.decode('utf-8')
                    else:
                        formatted_chunk = chunk.decode('utf-8')
                    common.port_write(formatted_chunk, self.serial_port, endWithEnter=False)
                    sent_bytes += len(chunk)
                    # 发送进度信号
                    self.progressUpdated.emit(int(sent_bytes / file_size * 100))
        except FileNotFoundError:
            QMessageBox.warning(self, "Warning", "File not found.")
        except PermissionError:
            QMessageBox.warning(self, "Warning", "Permission denied to open the file.")