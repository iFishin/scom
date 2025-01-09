from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QSpinBox, QCheckBox
from PySide6.QtGui import QClipboard, QGuiApplication
import random
import string

class LengthCalculateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("String Length Calculator")
        self.resize(400, 250)
        
        # Create layouts
        main_layout = QVBoxLayout()
        input_layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        
        # Create input field and labels
        self.input_label = QLabel("Enter string:")
        self.input_text = QTextEdit()
        self.input_text.setMinimumHeight(50)
        self.result_label = QLabel("String length: 0")
        
        self.paste_button = QPushButton("Paste from Clipboard")
        self.clear_button = QPushButton("Clear")
        
        # Add widgets to input layout
        input_layout.addWidget(self.input_label)
        input_layout.addWidget(self.input_text)
        input_layout.addWidget(self.result_label)
        
        # Add widgets to button layout
        button_layout.addWidget(self.paste_button)
        button_layout.addWidget(self.clear_button)
        
        # Add layouts to main layout
        main_layout.addLayout(input_layout)
        main_layout.addLayout(button_layout)
        
        # Set layout
        self.setLayout(main_layout)
        
        # Connect signals
        self.input_text.textChanged.connect(self.calculate_length)
        self.paste_button.clicked.connect(self.paste_from_clipboard)
        self.clear_button.clicked.connect(self.clear_text)
    
    def calculate_length(self):
        text = self.input_text.toPlainText()
        length = len(text)
        self.result_label.setText(f"String length: {length}")
    
    def paste_from_clipboard(self):
        clipboard = QGuiApplication.clipboard()
        clipboard_text = clipboard.text()
        self.input_text.setText(clipboard_text)
    
    def clear_text(self):
        self.input_text.clear()
