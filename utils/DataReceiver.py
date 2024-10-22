import datetime
from utils import common
from PySide6.QtCore import QThread, Signal, QMutex, QWaitCondition, QMutexLocker


class DataReceiver(QThread):
    dataReceived = Signal(str)
    exceptionOccurred = Signal(str)

    def __init__(self, serial_port):
        super().__init__()
        self.serial_port = serial_port
        self.is_paused = bool(0)
        self.is_show_symbol = bool(0)
        self.is_show_timeStamp = bool(1)
        self.mutex = QMutex()
        self.cond = QWaitCondition()

    def pause_thread(self):
        if not self.is_paused:
            with QMutexLocker(self.mutex):
                self.is_paused = True
    
    def resume_thread(self):
        if self.is_paused:
            with QMutexLocker(self.mutex):
                self.is_paused = False
                self.cond.wakeOne()
                
    def run(self):
        while True:
            with QMutexLocker(self.mutex):
                if self.is_paused:
                    self.cond.wait(self.mutex)
            # 互斥范围之外进行线程操作
            try:
                if not self.is_paused:
                    if self.is_show_symbol:
                        response = common.port_read_until(self.serial_port, is_show_symbol=self.is_show_symbol)
                    else:
                        response = common.port_readline(self.serial_port)
                        if response == "":
                            continue
                    if self.is_show_timeStamp:
                        now_time = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S:%f")[:-3]
                        now_time = "[" + now_time + "]"
                        response = response.strip()
                        formatted_lines = [f"{now_time}{item}" for item in response.split("\n")]
                    else:
                        formatted_lines = [item for item in response.split("\n")]
                    combined_data = "\n".join(formatted_lines)
                    self.dataReceived.emit(combined_data)
                    QThread.sleep(0.2)
            except UnicodeDecodeError as e:
                print(f"Error decoding serial data: {e}")
                self.dataReceived.emit("⚙ Error decoding serial data")
            except Exception as e:
                print(f"Error occurred: {e}")
                self.exceptionOccurred.emit(e)
