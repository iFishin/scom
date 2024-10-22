from PySide6.QtCore import QThread, Signal, QMutex, QWaitCondition, QMutexLocker
from serial.tools import list_ports

class PortUpdater(QThread):
    portUpdated = Signal(list)

    def __init__(self):
        super().__init__()
        self.is_paused = False
        self.mutex = QMutex()
        self.cond = QWaitCondition()

    def pause_thread(self):
        if not self.is_paused:
            with QMutexLocker(self.mutex):
                self.is_paused = True

    def resume_thread(self):
        with QMutexLocker(self.mutex):
            if self.is_paused:
                self.is_paused = False
                self.cond.wakeOne()

    def run(self):
        while True:
            with QMutexLocker(self.mutex):
                if self.is_paused:
                    self.cond.wait(self.mutex)
            # 互斥锁范围之外进行线程操作
            if not self.is_paused:
                ports = [port.device for port in list_ports.comports()]
                self.portUpdated.emit(ports)
                QThread.sleep(2)
