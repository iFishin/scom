import datetime
import time
from utils import common
from PySide6.QtCore import QThread, Signal, QMutex, QWaitCondition, QMutexLocker, QTimer
from serial import SerialTimeoutException


class DataReceiver(QThread):
    dataReceived = Signal(bytes)
    exceptionOccurred = Signal(str)

    def __init__(self, serial_port):
        super().__init__()
        self._last_data_size = 0
        self._curr_data_size = 0
        self.serial_port = serial_port
        self.baud_rate = self.serial_port.baudrate
        self.is_paused = False
        self.is_stopped = False
        self.is_show_symbol = False
        self.is_show_timeStamp = True
        self.is_show_hex = False
        self.is_new_data_written = False
        self.mutex = QMutex()
        self.cond = QWaitCondition()
        self._last_read_time = datetime.datetime.now()
        
        # 批处理相关配置 - 调整为更实时的处理
        self.batch_buffer = []
        self.batch_timeout = 0.02  # 减少到20ms批处理超时，提高实时性
        self.batch_max_size = 30   # 减少批处理最大条目数，更频繁地发送
        self.last_emit_time = time.time()
        
        # 持久化缓冲区
        self.persistent_buffer = bytearray()
        self.last_data_time = datetime.datetime.now()
        self.buffer_timeout = 0.05  # 50毫秒超时
        
        # 性能监控
        self.data_rate_monitor = {
            'last_time': time.time(),
            'data_count': 0,
            'bytes_per_second': 0
        }

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
            self.cond.wakeAll()

    def run(self):
        while not self.is_stopped:
            with QMutexLocker(self.mutex):
                if self.is_paused:
                    self.cond.wait(self.mutex)

            if self.is_new_data_written:
                with QMutexLocker(self.mutex):
                    self.is_new_data_written = False
                    self.cond.wakeAll()
                self._last_read_time = datetime.datetime.now()

            try:
                if not self.is_paused and self.serial_port.is_open:
                    waiting_bytes = self.serial_port.in_waiting
                    if waiting_bytes > 0:
                        # 分批读取数据，避免单次读取过多造成阻塞
                        max_read_size = min(waiting_bytes, 2048)  # 减少到2048，更频繁地发送数据
                        raw_data = self.serial_port.read(max_read_size)
                        if raw_data:
                            self.add_to_batch(raw_data)
                            self.update_data_rate_monitor(len(raw_data))
                            
                            # 如果还有数据等待，立即处理而不是等待下次循环
                            if self.serial_port.in_waiting > 0:
                                continue  # 继续读取剩余数据
                                
                    self.check_and_emit_batch()
                    sleep_ms = self.calculate_optimized_sleep_interval()
                    QThread.msleep(sleep_ms)
                    self._last_read_time = datetime.datetime.now()
            except Exception as e:
                self.handle_exception(e)

    def add_to_batch(self, data_bytes):
        """添加原始bytes到批处理缓冲区"""
        if not isinstance(data_bytes, bytes):
            raise ValueError("DataReceiver 只应接收 bytes 类型数据")
        self.batch_buffer.append(data_bytes)
        if len(self.batch_buffer) >= self.batch_max_size:
            self.emit_batch()

    def check_and_emit_batch(self):
        """检查并发送批处理数据"""
        current_time = time.time()
        
        # 如果有数据且超过批处理超时时间，发送数据
        if self.batch_buffer and (current_time - self.last_emit_time) >= self.batch_timeout:
            self.emit_batch()

    def emit_batch(self):
        """发送批处理数据（原始bytes输出）"""
        if self.batch_buffer:
            combined_data = b''.join(self.batch_buffer)
            self.dataReceived.emit(combined_data)
            self.batch_buffer.clear()
            self.last_emit_time = time.time()

    def update_data_rate_monitor(self, bytes_received):
        """更新数据速率监控"""
        current_time = time.time()
        self.data_rate_monitor['data_count'] += bytes_received
        
        # 每秒更新一次速率统计
        time_diff = current_time - self.data_rate_monitor['last_time']
        if time_diff >= 1.0:
            self.data_rate_monitor['bytes_per_second'] = self.data_rate_monitor['data_count'] / time_diff
            self.data_rate_monitor['data_count'] = 0
            self.data_rate_monitor['last_time'] = current_time

    def byte_transmission_time(self) -> float:
        """计算单个字节的传输时间（秒）"""
        bits_per_byte = 10  # 1起始 + 8数据 + 1停止
        return bits_per_byte / self.baud_rate

    def process_raw_data(self, raw_data, read_time):
        """兼容旧接口，直接返回bytes，后续不再使用"""
        if not isinstance(raw_data, bytes):
            raise ValueError(f"Expected raw_data to be bytes, but got {type(raw_data)}")
        return raw_data

    # 下面的格式化和解码方法已不再由DataReceiver负责，全部交由UI层处理
    # def format_hex_data(self, ...):
    # def format_text_data(self, ...):
    # def decode_line(self, ...):
    # def add_timestamp(self, ...):

    def calculate_optimized_sleep_interval(self):
        """优化的休眠间隔计算"""
        base_interval = 20  # 基础间隔(ms)
        min_interval = 5    # 最小间隔(ms)
        
        # 根据缓冲区状态调整
        if self.serial_port.is_open:
            waiting_bytes = self.serial_port.in_waiting
            if waiting_bytes > 0:
                return min_interval
            
            # 根据数据速率调整
            bps = self.data_rate_monitor['bytes_per_second']
            if bps > 1000:  # 高速数据流
                return min_interval
            elif bps > 100:  # 中速数据流
                return base_interval // 2
        
        return base_interval

    def handle_exception(self, error):
        """Centralized exception handling"""
        error_msg = str(error)
        # Handle exceptions based on type
        if isinstance(error, SerialTimeoutException):
            self.exceptionOccurred.emit("Read timeout occurred")
        elif "closed" in error_msg.lower():
            self.exceptionOccurred.emit("Serial port closed")
            if self.serial_port.is_open:
                self.serial_port.close()
        else:
            self.exceptionOccurred.emit(f"Error: {error_msg}")
            # Close the port only for critical errors
            if "critical" in error_msg.lower():
                self.serial_port.close()