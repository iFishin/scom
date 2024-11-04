import configparser
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                               QGridLayout, QMainWindow, QKeySequenceEdit)
from PySide6.QtCore import Qt

class HotkeysConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hotkeys Configuration")

        self.layout = QVBoxLayout()

        self.grid_layout = QGridLayout()

        self.hotkeys = {
            "Action 1": "Ctrl+A",
            "Action 2": "Ctrl+B",
            "Action 3": "Ctrl+C",
            "Action 4": "Ctrl+D",
            "Action 5": "",
            "Action 6": "",
            "Action 7": "",
            "Action 8": ""
        }
        
        

        self.hotkey_inputs = {}

        row = 0
        for index, (action, hotkey) in enumerate(self.hotkeys.items(), start=1):
            index_label = QLabel(str(index))
            input_hotkey_name = QLineEdit(action)
            input_hotkey_value = QLineEdit(hotkey)
            if index <= 4:
                input_hotkey_value.setReadOnly(True)
            shortcut_label = QLabel("Shortcut:")
            shortcut_input = QKeySequenceEdit()
            if index > 4:
                shortcut_input.setFocusPolicy(Qt.StrongFocus)

            self.hotkey_inputs[input_hotkey_name] = input_hotkey_value

            self.grid_layout.addWidget(index_label, row, 0, 1, 1, alignment=Qt.AlignCenter)
            self.grid_layout.addWidget(input_hotkey_name, row, 1, 1, 1, alignment=Qt.AlignCenter)
            self.grid_layout.addWidget(input_hotkey_value, row, 2, 1, 1, alignment=Qt.AlignCenter)
            self.grid_layout.addWidget(shortcut_label, row, 3, 1, 1, alignment=Qt.AlignCenter)
            self.grid_layout.addWidget(shortcut_input, row, 4, 1, 1, alignment=Qt.AlignCenter)
            row += 1

        add_button = QPushButton("Add")
        add_button.clicked.connect(self.add_row)

        self.layout.addLayout(self.grid_layout)
        self.layout.addWidget(add_button)

        self.setLayout(self.layout)

    def add_row(self):
        next_index = len(self.hotkeys) + 1
        new_action = f"Hotkey {next_index}"
        self.hotkeys[new_action] = ""
        row = len(self.hotkeys) - 1
        index_label = QLabel(str(next_index))
        input_hotkey_name = QLineEdit(new_action)
        input_hotkey_value = QLineEdit("")
        shortcut_label = QLabel("Shortcut:")
        shortcut_input = QKeySequenceEdit()
        shortcut_input.setFocusPolicy(Qt.StrongFocus)

        self.hotkey_inputs[input_hotkey_name] = input_hotkey_value

        self.grid_layout.addWidget(index_label, row, 0, 1, 1, alignment=Qt.AlignCenter)
        self.grid_layout.addWidget(input_hotkey_name, row, 1, 1, 1, alignment=Qt.AlignCenter)
        self.grid_layout.addWidget(input_hotkey_value, row, 2, 1, 1, alignment=Qt.AlignCenter)
        self.grid_layout.addWidget(shortcut_label, row, 3, 1, 1, alignment=Qt.AlignCenter)
        self.grid_layout.addWidget(shortcut_input, row, 4, 1, 1, alignment=Qt.AlignCenter)

    def save_hotkeys(self):
        for action, input_field in self.hotkey_inputs.items():
            self.hotkeys[action] = input_field.text()
        print("Hotkeys saved:", self.hotkeys)
        self.accept()