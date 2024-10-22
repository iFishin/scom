from PySide6.QtWidgets import QDialog, QGridLayout, QLabel, QCheckBox, QPushButton
from PySide6.QtCore import Qt
import configparser


class LayoutConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Layout Configuration")
        self.parent = parent

        # Create layout
        layout = QGridLayout()

        # Configure layout for parent widget
        layout.setHorizontalSpacing(20)
        layout.setVerticalSpacing(10)
        
        self.label_settings_box = QLabel("Settings")
        self.checkbox_settings_box = QCheckBox()
        self.checkbox_settings_box.setChecked(True)
        self.checkbox_settings_box.stateChanged.connect(self.checkbox_settings_box_stateChanged)
        
        self.label_command_box = QLabel("Command")
        self.checkbox_command_box = QCheckBox()
        self.checkbox_command_box.setChecked(True)
        self.checkbox_command_box.stateChanged.connect(self.checkbox_command_box_stateChanged)
        
        self.label_file_box = QLabel("File")
        self.checkbox_file_box = QCheckBox()
        self.checkbox_file_box.setChecked(True)
        self.checkbox_file_box.stateChanged.connect(self.checkbox_file_box_stateChanged)
        
        self.label_hotkeys_box = QLabel("Hotkeys")
        self.checkbox_hotkeys_box = QCheckBox()
        self.checkbox_hotkeys_box.setChecked(True)
        self.checkbox_hotkeys_box.stateChanged.connect(self.checkbox_hotkeys_box_stateChanged)
        
        self.label_data_received_box = QLabel("Data Received")
        self.checkbox_data_received_box = QCheckBox()
        self.checkbox_data_received_box.setChecked(True)
        self.checkbox_data_received_box.stateChanged.connect(self.checkbox_data_received_box_stateChanged)
        
        self.label_button_group_box = QLabel("Button Group")
        self.checkbox_button_group_box = QCheckBox()
        self.checkbox_button_group_box.setChecked(True)
        self.checkbox_button_group_box.stateChanged.connect(self.checkbox_button_group_box_stateChanged)
        
        layout.addWidget(self.label_settings_box, 0, 0, 1, 1, alignment=Qt.AlignCenter)
        layout.addWidget(self.checkbox_settings_box, 0, 1, 1, 1, alignment=Qt.AlignCenter)
        layout.addWidget(self.label_command_box, 1, 0, 1, 1, alignment=Qt.AlignCenter)
        layout.addWidget(self.checkbox_command_box, 1, 1, 1, 1, alignment=Qt.AlignCenter)
        layout.addWidget(self.label_file_box, 2, 0, 1, 1, alignment=Qt.AlignCenter)
        layout.addWidget(self.checkbox_file_box, 2, 1, 1, 1, alignment=Qt.AlignCenter)
        layout.addWidget(self.label_hotkeys_box, 3, 0, 1, 1, alignment=Qt.AlignCenter)
        layout.addWidget(self.checkbox_hotkeys_box, 3, 1, 1, 1, alignment=Qt.AlignCenter)
        layout.addWidget(self.label_data_received_box, 4, 0, 1, 1, alignment=Qt.AlignCenter)
        layout.addWidget(self.checkbox_data_received_box, 4, 1, 1, 1, alignment=Qt.AlignCenter)
        layout.addWidget(self.label_button_group_box, 5, 0, 1, 1, alignment=Qt.AlignCenter)
        layout.addWidget(self.checkbox_button_group_box, 5, 1, 1, 1, alignment=Qt.AlignCenter)
        
        # Add OK and Cancel buttons
        self.ok_button = QPushButton("Apply")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel")
        layout.addWidget(self.ok_button, 8, 0, 1, 1)
        layout.addWidget(self.cancel_button, 8, 1, 1, 1)

        # Set dialog layout
        self.setLayout(layout)

        # Connect buttons to functions
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
    
    def checkbox_settings_box_stateChanged(self, state):
        self.parent.settings_groupbox.setVisible(state)
    
    def checkbox_command_box_stateChanged(self, state):
        self.parent.command_groupbox.setVisible(state)
        
    def checkbox_file_box_stateChanged(self, state):
        self.parent.file_groupbox.setVisible(state)
        
    def checkbox_hotkeys_box_stateChanged(self, state):
        self.parent.hotkeys_groupbox.setVisible(state)
    
    def checkbox_data_received_box_stateChanged(self, state):
        self.parent.received_data_groupbox.setVisible(state)
    
    def checkbox_button_group_box_stateChanged(self, state):
        for i in range(self.parent.right_layout.count()):
            widget = self.parent.right_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(state)

    def accept(self):
        config = configparser.ConfigParser()
        config.read("config.ini")
        config["LayoutConfig"]["settings"] = str(self.checkbox_settings_box.isChecked())
        config["LayoutConfig"]["command"] = str(self.checkbox_command_box.isChecked())
        config["LayoutConfig"]["file"] = str(self.checkbox_file_box.isChecked())
        config["LayoutConfig"]["hotkeys"] = str(self.checkbox_hotkeys_box.isChecked())
        config["LayoutConfig"]["data_received"] = str(self.checkbox_data_received_box.isChecked())
        config["LayoutConfig"]["button_group"] = str(self.checkbox_button_group_box.isChecked())
        with open("config.ini", "w") as configfile:
            config.write(configfile)
        super().accept()
        
    def apply(self):
        config = configparser.ConfigParser()
        config.read("config.ini")
        self.checkbox_settings_box.setChecked(config.getboolean("LayoutConfig", "settings"))
        self.checkbox_command_box.setChecked(config.getboolean("LayoutConfig", "command"))
        self.checkbox_file_box.setChecked(config.getboolean("LayoutConfig", "file"))
        self.checkbox_hotkeys_box.setChecked(config.getboolean("LayoutConfig", "hotkeys"))
        self.checkbox_data_received_box.setChecked(config.getboolean("LayoutConfig", "data_received"))
        self.checkbox_button_group_box.setChecked(config.getboolean("LayoutConfig", "button_group"))
        self.accept()
        
    def cancel(self):
        config = configparser.ConfigParser()
        config.read("config.ini")
        self.checkbox_settings_box.setChecked(config.getboolean("LayoutConfig", "settings"))
        self.checkbox_command_box.setChecked(config.getboolean("LayoutConfig", "command"))
        self.checkbox_file_box.setChecked(config.getboolean("LayoutConfig", "file"))
        self.checkbox_hotkeys_box.setChecked(config.getboolean("LayoutConfig", "hotkeys"))
        self.checkbox_data_received_box.setChecked(config.getboolean("LayoutConfig", "data_received"))
        self.checkbox_button_group_box.setChecked(config.getboolean("LayoutConfig", "button_group"))
        self.accept()
        
    def closeEvent(self, event):
        self.cancel()
        event.accept()