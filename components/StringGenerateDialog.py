from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QSpinBox, QCheckBox, QMessageBox
import random
import string

class StringGenerateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generate String")
        self.resize(400, 300)
        
        # Create layouts
        main_layout = QVBoxLayout()
        length_layout = QHBoxLayout()
        options_layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        
        # Create widgets
        self.length_label = QLabel("String Length:")
        self.length_spinbox = QSpinBox()
        self.length_spinbox.setRange(1, 1000)
        self.length_spinbox.setValue(10)
        
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
        
        self.result_label = QLabel("Generated String:")
        self.result_edit = QTextEdit()
        self.result_edit.setMinimumHeight(100)
        self.result_edit.setReadOnly(True)
        
        self.generate_button = QPushButton("Generate")
        self.close_button = QPushButton("Close")
        
        # Add widgets to layouts
        length_layout.addWidget(self.length_label)
        length_layout.addWidget(self.length_spinbox)
        
        options_layout.addWidget(self.include_lowercase)
        options_layout.addWidget(self.include_uppercase)
        options_layout.addWidget(self.include_digits)
        options_layout.addWidget(self.include_special)
        options_layout.addWidget(self.include_whitespace)
        
        button_layout.addWidget(self.generate_button)
        button_layout.addWidget(self.close_button)
        
        main_layout.addLayout(length_layout)
        main_layout.addLayout(options_layout)
        main_layout.addWidget(self.result_label)
        main_layout.addWidget(self.result_edit)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
        # Connect signals
        self.generate_button.clicked.connect(self.generate_string)
        self.close_button.clicked.connect(self.close)
        
    def generate_string(self):
        length = self.length_spinbox.value()
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
        
        result = ''.join(random.choice(chars) for _ in range(length))
        self.result_edit.setText(result)
