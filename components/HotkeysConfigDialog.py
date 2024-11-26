from utils.common import read_config, write_config
from functools import partial
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QGridLayout,
    QKeySequenceEdit,
    QScrollArea,
    QWidget,
    QHBoxLayout,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence


class HotkeysConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hotkeys Configuration")
        self.setFixedWidth(650)
        self.setFixedHeight(450)

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
                hotkey_shortcuts_section.get(f"hotkeyshortcut_{i + 1}", ""),
            ]
            for i in range(len(hotkeys_section))
        }
        self.hotkey_inputs = {}

        self.populate_grid()

        self.scroll_layout.addLayout(self.grid_layout)
        self.scroll_area.setWidget(self.scroll_content)

        add_button = QPushButton("+")
        add_button.clicked.connect(self.add_row)

        self.layout.addWidget(self.scroll_area)
        self.layout.addWidget(add_button)

        # Add Save and Cancel buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_hotkeys)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)

        self.layout.addLayout(button_layout)
        self.setLayout(self.layout)

    def populate_grid(self):
        for row, (name, (value, shortcut)) in enumerate(self.hotkeys.items()):
            self.add_row_to_grid(row, name, value, shortcut)

    def add_row_to_grid(self, row, name, value, shortcut):
        delete_button = QPushButton("-")
        delete_button.clicked.connect(partial(self.delete_row, row))
        index_label = QLabel(str(row + 1))
        input_hotkey_name = QLineEdit(name)
        input_hotkey_value = QLineEdit(value)
        input_hotkey_value.setMinimumWidth(200)
        input_hotkey_shortcut = QKeySequenceEdit()
        input_hotkey_shortcut.setKeySequence(QKeySequence(shortcut))

        input_hotkey_value.setCursorPosition(0)

        if row < 4:
            input_hotkey_value.setReadOnly(True)
        shortcut_label = QLabel("Shortcut:")

        self.hotkey_inputs[input_hotkey_name] = [
            input_hotkey_value,
            input_hotkey_shortcut,
        ]

        self.grid_layout.addWidget(
            delete_button, row, 0, 1, 1, alignment=Qt.AlignCenter
        )
        self.grid_layout.addWidget(index_label, row, 1, 1, 1, alignment=Qt.AlignCenter)
        self.grid_layout.addWidget(
            input_hotkey_name, row, 2, 1, 1, alignment=Qt.AlignCenter
        )
        self.grid_layout.addWidget(
            input_hotkey_value, row, 3, 1, 3, alignment=Qt.AlignCenter
        )
        self.grid_layout.addWidget(
            shortcut_label, row, 6, 1, 1, alignment=Qt.AlignCenter
        )
        self.grid_layout.addWidget(
            input_hotkey_shortcut, row, 7, 1, 2, alignment=Qt.AlignCenter
        )

    def add_row(self):
        next_index = len(self.hotkeys)
        new_action = f"Hotkey {next_index + 1}"
        self.hotkeys[new_action] = ["", ""]
        self.add_row_to_grid(next_index, new_action, "", "")

    def delete_row(self, row):
        if row >= len(self.hotkeys):
            return

        hotkey_name = list(self.hotkeys.keys())[row]
        self.hotkeys.pop(hotkey_name)
        hotkey_input_keys = list(self.hotkey_inputs.keys())
        hotkey_input = self.hotkey_inputs.pop(hotkey_input_keys[row])
        for widget in hotkey_input:
            if widget is not None:
                widget.setParent(None)

        for i in range(self.grid_layout.columnCount()):
            item = self.grid_layout.itemAtPosition(row, i)
            if item is not None:
                widget = item.widget()
                if widget:
                    self.grid_layout.removeWidget(widget)
                    widget.deleteLater()

        # Remove references from hotkey_inputs
        del hotkey_input_keys[row]

        self.reindex_rows()
        self.update_grid()
        self.update_config()

    def reindex_rows(self):
        for row in range(self.grid_layout.rowCount()):
            index_label_item = self.grid_layout.itemAtPosition(row, 1)
            if index_label_item is not None:
                index_label = index_label_item.widget()
                if index_label:
                    index_label.setText(str(row + 1))

    def update_grid(self):
        for row in range(self.grid_layout.rowCount()):
            for col in range(self.grid_layout.columnCount()):
                item = self.grid_layout.itemAtPosition(row, col)
                if item is not None:
                    widget = item.widget()
                    if widget:
                        self.grid_layout.removeWidget(widget)
                        widget.deleteLater()
        self.populate_grid()
        
    def update_hotkeys(self):
        new_hotkeys = {}
        for name_input, (value_input, shortcut_input) in list(self.hotkey_inputs.items()):
            if name_input is not None:
                try:
                    if name_input.isVisible():
                        name = name_input.text()
                        value = value_input.text() if value_input is not None and value_input.isVisible() else ""
                        shortcut = shortcut_input.keySequence().toString() if shortcut_input is not None and shortcut_input.isVisible() else ""
                        new_hotkeys[name] = [value, shortcut]
                except RuntimeError:
                    # Handle the case where the widget has been deleted
                    continue
        self.hotkeys = new_hotkeys
        
    def update_config(self):
        self.update_hotkeys()
        # Clear existing config sections
        self.config.remove_section("Hotkeys")
        self.config.remove_section("HotkeyValues")
        self.config.remove_section("HotkeyShortcuts")
        
        # Recreate sections
        self.config.add_section("Hotkeys")
        self.config.add_section("HotkeyValues")
        self.config.add_section("HotkeyShortcuts")
        
        for index, (name, (value, shortcut)) in enumerate(self.hotkeys.items()):
            self.config.set("Hotkeys", f"hotkey_{index + 1}", name)
            self.config.set("HotkeyValues", f"hotkeyvalue_{index + 1}", value)
            self.config.set("HotkeyShortcuts", f"hotkeyshortcut_{index + 1}", shortcut)
        
        write_config(self.config, "config.ini")

    def update_parent_hotkeys(self):
        self.parent.config = self.config
        self.parent.update_hotkeys_groupbox()

    def save_hotkeys(self):
        self.update_config()
        self.update_parent_hotkeys()

    def closeEvent(self, event):
        self.save_hotkeys()
        self.update_parent_hotkeys()
        event.accept()