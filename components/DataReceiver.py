import datetime
from utils import common
from PySide6.QtCore import QThread, Signal, QMutex, QWaitCondition, QMutexLocker


class DataReceiver(QThread):
    dataReceived = Signal(str)
    exceptionOccurred = Signal(str)

    def __init__(self, serial_port):
        super().__init__()
        self.serial_port = serial_port
        self.is_paused = False
        self.is_stopped = False
        self.is_show_symbol = False
        self.is_show_timeStamp = True
        self.is_show_hex = False
        self.mutex = QMutex()
        self.cond = QWaitCondition()

    def pause_thread(self):
        with QMutexLocker(self.mutex):
            self.is_paused = True

    def resume_thread(self):
        with QMutexLocker(self.mutex):
            self.is_paused = False
            self.cond.wakeOne()
    
    def stop_thread(self):
        with QMutexLocker(self.mutex):
            self.is_stopped = True
            self.cond.wakeOne()

    def run(self):
        while not self.is_stopped:
            with QMutexLocker(self.mutex):
                if self.is_paused:
                    self.cond.wait(self.mutex)
            try:
                if not self.is_paused:
                    response = self.read_data()
                    if response:
                        formatted_data = self.format_data(response)
                        self.dataReceived.emit(formatted_data)
                    QThread.msleep(100)
            except UnicodeDecodeError as e:
                print(f"Error decoding serial data: {e}")
                self.dataReceived.emit("⚙ Error decoding serial data")
            except Exception as e:
                print(f"Error occurred: {e}")
                self.exceptionOccurred.emit(str(e))

    def read_data(self):
        if self.is_show_symbol:
            response = common.port_read(self.serial_port)
            if response:
                response = repr(response)[1:-1].replace("\\r\\n", "\\r\\n\r\n")
        elif self.is_show_hex:
            response = common.port_read_hex(self.serial_port)
        else:
            response = common.port_read(self.serial_port)
            if response:
                response = repr(response)[1:-1].replace("\\r", "").replace("\\n", "\n")
        return response.strip() if response else None

    def format_data(self, response):
        if self.is_show_timeStamp:
            now_time = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S:%f")[:-3]
            now_time = "[" + now_time + "]"
            formatted_lines = [f"{now_time}{item}" for item in response.split("\n")]
        else:
            formatted_lines = [item for item in response.split("\n")]
        return "\n".join(formatted_lines)
