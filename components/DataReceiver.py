import datetime
from utils import common
from PySide6.QtCore import QThread, Signal, QMutex, QWaitCondition, QMutexLocker
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
        
        # Add persistent buffer
        self.persistent_buffer = bytearray()
        self.last_data_time = datetime.datetime.now()
        self.buffer_timeout = 0.05  # 50 milliseconds timeout
        

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
        """Safely read raw bytes from serial port with proper buffer handling"""
        if not self.serial_port.is_open:
            raise RuntimeError("Serial port is not open")
        
        try:
            # Check the buffer status first
            if self.serial_port.in_waiting > 0:
                # If data is available, read all immediately
                return self.serial_port.read_all()
            
            # If no data is waiting, use the standard read method
            if self.is_show_hex:
                raw = common.port_read_hex(self.serial_port)
            else:
                raw = common.port_read(self.serial_port)
            
            # Type conversion protection
            if isinstance(raw, str):
                return raw.encode('utf-8')
            return raw or b''
        
        except Exception as e:
            self.serial_port.close()
            raise

    @property
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
        block_duration = self.byte_transmission_time * (byte_count - 1)
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
            line_duration = self.byte_transmission_time * current_pos
            line_time = start_time + datetime.timedelta(seconds=line_duration)
            
            # Calculate the number of bytes in the current line (including the newline character)
            line_length = len(line) + 1  # +1 for the split '\n'
            
            # Generate the timestamp
            ts = line_time.strftime("%Y-%m-%d_%H:%M:%S:%f")[:-3]
            formatted_lines.append(f"[{ts}]{line.decode('latin-1')}")
            
            current_pos += line_length
            
        return '\n'.join(formatted_lines)

    def format_text_data(self, data_bytes, start_time):
        """Format text data with precise timestamps"""
        try:
            if not isinstance(data_bytes, bytes):
                raise ValueError(f"Expected bytes, got {type(data_bytes)}")
            
            if not data_bytes:
                return ""

            # Add to persistent buffer and update the last data time
            self.persistent_buffer.extend(data_bytes)
            self.last_data_time = datetime.datetime.now()
            
            complete_lines = []
            current_pos = 0  # Current position in the data block
            
            # Split the buffer into complete lines
            while True:
                # Find the position of the newline character
                newline_pos = self.persistent_buffer.find(b'\n')
                if newline_pos == -1:
                    break
                    
                # Extract a single line of data (including the newline character)
                line_bytes = self.persistent_buffer[:newline_pos+1]
                
                # Calculate the start time of the line (considering transmission delay)
                line_duration = self.byte_transmission_time * current_pos
                line_time = start_time + datetime.timedelta(seconds=line_duration)
                
                # Decode and add a timestamp
                line_str = self.decode_line(line_bytes)
                formatted = self.add_timestamp(line_str, line_time)
                complete_lines.append(formatted)
                
                # Remove the processed line from the buffer
                del self.persistent_buffer[:newline_pos+1]
                
                # Update the position counter
                current_pos += len(line_bytes)
            
            # Handle timeout for remaining data
            if self.persistent_buffer:
                time_since_last = (datetime.datetime.now() - self.last_data_time).total_seconds()
                if time_since_last > self.buffer_timeout:
                    # Timeout, process remaining data
                    line_duration = self.byte_transmission_time * current_pos
                    line_time = start_time + datetime.timedelta(seconds=line_duration)
                    line_str = self.decode_line(bytes(self.persistent_buffer))
                    complete_lines.append(self.add_timestamp(line_str, line_time))
                    self.persistent_buffer.clear()
                    
            # Return all complete lines, joined by newline characters
            return '\n'.join(complete_lines)
            
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

    def calculate_sleep_interval(self):
        """Dynamic interval calculation based on data activity"""
        active_factor = 0.2  # 0-1, 1 indicates continuous data flow
        base_interval = 10  # Base interval (ms)
        min_interval = 2    # Minimum interval (ms)
        
        # Calculate activity level based on recent data size differences
        if hasattr(self, '_prev_data_size'):
            data_diff = abs(len(self._last_data) - self._prev_data_size)
            active_factor = min(1.0, data_diff / 64)  # 64 bytes as reference value
        
        # Dynamic adjustment formula
        interval = max(min_interval, base_interval * (1 - active_factor))
        return int(interval)

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