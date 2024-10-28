import sys
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QGridLayout
)
from PySide6.QtCore import Qt

class HotkeysConfigDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hotkeys Configuration")
        self.setGeometry(100, 100, 400, 300)
        
        self.layout = QGridLayout()
        
        self.hotkeys = {
            "Action 1": "Ctrl+A",
            "Action 2": "Ctrl+B",
            "Action 3": "Ctrl+C"
        }
        
        self.hotkey_inputs = {}
        
        row = 0
        for action, hotkey in self.hotkeys.items():
            label = QLabel(action)
            input_field = QLineEdit(hotkey)
            self.hotkey_inputs[action] = input_field
            
            self.layout.addWidget(label, row, 0, 1, 1, alignment=Qt.AlignCenter)
            self.layout.addWidget(input_field, row, 1, 1, 1, alignment=Qt.AlignCenter)
            row += 1
        
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        
        self.save_button.clicked.connect(self.save_hotkeys)
        self.cancel_button.clicked.connect(self.reject)
        
        self.layout.addWidget(self.save_button, row, 0, 1, 1)
        self.layout.addWidget(self.cancel_button, row, 1, 1, 1)
        
        self.setLayout(self.layout)
    
    def save_hotkeys(self):
        for action, input_field in self.hotkey_inputs.items():
            self.hotkeys[action] = input_field.text()
        print("Hotkeys saved:", self.hotkeys)
        self.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = HotkeysConfigDialog()
    if dialog.exec_():
        print("Dialog accepted")
    else:
        print("Dialog rejected")
    sys.exit(app.exec_())
