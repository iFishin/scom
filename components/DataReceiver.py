import datetime
from utils import common
from PySide6.QtCore import QThread, Signal, QMutex, QWaitCondition, QMutexLocker
from serial import SerialTimeoutException


class DataReceiver(QThread):
    dataReceived = Signal(str)
    exceptionOccurred = Signal(str)

    def __init__(self, serial_port):
        super().__init__()
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
                    raw_data = self.read_raw_data()
                    read_time = datetime.datetime.now()
                    if raw_data:
                        formatted = self.process_raw_data(raw_data, read_time)
                        self.dataReceived.emit(formatted)
                    
                    # Dynamic sleep based on data transmission time
                    sleep_ms = self.calculate_sleep_interval()
                    QThread.msleep(sleep_ms)
                    self._last_read_time = read_time
            
            except Exception as e:
                self.handle_exception(e)

    def read_raw_data(self):
        """Safely read raw bytes from serial port with type conversion"""
        if not self.serial_port.is_open:
            raise RuntimeError("Serial port is not open")
        
        try:
            # Force returning data as bytes
            if self.is_show_hex:
                raw = common.port_read_hex(self.serial_port)
            else:
                # Ensure port_read returns bytes
                raw = common.port_read(self.serial_port)
            
            # Perform real-time reading based on hardware buffer
            if self.serial_port.in_waiting > 32:  # Read immediately if buffer exceeds 32 bytes
                return self.serial_port.read_all()

            # Type conversion protection
            if isinstance(raw, str):
                return raw.encode('utf-8')
            return raw or b''
        
        except Exception as e:
            self.serial_port.close()
            raise

    def process_raw_data(self, raw_data, read_time):
        """Process raw bytes with type validation"""
        # Ensure raw_data is of type bytes
        if not isinstance(raw_data, bytes):
            raise ValueError(f"Expected raw_data to be bytes, but got {type(raw_data)}")
        
        if not raw_data:
            return ""
        
        try:
            if self.is_show_hex:
                return self.format_hex_data(raw_data, read_time)
            return self.format_text_data(raw_data, read_time)
        except Exception as e:
            print(f"[ERROR] Processing failed: {str(e)}")
            return "⚙ Data processing error"

    def format_hex_data(self, data_bytes, read_time):
        """Format hexadecimal data with timestamp"""
        if self.is_show_timeStamp:
            ts = read_time.strftime("%Y-%m-%d_%H:%M:%S:%f")[:-3]
            return f"[{ts}]{data_bytes.decode('latin-1')}"
        return data_bytes.decode('latin-1')

    def format_text_data(self, data_bytes, read_time):
        """Format text data with per-line timestamp calculation"""
        try:
            if not isinstance(data_bytes, bytes):
                raise ValueError(f"Expected bytes, got {type(data_bytes)}")
            
            if not data_bytes:
                return ""

            # Validate input parameters
            if not isinstance(data_bytes, bytes):
                raise ValueError("Invalid byte data received")

            # Calculate time parameters with safety checks
            byte_count = len(data_bytes)
            if byte_count == 0 or self.baud_rate <= 0:
                return ""

            bits_per_byte = 10  # 1 start + 8 data + 1 stop
            total_time = byte_count * bits_per_byte / self.baud_rate
            receive_duration = max(0.0, (read_time - self._last_read_time).total_seconds())
            
            # Calculate time_per_byte with bounds checking
            time_per_byte = min(total_time, receive_duration) / byte_count if byte_count > 0 else 0
            time_per_byte = max(0.0, time_per_byte)  # Prevent negative time

            lines = []
            line_buffer = []
            current_time = self._last_read_time
            
            # Add timestamp for each byte
            for i, byte in enumerate(data_bytes):
                try:
                    # Calculate progressive timestamp
                    current_time = self._last_read_time + datetime.timedelta(
                        seconds=(i * time_per_byte)
                    )
                    
                    line_buffer.append(byte)
                    
                    if byte == 0x0A:  # LF byte (\n)
                        line_str = self.decode_line(line_buffer)
                        lines.append(self.add_timestamp(line_str, current_time))
                        line_buffer = []
                except Exception as e:
                    print(f"Error processing byte {i}: {str(e)}")
                    line_buffer = []  # Reset buffer on error

            # Process remaining data
            if line_buffer:
                try:
                    line_str = self.decode_line(line_buffer)
                    lines.append(self.add_timestamp(line_str, current_time))
                except Exception as e:
                    print(f"Error processing final line: {str(e)}")

            return '\n'.join(lines)
        except Exception as e:
            print(f"Critical format error: {str(e)}")
            return "⚙ Data format error"  # Return error indicator instead of crashing

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

    def calculate_sleep_interval(self):
        """基于数据活跃度的动态间隔计算"""
        active_factor = 0.2  # 0-1, 1表示持续有数据
        base_interval = 10  # 基准间隔(ms)
        min_interval = 2    # 最小间隔(ms)
        
        # 根据最近两次数据量计算活跃度
        if hasattr(self, '_prev_data_size'):
            data_diff = abs(len(self._last_data) - self._prev_data_size)
            active_factor = min(1.0, data_diff / 64)  # 64字节为参考值
        
        # 动态调整公式
        interval = max(min_interval, base_interval * (1 - active_factor))
        return int(interval)

    def handle_exception(self, error):
        """Centralized exception handling"""
        error_msg = str(error)
        # 区分异常类型处理
        if isinstance(error, SerialTimeoutException):
            self.exceptionOccurred.emit("Read timeout occurred")
        elif "closed" in error_msg.lower():
            self.exceptionOccurred.emit("Serial port closed")
            if self.serial_port.is_open:
                self.serial_port.close()
        else:
            self.exceptionOccurred.emit(f"Error: {error_msg}")
            # 仅在严重错误时关闭端口
            if "critical" in error_msg.lower():
                self.serial_port.close()