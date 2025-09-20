from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QSpinBox, QCheckBox, QMessageBox, QProgressBar
from PySide6.QtCore import QThread, Signal, QTimer
import random
import string

class StringGeneratorThread(QThread):
    """字符串生成线程，避免UI阻塞"""
    finished = Signal(str)
    progress = Signal(int)
    error = Signal(str)
    
    def __init__(self, length, chars):
        super().__init__()
        self.length = length
        self.chars = chars
        
    def run(self):
        try:
            # 简化逻辑，直接限制最大长度为50万，避免过度优化导致的问题
            if self.length > 500000:
                self.error.emit("Length too large, maximum 500000 characters allowed")
                return
                
            # 对于大字符串分批生成
            if self.length > 10000:
                result = []
                batch_size = 5000
                total_batches = (self.length + batch_size - 1) // batch_size
                
                for i in range(total_batches):
                    if self.isInterruptionRequested():
                        return
                    
                    current_batch_size = min(batch_size, self.length - i * batch_size)
                    batch = ''.join(random.choice(self.chars) for _ in range(current_batch_size))
                    result.append(batch)
                    
                    progress = int((i + 1) * 100 / total_batches)
                    self.progress.emit(progress)
                
                final_result = ''.join(result)
            else:
                # 小字符串直接生成
                final_result = ''.join(random.choice(self.chars) for _ in range(self.length))
                self.progress.emit(100)
            
            self.finished.emit(final_result)
        except Exception as e:
            self.error.emit(str(e))

class StringGenerateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generate String")
        self.resize(400, 350)
        
        self.generator_thread = None
        
        # Create layouts
        main_layout = QVBoxLayout()
        length_layout = QHBoxLayout()
        options_layout = QVBoxLayout()
        progress_layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        
        # Create widgets
        self.length_label = QLabel("String Length(1~500000):")
        self.length_spinbox = QSpinBox()
        self.length_spinbox.setRange(1, 500000)  # 限制为50万
        self.length_spinbox.setValue(10)
        
        # 添加警告标签
        self.warning_label = QLabel("")
        self.warning_label.setStyleSheet("color: red; font-size: 10px;")
        
        self.include_lowercase = QCheckBox("Include Lowercase Letters")
        self.include_lowercase.setChecked(True)
        
        self.include_uppercase = QCheckBox("Include Uppercase Letters")
        self.include_uppercase.setChecked(True)
        
        self.include_digits = QCheckBox("Include Digits")
        self.include_digits.setChecked(True)
        
        self.include_special = QCheckBox("Include Special Characters")
        self.include_special.setChecked(False)
        
        self.include_whitespace = QCheckBox("Include Whitespace")
        self.include_whitespace.setChecked(False)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        self.result_label = QLabel("Generated String:")
        self.result_edit = QTextEdit()
        self.result_edit.setMinimumHeight(100)
        self.result_edit.setReadOnly(True)
        
        self.generate_button = QPushButton("Generate")
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setVisible(False)
        self.close_button = QPushButton("Close")
        
        # Add widgets to layouts
        length_layout.addWidget(self.length_label)
        length_layout.addWidget(self.length_spinbox)
        
        options_layout.addWidget(self.include_lowercase)
        options_layout.addWidget(self.include_uppercase)
        options_layout.addWidget(self.include_digits)
        options_layout.addWidget(self.include_special)
        options_layout.addWidget(self.include_whitespace)
        
        progress_layout.addWidget(self.progress_bar)
        
        button_layout.addWidget(self.generate_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.close_button)
        
        main_layout.addLayout(length_layout)
        main_layout.addWidget(self.warning_label)
        main_layout.addLayout(options_layout)
        main_layout.addLayout(progress_layout)
        main_layout.addWidget(self.result_label)
        main_layout.addWidget(self.result_edit)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
        # Connect signals
        self.generate_button.clicked.connect(self.generate_string)
        self.cancel_button.clicked.connect(self.cancel_generation)
        self.close_button.clicked.connect(self.close)
        self.length_spinbox.valueChanged.connect(self.update_warning)
        
        # 初始化警告
        self.update_warning()
        
    def update_warning(self):
        """根据长度显示警告"""
        length = self.length_spinbox.value()
        if length > 100000:
            self.warning_label.setText("Warning: Large strings may take longer to generate")
        elif length > 50000:
            self.warning_label.setText("Warning: Generation may take a few seconds")
        else:
            self.warning_label.setText("")
    
    def generate_string(self):
        length = self.length_spinbox.value()
        
        # 检查是否选择了字符集
        chars = ''
        if self.include_lowercase.isChecked():
            chars += string.ascii_lowercase
        if self.include_uppercase.isChecked():
            chars += string.ascii_uppercase
        if self.include_digits.isChecked():
            chars += string.digits
        if self.include_special.isChecked():
            chars += string.punctuation
        if self.include_whitespace.isChecked():
            chars += ' '
        
        if not chars:
            QMessageBox.warning(self, "Warning", "At least one character set must be selected!")
            return
        
        # 对于超大字符串的额外确认
        if length > 200000:
            reply = QMessageBox.question(
                self, 
                "Confirm Generation", 
                f"You are about to generate {length:,} characters. This may take some time and use significant memory.\n\nDo you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # 开始生成
        self.start_generation(length, chars)
    
    def start_generation(self, length, chars):
        """开始字符串生成"""
        self.generate_button.setVisible(False)
        self.cancel_button.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.result_edit.setText("Generating...")
        
        # 创建并启动线程
        self.generator_thread = StringGeneratorThread(length, chars)
        self.generator_thread.finished.connect(self.on_generation_finished)
        self.generator_thread.progress.connect(self.on_progress_updated)
        self.generator_thread.error.connect(self.on_generation_error)
        self.generator_thread.start()
    
    def cancel_generation(self):
        """取消生成"""
        if self.generator_thread and self.generator_thread.isRunning():
            self.generator_thread.requestInterruption()
            self.generator_thread.wait(3000)  # 等待3秒
        self.reset_ui()
    
    def on_generation_finished(self, result):
        """生成完成"""
        self.result_edit.setText(result)
        self.reset_ui()
    
    def on_progress_updated(self, progress):
        """更新进度"""
        self.progress_bar.setValue(progress)
    
    def on_generation_error(self, error_msg):
        """生成错误"""
        QMessageBox.critical(self, "Generation Error", f"Error generating string: {error_msg}")
        self.reset_ui()
    
    def reset_ui(self):
        """重置UI状态"""
        self.generate_button.setVisible(True)
        self.cancel_button.setVisible(False)
        self.progress_bar.setVisible(False)
        if self.generator_thread:
            self.generator_thread = None
    
    def closeEvent(self, event):
        """关闭窗口时取消生成"""
        if self.generator_thread and self.generator_thread.isRunning():
            self.generator_thread.requestInterruption()
            self.generator_thread.wait(3000)
        event.accept()
