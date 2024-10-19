import os
import sys
import io
import re
import time
import json
import serial
import random
import logging
import configparser
import threading
import datetime
from PySide6 import QtCore, QtWidgets, QtGui

from serial.tools import list_ports
import utils.common as common
from scom.QSSLoader import QSSLoader
from scom.DataReceiver import DataReceiver
from scom.PortUpdater import PortUpdater
from scom.FileSender import FileSender
from scom.CommandExecutor import CommandExecutor
from scom.SearchReplaceDialog import SearchReplaceDialog
from scom.LayoutConifgDialog import LayoutConfigDialog


class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.init_UI()
        
        # After init the UI, set the layout of the widget
        if not os.path.exists("config.ini"):
            self.create_default_config()
        self.layout_config_dialog = LayoutConfigDialog(self)
        self.layout_config_dialog.apply()
        
        # Init constants for the widget
        self.prompt_index = 0
        self.total_times = 0
        self.is_stop_batch = False
        
        
        # Read and apply the Configurations of SCOM from the config.ini
        self.config = self.read_config()
        self.apply_config(self.config)

        self.thread_pool = QtCore.QThreadPool()
        # Init the thread
        self.port_updater = PortUpdater()
        self.port_updater.portUpdated.connect(self.port_update)
        self.port_update_thread = QtCore.QThread()
        self.port_updater.moveToThread(self.port_update_thread)
        self.port_update_thread.started.connect(self.port_updater.run)
        self.port_update_thread.finished.connect(self.port_updater.deleteLater)
        self.port_update_thread.start()

        self.data_receiver = DataReceiver(None)
        self.data_receiver.dataReceived.connect(self.update_main_textarea)
        self.data_receive_thread = QtCore.QThread()
        self.data_receiver.moveToThread(self.data_receive_thread)
        self.data_receive_thread.started.connect(self.data_receiver.run)
        self.data_receive_thread.finished.connect(self.data_receiver.deleteLater)
        self.data_receiver.exceptionOccurred.connect(self.port_off)
        self.data_receive_thread.start()
        self.data_receiver.pause_thread()
        
        self.command_executor = None


    """
    Summary:
         Initialize the UI of the widget.
    """
    def init_UI(self):
        # Create menu bar
        self.menu_bar = QtWidgets.QMenuBar()

        # Create Settings menu
        self.settings_menu = self.menu_bar.addMenu("Settings")
        
        self.save_settings_action = self.settings_menu.addAction("Save Config")
        self.save_settings_action.triggered.connect(self.save_config)
        self.layout_config_action = self.settings_menu.addAction("Layout Config")
        self.layout_config_action.triggered.connect(self.layout_config)


        # Create About menu
        self.about_menu = self.menu_bar.addMenu("About")
        
        self.about_menu_action = self.about_menu.addAction("About")
        self.about_menu_action.triggered.connect(self.show_about_info)

        # Create Exit menu
        self.exit_menu = self.menu_bar.addMenu("help?")

        # Create a flag to indicate whether the thread should stop
        self.stop_ports_update_thread = False
        self.stop_textarea_update_thread = True

        self.serial_port_label = QtWidgets.QLabel("Port:")
        self.serial_port_combo = QtWidgets.QComboBox()
        self.serial_port_combo.addItems([port.device for port in list_ports.comports()])

        self.baud_rate_label = QtWidgets.QLabel("BaudRate:")
        self.baud_rate_combo = QtWidgets.QComboBox()
        self.baud_rate_combo.addItems(
            [
                    "50",
                    "75",
                    "110",
                    "134",
                    "150",
                    "200",
                    "300",
                    "600",
                    "1200",
                    "1800",
                    "2400",
                    "4800",
                    "9600",
                    "19200",
                    "38400",
                    "57600",
                    "115200",
                    "230400",
                    "460800",
                    "500000",
                    "576000",
                    "921600",
                    "1000000",
                    "1152000",
                    "1500000",
                    "2000000",
                    "2500000",
                    "3000000",
                    "3500000",
                    "4000000",
            ]
        )
        self.baud_rate_combo.setCurrentText("115200")
        self.stopbits_label = QtWidgets.QLabel("StopBits:")
        self.stopbits_combo = QtWidgets.QComboBox()
        self.stopbits_combo.addItems(["1", "1.5", "2"])
        self.stopbits_combo.setCurrentText("1")

        self.parity_label = QtWidgets.QLabel("Parity:")
        self.parity_combo = QtWidgets.QComboBox()
        self.parity_combo.addItems(["None", "Even", "Odd", "Mark", "Space"])
        self.parity_combo.setCurrentText("None")

        self.bytesize_label = QtWidgets.QLabel("ByteSize:")
        self.bytesize_combo = QtWidgets.QComboBox()
        self.bytesize_combo.addItems(["5", "6", "7", "8"])
        self.bytesize_combo.setCurrentText("8")

        self.flowcontrol_label = QtWidgets.QLabel("FlowControl:")
        self.flowcontrol_checkbox = QtWidgets.QComboBox()
        self.flowcontrol_checkbox.addItems(["None", "RTS/CTS", "XON/XOFF"])
        self.flowcontrol_checkbox.setCurrentText("None")
        
        self.dtr_label = QtWidgets.QLabel("DTR:")
        self.dtr_checkbox = QtWidgets.QCheckBox()
        self.dtr_checkbox.stateChanged.connect(self.dtr_state_changed)
        
        self.rts_label = QtWidgets.QLabel("RTS:")
        self.rts_checkbox = QtWidgets.QCheckBox()
        self.rts_checkbox.stateChanged.connect(self.rts_state_changed)
        
        self.label_send_with_enter = QtWidgets.QLabel("SendWithEnter:")
        self.checkbox_send_with_enter = QtWidgets.QCheckBox()
        self.checkbox_send_with_enter.setChecked(True)
        
        self.symbol_label = QtWidgets.QLabel("Show\\r\\n:")
        self.symbol_checkbox = QtWidgets.QCheckBox()
        self.symbol_checkbox.stateChanged.connect(self.symbol_state_changed)
        
        self.timeStamp_label = QtWidgets.QLabel("TimeStamp:")
        self.timeStamp_checkbox = QtWidgets.QCheckBox()
        self.timeStamp_checkbox.stateChanged.connect(self.timeStamp_state_changed)
        
        self.label_data_received = QtWidgets.QLabel("Data Received:")
        self.input_path_data_received = QtWidgets.QLineEdit()
        self.input_path_data_received.setText(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmps/temp.log"))
        self.input_path_data_received.setReadOnly(True)
        self.input_path_data_received.mouseDoubleClickEvent = self.set_default_received_file
        self.checkbox_data_received = QtWidgets.QCheckBox()
        self.checkbox_data_received.stateChanged.connect(self.handle_data_received_checkbox)
        self.button_data_received_select = QtWidgets.QPushButton("Select")
        self.button_data_received_select.clicked.connect(self.select_received_file)
        self.button_data_received_save = QtWidgets.QPushButton("Save")
        self.button_data_received_save.clicked.connect(self.save_received_file)

        self.port_button = QtWidgets.QPushButton("Open Port")
        self.port_button.clicked.connect(self.port_on)

        self.toggle_button = QtWidgets.QPushButton()
        self.toggle_button.setToolTip("Show More Options")
        self.toggle_button.setIcon(QtGui.QIcon("./res/expander-down.png"))
        self.toggle_button_is_expanded = False
        self.toggle_button.clicked.connect(self.show_more_options)
        
        self.status_label = QtWidgets.QLabel("Closed")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        self.status_label.setStyleSheet(
            "QLabel { color: #198754; border: 2px solid white; border-radius: 10px; padding: 10px; font-size: 20px; font-weight: bold; }"
        )

        self.command_label = QtWidgets.QLabel("Command:")
        self.command_input = QtWidgets.QTextEdit()
        self.command_input.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)
        self.command_input.setFixedHeight(30)
        self.command_input.setAcceptRichText(False)
        # self.command_input.keyPressEvent = self.handle_key_press  # 重写 keyPressEvent 方法
        
        self.file_label = QtWidgets.QLabel("File:")
        self.file_input = QtWidgets.QLineEdit()
        self.file_input.setToolTip("Double click to Clear")
        self.file_input.mouseDoubleClickEvent = lambda event: self.file_input.clear()
        self.file_input.setPlaceholderText("Path")
        self.file_input.setReadOnly(True)
        self.file_button_select = QtWidgets.QPushButton("Select")
        self.file_button_select.clicked.connect(self.select_file)        
        self.file_button_send = QtWidgets.QPushButton("Send")
        self.file_button_send.clicked.connect(self.send_file)
        
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        
        # Create a button for expanding/collapsing the input field
        self.expand_button = QtWidgets.QPushButton()
        self.expand_button.setIcon(
            QtGui.QIcon("./res/expand.png")
        )  # You need to have an icon for this
        self.expand_button.setCheckable(True)
        self.expand_button.setChecked(False)
        self.expand_button.clicked.connect(self.expand_command_input)

        self.send_button = QtWidgets.QPushButton("Send")
        self.send_button.setEnabled(False)
        self.send_button.clicked.connect(self.send_command)

        self.hotkeys_buttons = []
        for i in range(1, 9):
            button = QtWidgets.QPushButton(f"Hotkey {i}")
            button.clicked.connect(self.handle_hotkey_click(i))
            self.hotkeys_buttons.append(button)

        self.received_data_textarea = QtWidgets.QTextEdit()
        self.received_data_textarea.setAcceptRichText(False)
        self.received_data_textarea.setDocument(QtGui.QTextDocument(None))
        shortcut = QtGui.QShortcut(QtCore.Qt.ControlModifier | QtCore.Qt.Key_F, self)
        shortcut.activated.connect(self.show_search_dialog)
        # self.received_data_textarea.setReadOnly(True)

        # Create a group box for the settings section
        self.settings_groupbox = QtWidgets.QGroupBox("Settings")
        settings_layout = QtWidgets.QGridLayout(self.settings_groupbox)
        settings_layout.addWidget(self.serial_port_label, 0, 0, 1, 1, alignment=QtCore.Qt.AlignRight)
        settings_layout.addWidget(self.serial_port_combo, 0, 1, 1, 1)
        settings_layout.addWidget(self.baud_rate_label, 1, 0, 1, 1, alignment=QtCore.Qt.AlignRight)
        settings_layout.addWidget(self.baud_rate_combo, 1, 1, 1, 1)
        settings_layout.addWidget(self.port_button, 0, 2, 1, 2)
        settings_layout.addWidget(self.status_label, 1, 2, 1, 1)
        settings_layout.addWidget(self.toggle_button, 1, 3, 1, 1)
        
        self.settings_more_layout = QtWidgets.QGridLayout()

        self.settings_more_layout.addWidget(self.stopbits_label, 0, 0, 1, 1, alignment=QtCore.Qt.AlignRight)
        self.settings_more_layout.addWidget(self.stopbits_combo, 0, 1, 1, 1)
        self.settings_more_layout.addWidget(self.parity_label, 0, 2, 1, 1, alignment=QtCore.Qt.AlignRight)
        self.settings_more_layout.addWidget(self.parity_combo, 0, 3, 1, 1)
        self.settings_more_layout.addWidget(self.bytesize_label, 1, 0, 1, 1, alignment=QtCore.Qt.AlignRight)
        self.settings_more_layout.addWidget(self.bytesize_combo, 1, 1, 1, 1)
        self.settings_more_layout.addWidget(self.flowcontrol_label, 1, 2, 1, 1, alignment=QtCore.Qt.AlignRight)
        self.settings_more_layout.addWidget(self.flowcontrol_checkbox, 1, 3, 1, 1)
        
        self.settings_more_layout.addWidget(self.dtr_label, 2, 0, 1, 1, alignment=QtCore.Qt.AlignRight)
        self.settings_more_layout.addWidget(self.dtr_checkbox, 2, 1, 1, 1)
        self.settings_more_layout.addWidget(self.rts_label, 2, 2, 1, 1, alignment=QtCore.Qt.AlignRight)
        self.settings_more_layout.addWidget(self.rts_checkbox, 2, 3, 1, 1)
        self.settings_more_layout.addWidget(self.symbol_label, 3, 0, 1, 1, alignment=QtCore.Qt.AlignRight)
        self.settings_more_layout.addWidget(self.symbol_checkbox, 3, 1, 1, 1)
        self.settings_more_layout.addWidget(self.timeStamp_label, 3, 2, 1, 1, alignment=QtCore.Qt.AlignRight)
        self.settings_more_layout.addWidget(self.timeStamp_checkbox, 3, 3, 1, 1)
        self.settings_more_layout.addWidget(self.label_send_with_enter, 4, 0, 1, 1, alignment=QtCore.Qt.AlignRight)
        self.settings_more_layout.addWidget(self.checkbox_send_with_enter, 4, 1, 1, 1)

        self.settings_more_layout.addWidget(self.label_data_received, 5, 0, 1, 1)
        self.settings_more_layout.addWidget(self.input_path_data_received, 5, 1, 1, 2)
        self.settings_more_layout.addWidget(self.checkbox_data_received, 5, 3, 1, 1)
        self.settings_more_layout.addWidget(self.button_data_received_select, 6, 0, 1, 2)
        self.settings_more_layout.addWidget(self.button_data_received_save, 6, 2, 1, 2)
        
        settings_layout.addLayout(self.settings_more_layout, 2, 0, 1, 4)
        
        # Set the button to be invisible
        for i in range(self.settings_more_layout.count()):
            self.settings_more_layout.itemAt(i).widget().setVisible(False)

        # Create a group box for the command section
        self.command_groupbox = QtWidgets.QGroupBox("Command")
        command_layout = QtWidgets.QHBoxLayout(self.command_groupbox)
        command_layout.addWidget(self.command_label)
        command_layout.addWidget(self.command_input)
        command_layout.addWidget(self.expand_button)
        command_layout.addWidget(self.send_button)
        
        # Create a group box for the file section
        self.file_groupbox = QtWidgets.QGroupBox("File")
        file_layout = QtWidgets.QVBoxLayout(self.file_groupbox)
        file_row_layout = QtWidgets.QHBoxLayout()
        file_row_layout.addWidget(self.file_label)
        file_row_layout.addWidget(self.file_input)
        file_row_layout.addWidget(self.file_button_select)
        file_row_layout.addWidget(self.file_button_send)
        file_progress_layout = QtWidgets.QHBoxLayout()
        file_progress_layout.addWidget(self.progress_bar)
        file_layout.addLayout(file_row_layout)
        file_layout.addLayout(file_progress_layout)
        
        # Create a group box for the Hotkeys section
        self.hotkeys_groupbox = QtWidgets.QGroupBox("Hotkeys")
        hotkeys_layout = QtWidgets.QGridLayout(self.hotkeys_groupbox)
        for i, button in enumerate(self.hotkeys_buttons):
            row = i // 4
            col = i % 4
            hotkeys_layout.addWidget(button, row, col)

        # Create a group box for the received data section
        self.received_data_groupbox = QtWidgets.QGroupBox("Received Data")
        received_data_layout = QtWidgets.QVBoxLayout(self.received_data_groupbox)
        received_data_layout.addWidget(self.received_data_textarea)

        # Create a group box for the button group section
        self.button_groupbox = QtWidgets.QGroupBox("Button Group")
        button_layout = QtWidgets.QGridLayout(self.button_groupbox)
        # button_layout.setColumnStretch(2, 2)

        # Create a scroll area for the button group
        button_scroll_area = QtWidgets.QScrollArea()
        button_scroll_area.setWidget(self.button_groupbox)
        button_scroll_area.setWidgetResizable(True)
        button_scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        QtCore.QTimer.singleShot(0, lambda: button_scroll_area.verticalScrollBar().setValue(self.settings_button_group.height()))

        # Add setting area for the button group
        self.settings_button_group = QtWidgets.QGroupBox()
        settings_button_layout = QtWidgets.QGridLayout(self.settings_button_group)
        settings_button_layout.setColumnStretch(1, 3)
        
        self.prompt_button = QtWidgets.QPushButton("Prompt")
        self.prompt_button.setToolTip("Left button clicked to Execute; Right button clicked to Switch Next")
        self.prompt_button.setStyleSheet(
            "QPushButton { width: 100%; color: white; background-color: #198754; border: 4px solid white; border-radius: 10px; padding: 10px; font-size: 20px; font-weight: bold; }"
            "QPushButton:hover { background-color: #0d6e3f; }"
            "QPushButton:pressed { background-color: #0a4c2b; }"
        )
        self.prompt_button.installEventFilter(self)
        
        self.input_prompt = QtWidgets.QLineEdit()
        self.input_prompt.setPlaceholderText("COMMAND: click the LEFT BUTTON to start")
        self.input_prompt.setStyleSheet(
            "QLineEdit { color: #198754; border: 2px solid white; border-radius: 10px; padding: 10px; font-size: 20px; font-weight: bold; }"
            )
        
        self.input_prompt_index = QtWidgets.QLineEdit()
        self.input_prompt_index.setPlaceholderText("Idx")
        self.input_prompt_index.setToolTip("Double click to edit")
        self.input_prompt_index.setStyleSheet(
            "QLineEdit { color: #198754; border: 2px solid white; border-radius: 10px; padding: 10px; font-size: 20px; font-weight: bold; }"
            )
        self.input_prompt_index.setReadOnly(True)
        self.input_prompt_index.setMaximumWidth(self.width() * 0.1)
        self.input_prompt_index.mouseDoubleClickEvent = lambda event: self.input_prompt_index.setReadOnly(False)
        self.input_prompt_index.editingFinished.connect(self.set_prompt_index)
        
        self.prompt_batch_start_button = QtWidgets.QPushButton("Start")
        self.prompt_batch_start_button.setStyleSheet(
            "QPushButton { width: 100%; color: white; background-color: #198754; border: 4px solid white; border-radius: 10px; padding: 10px; font-size: 20px; font-weight: bold; }"
            "QPushButton:hover { background-color: #0d6e3f; }"
            "QPushButton:pressed { background-color: #0a4c2b; }"
        )
        
        self.prompt_batch_start_button.clicked.connect(self.handle_prompt_batch_start)
        
        self.prompt_batch_stop_button = QtWidgets.QPushButton("Stop")
        self.prompt_batch_stop_button.setStyleSheet(
            "QPushButton { width: 100%; color: white; background-color: #dc3545; border: 4px solid white; border-radius: 10px; padding: 10px; font-size: 20px; font-weight: bold; }"
            "QPushButton:hover { background-color: #a71d2a; }"
            "QPushButton:pressed { background-color: #7b1520; }"
        )
        
        self.prompt_batch_stop_button.clicked.connect(self.handle_prompt_batch_stop)
        
        self.input_prompt_batch_times = QtWidgets.QLineEdit()
        self.input_prompt_batch_times.setPlaceholderText("Total Times")
        self.input_prompt_batch_times.setStyleSheet(
                "QLineEdit { color: #198754; border: 2px solid white; border-radius: 10px; padding: 10px; font-size: 20px; font-weight: bold; }"
            )

        settings_button_layout.addWidget(self.prompt_button, 0, 0, 1, 1)
        settings_button_layout.addWidget(self.input_prompt, 0, 1, 1, 4)
        settings_button_layout.addWidget(self.input_prompt_index, 0, 5, 1, 1)
        settings_button_layout.addWidget(self.prompt_batch_start_button, 1, 0, 1, 1)
        settings_button_layout.addWidget(self.input_prompt_batch_times, 1, 1, 1, 3,)
        settings_button_layout.addWidget(self.prompt_batch_stop_button, 1, 4, 1, 2)
        button_layout.addWidget(self.settings_button_group, 0, 0, 1, 5)

        # Set the input field to expand horizontally
        self.input_prompt.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)

        # Add column titles
        self.total_checkbox = QtWidgets.QCheckBox()
        button_layout.addWidget(self.total_checkbox, 1, 0)
        self.total_checkbox.stateChanged.connect(self.handle_total_checkbox_click)
        label_function = QtWidgets.QLabel("Function")
        label_input_field = QtWidgets.QLabel("Input Field")
        label_enter = QtWidgets.QLabel("Enter")
        label_sec = QtWidgets.QLabel("Sec")
        label_sec.setToolTip("Double click to Clear")
        label_sec.mouseDoubleClickEvent = self.set_interval
        button_layout.addWidget(label_function, 1, 1, alignment=QtCore.Qt.AlignCenter)
        button_layout.addWidget(label_input_field, 1, 2, alignment=QtCore.Qt.AlignCenter)
        button_layout.addWidget(label_enter, 1, 3, alignment=QtCore.Qt.AlignCenter)
        button_layout.addWidget(label_sec, 1, 4, alignment=QtCore.Qt.AlignRight)

        # Add buttons and input fields to the button group
        self.checkbox = []
        self.buttons = []
        self.input_fields = []
        self.checkbox_send_with_enters = []
        self.interVal = []
        for i in range(1, 101):
            # Create a combobox for selecting the function
            checkbox = QtWidgets.QCheckBox()
            label = f"Func {i}"
            button = QtWidgets.QPushButton(label)
            input_field = QtWidgets.QLineEdit()
            
            checkbox_send_with_enter = QtWidgets.QCheckBox()
            checkbox_send_with_enter.setChecked(True)
            input_interval = QtWidgets.QLineEdit()
            input_interval.setMaximumWidth(self.width() * 0.06)
            input_interval.setValidator(QtGui.QIntValidator(0, 1000))
            input_interval.setPlaceholderText("sec")
            input_interval.setAlignment(QtCore.Qt.AlignCenter)
            button_layout.addWidget(checkbox, i+1, 0)
            button_layout.addWidget(button, i+1, 1)
            button_layout.addWidget(input_field, i+1, 2)
            button_layout.addWidget(checkbox_send_with_enter, i+1, 3)
            button_layout.addWidget(input_interval, i+1, 4)
            self.checkbox.append(checkbox)
            self.buttons.append(button)
            self.input_fields.append(input_field)
            self.checkbox_send_with_enters.append(checkbox_send_with_enter)
            self.interVal.append(input_interval)
            button.setEnabled(False)
            input_field.returnPressed.connect(
            self.handle_button_click(i, self.input_fields[i - 1], self.checkbox[i - 1], self.checkbox_send_with_enters[i - 1], self.interVal[i - 1])
            )
            button.clicked.connect(
            self.handle_button_click(i, self.input_fields[i - 1], self.checkbox[i - 1], self.checkbox_send_with_enters[i - 1], self.interVal[i - 1])
            )

        # Create a layout for the left half
        self.left_layout = QtWidgets.QVBoxLayout()
        self.left_layout.addWidget(self.settings_groupbox)
        self.left_layout.addWidget(self.command_groupbox)
        self.left_layout.addWidget(self.file_groupbox)
        self.left_layout.addWidget(self.hotkeys_groupbox)
        self.left_layout.addWidget(self.received_data_groupbox)

        self.right_layout = QtWidgets.QVBoxLayout()
        self.right_layout.addWidget(button_scroll_area)
        
        # Create a layout_1 for the widget
        layout_1 = QtWidgets.QHBoxLayout()
        layout_1.addLayout(self.left_layout)
        layout_1.addLayout(self.right_layout)

        layout_2 = QtWidgets.QVBoxLayout()
        self.label_layout_2 = QtWidgets.QLabel("ATCommand")
        self.text_input_layout_2 = QtWidgets.QTextEdit()
        self.text_input_layout_2.setDocument(QtGui.QTextDocument(None))
        self.text_input_layout_2.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        layout_2.addWidget(self.label_layout_2)
        layout_2.addWidget(self.text_input_layout_2)
        self.text_input_layout_2.setStyleSheet(
            "QTextEdit { height: 100%; width: 100%; font-size: 24px; font-weight: 600; }"
        )
        self.text_input_layout_2.setAcceptRichText(False)

        layout_3 = QtWidgets.QVBoxLayout()
        self.label_layout_3 = QtWidgets.QLabel("temp.log")
        self.text_input_layout_3 = QtWidgets.QTextEdit()
        self.text_input_layout_3.setDocument(QtGui.QTextDocument(None))
        self.text_input_layout_3.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        layout_3.addWidget(self.label_layout_3)
        layout_3.addWidget(self.text_input_layout_3)
        self.text_input_layout_3.setStyleSheet(
            "QTextEdit { height: 100%; width: 100%; font-size: 24px; font-weight: bold; }"
        )
        self.text_input_layout_3.setAcceptRichText(False)
        
        layout_4 = QtWidgets.QVBoxLayout()
        self.label_layout_4 = QtWidgets.QLabel("No TimeStamp")
        self.text_input_layout_4 = QtWidgets.QTextEdit()
        self.text_input_layout_4.setDocument(QtGui.QTextDocument(None))
        self.text_input_layout_4.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        layout_4.addWidget(self.label_layout_4)
        layout_4.addWidget(self.text_input_layout_4)
        self.text_input_layout_4.setStyleSheet(
            "QTextEdit { height: 100%; width: 100%; font-size: 24px; font-weight: bold; }"
        )
        self.text_input_layout_4.setAcceptRichText(False)

        # Create a button section for switching other layouts
        self.button1 = QtWidgets.QPushButton("Window 1")
        self.button1.setToolTip("Shortcut: F1")
        self.button1.setStyleSheet(
            "QPushButton { background-color: #198754; color: white; border-radius: 3px; padding: 5px; font-size: 16px; }"
            "QPushButton:hover { background-color: #0d6e3f; }"
            "QPushButton:pressed { background-color: #0a4c2b; }"
        )
        self.button1.clicked.connect(lambda: self.show_page(0))

        self.button2 = QtWidgets.QPushButton("Window 2")
        self.button2.setToolTip("Shortcut: F2")
        self.button2.setStyleSheet(
            "QPushButton { background-color: #198754; color: white; border-radius: 3px; padding: 5px; font-size: 16px; }"
            "QPushButton:hover { background-color: #0d6e3f; }"
            "QPushButton:pressed { background-color: #0a4c2b; }"
        )
        self.button2.clicked.connect(lambda: self.show_page(1))

        self.button3 = QtWidgets.QPushButton("Window 3")
        self.button3.setToolTip("Shortcut: F3")
        self.button3.setStyleSheet(
            "QPushButton { background-color: #198754; color: white; border-radius: 3px; padding: 5px; font-size: 16px; }"
            "QPushButton:hover { background-color: #0d6e3f; }"
            "QPushButton:pressed { background-color: #0a4c2b; }"
        )
        self.button3.clicked.connect(lambda: self.show_page(2))

        self.button4 = QtWidgets.QPushButton("Window 4")
        self.button4.setToolTip("Shortcut: F4")
        self.button4.setStyleSheet(
            "QPushButton { background-color: #198754; color: white; border-radius: 3px; padding: 5px; font-size: 16px; }"
            "QPushButton:hover { background-color: #0d6e3f; }"
            "QPushButton:pressed { background-color: #0a4c2b; }"
        )
        self.button4.clicked.connect(lambda: self.show_page(3))

        button_switch_layout = QtWidgets.QHBoxLayout()
        button_switch_layout.addWidget(self.button1)
        button_switch_layout.addWidget(self.button2)
        button_switch_layout.addWidget(self.button3)
        button_switch_layout.addWidget(self.button4)
        # Create a stacked widget to switch between layouts
        self.stacked_widget = QtWidgets.QStackedWidget()
        self.stacked_widget.addWidget(QtWidgets.QWidget())
        self.stacked_widget.addWidget(QtWidgets.QWidget())
        self.stacked_widget.addWidget(QtWidgets.QWidget())
        self.stacked_widget.addWidget(QtWidgets.QWidget())

        # Set the layouts for the stacked widget
        self.stacked_widget.widget(0).setLayout(layout_1)
        self.stacked_widget.widget(1).setLayout(layout_2)
        self.stacked_widget.widget(2).setLayout(layout_3)
        self.stacked_widget.widget(3).setLayout(layout_4)
        self.stacked_widget.setCurrentIndex(0)

        # Create a main layout for the widget
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.menu_bar)
        main_layout.addLayout(button_switch_layout)
        main_layout.addWidget(self.stacked_widget)

        hotkeys_names = [
            "Clear-Log",
            "Read-ATC",
            "Update-ATC",
            "Restore-ATC",
            "Internet",
            "RST",
            "ECHO",
            ""
        ]
        for i, button in enumerate(self.hotkeys_buttons):
            if i == len(hotkeys_names):
                break
            button.setText(hotkeys_names[i])

        input_fields_values = [
            "AT+QECHO=1",
            "AT+QVERSION",
            "AT+QSUB",
            "AT+QBLEADDR?",
            "AT+QBLEINIT=1",
            "AT+QBLESCAN=1",
            "AT+QBLESCAN=0",
            "AT+QWSCAN",
            "AT+RESTORE",
            "AT+QWSCAN",
        ]
        for i in range(1, len(self.input_fields) + 1):
            if i <= len(input_fields_values):
                self.input_fields[i - 1].setText(input_fields_values[i - 1])
            else:
                break

    """
    Summary:
        The function to handle the event when the button is clicked. 
    
    """
    def read_config(self):
        config = configparser.ConfigParser()
        config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini"))
        return config
    
    def apply_config(self, config: configparser.ConfigParser):
        # Set
        self.baud_rate_combo.setCurrentText(config.get("Set", "BaudRate"))
        self.stopbits_combo.setCurrentText(config.get("Set", "StopBits"))
        self.parity_combo.setCurrentText(config.get("Set", "Parity"))
        self.bytesize_combo.setCurrentText(config.get("Set", "ByteSize"))
        self.flowcontrol_checkbox.setCurrentText(config.get("Set", "FlowControl"))
        self.dtr_checkbox.setChecked(config.getboolean("Set", "DTR"))
        self.rts_checkbox.setChecked(config.getboolean("Set", "RTS"))
        self.checkbox_send_with_enter.setChecked(config.getboolean("Set", "SendWithEnter"))
        self.symbol_checkbox.setChecked(config.getboolean("Set", "ShowSymbol"))
        self.timeStamp_checkbox.setChecked(config.getboolean("Set", "TimeStamps"))
        self.input_path_data_received.setText(config.get("Set", "PathDataReceived"))
        self.checkbox_data_received.setChecked(config.getboolean("Set", "IsSaveDataReceived"))
        self.file_input.setText(config.get("Set", "PathFileSend"))
        
        # Hotkeys
        for i in range(1, 9):
            hotkey_name = config.get("Hotkeys", f"Hotkey_{i}")
            self.hotkeys_buttons[i - 1].setText(hotkey_name)
            hotkey_value = config.get("HotkeyValues", f"HotkeyValue_{i}")
            self.hotkeys_buttons[i - 1].clicked.connect(self.handle_hotkey_click(i, hotkey_value))
    
    def save_config(self, config: configparser.ConfigParser):
        # Set
        config.set("Set", "BaudRate", self.baud_rate_combo.currentText())
        config.set("Set", "StopBits", self.stopbits_combo.currentText())
        config.set("Set", "Parity", self.parity_combo.currentText())
        config.set("Set", "ByteSize", self.bytesize_combo.currentText())
        config.set("Set", "FlowControl", self.flowcontrol_checkbox.currentText())
        config.set("Set", "DTR", str(self.dtr_checkbox.isChecked()))
        config.set("Set", "RTS", str(self.rts_checkbox.isChecked()))
        config.set("Set", "SendWithEnter", str(self.checkbox_send_with_enter.isChecked()))
        config.set("Set", "ShowSymbol", str(self.symbol_checkbox.isChecked()))
        config.set("Set", "TimeStamps", str(self.timeStamp_checkbox.isChecked()))
        config.set("Set", "PathDataReceived", self.input_path_data_received.text())
        config.set("Set", "IsSaveDataReceived", str(self.checkbox_data_received.isChecked()))
        config.set("Set", "PathFileSend", self.file_input.text())

        # Hotkeys
        # for i in range(1, 9):
        #     config.set("Hotkeys", f"Hotkey_{i}", self.hotkeys_buttons[i - 1].text())
        #     config.set("HotkeyValues", f"HotkeyValue_{i}", self.input_fields[i - 1].text())

        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini"), "w", encoding="utf-8") as configfile:
            config.write(configfile)
        
        
            
    def apply_style(self):
        text = self.received_data_textarea.toPlainText()
        doc = self.received_data_textarea.document()
        cursor = QtGui.QTextCursor(doc)

        # 使用正则表达式查找匹配的字符串
        pattern_timestamp = r"\[20(.*?)\]"
        matches_timestamp = re.finditer(pattern_timestamp, text)
        
        # pattern_ATCommand = r"AT\+[^（）\n\t\\\r]+"
        # matches_ATCommand = re.finditer(pattern_ATCommand, text)

        # for match in matches_ATCommand:
        #     start_pos = match.start()
        #     end_pos = match.end()

        #     # 设置底色和圆角
        #     cursor.setPosition(start_pos)
        #     cursor.movePosition(QtGui.QTextCursor.NextCharacter, QtGui.QTextCursor.KeepAnchor, end_pos - start_pos)
        #     char_format = cursor.charFormat()
        #     # 设置字体颜色
        #     char_format.setForeground(QtGui.QBrush(QtGui.QColor("#198754")))
        #     cursor.setCharFormat(char_format)

        for match in matches_timestamp:
            # 设置底色和圆角
            start_pos = match.start()
            end_pos = match.end()
            cursor.setPosition(start_pos)
            cursor.movePosition(QtGui.QTextCursor.NextCharacter, QtGui.QTextCursor.KeepAnchor, end_pos - start_pos)
            char_format = cursor.charFormat()
            char_format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
            char_format.setBackground(QtGui.QBrush(QtGui.QColor("#cccccc")))
            char_format.setProperty(QtGui.QTextFormat.OutlinePen, QtGui.QPen(QtGui.QColor("#cccccc")))
            
            cursor.setCharFormat(char_format)
    
    def show_page(self, index):
        if index == 1 or self.stacked_widget.currentIndex() == 1:
            if self.text_input_layout_2.toPlainText() == "":
                self.text_input_layout_2.setPlainText(common.join_text(common.read_ATCommand(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmps/ATCommand.json"))))
            else:
                common.write_ATCommand(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmps/ATCommand.json"), common.split_text(self.text_input_layout_2.toPlainText()))
        elif index == 2 or self.stacked_widget.currentIndex() == 2:
            self.text_input_layout_3.setPlainText(self.received_data_textarea.toPlainText())
        elif index == 3 or self.stacked_widget.currentIndex() == 3:
            self.text_input_layout_4.setPlainText(
                common.remove_TimeStamp(self.received_data_textarea.toPlainText())
            )
        self.stacked_widget.setCurrentIndex(index)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_F1:
            self.show_page(0)
        elif event.key() == QtCore.Qt.Key_F2:
            self.show_page(1)
        elif event.key() == QtCore.Qt.Key_F3:
            self.show_page(2)
        elif event.key() == QtCore.Qt.Key_F4:
            self.show_page(3)

    def layout_config(self):
        # LayoutConfigDialog
        self.layout_config_dialog.exec()

    def show_about_info(self):
        msg_box = QtWidgets.QMessageBox()
        msg_box.setWindowTitle("About")
        msg_box.setTextFormat(QtCore.Qt.RichText)
        msg_box.setText(
            "Repository: <a href='https://github.com/ifishin/SCOM'>SCOM</a> <br/>\
            Version: 1.0 <br/>\
            Description: Serial Communication Tool <br/>"
        )
        msg_box.setIconPixmap(QtGui.QPixmap("./favicon.ico").scaled(100, 100))
        # 设置图片样式
        msg_box.setStyleSheet(
            "QLabel { color: #198754; font-size: 20px; font-weight: bold; }"
            "QMessageBox { background-color: #cccccc; }"
        )
        msg_box.exec()

    def dtr_state_changed(self, state):
        if state == 2:
            self.data_receiver.serial_port.dtr = True
            self.main_Serial.dtr = True
        else:
            self.data_receiver.serial_port.dtr = False
            self.main_Serial.dtr = False
    
    def rts_state_changed(self, state):
        if state == 2:
            self.data_receiver.serial_port.rts = True
            self.main_Serial.rts = True
        else:
            self.data_receiver.serial_port.rts = False
            self.main_Serial.rts = False

    def symbol_state_changed(self, state):
        if state == 2:
            self.data_receiver.is_show_symbol = True
        else:
            self.data_receiver.is_show_symbol = False
            
    def timeStamp_state_changed(self, state):
        if state == 2:
            self.data_receiver.is_show_timeStamp = True
        else:
            self.data_receiver.is_show_timeStamp = False

    def show_more_options(self):
        for i in range(self.settings_more_layout.count()):
            widget = self.settings_more_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(not widget.isVisible())
        if self.toggle_button_is_expanded:
            self.toggle_button.setIcon(QtGui.QIcon("./res/expander-down.png"))
        else:
            self.toggle_button.setIcon(QtGui.QIcon("./res/fork.png"))
        self.toggle_button_is_expanded = not self.toggle_button_is_expanded
                
    def expand_command_input(self):
        self.command_input.setFixedHeight(100)
        self.command_input.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        self.expand_button.setIcon(QtGui.QIcon("./res/collapse.png"))
        self.expand_button.setChecked(True)
        self.expand_button.clicked.connect(self.collapse_command_input)
    
    def collapse_command_input(self):
        self.command_input.setFixedHeight(30)
        self.command_input.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        self.expand_button.setIcon(QtGui.QIcon("./res/expand.png"))
        self.expand_button.setChecked(False)
        self.expand_button.clicked.connect(self.expand_command_input)

    def send_command(self):
        command = self.command_input.toPlainText()        
        try:
            common.port_write(command, self.main_Serial, self.checkbox_send_with_enter.isChecked())
        except Exception as e:
            print(f"Error sending command: {e}")
            self.status_label.setText("Failed")
            self.status_label.setStyleSheet(
                "QLabel { color: #dc3545; border: 2px solid white; border-radius: 10px; padding: 10px; font-size: 20px; font-weight: bold; }"
            )
            self.port_off()
            
    def handle_data_received_checkbox(self, state):
        if state == 2:
            self.input_path_data_received.setReadOnly(False)
        else:
            self.input_path_data_received.setReadOnly(True)
        
    def save_received_file(self):
        file_path = self.input_path_data_received.text()
        if not file_path:
            QtWidgets.QMessageBox.warning(self, "Warning", "No file selected.")
            return
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.received_data_textarea.toPlainText())
        except FileNotFoundError:
            QtWidgets.QMessageBox.warning(self, "Warning", "File not found.")
        except PermissionError:
            QtWidgets.QMessageBox.warning(self, "Warning", "Permission denied to save the file.")
           
    def set_default_received_file(self, event):
        self.input_path_data_received.setText(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmps/temp.log"))
               
     
    def select_received_file(self):
        file_dialog = QtWidgets.QFileDialog()
        file_dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
        file_dialog.setNameFilter("Files (*)")
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            if file_path:
                self.input_path_data_received.setText(file_path)
        
    def select_file(self):
        file_dialog = QtWidgets.QFileDialog()
        file_dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Files (*)")
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            if file_path:
                self.file_input.setText(file_path)
            
    def send_file(self):
        file_path = self.file_input.text()
        if not file_path:
            QtWidgets.QMessageBox.warning(self, "Warning", "No file selected.")
            return
        try:
            # chunk_size = 4096  # 可以根据实际情况调整块大小
            # with open(file_path, "r", encoding="utf-8") as f:
            #     while True:
            #         chunk = f.read(chunk_size)
            #         if not chunk:
            #             break
            #         print(f"Read chunk of size: {len(chunk)}")
            #         common.port_write(chunk, self.main_Serial, False)
            self.file_sender = FileSender(file_path, self.main_Serial)
            self.file_sender.progressUpdated.connect(self.progress_bar.setValue)
            self.progress_bar.setValue(0)
            self.file_sender.start()
        except FileNotFoundError:
            QtWidgets.QMessageBox.warning(self, "Warning", "File not found.")
        except PermissionError:
            QtWidgets.QMessageBox.warning(self, "Warning", "Permission denied to open the file.")
        
    def update_progress_bar(self, progress):
        self.progress_bar.setValue(progress)
                
    def handle_key_press(self, event):
        if event.key() == QtCore.Qt.Key_Return and event.modifiers() == QtCore.Qt.ShiftModifier:
            # 处理 Shift + Enter 按下
            print("Shift + Enter pressed")
        elif event.key() == QtCore.Qt.Key_Return and event.modifiers() == QtCore.Qt.NoModifier:
            # 处理单独 Enter 按下
            self.send_command()
        else:
            # 让其他输入事件正常处理
            super(QtWidgets.QTextEdit, self.command_input).keyPressEvent(event)

    def port_update(self, data):
        old_ports = [self.serial_port_combo.itemText(i) for i in range(self.serial_port_combo.count())]
        if old_ports != data:
            self.serial_port_combo.clear()
            self.serial_port_combo.addItems(data)
        
    def update_main_textarea(self, data):
        self.received_data_textarea.append(data.strip().replace('\r\n', '\n'))
        # self.apply_style()
        file_path = self.input_path_data_received.text()
        if file_path and self.checkbox_data_received.isChecked():
            common.print_write(data, file_path)
        elif self.checkbox_data_received.isChecked():
            common.print_write(data)
        else:
            pass
        self.received_data_textarea.ensureCursorVisible()
        self.received_data_textarea.moveCursor(QtGui.QTextCursor.End)
        
    def show_search_dialog(self):
        dialog = SearchReplaceDialog(self.received_data_textarea, self)
        dialog.exec()

    def port_on(self):
            self.port_updater.pause_thread()

            serial_port = self.serial_port_combo.currentText()
            baud_rate = int(self.baud_rate_combo.currentText())
            stop_bits = float(self.stopbits_combo.currentText())
            parity = self.parity_combo.currentText()
            if parity == "None":
                parity = serial.PARITY_NONE
            elif parity == "Even":
                parity = serial.PARITY_EVEN
            elif parity == "Odd":
                parity = serial.PARITY_ODD
            elif parity == "Mark":
                parity = serial.PARITY_MARK
            elif parity == "Space":
                parity = serial.PARITY_SPACE
            else:
                raise ValueError("Not a valid parity: {!r}".format(parity))
            byte_size = int(self.bytesize_combo.currentText())
            flow_control = self.flowcontrol_checkbox.currentText()

            try:
                self.main_Serial = common.port_on(
                    serial_port,
                    baud_rate,
                    stopbits=stop_bits,
                    parity=parity,
                    bytesize=byte_size,
                    flowcontrol=flow_control,
                )
                if self.main_Serial:
                    self.port_button.setText("Close Port")
                    self.status_label.setText("Opened")
                    self.status_label.setStyleSheet(
                        "QLabel { color: #198754; border: 2px solid white; border-radius: 10px; padding: 10px; font-size: 20px; font-weight: bold; }"
                    )
                    self.port_button.clicked.disconnect(self.port_on)
                    self.port_button.clicked.connect(self.port_off)
                    # 禁用相关控件
                    self.serial_port_combo.setEnabled(False)
                    self.baud_rate_combo.setEnabled(False)
                    self.send_button.setEnabled(True)
                    for button in self.buttons:
                        button.setEnabled(True)
                else:
                    print("⚙ Port Open Failed")
                    self.status_label.setText("Failed")
                    self.status_label.setStyleSheet(
                        "QLabel { color: #dc3545; border: 2px solid white; border-radius: 10px; padding: 10px; font-size: 20px; font-weight: bold; }"
                    )
            except serial.SerialException as e:
                print(f"Error opening serial port: {e}")
                print("suggestion:11")
            
            self.data_receiver.serial_port = self.main_Serial
            self.data_receiver.serial_port.dtr = False
            self.data_receiver.serial_port.rts = False
            self.data_receiver.resume_thread()
            
            
    def port_off(self):
        self.data_receiver.pause_thread()
        
        try:
            self.main_Serial = common.port_off(self.main_Serial)
            if self.main_Serial is None:
                self.port_button.setText("Open Port")
                self.status_label.setText("Closed")
                self.status_label.setStyleSheet(
                    "QLabel { color: #198754; border: 2px solid white; border-radius: 10px; padding: 10px; font-size: 20px; font-weight: bold; }"
                )
                self.port_button.clicked.disconnect(self.port_off)
                self.port_button.clicked.connect(self.port_on)
                
                self.serial_port_combo.setEnabled(True)
                self.baud_rate_combo.setEnabled(True)
                self.send_button.setEnabled(False)
                for button in self.buttons:
                    button.setEnabled(False)
            else:
                print("⚙ Port Close Failed")
                self.port_button.setEnabled(True)
        except Exception as e:
            print(f"Error closing serial port: {e}")
        
        self.port_updater.resume_thread()


    """
    Summary:
        Hotkeys click handler       
    """
    def clear_log(self):
        self.received_data_textarea.clear()
        if self.input_path_data_received.text():
            with open(self.input_path_data_received.text(), "w", encoding="utf-8") as f:
                f.write("")
        else:
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmps/temp.log"), "w", encoding="utf-8") as f:
                f.write("")
        common.clear_terminal()
    
    def read_ATCommand(self):
        # 读取 ATCommand.json 文件
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmps/ATCommand.json"), "r", encoding="utf-8") as f:
            ATCommandFromFile = json.load(f).get("commands")
            for i in range(1, len(self.input_fields) + 1):
                if i <= len(ATCommandFromFile):
                    self.checkbox[i - 1].setChecked(ATCommandFromFile[i - 1].get("selected"))
                    self.input_fields[i - 1].setText(ATCommandFromFile[i - 1].get("command"))
                    self.input_fields[i - 1].setCursorPosition(0)
                    self.checkbox_send_with_enters[i - 1].setChecked(ATCommandFromFile[i - 1].get("withEnter"))
                    self.interVal[i - 1].setText(str(ATCommandFromFile[i - 1].get("interval")))
                else:
                    self.input_fields[i - 1].setText("")
        
    def update_ATCommand(self):
        result = common.update_AT_command(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmps/ATCommand.json"))
        self.text_input_layout_2.setPlainText(result)
        
    def restore_ATCommand(self):
        self.text_input_layout_2.setPlainText(
            "\n".join(
                [item.text() for item in self.input_fields]
            )
        )
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmps/ATCommand.json"), "w", encoding="utf-8") as f:
            command_list = []
            for i in range(len(self.input_fields)):
                command_info = {
                    "selected": self.checkbox[i].isChecked(),
                    "command": self.input_fields[i].text(),
                    "interval": self.interVal[i].text() if self.interVal[i].text() else '',
                    "withEnter": self.checkbox_send_with_enters[i].isChecked()
                }
                command_list.append(command_info)
            json.dump({"commands": command_list}, f, ensure_ascii=False, indent=4)
    
    def handle_hotkey_click(self, index: int, value: str=''):
        def hotkey_clicked():
            if value:
                common.port_write(value, self.main_Serial)
            else:
                if index == 1:
                    self.clear_log()
                elif index == 2:
                    self.read_ATCommand()
                elif index == 3:
                    self.update_ATCommand()
                elif index == 4:
                    self.restore_ATCommand()
        return hotkey_clicked
    
    """
    Summary:
        Button group settings click handler
    
    """
    def eventFilter(self, watched, event):
        if watched == self.prompt_button:
            if event.type() == QtCore.QEvent.MouseButtonDblClick:
                if event.button() == QtCore.Qt.RightButton:
                    self.handle_right_double_click()
            elif event.type() == QtCore.QEvent.MouseButtonPress:
                if event.button() == QtCore.Qt.LeftButton:
                    self.handle_left_click()
                elif event.button() == QtCore.Qt.RightButton:
                    if event.modifiers() & QtCore.Qt.ControlModifier:
                        self.handle_right_control_click()
                    elif event.modifiers() & QtCore.Qt.ShiftModifier:
                        self.handle_right_shift_click()
                    else:
                        # Single right click
                        self.handle_right_click()
                elif event.button() == QtCore.Qt.MiddleButton:
                    self.handle_middle_click()
        return super().eventFilter(watched, event)

    def handle_left_click(self):
        # Left button click to SEND
        common.port_write(self.input_prompt.text(), self.main_Serial, self.checkbox_send_with_enters[self.prompt_index].isChecked())
        self.checkbox[self.prompt_index-1].setChecked(True)
        if self.prompt_index < len(self.input_fields) - 1:
            self.input_prompt.setText(self.input_fields[self.prompt_index].text())
            self.input_prompt.setCursorPosition(0)
            self.prompt_index += 1
        # Set Input Prompt Index read-only
        self.input_prompt_index.setReadOnly(True)

    def handle_right_click(self):
        # Right button click to SKIP
        if self.prompt_index < len(self.input_fields) - 1:
            self.input_prompt.setText(self.input_fields[self.prompt_index].text())
            self.input_prompt.setCursorPosition(0)
            self.prompt_index += 1
            
    def handle_right_double_click(self):
        pass

    def handle_right_control_click(self):
        if self.prompt_index >= 0:
            self.input_prompt.setText(self.input_fields[self.prompt_index].text())
            self.prompt_index -= 1

    def handle_right_shift_click(self):
        print("Right button click with Shift modifier")
            
    def handle_middle_click(self):
        if self.prompt_index >= 0:
            self.input_prompt.setText(self.input_fields[self.prompt_index].text())
            self.prompt_index -= 1
    
    def set_prompt_index(self):
        self.prompt_index = int(self.input_prompt_index.text())
        self.input_prompt.setText(self.input_fields[self.prompt_index].text())
        self.input_prompt.setCursorPosition(0)
        self.input_prompt_index.setReadOnly(True)
    
    def set_interval(self):
        for i in range(len(self.interVal)):
            self.interVal[i].setText("")
        
    # 过滤已选择的命令    
    def filter_selected_command(self):
        self.selected_commands = []
        for i in range(len(self.input_fields)):
            if self.checkbox[i].isChecked():
                command_info = {
                    "index": i,
                    "command": self.input_fields[i].text(),
                    "interval": self.interVal[i].text(),
                    "withEnter": self.checkbox_send_with_enters[i].isChecked()
                }
                self.selected_commands.append(command_info)
        return self.selected_commands
    
    def handle_command_executed(self, index, command):
        self.checkbox[index].setChecked(True)
        self.input_prompt_index.setText(str(index))
        self.input_prompt.setText(command)
        self.input_prompt.setCursorPosition(0)
    
    def handle_command_executed_total_times(self, total_times):
        self.input_prompt_batch_times.setText(str(total_times))
            
    def handle_prompt_batch_start(self):
        if not self.command_executor:
            self.command_executor = CommandExecutor(self.filter_selected_command(), self.main_Serial, int(self.input_prompt_batch_times.text()))
            self.command_executor.commandExecuted.connect(self.handle_command_executed) 
            self.command_executor.totalTimes.connect(self.handle_command_executed_total_times)           
            self.command_executor.start()
            self.prompt_batch_start_button.setText("Pause")
            self.prompt_batch_start_button.clicked.disconnect()
            self.prompt_batch_start_button.clicked.connect(self.handle_prompt_batch_pause)
        
    def handle_prompt_batch_pause(self):
        if self.command_executor:
            self.command_executor.pause_thread()
            self.prompt_batch_start_button.setText("Resume")
            self.prompt_batch_start_button.clicked.disconnect()
            self.prompt_batch_start_button.clicked.connect(self.handle_prompt_batch_resume)
            
    def handle_prompt_batch_resume(self):
        if self.command_executor:
            self.command_executor.resume_thread()
            self.prompt_batch_start_button.setText("Pause")
            self.prompt_batch_start_button.clicked.disconnect()
            self.prompt_batch_start_button.clicked.connect(self.handle_prompt_batch_pause)
    
    def handle_prompt_batch_stop(self):
        if self.command_executor:
            self.command_executor.pause_thread()
            self.command_executor = None
            self.prompt_batch_start_button.setText("Start")
            self.prompt_batch_start_button.clicked.disconnect()
            self.prompt_batch_start_button.clicked.connect(self.handle_prompt_batch_start)
            
    def handle_total_checkbox_click(self, state):
        for checkbox in self.checkbox:
            checkbox.setChecked(state == 2)

    # Button Click Handler
    global last_one_click_time
    
    def handle_button_click(self, index, input_field, checkbox, checkbox_send_with_enter, interVal):
        global last_one_click_time
        last_one_click_time = None
        def button_clicked():
            global last_one_click_time
            if not last_one_click_time:
                last_one_click_time = time.time()
            common.port_write(input_field.text(), self.main_Serial, checkbox_send_with_enter.isChecked())
            checkbox.setChecked(True)
            self.prompt_index = index
            self.input_prompt_index.setText(str(index-1))
            self.input_prompt.setText(input_field.text())
            now_click_time = time.time()
            self.interVal[index - 2].setText(str(min(99, int(now_click_time - last_one_click_time)+1)))
            last_one_click_time = now_click_time

        return button_clicked

    """
    Summary:
    Main window close event handler
    
    """
    def closeEvent(self, event):
        # Save configuration settings
        self.save_config(self.read_config())
        
        # Signal all running threads to stop
        active_threads = self.thread_pool.activeThreadCount()
        while active_threads > 0:
            self.thread_pool.waitForDone(100)
            active_threads = self.thread_pool.activeThreadCount()
        event.accept()

# Create a logger for the application
logger = logging.getLogger(__name__)

def main():
    try:
        app = QtWidgets.QApplication([])
        widget = MyWidget()
        widget.setStyleSheet(QSSLoader.load_stylesheet("./styles/fish.qss"))
        widget.setWindowTitle("Serial Communication")
        app.setWindowIcon(QtGui.QIcon("./favicon.ico"))

        # widget.showMaximized()
        widget.resize(1000, 900)
        widget.show()
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    logging.basicConfig(
        filename=os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs/error.log"),
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    main()