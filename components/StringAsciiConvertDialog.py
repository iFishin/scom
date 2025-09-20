from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QMessageBox, QFormLayout, QCheckBox
from PySide6.QtCore import Qt

class StringAsciiConvertDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("String - ASCII(HEX) Converter")
        self.resize(400, 350)

        # Create layouts
        main_layout = QVBoxLayout()
        switch_layout = QHBoxLayout()
        button_layout = QHBoxLayout()

        # Create mode switch
        self.mode_label = QLabel("Input Mode:")
        self.mode_switch = QCheckBox("ASCII HEX")
        self.mode_switch.setChecked(False)  # Default to String mode
        self.mode_switch.setStyleSheet("""
            QCheckBox {
                font-size: 12px;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #f0f0f0;
                border: 2px solid #ccc;
                border-radius: 10px;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d7;
                border-radius: 10px;
            }
        """)
        
        switch_layout.addWidget(self.mode_label)
        switch_layout.addWidget(self.mode_switch)
        switch_layout.addStretch()

        # Create widgets
        self.input_label = QLabel("Input (String):")
        self.input_text = QTextEdit()
        self.input_text.setMaximumHeight(80)
        self.input_text.setText("Hello")  # Set default text

        self.output_label = QLabel("Output (ASCII HEX):")
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(80)
        self.output_text.setText("48656C6C6F")  # Set default ASCII codes

        self.close_button = QPushButton("Close")

        # Add widgets to main layout (each on separate line)
        main_layout.addLayout(switch_layout)
        main_layout.addWidget(self.input_label)
        main_layout.addWidget(self.input_text)
        main_layout.addWidget(self.output_label)
        main_layout.addWidget(self.output_text)

        # Add buttons to button layout
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)

        # Add button layout to main layout
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        # Connect signals
        self.mode_switch.toggled.connect(self.on_mode_changed)
        self.input_text.textChanged.connect(self.on_input_changed)
        self.close_button.clicked.connect(self.close)

        # Initialize the display
        self.update_labels()

    def on_mode_changed(self):
        """Update labels and perform conversion when mode is switched"""
        self.update_labels()
        self.on_input_changed()

    def update_labels(self):
        """Update input and output labels"""
        if self.mode_switch.isChecked():  # ASCII HEX mode
            self.input_label.setText("Input (ASCII HEX):")
            self.output_label.setText("Output (String):")
        else:  # String mode
            self.input_label.setText("Input (String):")
            self.output_label.setText("Output (ASCII HEX):")

    def on_input_changed(self):
        """Automatically convert when input text changes"""
        input_text = self.input_text.toPlainText()
        
        if not input_text:
            self.output_text.clear()
            return
            
        try:
            if self.mode_switch.isChecked():  # ASCII HEX to String
                self.convert_hex_to_string(input_text)
            else:  # String to ASCII HEX
                self.convert_string_to_hex(input_text)
        except Exception as e:
            self.output_text.setText(f"Conversion error: {str(e)}")

    def convert_string_to_hex(self, input_string):
        """Convert string to ASCII HEX"""
        try:
            ascii_codes = [format(ord(char), '02X') for char in input_string]
            ascii_output_text = "".join(ascii_codes)
            self.output_text.setText(ascii_output_text)
        except Exception as e:
            self.output_text.setText("Conversion error: Invalid string")

    def convert_hex_to_string(self, input_hex):
        """Convert ASCII HEX to string"""
        try:
            # Remove spaces and non-hex characters
            clean_hex = ''.join(c for c in input_hex if c in '0123456789ABCDEFabcdef')
            
            if len(clean_hex) % 2 != 0:
                self.output_text.setText("Conversion error: HEX character count must be even")
                return
                
            hex_pairs = [clean_hex[i:i+2] for i in range(0, len(clean_hex), 2)]
            output_string = "".join(chr(int(pair, 16)) for pair in hex_pairs)
            self.output_text.setText(output_string)
        except ValueError:
            self.output_text.setText("Conversion error: Invalid HEX format")
        except Exception as e:
            self.output_text.setText(f"Conversion error: {str(e)}")
