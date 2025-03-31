from utils.common import read_config, write_config
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QScrollArea,
    QWidget,
)


class MoreSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("More Settings")
        self.setFixedSize(400, 300)
        self.parent = parent
        self.isReconstructUI = False
        
        self.config = read_config("config.ini")
        self.layout = QVBoxLayout()

        # Scroll area setup
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Container widget for settings
        settings_container = QWidget()
        settings_layout = QVBoxLayout(settings_container)

        self.settings = dict(self.config.items("MoreSettings"))

        self.setting_inputs = {}

        # Create input fields for each setting
        for name, value in self.settings.items():
            label = QLabel(name)
            input_field = QLineEdit(value)
            settings_layout.addWidget(label)
            settings_layout.addWidget(input_field)
            self.setting_inputs[name] = input_field

        # Add the settings container to the scroll area
        scroll_area.setWidget(settings_container)

        # Add scroll area to the main layout
        self.layout.addWidget(scroll_area)

        # Add Save and Close buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(save_button)
        button_layout.addWidget(close_button)

        self.layout.addLayout(button_layout)
        self.setLayout(self.layout)

    def save_settings(self):
        # Update settings with input values
        new_settings = {
            name: input_field.text()
            for name, input_field in self.setting_inputs.items()
        }

        # Check if reconstructUI needs to be triggered
        if new_settings.get("MaxRowsOfButtonGroup") != self.settings.get("MaxRowsOfButtonGroup"):
            self.isReconstructUI = True

        # Update the config with new settings
        self.config["MoreSettings"] = new_settings
        write_config(self.config, "config.ini")
        self.parent.config = self.config

        # Reinitialize UI if needed
        if self.isReconstructUI:
            self.parent.modify_max_rows_of_button_group(int(new_settings.get("MaxRowsOfButtonGroup")))
        
        # self.close()
