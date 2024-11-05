from utils.common import read_config, write_config
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QGridLayout,
    QKeySequenceEdit,
    QScrollArea,
    QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence


class HotkeysConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hotkeys Configuration")
        self.setFixedWidth(550)
        self.setFixedHeight(400)

        self.parent = parent
        self.layout = QVBoxLayout()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)

        self.grid_layout = QGridLayout()

        self.hotkeys = {}

        self.config = read_config("config.ini")
        hotkeys_section = dict(self.config.items("Hotkeys"))
        hotkey_values_section = dict(self.config.items("HotkeyValues"))
        hotkey_shortcuts_section = dict(self.config.items("HotkeyShortcuts"))
        self.hotkeys = {
            hotkeys_section.get(f"hotkey_{i + 1}", ""): [
                hotkey_values_section.get(f"hotkeyvalue_{i + 1}", ""),
                hotkey_shortcuts_section.get(f"hotkeyshortcut_{i + 1}", "")
            ]
            for i in range(8)
        }
        print(self.hotkeys)
        self.hotkey_inputs = {}

        row = 0
        for index, (name, (value, shortcut)) in enumerate(self.hotkeys.items(), start=1):
            index_label = QLabel(str(index))
            input_hotkey_name = QLineEdit(name)
            input_hotkey_value = QLineEdit(value)
            input_hotkey_shortcut = QKeySequenceEdit()
            input_hotkey_shortcut.setKeySequence(QKeySequence(shortcut))
            
            input_hotkey_value.setCursorPosition(0)
            
            if index <= 4:
                input_hotkey_value.setReadOnly(True)
            shortcut_label = QLabel("Shortcut:")
            shortcut_input = QKeySequenceEdit()
            if index > 4:
                shortcut_input.setFocusPolicy(Qt.StrongFocus)

            self.hotkey_inputs[input_hotkey_name] = [input_hotkey_value, input_hotkey_shortcut]

            self.grid_layout.addWidget(index_label, row, 0, 1, 1, alignment=Qt.AlignCenter)
            self.grid_layout.addWidget(
                input_hotkey_name, row, 1, 1, 1, alignment=Qt.AlignCenter
            )
            self.grid_layout.addWidget(
                input_hotkey_value, row, 2, 1, 3, alignment=Qt.AlignCenter
            )
            self.grid_layout.addWidget(
                shortcut_label, row, 5, 1, 1, alignment=Qt.AlignCenter
            )
            self.grid_layout.addWidget(
                input_hotkey_shortcut, row, 6, 1, 2, alignment=Qt.AlignCenter
            )
            row += 1

        self.scroll_layout.addLayout(self.grid_layout)
        self.scroll_area.setWidget(self.scroll_content)

        add_button = QPushButton("Add")
        add_button.clicked.connect(self.add_row)

        self.layout.addWidget(self.scroll_area)
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
        self.grid_layout.addWidget(
            input_hotkey_name, row, 1, 1, 1, alignment=Qt.AlignCenter
        )
        self.grid_layout.addWidget(
            input_hotkey_value, row, 2, 1, 3, alignment=Qt.AlignCenter
        )
        self.grid_layout.addWidget(
            shortcut_label, row, 5, 1, 1, alignment=Qt.AlignCenter
        )
        self.grid_layout.addWidget(
            shortcut_input, row, 6, 1, 2, alignment=Qt.AlignCenter
        )
        
    def update_parent_hotkeys(self):
        for index, (name, [value, shortcut]) in enumerate(self.hotkey_inputs.items()):
            self.parent.hotkeys[name.text()] = [value.text(), shortcut.keySequence().toString()]
            
    
    def save_hotkeys(self):
        for index, (name, [value, shortcut]) in enumerate(self.hotkey_inputs.items()):
            print(name.text(), value.text(), shortcut.keySequence().toString())
            self.config.set("Hotkeys", f"hotkey_{index + 1}", name.text())
            self.config.set("HotkeyValues", f"hotkeyvalue_{index + 1}", value.text())
            self.config.set("HotkeyShortcuts", f"hotkeyshortcut_{index + 1}", shortcut.keySequence().toString())
        write_config(self.config)
        self.accept()
    
    # Close and save
    def closeEvent(self, event):
        self.save_hotkeys()
        event.accept()