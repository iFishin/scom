from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QMessageBox, QFormLayout


class StringAsciiConvertDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("String - ASCII(HEX) Converter")
        self.resize(400, 400)

        # Create layouts
        main_layout = QVBoxLayout()
        form_layout = QFormLayout()
        button_layout = QHBoxLayout()

        # Create widgets
        self.string_label = QLabel("Input:")
        self.string_input = QTextEdit()
        self.string_input.setMaximumHeight(50)
        self.string_input.setText("Hello")  # Set default text

        self.ascii_label = QLabel("Result:")
        self.ascii_output = QTextEdit()
        self.ascii_output.setReadOnly(True)
        self.ascii_output.setMinimumHeight(150)
        self.ascii_output.setText("48656C6C6F")  # Set default ASCII codes

        self.convert_to_ascii_button = QPushButton("String to ASCII")
        self.convert_to_string_button = QPushButton("ASCII to String")
        self.close_button = QPushButton("Close")

        # Add widgets to form layout
        form_layout.addRow(self.string_label, self.string_input)
        form_layout.addRow(self.ascii_label, self.ascii_output)

        # Add buttons to button layout
        button_layout.addWidget(self.convert_to_ascii_button)
        button_layout.addWidget(self.convert_to_string_button)
        button_layout.addWidget(self.close_button)

        # Add layouts to main layout
        main_layout.addLayout(form_layout)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        # Connect signals
        self.convert_to_ascii_button.clicked.connect(self.convert_string_to_ascii)
        self.convert_to_string_button.clicked.connect(self.convert_ascii_to_string)
        self.close_button.clicked.connect(self.close)

    def convert_string_to_ascii(self):
        input_string = self.string_input.toPlainText()
        if not input_string:
            QMessageBox.warning(self, "Warning", "Please enter a string!")
            return
        ascii_codes = [format(ord(char), '02X') for char in input_string]
        ascii_output_text = "".join(ascii_codes)
        self.ascii_output.setText(ascii_output_text)

    def convert_ascii_to_string(self):
        input_ascii = self.string_input.toPlainText()
        if not input_ascii:
            QMessageBox.warning(self, "Warning", "Please enter ASCII codes!")
            return
        try:
            ascii_list = [input_ascii[i:i+2] for i in range(0, len(input_ascii), 2)]
            output_string = "".join(chr(int(code, 16)) for code in ascii_list)
            self.ascii_output.setText(output_string)
        except ValueError:
            QMessageBox.warning(self, "Warning", "Please enter valid ASCII codes!")
