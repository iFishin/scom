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
                
                # 先检测文件的换行符类型
                has_crlf = b'\r\n' in file_content
                has_lf = b'\n' in file_content
                
                # Step 1: 规范化文件内容（全部转换为 LF）
                # 这样避免分块时 \r\n 被分割导致处理错误
                normalized_content = file_content.replace(b'\r\n', b'\n')
                
                # Step 2: 根据原文件类型决定最终的换行符格式
                # 如果原文件是 CRLF，则转换回 CRLF；否则保持 LF
                if has_crlf:
                    normalized_content = normalized_content.replace(b'\n', b'\r\n')
                
                # Step 3: 转换为字符串并分块发送
                try:
                    file_text = normalized_content.decode('utf-8', errors='replace')
                except Exception as decode_error:
                    # 如果 UTF-8 解码失败，使用忽略错误的方式
                    file_text = normalized_content.decode('utf-8', errors='ignore')
                
                file_size = len(file_text)
                sent_chars = 0
                chunk_size = 16
                
                while sent_chars < file_size:
                    chunk = file_text[sent_chars:sent_chars + chunk_size]
                    if not chunk:
                        break
                    
                    # 发送分块内容，不添加额外的换行符
                    common.port_write(chunk, self.serial_port, ender='')
                    sent_chars += len(chunk)
                    
                    # 发送进度信号
                    self.progressUpdated.emit(int(sent_chars / file_size * 100))
        except FileNotFoundError:
            QMessageBox.warning(self, "Warning", "File not found.")
        except PermissionError:
            QMessageBox.warning(self, "Warning", "Permission denied to open the file.")