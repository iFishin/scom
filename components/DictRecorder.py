import json
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QTextEdit,
    QLabel,
    QFileDialog,
    QMessageBox,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
)
from PySide6.QtCore import Qt
import utils.common as common


class DictRecorder:
    def __init__(self):
        self.data = {"Devices": [], "Commands": []}

    def add_device(self, name, status, port, baud_rate):
        device = {"name": name, "status": status, "port": port, "baud_rate": baud_rate}
        self.data["Devices"].append(device)

    def add_command(
        self,
        command,
        status,
        expected_responses,
        device,
        order,
        parameters,
        timeout,
        concurrent_strategy,
        success_actions,
        error_actions,
    ):
        cmd = {
            "command": command,
            "status": status,
            "expected_responses": expected_responses,
            "device": device,
            "order": order,
            "parameters": parameters,
            "timeout": timeout,
            "concurrent_strategy": concurrent_strategy,
            "success_actions": success_actions,
            "error_actions": error_actions,
        }
        self.data["Commands"].append(cmd)

    def save_to_file(self, file_path):
        with open(file_path, "w") as file:
            json.dump(self.data, file, indent=4)


class DictRecorderWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DictRecorder GUI")
        self.setGeometry(100, 100, 1200, 600)

        self.recorder = DictRecorder()

        # Create main widget and horizontal layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        # Left panel for execution
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout()
        self.left_panel.setLayout(self.left_layout)
        self.execute_button = QPushButton("Execute Command")
        self.execute_button.clicked.connect(self.execute_command)
        self.left_layout.addWidget(self.execute_button)
        
        # Log display panel
        self.log_label = QLabel("Execution Log")
        self.left_layout.addWidget(self.log_label)
        self.log_edit = QTextEdit()
        self.log_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.left_layout.addWidget(self.log_edit)
        
        self.main_layout.addWidget(self.left_panel, stretch=2)
       
        # Middle panel for command details
        self.middle_panel = QWidget()
        self.middle_layout = QVBoxLayout()
        self.middle_panel.setLayout(self.middle_layout)
        self.details_table = QTableWidget()
        self.details_table.setColumnCount(2)
        self.details_table.setHorizontalHeaderLabels(["Property", "Value"])
        # Set Property column to be fixed width and Value column to stretch
        self.details_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.details_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.details_table.setColumnWidth(0, 100)  # Set Property column width to 100 pixels
        self.details_table.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.details_table.itemChanged.connect(self.on_item_changed)
        self.middle_layout.addWidget(self.details_table)
        self.main_layout.addWidget(self.middle_panel, stretch=5)

        # Right panel for command list
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout()
        self.right_panel.setLayout(self.right_layout)
        
        # Add file path label
        self.file_path_label = QLabel("No file loaded")
        self.right_layout.addWidget(self.file_path_label)
        
        self.command_list = QListWidget()
        self.command_list.setDragDropMode(QListWidget.InternalMove)
        self.command_list.itemClicked.connect(self.on_list_item_clicked)
        self.right_layout.addWidget(self.command_list)

        # Button layout
        button_layout = QVBoxLayout()
        
        self.load_button = QPushButton("Load from File")
        self.load_button.clicked.connect(self.load_from_file)
        button_layout.addWidget(self.load_button)

        self.add_button = QPushButton("Add Command")
        self.add_button.clicked.connect(self.add_command)
        button_layout.addWidget(self.add_button)

        self.save_button = QPushButton("Save to File")
        self.save_button.clicked.connect(self.save_to_file)
        button_layout.addWidget(self.save_button)

        self.right_layout.addLayout(button_layout)
        self.main_layout.addWidget(self.right_panel, stretch=3)

        self.load_data()
    
    
    def execute_command(self):
        current_item = self.command_list.currentItem()
        if current_item:
            command = current_item.data(Qt.UserRole)["command"]
            # response = common.port_write
            print(command["command"])

    def load_data(self):
        for cmd in self.recorder.data["Commands"]:
            self.add_command_to_list(cmd)

    def add_command(self):
        command = {
            "command": "AT+NEWCMD",
            "status": "enabled",
            "expected_responses": ["OK"],
            "device": "DeviceA",
            "order": self.command_list.count() + 1,
            "parameters": [],
            "timeout": 1000,
            "concurrent_strategy": "parallel",
            "success_actions": [{"set_status": "disabled"}],
            "error_actions": [{"retry": 1}],
        }
        self.recorder.add_command(**command)
        self.add_command_to_list(command)

    def add_command_to_list(self, command):
        item_text = f"{command['order']}. {command['command']}"
        item = QListWidgetItem(item_text)
        item.setData(Qt.UserRole, command)
        self.command_list.addItem(item)

    def on_list_item_clicked(self, item):
        command = item.data(Qt.UserRole)
        self.show_command_details(command)

    def show_command_details(self, command):
        self.details_table.setRowCount(len(command))
        for i, (key, value) in enumerate(command.items()):
            self.details_table.setItem(i, 0, QTableWidgetItem(key))
            self.details_table.setItem(i, 1, QTableWidgetItem(str(value)))
            
    def on_item_double_clicked(self, item):
        self.details_table.blockSignals(True)
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        if item.column() == 1:  # Only for value column
            editor = QTextEdit()
            editor.setMinimumHeight(100)
            editor.setFixedHeight(100)
            editor.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            editor.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.details_table.setCellWidget(item.row(), item.column(), editor)
            editor.setText(item.text())
            
            # Add focusOut event handling
            def finish_editing():
                content = editor.toPlainText()
                self.details_table.removeCellWidget(item.row(), item.column())
                new_item = QTableWidgetItem(content)
                self.details_table.setItem(item.row(), item.column(), new_item)
                self.on_item_changed(new_item)
            
            editor.focusOutEvent = lambda e: finish_editing()
            editor.setFocus()
            
        self.details_table.blockSignals(False)

    def update_cell_content(self, row, column, editor):
        item = QTableWidgetItem(editor.toPlainText())
        self.details_table.setItem(row, column, item)

    def on_item_changed(self, item):
        if item.column() == 1:  # Only process changes in the value column
            current_item = self.command_list.currentItem()
            if current_item:
                command = current_item.data(Qt.UserRole)
                property_name = self.details_table.item(item.row(), 0).text()
                new_value = item.text()
                
                # Convert string to appropriate type
                if isinstance(command[property_name], bool):
                    new_value = new_value.lower() == 'true'
                elif isinstance(command[property_name], int):
                    new_value = int(new_value)
                elif isinstance(command[property_name], list):
                    new_value = json.loads(new_value)
                
                command[property_name] = new_value
                current_item.setData(Qt.UserRole, command)

    def save_to_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "JSON Files (*.json)")
    def save_to_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "JSON Files (*.json)")
        if file_path:
            self.recorder.save_to_file(file_path)
            QMessageBox.information(self, "Success", "File saved successfully!")

    def load_from_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "JSON Files (*.json)")
        if file_path:
            with open(file_path, 'r') as file:
                self.recorder.data = json.load(file)
                self.command_list.clear()
                self.load_data()
                self.file_path_label.setText(file_path)
if __name__ == "__main__":
    app = QApplication([])
    window = DictRecorderWindow()
    window.show()
    app.exec()