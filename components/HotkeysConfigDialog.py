from components.ConfigManager import read_config, write_config
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
    QHeaderView,
    QFrame,
    QSpacerItem,
    QSizePolicy,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence


class HotkeysConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hotkeys Configuration")
        self.setMinimumWidth(900)
        self.setMinimumHeight(550)
        self.resize(950, 650)

        self.parent = parent
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(25, 25, 25, 25)
        self.layout.setSpacing(20)

        # Create title
        title_label = QLabel("Hotkeys Configuration")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 15px; color: #2c3e50;")
        self.layout.addWidget(title_label)

        # Create info text
        info_label = QLabel("First 4 hotkeys are system presets. Values cannot be modified, but shortcuts can be changed.")
        info_label.setStyleSheet("color: #7f8c8d; margin-bottom: 15px; font-size: 12px; font-style: italic;")
        info_label.setWordWrap(True)
        self.layout.addWidget(info_label)

        # Create scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameStyle(QFrame.StyledPanel)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                background-color: white;
            }
        """)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(15, 15, 15, 15)

        # Create table layout with proper spacing
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(10)
        self.grid_layout.setColumnStretch(0, 0)  # Delete button column
        self.grid_layout.setColumnStretch(1, 0)  # Index column  
        self.grid_layout.setColumnStretch(2, 1)  # Name column
        self.grid_layout.setColumnStretch(3, 0)  # Spacer
        self.grid_layout.setColumnStretch(4, 2)  # Value column
        self.grid_layout.setColumnStretch(5, 0)  # Spacer
        self.grid_layout.setColumnStretch(6, 1)  # Shortcut column
        
        self.hotkeys = {}
        self.row_count = 0
        
        # Add headers
        self.add_headers()

        # 加载配置
        self.config = read_config("config.ini")
        hotkeys_section = dict(self.config.items("Hotkeys"))
        hotkey_values_section = dict(self.config.items("HotkeyValues"))
        hotkey_shortcuts_section = dict(self.config.items("HotkeyShortcuts"))
        self.hotkeys = {
            hotkeys_section.get(f"Hotkey_{i + 1}", ""): [
                hotkey_values_section.get(f"HotkeyValue_{i + 1}", ""),
                hotkey_shortcuts_section.get(f"HotkeyShortcut_{i + 1}", ""),
            ]
            for i in range(len(hotkeys_section))
        }
        self.hotkey_inputs = {}

        self.populate_grid()

        self.scroll_layout.addLayout(self.grid_layout)
        
        # Add flexible space
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.scroll_layout.addItem(spacer)
        
        self.scroll_area.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll_area)

        # Add button area
        self.create_button_area()

        self.setLayout(self.layout)

    def add_headers(self):
        """Add table headers"""
        headers = ["Delete", "No.", "Name", "", "Command/Value", "", "Shortcut"]
        header_style = """
            QLabel {
                font-weight: bold; 
                padding: 10px 8px; 
                background-color: #ecf0f1; 
                border: 1px solid #bdc3c7;
                color: #2c3e50;
                font-size: 13px;
            }
        """
        
        for col, header in enumerate(headers):
            if header:  # Skip empty spacer columns
                header_label = QLabel(header)
                header_label.setStyleSheet(header_style)
                header_label.setAlignment(Qt.AlignCenter)
                self.grid_layout.addWidget(header_label, 0, col, 1, 1)
        
        self.row_count = 1  # Header occupies row 0, data starts from row 1

    def create_button_area(self):
        """Create button area"""
        # Add separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #bdc3c7; margin: 10px 0;")
        self.layout.addWidget(separator)
        
        # Single button layout containing all buttons
        button_layout = QHBoxLayout()
        
        # Add new hotkey button (left side)
        add_button = QPushButton("+ Add New Hotkey")
        add_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                min-width: 140px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        add_button.clicked.connect(self.add_row)
        button_layout.addWidget(add_button)
        
        # Add stretch to push Cancel/Save buttons to the right
        button_layout.addStretch()
        
        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 24px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                min-width: 90px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        cancel_button.clicked.connect(self.reject)
        
        # Save button
        save_button = QPushButton("Save")
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 24px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                min-width: 90px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        save_button.clicked.connect(self.save_hotkeys)
        
        # Add Cancel and Save buttons with spacing
        button_layout.addWidget(cancel_button)
        button_layout.addSpacing(15)
        button_layout.addWidget(save_button)
        
        # Add the complete button layout to main layout
        self.layout.addLayout(button_layout)

    def populate_grid(self):
        """Populate grid data"""
        for i, (name, (value, shortcut)) in enumerate(self.hotkeys.items()):
            self.add_row_to_grid(self.row_count + i, name, value, shortcut, i < 4)

    def add_row_to_grid(self, row, name, value, shortcut, is_system=False):
        """Add a row to the grid"""
        # Delete button
        delete_button = QPushButton("✕")
        delete_button.setFixedSize(32, 32)
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        if is_system:
            delete_button.setEnabled(False)
            delete_button.setToolTip("System preset hotkeys cannot be deleted")
        else:
            delete_button.clicked.connect(partial(self.delete_row, row))
            delete_button.setToolTip("Delete this hotkey")

        # Index label
        index_label = QLabel(str(row - self.row_count + 1))  # Display 1-based index
        index_label.setAlignment(Qt.AlignCenter)
        index_label.setStyleSheet("""
            QLabel {
                padding: 8px; 
                border: 1px solid #bdc3c7; 
                background-color: #f8f9fa;
                color: #2c3e50;
                font-weight: 500;
                border-radius: 4px;
            }
        """)

        # Name input field
        input_hotkey_name = QLineEdit(name)
        input_hotkey_name.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 13px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #3498db;
                outline: none;
            }
            QLineEdit:read-only {
                background-color: #ecf0f1;
                color: #7f8c8d;
            }
        """)
        if is_system:
            input_hotkey_name.setReadOnly(True)
            input_hotkey_name.setToolTip("System preset hotkey names cannot be modified")

        # Value input field
        input_hotkey_value = QLineEdit(value)
        input_hotkey_value.setMinimumWidth(280)
        input_hotkey_value.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 13px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #3498db;
                outline: none;
            }
            QLineEdit:read-only {
                background-color: #ecf0f1;
                color: #7f8c8d;
            }
        """)
        input_hotkey_value.setCursorPosition(0)
        if is_system:
            input_hotkey_value.setReadOnly(True)
            input_hotkey_value.setToolTip("System preset hotkey values cannot be modified")

        # Shortcut input field
        input_hotkey_shortcut = QKeySequenceEdit()
        input_hotkey_shortcut.setKeySequence(QKeySequence(shortcut))
        input_hotkey_shortcut.setStyleSheet("""
            QKeySequenceEdit {
                padding: 8px 12px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 13px;
                min-width: 160px;
                background-color: white;
            }
            QKeySequenceEdit:focus {
                border-color: #3498db;
                outline: none;
            }
        """)

        # Store input control references
        self.hotkey_inputs[input_hotkey_name] = [
            input_hotkey_value,
            input_hotkey_shortcut,
        ]

        # Add to grid layout with proper spacing
        self.grid_layout.addWidget(delete_button, row, 0, 1, 1, alignment=Qt.AlignCenter)
        self.grid_layout.addWidget(index_label, row, 1, 1, 1, alignment=Qt.AlignCenter)
        self.grid_layout.addWidget(input_hotkey_name, row, 2, 1, 1)
        # Column 3 is spacer
        self.grid_layout.addWidget(input_hotkey_value, row, 4, 1, 1)
        # Column 5 is spacer  
        self.grid_layout.addWidget(input_hotkey_shortcut, row, 6, 1, 1)

    def add_row(self):
        """Add new row"""
        next_index = len(self.hotkeys) + 1
        new_action = f"Custom Hotkey {next_index - 4}"  # Subtract 4 system presets
        self.hotkeys[new_action] = ["", ""]
        # Calculate the correct row: row_count (header row + 1) + existing hotkeys count
        current_row = self.row_count + len(self.hotkeys) - 1
        self.add_row_to_grid(current_row, new_action, "", "", False)

    def delete_row(self, row):
        """Delete specified row"""
        # Find the hotkey name corresponding to the row to be deleted
        row_widgets = []
        for col in range(self.grid_layout.columnCount()):
            item = self.grid_layout.itemAtPosition(row, col)
            if item is not None:
                widget = item.widget()
                if widget:
                    row_widgets.append(widget)
        
        if not row_widgets:
            return
            
        # Get hotkey name from the name input field (column 2)
        name_widget = None
        for col in range(self.grid_layout.columnCount()):
            item = self.grid_layout.itemAtPosition(row, col)
            if item is not None:
                widget = item.widget()
                if isinstance(widget, QLineEdit) and col == 2:  # Name column
                    name_widget = widget
                    break
        
        if name_widget is None:
            return
            
        hotkey_name = name_widget.text()
        
        # Remove from data structure
        if hotkey_name in self.hotkeys:
            self.hotkeys.pop(hotkey_name)
        
        # Remove from input controls dictionary
        if name_widget in self.hotkey_inputs:
            self.hotkey_inputs.pop(name_widget)
        
        # Delete interface controls
        for widget in row_widgets:
            self.grid_layout.removeWidget(widget)
            widget.deleteLater()
        
        # Rebuild grid (simpler and more reliable)
        self.rebuild_grid()

    def rebuild_grid(self):
        """Rebuild grid"""
        # Clear input controls dictionary
        self.hotkey_inputs.clear()
        
        # Clear all widgets from grid layout
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Re-add headers
        self.add_headers()
        
        # Re-populate data
        self.populate_grid()
        
    def update_hotkeys(self):
        """Update hotkeys data"""
        new_hotkeys = {}
        for name_input, (value_input, shortcut_input) in list(self.hotkey_inputs.items()):
            if name_input is not None:
                try:
                    if name_input.isVisible():
                        name = name_input.text().strip()
                        if name:  # Only save hotkeys with names
                            value = value_input.text() if value_input is not None and value_input.isVisible() else ""
                            shortcut = shortcut_input.keySequence().toString() if shortcut_input is not None and shortcut_input.isVisible() else ""
                            new_hotkeys[name] = [value, shortcut]
                except RuntimeError:
                    # Handle case where controls have been deleted
                    continue
        self.hotkeys = new_hotkeys
        
    def update_config(self):
        """Update configuration file"""
        self.update_hotkeys()
        
        # Clear existing config sections
        sections_to_remove = ["Hotkeys", "HotkeyValues", "HotkeyShortcuts"]
        for section in sections_to_remove:
            if self.config.has_section(section):
                self.config.remove_section(section)
        
        # Recreate config sections
        for section in sections_to_remove:
            self.config.add_section(section)
        
        # Write new configuration
        for index, (name, (value, shortcut)) in enumerate(self.hotkeys.items()):
            self.config.set("Hotkeys", f"Hotkey_{index + 1}", name)
            self.config.set("HotkeyValues", f"HotkeyValue_{index + 1}", value)
            self.config.set("HotkeyShortcuts", f"HotkeyShortcut_{index + 1}", shortcut)

        write_config(self.config, "config.ini")

    def update_parent_hotkeys(self):
        """Update parent window hotkeys"""
        if self.parent:
            self.parent.config = self.config
            if hasattr(self.parent, 'update_hotkeys_groupbox'):
                self.parent.update_hotkeys_groupbox()

    def save_hotkeys(self):
        """Save hotkeys configuration"""
        try:
            self.update_config()
            self.update_parent_hotkeys()
            self.accept()  # Close dialog and return accepted status
        except Exception as e:
            # Error handling could be added here, such as showing an error dialog
            print(f"Error saving hotkeys configuration: {e}")

    def closeEvent(self, event):
        """Close event handler"""
        # Ask whether to save changes
        reply = QDialog.Accepted  # Default to accept
        if reply == QDialog.Accepted:
            self.save_hotkeys()
        event.accept()