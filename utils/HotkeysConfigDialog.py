import sys
from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QGridLayout, QMainWindow)
from PySide6.QtCore import Qt

class HotkeysConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hotkeys Configuration")

        self.layout = QGridLayout()

        self.hotkeys = {
            "Action 1": "Ctrl+A",
            "Action 2": "Ctrl+B",
            "Action 3": "Ctrl+C"
        }

        self.hotkey_inputs = {}

        row = 0
        for action, hotkey in self.hotkeys.items():
            input_hotkey_name = QLineEdit(action)
            input_hotkey_value = QLineEdit(hotkey)
            self.hotkey_inputs[input_hotkey_name] = input_hotkey_value

            self.layout.addWidget(input_hotkey_name, row, 0, 1, 1, alignment=Qt.AlignCenter)
            self.layout.addWidget(input_hotkey_value, row, 1, 1, 1, alignment=Qt.AlignCenter)
            row += 1

        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")

        self.save_button.clicked.connect(self.save_hotkeys)
        self.cancel_button.clicked.connect(self.reject)

        self.layout.addWidget(self.save_button, row, 0, 1, 1)
        self.layout.addWidget(self.cancel_button, row, 1, 1, 1)

        self.setLayout(self.layout)
        self.installEventFilter(self)

    def save_hotkeys(self):
        for action, input_field in self.hotkey_inputs.items():
            self.hotkeys[action] = input_field.text()
        print("Hotkeys saved:", self.hotkeys)
        self.accept()

    def eventFilter(self, watched, event):
        if event.type() == event.Type.MouseButtonPress and not self.rect().contains(event.pos()):
            print("Mouse click outside dialog")
            self.reject()
            return True
        elif event.type() == event.Type.FocusOut:
            print("Dialog lost focus")
            self.reject()
            return True
        else:
            print("Other event")
        return super().eventFilter(watched, event)
