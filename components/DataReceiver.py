import datetime
import time
from utils import common
from PySide6.QtCore import QThread, Signal, QMutex, QWaitCondition, QMutexLocker, QTimer
from serial import SerialTimeoutException


class DataReceiver(QThread):
    dataReceived = Signal(str)
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
        
        # 批处理相关配置
        self.batch_buffer = []
        self.batch_timeout = 0.1  # 100ms批处理超时
        self.batch_max_size = 50  # 最大批处理条目数
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
                    # 检查缓冲区状态
                    waiting_bytes = self.serial_port.in_waiting
                    
                    if waiting_bytes > 0:
                        # 一次性读取所有可用数据
                        raw_data = self.serial_port.read(min(waiting_bytes, 4096))
                        if raw_data:
                            read_time = datetime.datetime.now()
                            formatted = self.process_raw_data(raw_data, read_time)
                            if formatted:
                                self.add_to_batch(formatted)
                            
                            # 更新数据速率监控
                            self.update_data_rate_monitor(len(raw_data))
                    
                    # 检查是否需要发送批处理数据
                    self.check_and_emit_batch()
                    
                    # 智能休眠
                    sleep_ms = self.calculate_optimized_sleep_interval()
                    QThread.msleep(sleep_ms)
                    self._last_read_time = datetime.datetime.now()
            
            except Exception as e:
                self.handle_exception(e)

    def add_to_batch(self, data):
        """添加数据到批处理缓冲区"""
        self.batch_buffer.append(data)
        
        # 如果达到最大批处理大小，立即发送
        if len(self.batch_buffer) >= self.batch_max_size:
            self.emit_batch()

    def check_and_emit_batch(self):
        """检查并发送批处理数据"""
        current_time = time.time()
        
        # 如果有数据且超过批处理超时时间，发送数据
        if self.batch_buffer and (current_time - self.last_emit_time) >= self.batch_timeout:
            self.emit_batch()

    def emit_batch(self):
        """发送批处理数据"""
        if self.batch_buffer:
            # 合并所有数据为一个字符串
            combined_data = '\n'.join(self.batch_buffer)
            self.dataReceived.emit(combined_data)
            
            # 清空缓冲区并更新时间
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
        """Process raw bytes with type validation"""
        # Ensure raw_data is of type bytes
        if not isinstance(raw_data, bytes):
            raise ValueError(f"Expected raw_data to be bytes, but got {type(raw_data)}")
        
        if not raw_data:
            return ""
        
        # Calculate the number of bytes received
        byte_count = len(raw_data)
        if byte_count == 0:
            return ""
        
        # Calculate the time when the first byte was received
        block_duration = self.byte_transmission_time() * (byte_count - 1)
        start_time = read_time - datetime.timedelta(seconds=block_duration)
        
        try:
            if self.is_show_hex:
                return self.format_hex_data(raw_data, start_time)
            return self.format_text_data(raw_data, start_time)
        except Exception as e:
            print(f"[ERROR] Processing failed: {str(e)}")
            return "⚙ Data processing error"

    def format_hex_data(self, data_bytes, start_time):
        """Format HEX data with precise timestamps"""
        formatted_lines = []
        current_pos = 0
        
        # Split data by newline character
        for line in data_bytes.split(b'\n'):
            if not line:
                continue
                
            # Calculate the timestamp for the current line
            line_duration = self.byte_transmission_time() * current_pos
            line_time = start_time + datetime.timedelta(seconds=line_duration)
            
            # Calculate the number of bytes in the current line (including the newline character)
            line_length = len(line) + 1  # +1 for the split '\n'
            
            # Generate the timestamp
            ts = line_time.strftime("%Y-%m-%d_%H:%M:%S:%f")[:-3]
            formatted_lines.append(f"[{ts}]{line.decode('latin-1')}")
            
            current_pos += line_length
            
        return '\n'.join(formatted_lines)

    def format_text_data(self, data_bytes, start_time):
        """优化的文本数据格式化"""
        try:
            if not isinstance(data_bytes, bytes) or not data_bytes:
                return ""

            # 添加到持久缓冲区
            self.persistent_buffer.extend(data_bytes)
            self.last_data_time = datetime.datetime.now()
            
            complete_lines = []
            current_pos = 0
            
            # 使用更高效的行分割
            buffer_parts = self.persistent_buffer.split(b'\n')
            
            # 处理除最后一部分外的所有完整行
            for i in range(len(buffer_parts) - 1):
                line_bytes = buffer_parts[i]
                if line_bytes:  # 忽略空行
                    line_duration = self.byte_transmission_time() * current_pos
                    line_time = start_time + datetime.timedelta(seconds=line_duration)
                    
                    line_str = self.decode_line(line_bytes + b'\n')
                    formatted = self.add_timestamp(line_str, line_time)
                    complete_lines.append(formatted)
                    
                    current_pos += len(line_bytes) + 1  # +1 for newline
            
            # 最后一部分是不完整行，保留在缓冲区
            remaining_buffer = buffer_parts[-1]
            
            # 检查超时
            time_since_last = (datetime.datetime.now() - self.last_data_time).total_seconds()
            if time_since_last > self.buffer_timeout and remaining_buffer:
                line_duration = self.byte_transmission_time() * current_pos
                line_time = start_time + datetime.timedelta(seconds=line_duration)
                line_str = self.decode_line(remaining_buffer)
                complete_lines.append(self.add_timestamp(line_str, line_time))
                remaining_buffer = b''
            
            # 更新缓冲区
            self.persistent_buffer = bytearray(remaining_buffer)
            
            return '\n'.join(complete_lines) if complete_lines else ""
            
        except Exception as e:
            print(f"Format error: {str(e)}")
            return "⚙ Data format error"
    
    def decode_line(self, byte_buffer):
        """Decode byte buffer to string with error handling"""
        line = common.force_decode(bytes(byte_buffer))
        
        if self.is_show_symbol:
            return repr(line)[1:-1]
        return line.replace('\r', '').strip()

    def add_timestamp(self, content, timestamp):
        """Add timestamp prefix if enabled"""
        if not self.is_show_timeStamp:
            return content
        
        ts = timestamp.strftime("%Y-%m-%d_%H:%M:%S:%f")[:-3]
        return f"[{ts}]{content}"

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