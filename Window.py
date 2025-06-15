import os
import sys
import re
import time
import json
import serial
import logging
import configparser
from PySide6.QtWidgets import (
    QMenuBar,
    QFileDialog,
    QProgressBar,
    QStackedWidget,
    QScrollArea,
    QSizePolicy,
    QGroupBox,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QLineEdit,
    QComboBox,
    QRadioButton,
    QCheckBox,
    QPushButton,
    QLabel,
    QWidget,
    QApplication,
    QMenuBar,
    QDialog,
    QMessageBox,
    QMainWindow,
    QSplashScreen,
)
from PySide6.QtCore import Qt, QTimer, QThreadPool, QEvent, QThread, QMimeData, QRunnable, Signal, QObject
from PySide6.QtGui import (
    QTextDocument,
    QTextCursor,
    QIcon,
    QIntValidator,
    QBrush,
    QColor,
    QShortcut,
    QKeySequence,
    QTextCharFormat,
    QFont,
    QDrag,
    QPixmap,
    QPainter,
)
from serial.tools import list_ports
import utils.common as common
from components.QSSLoader import QSSLoader
from components.DataReceiver import DataReceiver
from components.FileSender import FileSender
from components.CommandExecutor import CommandExecutor
from components.SearchReplaceDialog import SearchReplaceDialog
from components.HotkeysConfigDialog import HotkeysConfigDialog
from components.MoreSettingsDialog import MoreSettingsDialog
from components.LayoutConfigDialog import LayoutConfigDialog
from components.AboutDialog import AboutDialog
from components.HelpDialog import HelpDialog
from components.UpdateInfoDialog import UpdateInfoDialog
from components.ConfirmExitDialog import ConfirmExitDialog
from components.LengthCalculateDialog import LengthCalculateDialog
from components.StringAsciiConvertDialog import StringAsciiConvertDialog
from components.StringGenerateDialog import StringGenerateDialog
from components.CustomToggleSwitchDialog import CustomToggleSwitchDialog
from components.DictRecorder import DictRecorderWindow
from components.DraggableGroupBox import DraggableGroupBox
from dotenv import load_dotenv
import os


class MyWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Init constants for the widget
        self.main_Serial = None
        self.hotkey_buttons = []
        self.shortcuts = []
        self.prompt_index = -1
        self.total_times = 0
        self.is_stop_batch = False
        self.last_one_click_time = None
        self.path_ATCommand = common.get_absolute_path("tmps\\ATCommand.json")
        self.received_data_textarea_scrollBottom = True
        self.thread_pool = QThreadPool()
        self.data_receiver = None
        self.command_executor = None
        
        ## Update main text area - 优化的缓冲区管理
        self.hex_buffer = []
        self.buffer_size = 1000     # Maximum stored lines
        self.visible_lines = 100
        self.current_offset = 0    # Scroll position tracker
        self.full_data_store = [] # Complete history
        
        # 添加UI更新优化相关变量
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.batch_update_ui)
        self.update_timer.setSingleShot(True)
        self.pending_updates = []
        self.last_ui_update_time = time.time()
        self.ui_update_interval = 0.1  # 100ms最小更新间隔
        
        # 性能监控
        self.performance_stats = {
            'updates_per_second': 0,
            'last_stats_time': time.time(),
            'update_count': 0
        }

        # Before init the UI, read the Configurations of SCOM from the config.ini
        self.config = common.read_config("config.ini")
        
        # Init the UI of the widget
        self.init_UI()    
    
    """
    🎨🎨🎨
    Summary:
        Pre actions before the initialization of the UI.
    
    """
    def pre_init_UI(self):
        # Remove the existing layout if it exists
        if self.layout():
            QWidget().setLayout(self.layout())  # Detach the existing layout
    
       
    """
    🎨🎨🎨
    Summary:
         Initialize the UI of the widget.
         
    """
    
    def modify_max_rows_of_button_group(self, max_rows):
        # Clear the existing button group
        if hasattr(self, "settings_button_group"):
            self.settings_button_group.deleteLater()

        # Add setting area for the button group
        self.settings_button_group = QGroupBox()
        settings_button_layout = QGridLayout(self.settings_button_group)
        settings_button_layout.setColumnStretch(1, 3)

        self.prompt_button = QPushButton("Prompt")
        self.prompt_button.setObjectName("prompt_button")  # Add an object name for debugging
        self.prompt_button.setToolTip(
            "Left button clicked to Execute; Right button clicked to Switch Next"
        )
        self.prompt_button.setStyleSheet(
            "QPushButton { width: 100%; color: white; background-color: #198754; border: 4px solid white; border-radius: 10px; padding: 10px; font-size: 20px; font-weight: bold; }"
            "QPushButton:hover { background-color: #0d6e3f; }"
            "QPushButton:pressed { background-color: #0a4c2b; }"
        )
        self.prompt_button.installEventFilter(self)
        self.prompt_button.setEnabled(False)

        self.input_prompt = QLineEdit()
        self.input_prompt.setPlaceholderText("COMMAND: click the LEFT BUTTON to start")
        self.input_prompt.setStyleSheet(
            "QLineEdit { color: #198754; border: 2px solid white; border-radius: 10px; padding: 10px; font-size: 20px; font-weight: bold; }"
        )

        self.input_prompt_index = QLineEdit()
        self.input_prompt_index.setPlaceholderText("Idx")
        self.input_prompt_index.setToolTip("Double click to edit")
        self.input_prompt_index.setStyleSheet(
            "QLineEdit { color: #198754; border: 2px solid white; border-radius: 10px; padding: 10px; font-size: 20px; font-weight: bold; }"
        )
        self.input_prompt_index.setReadOnly(True)
        self.input_prompt_index.setMaximumWidth(self.width() * 0.1)
        self.input_prompt_index.mouseDoubleClickEvent = (
            lambda event=None: self.input_prompt_index.setReadOnly(False)
        )
        self.input_prompt_index.editingFinished.connect(self.set_prompt_index)

        self.prompt_batch_start_button = QPushButton("Start")
        self.prompt_batch_start_button.setStyleSheet(
            "QPushButton { width: 100%; color: white; background-color: #198754; border: 4px solid white; border-radius: 10px; padding: 10px; font-size: 20px; font-weight: bold; }"
            "QPushButton:hover { background-color: #0d6e3f; }"
            "QPushButton:pressed { background-color: #0a4c2b; }"
        )
        self.prompt_batch_start_button.setEnabled(False)

        self.prompt_batch_start_button.clicked.connect(self.handle_prompt_batch_start)

        self.prompt_batch_stop_button = QPushButton("Stop")
        self.prompt_batch_stop_button.setStyleSheet(
            "QPushButton { width: 100%; color: white; background-color: #dc3545; border: 4px solid white; border-radius: 10px; padding: 10px; font-size: 20px; font-weight: bold; }"
            "QPushButton:hover { background-color: #a71d2a; }"
            "QPushButton:pressed { background-color: #7b1520; }"
        )
        self.prompt_batch_stop_button.setEnabled(False)

        self.prompt_batch_stop_button.clicked.connect(self.handle_prompt_batch_stop)

        self.input_prompt_batch_times = QLineEdit()
        self.input_prompt_batch_times.setPlaceholderText("Total Times")
        self.input_prompt_batch_times.setStyleSheet(
            "QLineEdit { color: #198754; border: 2px solid white; border-radius: 10px; padding: 10px; font-size: 20px; font-weight: bold; }"
        )

        settings_button_layout.addWidget(self.prompt_button, 0, 0, 1, 1)
        settings_button_layout.addWidget(self.input_prompt, 0, 1, 1, 4)
        settings_button_layout.addWidget(self.input_prompt_index, 0, 5, 1, 1)
        settings_button_layout.addWidget(self.prompt_batch_start_button, 1, 0, 1, 1)
        settings_button_layout.addWidget(
            self.input_prompt_batch_times,
            1,
            1,
            1,
            3,
        )
        
        # Clear the existing layout if it exists
        if self.button_groupbox.layout():
            QWidget().setLayout(self.button_groupbox.layout())
        button_layout = QGridLayout(self.button_groupbox)
        button_layout.setColumnStretch(2, 2)
        settings_button_layout.addWidget(self.prompt_batch_stop_button, 1, 4, 1, 2)
        button_layout.addWidget(self.settings_button_group, 0, 0, 1, 5)

        # Set the input field to expand horizontally
        self.input_prompt.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        # Store the screen width
        self.screen_width = QApplication.primaryScreen().size().width()
        
        # Add column titles
        self.total_checkbox = QCheckBox()
        button_layout.addWidget(self.total_checkbox, 1, 0)
        self.total_checkbox.stateChanged.connect(self.handle_total_checkbox_click)
        label_function = QLabel("Function")
        label_function.setToolTip("nothing")
        label_input_field = QLabel("Input Field")
        label_input_field.setToolTip("Double click to Clear")
        label_input_field.mouseDoubleClickEvent = lambda event: self.set_input_none()
        label_enter = QLabel("Enter")
        label_enter.setToolTip("Double click to Clear")
        label_enter.mouseDoubleClickEvent = lambda event: self.set_enter_none()
        label_sec = QLabel("Sec")
        label_sec.setToolTip("Double click to Clear")
        label_sec.mouseDoubleClickEvent = lambda event: self.set_interval_none()
        button_layout.addWidget(label_function, 1, 1, alignment=Qt.AlignCenter)
        button_layout.addWidget(label_input_field, 1, 2, alignment=Qt.AlignCenter)
        button_layout.addWidget(label_enter, 1, 3, alignment=Qt.AlignCenter)
        button_layout.addWidget(label_sec, 1, 4, alignment=Qt.AlignRight)

        # Add new components
        self.checkbox = []
        self.buttons = []
        self.input_fields = []
        self.checkbox_send_with_enters = []
        self.interVal = []
        isEnable = self.main_Serial is not None
        for i in range(1, max_rows + 1):
            checkbox = QCheckBox()
            checkbox.mouseDoubleClickEvent = lambda event: self.set_checkbox_none()
            button = QPushButton(f"Func {i}")
            input_field = QLineEdit()
            input_field.setMinimumWidth(self.screen_width * 0.08)
            checkbox_send_with_enter = QCheckBox()
            checkbox_send_with_enter.setChecked(True)
            input_interval = QLineEdit()
            input_interval.setMaximumWidth(self.screen_width * 0.025)
            input_interval.setValidator(QIntValidator(0, 1000))
            input_interval.setPlaceholderText("sec")
            input_interval.setAlignment(Qt.AlignCenter)

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

            button.setEnabled(isEnable)
            input_field.setEnabled(isEnable)
            input_field.returnPressed.connect(
                self.handle_button_click(
                    i,
                    input_field,
                    checkbox,
                    checkbox_send_with_enter,
                    input_interval,
                )
            )
            button.clicked.connect(
                self.handle_button_click(
                    i,
                    input_field,
                    checkbox,
                    checkbox_send_with_enter,
                    input_interval,
                )
            )
        
    def init_UI(self):
        # Pre actions before the initialization of the UI.
        self.pre_init_UI()
        
        # Create menu bar
        self.menu_bar = QMenuBar()

        # Create Settings menu
        self.settings_menu = self.menu_bar.addMenu("Settings")

        self.save_settings_action = self.settings_menu.addAction("Save Config")
        self.save_settings_action.setShortcut("Ctrl+S")
        self.save_settings_action.triggered.connect(self.config_save)
        self.layout_config_action = self.settings_menu.addAction("Layout Config")
        self.layout_config_action.setShortcut("Ctrl+L")
        self.layout_config_action.triggered.connect(self.layout_config)
        self.hotkeys_config_action = self.settings_menu.addAction("Hotkeys Config")
        self.hotkeys_config_action.setShortcut("Ctrl+H")
        self.hotkeys_config_action.triggered.connect(self.hotkeys_config)
        self.more_settings_action = self.settings_menu.addAction("More Settings")
        self.more_settings_action.setShortcut("Ctrl+M")
        self.more_settings_action.triggered.connect(self.more_settings)
        
        # Crete Tools menu
        self.tools_menu = self.menu_bar.addMenu("Tools")
        
        self.calculate_length_action = self.tools_menu.addAction("Calculate Length")
        self.calculate_length_action.triggered.connect(self.calculate_length)
        self.generate_string_action = self.tools_menu.addAction("Generate String")
        self.generate_string_action.triggered.connect(self.generate_string)
        self.string_ascii_convert_action = self.tools_menu.addAction("String - ASCII Converter")
        self.string_ascii_convert_action.triggered.connect(self.string_ascii_convert)
        self.custom_toggle_switch_action = self.tools_menu.addAction("Custom Toggle Switch")
        self.custom_toggle_switch_action.triggered.connect(self.custom_toggle_switch)
        

        # Create About menu
        self.about_menu = self.menu_bar.addMenu("About")

        self.help_menu_action = self.about_menu.addAction("Help")
        self.help_menu_action.setShortcut("Ctrl+/")
        self.help_menu_action.triggered.connect(self.show_help_info)

        self.update_info_action = self.about_menu.addAction("Update Info")
        self.update_info_action.setShortcut("Ctrl+U")
        self.update_info_action.triggered.connect(self.show_update_info)

        self.about_menu_action = self.about_menu.addAction("About")
        self.about_menu_action.setShortcut("Ctrl+I")
        self.about_menu_action.triggered.connect(self.show_about_info)

        # Create a flag to indicate whether the thread should stop
        self.stop_ports_update_thread = False
        self.stop_textarea_update_thread = True

        self.serial_port_label = QLabel("Port:")
        self.serial_port_combo = QComboBox()
        self.serial_port_combo.addItems([port.device for port in list_ports.comports()])
        # Use the default showPopup method
        self.serial_port_combo.showPopup = self.port_update

        self.baud_rate_label = QLabel("BaudRate:")
        self.baud_rate_combo = QComboBox()
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
            "7200",
            "9600",
            "14400",
            "19200",
            "28800",
            "38400",
            "57600",
            "76800",
            "115200",
            "128000",
            "153600",
            "230400",
            "256000",
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
            "4500000",
            "5000000",
            "5500000",
            "6000000",
            "6500000",
            "7000000",
            "7500000",
            "8000000",
            ]
        )
        self.baud_rate_combo.setCurrentText("115200")
        self.stopbits_label = QLabel("StopBits:")
        self.stopbits_combo = QComboBox()
        self.stopbits_combo.addItems(["1", "1.5", "2"])
        self.stopbits_combo.setCurrentText("1")

        self.parity_label = QLabel("Parity:")
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(["None", "Even", "Odd", "Mark", "Space"])
        self.parity_combo.setCurrentText("None")

        self.bytesize_label = QLabel("ByteSize:")
        self.bytesize_combo = QComboBox()
        self.bytesize_combo.addItems(["5", "6", "7", "8"])
        self.bytesize_combo.setCurrentText("8")

        self.flowcontrol_label = QLabel("FlowControl:")
        self.flowcontrol_checkbox = QComboBox()
        self.flowcontrol_checkbox.addItems(["None", "RTS/CTS", "XON/XOFF", "DSR/DTR"])
        self.flowcontrol_checkbox.setCurrentText("None")

        self.dtr_label = QLabel("DTR:")
        self.dtr_checkbox = QCheckBox()
        self.dtr_checkbox.stateChanged.connect(self.dtr_state_changed)

        self.rts_label = QLabel("RTS:")
        self.rts_checkbox = QCheckBox()
        self.rts_checkbox.stateChanged.connect(self.rts_state_changed)

        self.label_send_with_enter = QLabel("SendWithEnter:")
        self.checkbox_send_with_enter = QCheckBox()
        self.checkbox_send_with_enter.setChecked(True)

        self.symbol_label = QLabel("Show\\r\\n:")
        self.symbol_checkbox = QCheckBox()
        self.symbol_checkbox.stateChanged.connect(self.symbol_state_changed)

        self.timeStamp_label = QLabel("TimeStamp:")
        self.timeStamp_checkbox = QCheckBox()
        self.timeStamp_checkbox.stateChanged.connect(self.timeStamp_state_changed)

        self.received_hex_data_label = QLabel("ReceivedHexData:")
        self.received_hex_data_checkbox = QCheckBox()
        self.received_hex_data_checkbox.stateChanged.connect(
            self.received_hex_data_state_changed
        )

        self.label_data_received = QLabel("Data Received:", Alignment=Qt.AlignRight)
        self.input_path_data_received = QLineEdit()
        self.input_path_data_received.setText(
            common.get_absolute_path("tmps/temp.log")
        )
        self.input_path_data_received.setReadOnly(True)
        self.input_path_data_received.mouseDoubleClickEvent = (
            self.set_default_received_file
        )
        self.checkbox_data_received = QCheckBox()
        self.checkbox_data_received.stateChanged.connect(
            self.handle_data_received_checkbox
        )
        self.button_data_received_select = QPushButton("Select Log File")
        self.button_data_received_select.clicked.connect(self.select_received_file)
        self.button_data_received_save = QPushButton("Save Log File")
        self.button_data_received_save.clicked.connect(self.save_received_file)

        self.port_button = QPushButton("Open Port")
        self.port_button.clicked.connect(self.port_on)
        self.port_button.setShortcut("Ctrl+O")
        self.port_button.setToolTip("Shortcut: Ctrl+O")

        self.toggle_button = QPushButton()
        self.toggle_button.setToolTip("Show More Options")
        self.toggle_button.setIcon(QIcon("res/expander-down.png"))
        self.toggle_button_is_expanded = False
        self.toggle_button.clicked.connect(self.show_more_options)

        self.status_label = QLabel("Closed")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(
            "QLabel { color: #198754; border: 2px solid white; border-radius: 10px; padding: 10px; font-size: 20px; font-weight: bold; }"
        )

        self.command_input = QTextEdit()
        self.command_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.command_input.setFixedHeight(35)
        self.command_input.setAcceptRichText(False)
        self.command_input.keyPressEvent = (
            self.handle_key_press
        )  # Override keyPressEvent method
        self.command_input.setEnabled(False)

        self.file_label = QLabel("File:")
        self.file_input = QLineEdit()
        self.file_input.setToolTip("Double click to Clear")
        self.file_input.mouseDoubleClickEvent = lambda event: self.file_input.clear()
        self.file_input.setPlaceholderText("Path")
        self.file_input.setReadOnly(True)
        self.file_button_select = QPushButton("Select")
        self.file_button_select.clicked.connect(self.select_file)
        self.file_button_send = QPushButton("Send")
        self.file_button_send.clicked.connect(self.send_file)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)

        # Create a button for expanding/collapsing the input field
        self.expand_button = QPushButton()
        self.expand_button.setIcon(
            QIcon("res/expand.png")
        )  # You need to have an icon for this
        self.expand_button.setCheckable(True)
        self.expand_button.setChecked(False)
        self.expand_button.clicked.connect(self.expand_command_input)

        self.send_button = QPushButton("Send")
        self.send_button.setEnabled(False)
        self.send_button.clicked.connect(self.send_command)

        self.received_data_textarea = QTextEdit()
        self.received_data_textarea.setAcceptRichText(True)
        self.received_data_textarea.installEventFilter(self)  # Install event filter
        # self.received_data_textarea.setDocument(QTextDocument(None))
        shortcut = QShortcut(Qt.ControlModifier | Qt.Key_F, self)
        shortcut.activated.connect(self.show_search_dialog)
        # self.received_data_textarea.setReadOnly(True)

        # Create a group box for the settings section
        self.settings_groupbox = QGroupBox("Settings")
        self.settings_groupbox.mouseDoubleClickEvent = (
            lambda event: self.set_settings_groupbox_visible()
        )
        self.settings_layout = QGridLayout(self.settings_groupbox)
        self.settings_layout.addWidget(
            self.serial_port_label, 0, 0, 1, 1, alignment=Qt.AlignRight
        )
        self.settings_layout.addWidget(self.serial_port_combo, 0, 1, 1, 1)
        self.settings_layout.addWidget(
            self.baud_rate_label, 1, 0, 1, 1, alignment=Qt.AlignRight
        )
        self.settings_layout.addWidget(self.baud_rate_combo, 1, 1, 1, 1)
        self.settings_layout.addWidget(self.port_button, 0, 2, 1, 2)
        self.settings_layout.addWidget(self.status_label, 1, 2, 1, 1)
        self.settings_layout.addWidget(self.toggle_button, 1, 3, 1, 1)

        self.settings_more_layout = QGridLayout()

        self.settings_more_layout.addWidget(
            self.stopbits_label, 0, 0, 1, 1, alignment=Qt.AlignRight
        )
        self.settings_more_layout.addWidget(self.stopbits_combo, 0, 1, 1, 1)
        self.settings_more_layout.addWidget(
            self.parity_label, 0, 2, 1, 1, alignment=Qt.AlignRight
        )
        self.settings_more_layout.addWidget(self.parity_combo, 0, 3, 1, 1)
        self.settings_more_layout.addWidget(
            self.bytesize_label, 1, 0, 1, 1, alignment=Qt.AlignRight
        )
        self.settings_more_layout.addWidget(self.bytesize_combo, 1, 1, 1, 1)
        self.settings_more_layout.addWidget(
            self.flowcontrol_label, 1, 2, 1, 1, alignment=Qt.AlignRight
        )
        self.settings_more_layout.addWidget(self.flowcontrol_checkbox, 1, 3, 1, 1)

        self.settings_more_layout.addWidget(
            self.dtr_label, 2, 0, 1, 1, alignment=Qt.AlignRight
        )
        self.settings_more_layout.addWidget(self.dtr_checkbox, 2, 1, 1, 1)
        self.settings_more_layout.addWidget(
            self.rts_label, 2, 2, 1, 1, alignment=Qt.AlignRight
        )
        self.settings_more_layout.addWidget(self.rts_checkbox, 2, 3, 1, 1)
        self.settings_more_layout.addWidget(
            self.symbol_label, 3, 0, 1, 1, alignment=Qt.AlignRight
        )
        self.settings_more_layout.addWidget(self.symbol_checkbox, 3, 1, 1, 1)
        self.settings_more_layout.addWidget(
            self.timeStamp_label, 3, 2, 1, 1, alignment=Qt.AlignRight
        )
        self.settings_more_layout.addWidget(self.timeStamp_checkbox, 3, 3, 1, 1)
        self.settings_more_layout.addWidget(
            self.label_send_with_enter, 4, 0, 1, 1, alignment=Qt.AlignRight
        )
        self.settings_more_layout.addWidget(self.checkbox_send_with_enter, 4, 1, 1, 1)
        self.settings_more_layout.addWidget(
            self.received_hex_data_label, 4, 2, 1, 1, alignment=Qt.AlignRight
        )
        self.settings_more_layout.addWidget(self.received_hex_data_checkbox, 4, 3, 1, 1)

        self.settings_more_layout.addWidget(self.label_data_received, 5, 0, 1, 1)
        self.settings_more_layout.addWidget(self.input_path_data_received, 5, 1, 1, 2)
        self.settings_more_layout.addWidget(self.checkbox_data_received, 5, 3, 1, 1)
        self.settings_more_layout.addWidget(
            self.button_data_received_select, 6, 0, 1, 2
        )
        self.settings_more_layout.addWidget(self.button_data_received_save, 6, 2, 1, 2)

        self.settings_layout.addLayout(self.settings_more_layout, 2, 0, 1, 4)

        # Set the button to be invisible
        for i in range(self.settings_more_layout.count()):
            self.settings_more_layout.itemAt(i).widget().setVisible(False)

        # Create a group box for the command section
        self.command_groupbox = QGroupBox("Command")
        self.command_groupbox.mouseDoubleClickEvent = (
            lambda event: self.set_command_groupbox_visible()
        )
        self.command_layout = QHBoxLayout(self.command_groupbox)
        self.command_layout.addWidget(self.command_input)
        self.command_layout.addWidget(self.expand_button)
        self.command_layout.addWidget(self.send_button)

        # Create a group box for the file section
        self.file_groupbox = QGroupBox("File")
        self.file_groupbox.mouseDoubleClickEvent = (
            lambda event: self.set_file_groupbox_visible()
        )
        self.file_layout = QVBoxLayout(self.file_groupbox)
        file_row_layout = QHBoxLayout()
        file_row_layout.addWidget(self.file_label)
        file_row_layout.addWidget(self.file_input)
        file_row_layout.addWidget(self.file_button_select)
        file_row_layout.addWidget(self.file_button_send)
        file_progress_layout = QHBoxLayout()
        file_progress_layout.addWidget(self.progress_bar)
        self.file_layout.addLayout(file_row_layout)
        self.file_layout.addLayout(file_progress_layout)

        # Create a group box for the Hotkeys section
        self.hotkeys_groupbox = QGroupBox("Hotkeys")
        self.hotkeys_groupbox.mouseDoubleClickEvent = (
            lambda event: self.set_hotkeys_groupbox_visible()
        )
        self.hotkeys_layout = QGridLayout(self.hotkeys_groupbox)

        # Create a group box for the received data section
        self.received_data_groupbox = QGroupBox("Received Data")
        received_data_layout = QVBoxLayout(self.received_data_groupbox)
        received_data_layout.addWidget(self.received_data_textarea)
        
        # Create a group box for the button group section
        self.button_groupbox = QGroupBox("Button Group")

        # Create a scroll area for the button group
        self.button_scroll_area = QScrollArea()
        self.button_scroll_area.setWidget(self.button_groupbox)
        self.button_scroll_area.setWidgetResizable(True)
        self.button_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        QTimer.singleShot(
            0,
            lambda: self.button_scroll_area.verticalScrollBar().setValue(
                self.settings_button_group.height()
            ),
        )
        
        # call the function to modify the max rows of button group
        self.modify_max_rows_of_button_group(int(self.config["MoreSettings"]["MaxRowsOfButtonGroup"]))
       
        # Create a layout for the left half
        self.left_layout = QVBoxLayout()
        self.left_layout.addWidget(self.settings_groupbox)
        self.left_layout.addWidget(self.command_groupbox)
        self.left_layout.addWidget(self.file_groupbox)
        self.left_layout.addWidget(self.hotkeys_groupbox)
        self.left_layout.addWidget(self.received_data_groupbox)

        self.right_layout = QVBoxLayout()
        self.right_layout.addWidget(self.button_scroll_area)

        # Create a layout_1 for the widget
        layout_1 = QHBoxLayout()
        layout_1.addLayout(self.left_layout)
        layout_1.addLayout(self.right_layout)

        layout_2 = QVBoxLayout()
        self.label_layout_2 = QLabel("ATCommand")
        self.text_input_layout_2 = QTextEdit()
        self.text_input_layout_2.setDocument(QTextDocument(None))
        self.text_input_layout_2.setLineWrapMode(QTextEdit.WidgetWidth)
        layout_2.addWidget(self.label_layout_2)
        layout_2_main = QHBoxLayout()
        layout_2_main.addWidget(self.text_input_layout_2)
        self.text_input_layout_2.setStyleSheet(
            "QTextEdit { height: 100%; width: 100%; font-size: 24px; font-weight: 600; }"
        )
        self.text_input_layout_2.setAcceptRichText(False)
        
        # Create a group box for the radio buttons
        self.radio_groupbox = QGroupBox()
        self.radio_layout = QGridLayout(self.radio_groupbox)
        
        # 创建一个滚动区域来容纳radio按钮
        self.radio_scroll_area = QScrollArea()
        self.radio_scroll_area.setWidgetResizable(True)
        self.radio_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.radio_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.radio_scroll_area.setWidget(self.radio_groupbox)
        
        # 设置radio_groupbox的最大高度，使其不会占据太多空间
        # self.radio_groupbox.setMaximumHeight(300)
        
        # 在radio_container_layout部分修改代码
        radio_container = QWidget()
        radio_container_layout = QHBoxLayout(radio_container)
        radio_container_layout.setContentsMargins(0, 0, 0, 0)
        radio_container_layout.setSpacing(0)

        # 创建左侧按钮容器（垂直布局）
        left_buttons_container = QWidget()
        left_buttons_layout = QVBoxLayout(left_buttons_container)
        left_buttons_layout.setContentsMargins(0, 0, 0, 0)
        left_buttons_layout.setSpacing(2)

        # 创建存储按钮
        self.save_paths_button = QPushButton()
        self.save_paths_button.setFixedSize(30, 30)
        self.save_paths_button.setIcon(QIcon("res/save.png"))
        self.save_paths_button.setStyleSheet(
            "QPushButton { "
            "background-color: transparent; "
            "border-radius: 5px; "
            "font-size: 12px; "
            "font-weight: bold; "
            "}"
            "QPushButton:hover { background-color: rgba(76, 175, 80, 0.5); }"
            "QPushButton:pressed { background-color: rgba(68, 138, 72, 0.5); }"
        )
        self.save_paths_button.setToolTip("Save current path configuration")
        self.save_paths_button.clicked.connect(self.save_paths_to_config)

        # 展开/收起按钮保持原有设置
        self.expand_left_button = QPushButton()
        self.expand_left_button.setFixedWidth(30)
        self.expand_left_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.expand_left_button.setStyleSheet(
            "QPushButton { background-color: transparent; color: #00A86B; border-radius: 5px; padding: 5px; font-size: 16px; font-weight: bold; }"
            "QPushButton:hover { background-color: rgba(76, 175, 80, 0.5); }"
            "QPushButton:pressed { background-color: rgba(68, 138, 72, 0.5); }"
        )
        self.expand_left_button.setIcon(QIcon("res/direction_left.png"))
        self.expand_left_button.clicked.connect(self.set_radio_groupbox_visible)

        # 将按钮添加到左侧容器
        left_buttons_layout.addWidget(self.save_paths_button)
        left_buttons_layout.addWidget(self.expand_left_button)

        # 设置左侧按钮容器的固定宽度
        left_buttons_container.setFixedWidth(30)

        # 将左侧按钮容器和滚动区域添加到主容器
        radio_container_layout.addWidget(left_buttons_container)
        radio_container_layout.addWidget(self.radio_scroll_area)
        
        layout_2_main.addWidget(radio_container)
        
        self.radio_path_command_buttons = []
        self.path_command_inputs = []

        # 从配置文件中读取路径
        self.path_configs = []
        for i in range(15):
            path_key = f"Path_{i+1}"
            path_value = self.config.get("Paths", path_key, fallback="")
            self.path_configs.append(path_value)

        for i in range(15):
            radio_button = QRadioButton(f"Path {i + 1}")
            radio_button.toggled.connect(
                lambda state, x=i: self.handle_radio_button_click(x)
            )
            path_input = QLineEdit()
            path_input.mouseDoubleClickEvent = lambda event, pi=path_input: (
                self.select_json_file(pi) if event else None
            )
            path_input.setPlaceholderText("Path, double click to select")
            path_input.setVisible(False)  # 默认隐藏路径输入框
            
            # 设置初始值
            if i == 0 and not self.path_configs[0]:
                path_input.setText(common.get_absolute_path("tmps\\ATCommand.json"))
            else:
                path_input.setText(self.path_configs[i])
                
            self.radio_layout.addWidget(radio_button, i + 1, 0)
            self.radio_layout.addWidget(path_input, i + 1, 1)
            self.radio_path_command_buttons.append(radio_button)
            self.path_command_inputs.append(path_input)

        self.radio_path_command_buttons[0].setChecked(True)
        layout_2_main.addWidget(self.radio_scroll_area)
        layout_2.addLayout(layout_2_main)

        layout_3 = QVBoxLayout()
        self.label_layout_3 = QLabel("temp.log")
        self.text_input_layout_3 = QTextEdit()
        self.text_input_layout_3.setDocument(QTextDocument(None))
        self.text_input_layout_3.setLineWrapMode(QTextEdit.WidgetWidth)
        layout_3.addWidget(self.label_layout_3)
        layout_3.addWidget(self.text_input_layout_3)
        self.text_input_layout_3.setStyleSheet(
            "QTextEdit { height: 100%; width: 100%; font-size: 24px; font-weight: bold; }"
        )
        self.text_input_layout_3.setAcceptRichText(False)

        layout_4 = QVBoxLayout()
        self.label_layout_4 = QLabel("No TimeStamp")
        self.text_input_layout_4 = QTextEdit()
        self.text_input_layout_4.setDocument(QTextDocument(None))
        self.text_input_layout_4.setLineWrapMode(QTextEdit.WidgetWidth)
        layout_4.addWidget(self.label_layout_4)
        layout_4.addWidget(self.text_input_layout_4)
        self.text_input_layout_4.setStyleSheet(
            "QTextEdit { height: 100%; width: 100%; font-size: 24px; font-weight: bold; }"
        )
        self.text_input_layout_4.setAcceptRichText(False)
        
        layout_5 = QVBoxLayout()
        self.dict_recorder_window = DictRecorderWindow()
        layout_5.addWidget(self.dict_recorder_window)

        # Create a button section for switching other layouts
        self.button1 = QPushButton("Main")
        self.button1.setToolTip("Shortcut: F1")
        self.button1.setStyleSheet(
            "QPushButton { background-color: transparent; color: #00A86B;; border-radius: 5px; padding: 10px; font-size: 16px; font-weight: bold; border-bottom: 2px solid #00A86B; border-top: 2px solid transparent; }"
            "QPushButton:hover { background-color: rgba(76, 175, 80, 0.5); }"
            "QPushButton:pressed { background-color: rgba(68, 138, 72, 0.5); }"
        )
        self.button1.setDefault(True)
        self.button1.clicked.connect(lambda: self.show_page(0))

        self.button2 = QPushButton("ATCommand")
        self.button2.setToolTip("Shortcut: F2")
        self.button2.setStyleSheet(
            "QPushButton { background-color: transparent; color: #00A86B;; border-radius: 5px; padding: 10px; font-size: 16px; font-weight: bold; border-top: 2px solid transparent; }"
            "QPushButton:hover { background-color: rgba(76, 175, 80, 0.5); }"
            "QPushButton:pressed { background-color: rgba(68, 138, 72, 0.5); }"
        )
        self.button2.clicked.connect(lambda: self.show_page(1))

        self.button3 = QPushButton("Log")
        self.button3.setToolTip("Shortcut: F3")
        self.button3.setStyleSheet(
            "QPushButton { background-color: transparent; color: #00A86B;; border-radius: 5px; padding: 10px; font-size: 16px; font-weight: bold; border-top: 2px solid transparent; }"
            "QPushButton:hover { background-color: rgba(76, 175, 80, 0.5); }"
            "QPushButton:pressed { background-color: rgba(68, 138, 72, 0.5); }"
        )
        self.button3.clicked.connect(lambda: self.show_page(2))

        self.button4 = QPushButton("NoTimeStamp")
        self.button4.setToolTip("Shortcut: F4")
        self.button4.setStyleSheet(
            "QPushButton { background-color: transparent; color: #00A86B;; border-radius: 5px; padding: 10px; font-size: 16px; font-weight: bold; border-top: 2px solid transparent; }"
            "QPushButton:hover { background-color: rgba(76, 175, 80, 0.5); }"
            "QPushButton:pressed { background-color: rgba(68, 138, 72, 0.5); }"
        )
        self.button4.clicked.connect(lambda: self.show_page(3))
        
        self.button5 = QPushButton("DictRecorder")
        self.button5.setToolTip("Shortcut: F5")
        self.button5.setStyleSheet(
            "QPushButton { background-color: transparent; color: #00A86B;; border-radius: 5px; padding: 10px; font-size: 16px; font-weight: bold; border-top: 2px solid transparent; }"
        )
        self.button5.clicked.connect(lambda: self.show_page(4))
        
        self.button6 = QPushButton("DictExecuter")
        self.button6.setToolTip("Shortcut: F6")
        self.button6.setStyleSheet(
            "QPushButton { background-color: transparent; color: #00A86B;; border-radius: 5px; padding: 10px; font-size: 16px; font-weight: bold; border-top: 2px solid transparent; }"
        )
        self.button6.clicked.connect(lambda: self.show_page(5))
              
        button_switch_layout = QHBoxLayout()
        button_switch_layout.setSpacing(0)
        button_switch_layout.addWidget(self.button1)
        button_switch_layout.addWidget(self.button2)
        button_switch_layout.addWidget(self.button3)
        button_switch_layout.addWidget(self.button4)
        # button_switch_layout.addWidget(self.button5)
        # button_switch_layout.addWidget(self.button6)
        
        # Create a stacked widget to switch between layouts
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(QWidget())
        self.stacked_widget.addWidget(QWidget())
        self.stacked_widget.addWidget(QWidget())
        self.stacked_widget.addWidget(QWidget())
        # self.stacked_widget.addWidget(QWidget())
        # self.stacked_widget.addWidget(QWidget())

        # Set the layouts for the stacked widget
        self.stacked_widget.widget(0).setLayout(layout_1)
        self.stacked_widget.widget(1).setLayout(layout_2)
        self.stacked_widget.widget(2).setLayout(layout_3)
        self.stacked_widget.widget(3).setLayout(layout_4)
        # self.stacked_widget.widget(4).setLayout(layout_5)
        # self.stacked_widget.widget(5).setLayout(layout_6)
        self.stacked_widget.setCurrentIndex(0)

        # Create a main layout for the widget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.menu_bar)
        main_layout.addLayout(button_switch_layout)
        main_layout.addWidget(self.stacked_widget)
        
        # 设置初始状态 - 路径选项框收起
        self.radio_scroll_area.setMaximumWidth(50)
        self.expand_left_button.setIcon(QIcon("res/direction_left.png"))
        
        # Post actions after the initialization of the UI.
        self.post_init_UI()

    """
    🎨🎨🎨
    Summary:
        After init the ui, we need to modify the layout of the main window.
         
    """ 
    def post_init_UI(self):
        self.update_hotkeys_groupbox()
                             
        input_fields_values = [
            "AT+QRST",
            "AT+QECHO=1",
            "AT+QVERSION",
            "AT+CSUB",
            "AT+QBLEADDR?",
            "AT+QBLEINIT=1",
            "AT+QBLESCAN=1",
            "AT+QBLESCAN=0",
            "AT+QWLMAC",
            "AT+QWSCAN",
            "AT+RESTORE"
        ]
        for i in range(1, len(self.input_fields) + 1):
            if i <= len(input_fields_values):
                self.input_fields[i - 1].setText(input_fields_values[i - 1])
            else:
                break

        self.layout_config_dialog = LayoutConfigDialog(self)

        if not os.path.exists("config.ini"):
            self.create_default_config()

        self.apply_config(self.config)
        self.layout_config_dialog.apply()

        # self.save_settings_action.triggered.connect(self.save_config(self.config))        
        self.save_settings_action.triggered.connect(lambda: self.save_config(self.config))


    """
    ⚙⚙⚙
    Summary:
        The FUNCTION to handle the window event.
    
    """

    def apply_config(self, config):
        # Set
        try:
            self.serial_port_combo.setCurrentText(config.get("Set", "Port"))
            self.baud_rate_combo.setCurrentText(config.get("Set", "BaudRate"))
            self.stopbits_combo.setCurrentText(config.get("Set", "StopBits"))
            self.parity_combo.setCurrentText(config.get("Set", "Parity"))
            self.bytesize_combo.setCurrentText(config.get("Set", "ByteSize"))
            self.flowcontrol_checkbox.setCurrentText(config.get("Set", "FlowControl"))
            self.dtr_checkbox.setChecked(config.getboolean("Set", "DTR"))
            self.rts_checkbox.setChecked(config.getboolean("Set", "RTS"))
            self.checkbox_send_with_enter.setChecked(
                config.getboolean("Set", "SendWithEnter")
            )
            self.symbol_checkbox.setChecked(config.getboolean("Set", "ShowSymbol"))
            self.timeStamp_checkbox.setChecked(config.getboolean("Set", "TimeStamp"))
            self.received_hex_data_checkbox.setChecked(
                config.getboolean("Set", "ReceivedHex")
            )
            self.input_path_data_received.setText(config.get("Set", "PathDataReceived"))
            self.checkbox_data_received.setChecked(
                config.getboolean("Set", "IsSaveDataReceived")
            )
            self.file_input.setText(config.get("Set", "PathFileSend"))
            
            # 加载路径配置
            if "Paths" in config:
                for i in range(1, 16):
                    path_key = f"Path_{i}"
                    if path_key in config["Paths"]:
                        path_value = config["Paths"][path_key]
                        if i <= len(self.path_command_inputs):
                            self.path_command_inputs[i-1].setText(path_value)
        except configparser.NoSectionError as e:
            logging.error(f"Error applying config: {e}")
        except configparser.NoOptionError as e:
            logging.error(f"Error applying config: {e}")

        # Hotkeys
        # for i in range(1, 9):
        #     hotkey_text = config.get("Hotkeys", f"Hotkey_{i}", fallback="")
        #     self.hotkey_buttons[i - 1].setText(hotkey_text)
        #     hotkey_value = config.get("HotkeyValues", f"HotkeyValue_{i}", fallback="")
        #     self.hotkey_buttons[i - 1].clicked.connect(
        #         self.handle_hotkey_click(i, hotkey_value)
        #     )

    def save_config(self, config):
        try:
            # Set
            config.set("Set", "Port", self.serial_port_combo.currentText())
            config.set("Set", "BaudRate", self.baud_rate_combo.currentText())
            config.set("Set", "StopBits", self.stopbits_combo.currentText())
            config.set("Set", "Parity", self.parity_combo.currentText())
            config.set("Set", "ByteSize", self.bytesize_combo.currentText())
            config.set("Set", "FlowControl", self.flowcontrol_checkbox.currentText())
            config.set("Set", "DTR", str(self.dtr_checkbox.isChecked()))
            config.set("Set", "RTS", str(self.rts_checkbox.isChecked()))
            config.set(
                "Set", "SendWithEnter", str(self.checkbox_send_with_enter.isChecked())
            )
            config.set("Set", "ShowSymbol", str(self.symbol_checkbox.isChecked()))
            config.set("Set", "TimeStamp", str(self.timeStamp_checkbox.isChecked()))
            config.set(
                "Set", "ReceivedHex", str(self.received_hex_data_checkbox.isChecked())
            )
            config.set("Set", "PathDataReceived", self.input_path_data_received.text())
            config.set(
                "Set",
                "IsSaveDataReceived",
                str(self.checkbox_data_received.isChecked()),
            )
            config.set("Set", "PathFileSend", self.file_input.text())
            
            # 保存路径配置
            if "Paths" not in config:
                config.add_section("Paths")
            for i in range(len(self.path_command_inputs)):
                path_key = f"Path_{i+1}"
                path_value = self.path_command_inputs[i].text()
                config.set("Paths", path_key, path_value)

            # Hotkeys
            # for i in range(1, 9):
            #     config.set("Hotkeys", f"Hotkey_{i}", self.hotkey_buttons[i - 1].text())
            #     config.set("HotkeyValues", f"HotkeyValue_{i}", self.input_fields[i - 1].text())

            common.write_config(config)
        except Exception as e:
            logging.error(f"Error saving config: {e}")

    def apply_style(self, data):
        text = self.received_data_textarea.toPlainText()
        doc = self.received_data_textarea.document()
        cursor = QTextCursor(doc)

        # 创建字符格式对象
        ok_char_format = QTextCharFormat()
        ok_char_format.setForeground(QBrush(QColor("#198754")))
        ok_char_format.setFontWeight(QFont.Bold)

        error_char_format = QTextCharFormat()
        error_char_format.setForeground(QBrush(QColor("#dc3545")))
        error_char_format.setFontWeight(QFont.Bold)

        # 匹配字符串 "OK" 并设置样式
        pattern_ok = r"OK\n"
        matches_ok = re.finditer(pattern_ok, text, re.MULTILINE)
        for match in matches_ok:
            start_pos = match.start()
            end_pos = match.end()
            cursor.setPosition(start_pos)
            cursor.movePosition(
                QTextCursor.NextCharacter, QTextCursor.KeepAnchor, end_pos - start_pos
            )
            existing_format = cursor.charFormat()
            new_format = QTextCharFormat(existing_format)
            new_format.setForeground(ok_char_format.foreground())
            new_format.setFontWeight(ok_char_format.fontWeight())
            cursor.setCharFormat(new_format)

        # 匹配字符串 "ERROR" 并设置样式
        pattern_error = r"ERROR\n"
        matches_error = re.finditer(pattern_error, text, re.MULTILINE)
        for match in matches_error:
            start_pos = match.start()
            end_pos = match.end()
            cursor.setPosition(start_pos)
            cursor.movePosition(
                QTextCursor.NextCharacter, QTextCursor.KeepAnchor, end_pos - start_pos
            )
            existing_format = cursor.charFormat()
            new_format = QTextCharFormat(existing_format)
            new_format.setForeground(error_char_format.foreground())
            new_format.setFontWeight(error_char_format.fontWeight())
            cursor.setCharFormat(new_format)

        self.received_data_textarea.setDocument(doc)

    def update_hotkeys_groupbox(self):
        # Clear existing buttons
        for i in reversed(range(self.hotkeys_layout.count())):
            widget = self.hotkeys_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        # Update self.hotkey_buttons
        self.hotkey_buttons = []
        for i in range(1, len(self.config.items("Hotkeys")) + 1):
            button = QPushButton(f"Hotkey {i}")
            hotkey_value = self.config.get(
                "HotkeyValues", f"HotkeyValue_{i}", fallback=""
            )
            self.hotkey_buttons.append(button)

        for i, button in enumerate(self.hotkey_buttons):
            row = i // 4
            col = i % 4
            self.hotkeys_layout.addWidget(button, row, col)

        for i in range(1, len(self.config.items("Hotkeys")) + 1):
            hotkey_name = self.config.get("Hotkeys", f"Hotkey_{i}", fallback="")
            hotkey_shortcut = self.config.get(
                "HotkeyShortcuts", f"HotkeyShortcut_{i}", fallback=""
            )
            button = self.hotkey_buttons[i - 1]
            button.setText(hotkey_name)
            button.setToolTip(hotkey_shortcut)
            try:
                shortcut = QKeySequence(hotkey_shortcut)
                button.setShortcut(shortcut)
            except ValueError:
                common.custom_print(f"Invalid shortcut: {hotkey_shortcut}")

        # Ensure each button is only connected once
        for button in self.hotkey_buttons:
            hotkey_value = self.config.get("HotkeyValues", f"HotkeyValue_{self.hotkey_buttons.index(button) + 1}", fallback="")
            button.clicked.connect(self.handle_hotkey_click(self.hotkey_buttons.index(button) + 1, hotkey_value))

    def show_page(self, index):
        if index == 1 or self.stacked_widget.currentIndex() == 1:
            if self.text_input_layout_2.toPlainText() == "":
                self.text_input_layout_2.setPlainText(
                    common.join_text(common.read_ATCommand(self.path_ATCommand))
                )
            else:
                common.write_ATCommand(
                    self.path_ATCommand,
                    common.split_text(self.text_input_layout_2.toPlainText()),
                )
                # 保存路径到配置文件
                self.save_paths_to_config()
        elif index == 2 or self.stacked_widget.currentIndex() == 2:
            self.text_input_layout_3.setPlainText(
                self.received_data_textarea.toPlainText()
            )
        elif index == 3 or self.stacked_widget.currentIndex() == 3:
            self.text_input_layout_4.setPlainText(
                common.remove_TimeStamp(
                    self.received_data_textarea.toPlainText(),
                    self.config["MoreSettings"]["TimeStampRegex"]
                )
            )
        elif index == 4 or self.stacked_widget.currentIndex() == 4:
            pass
        self.stacked_widget.setCurrentIndex(index)
        self.update_button_style(index)

    def update_button_style(self, index):
        buttons = [self.button1, self.button2, self.button3, self.button4, self.button5, self.button6]
        for i, button in enumerate(buttons):
            if i == index:
                button.setStyleSheet(
                    "QPushButton { background-color: transparent; color: #00A86B;; border-radius: 5px; padding: 10px; font-size: 16px; font-weight: bold; border-top: 2px solid transparent; border-bottom: 2px solid #00A86B; }"
                    "QPushButton:hover { background-color: rgba(76, 175, 80, 0.5); }"
                    "QPushButton:pressed { background-color: rgba(68, 138, 72, 0.5); }"
                )
            else:
                button.setStyleSheet(
                    "QPushButton { background-color: transparent; color: #00A86B;; border-radius: 5px; padding: 10px; font-size: 16px; font-weight: bold; border-top: 2px solid transparent; }"
                    "QPushButton:hover { background-color: rgba(76, 175, 80, 0.5); }"
                    "QPushButton:pressed { background-color: rgba(68, 138, 72, 0.5); }"
                )

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F1:
            self.show_page(0)
        elif event.key() == Qt.Key_F2:
            self.show_page(1)
        elif event.key() == Qt.Key_F3:
            self.show_page(2)
        elif event.key() == Qt.Key_F4:
            self.show_page(3)

    def config_save(self):
        self.save_config(self.config)
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle("Save Successful")
        msg_box.setText("Configuration has been saved successfully!")
        msg_box.setInformativeText("Your settings are now up to date.\n\n"
                       "You can continue using the application or close this dialog.")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()

    def layout_config(self):
        # LayoutConfigDialog
        self.layout_config_dialog.exec()

    def hotkeys_config(self):
        self.hotkeys_config_dialog = HotkeysConfigDialog(self)
        self.hotkeys_config_dialog.show()
    
    def more_settings(self):
        self.more_settings_dialog = MoreSettingsDialog(self)
        self.more_settings_dialog.show()
        
    def calculate_length(self):
        self.length_caculate_dialog = LengthCalculateDialog(self)
        self.length_caculate_dialog.show()
        
    def generate_string(self):
        self.string_generate_dialog = StringGenerateDialog(self)
        self.string_generate_dialog.show()
    
    def string_ascii_convert(self):
        self.string_ascii_convert_dialog = StringAsciiConvertDialog(self)
        self.string_ascii_convert_dialog.show()

    def custom_toggle_switch(self):
        self.custom_toggle_switch_dialog = CustomToggleSwitchDialog()
        self.custom_toggle_switch_dialog.show()

    def show_help_info(self):
        help_dialog = HelpDialog()
        help_dialog.exec()

    def show_update_info(self):
        update_dialog = UpdateInfoDialog(self)
        update_dialog.exec()

    def show_about_info(self):
        about_dialog = AboutDialog(self)
        about_dialog.exec()

    def dtr_state_changed(self, state):
        if self.main_Serial:
            if state == 2:
                self.data_receiver.serial_port.dtr = True
                self.main_Serial.dtr = True
            else:
                self.data_receiver.serial_port.dtr = False
                self.main_Serial.dtr = False
        else:
            self.dtr_checkbox.setChecked(state)

    def rts_state_changed(self, state):
        if self.main_Serial:
            if state == 2:
                self.data_receiver.serial_port.rts = True
                self.main_Serial.rts = True
            else:
                self.data_receiver.serial_port.rts = False
                self.main_Serial.rts = False
        else:
            self.rts_checkbox.setChecked(state)

    def symbol_state_changed(self, state):
        if self.main_Serial:
            if state == 2:
                self.data_receiver.is_show_symbol = True
            else:
                self.data_receiver.is_show_symbol = False
        else:
            self.symbol_checkbox.setChecked(state)

    def timeStamp_state_changed(self, state):
        if self.main_Serial:
            if state == 2:
                self.data_receiver.is_show_timeStamp = True
            else:
                self.data_receiver.is_show_timeStamp = False
        else:
            self.timeStamp_checkbox.setChecked(state)

    def received_hex_data_state_changed(self, state):
        if self.main_Serial:
            if state == 2:
                self.data_receiver.is_show_hex = True
            else:
                self.data_receiver.is_show_hex = False

    def show_more_options(self):
        for i in range(self.settings_more_layout.count()):
            widget = self.settings_more_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(not widget.isVisible())
        if self.toggle_button_is_expanded:
            self.toggle_button.setIcon(QIcon("res/expander-down.png"))
        else:
            self.toggle_button.setIcon(QIcon("res/fork.png"))
        self.toggle_button_is_expanded = not self.toggle_button_is_expanded

    def expand_command_input(self):
        self.command_input.setFixedHeight(100)
        self.command_input.setLineWrapMode(QTextEdit.WidgetWidth)
        self.expand_button.setIcon(QIcon("res/collapse.png"))
        self.expand_button.setChecked(True)
        self.expand_button.clicked.connect(self.collapse_command_input)

    def collapse_command_input(self):
        self.command_input.setFixedHeight(35)
        self.command_input.setLineWrapMode(QTextEdit.WidgetWidth)
        self.expand_button.setIcon(QIcon("res/expand.png"))
        self.expand_button.setChecked(False)
        self.expand_button.clicked.connect(self.expand_command_input)

    def set_status_label(self, text, color):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(
            f"QLabel {{ color: {color}; border: 2px solid white; border-radius: 10px; padding: 10px; font-size: 20px; font-weight: bold; }}"
        )

    def port_write(self, command, serial_port, send_with_enter):
        try:
            if send_with_enter:
                common.port_write(command, serial_port, True)
            else:
                common.port_write(command, serial_port, False)
            self.data_receiver.is_new_data_written = True
            
            # If `ShowCommandEcho` is enabled, show the command in the received data area
            if self.config.getboolean("MoreSettings", "ShowCommandEcho"):
                command_withTimestamp = '(' + common.get_current_time() + ')--> ' + command
                self.full_data_store.append(command_withTimestamp)
                self.received_data_textarea.append(command_withTimestamp)
                # self.apply_style(command)
        except Exception as e:
            common.custom_print(f"Error sending command: {e}")
            self.set_status_label("Failed", "#dc3545")

    def send_command(self):
        command = self.command_input.toPlainText()
        if not command:
            return
        if self.checkbox_send_with_enter.isChecked():
            self.port_write(command, self.main_Serial, True)
        else:
            self.port_write(command, self.main_Serial, False)

    def handle_data_received_checkbox(self, state):
        if state == 2:
            self.input_path_data_received.setReadOnly(False)
        else:
            self.input_path_data_received.setReadOnly(True)

    def save_received_file(self):
        file_path = self.input_path_data_received.text()
        if not file_path:
            QMessageBox.warning(self, "Warning", "No file selected.")
            return
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.received_data_textarea.toPlainText())
        except FileNotFoundError:
            QMessageBox.warning(self, "Warning", "File not found.")
        except PermissionError:
            QMessageBox.warning(self, "Warning", "Permission denied to save the file.")

    def set_default_received_file(self, event):
        self.input_path_data_received.setText(
            common.get_absolute_path("tmps\\temp.log")
        )

    def select_received_file(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.AnyFile)
        file_dialog.setNameFilter("Files (*)")
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0].replace("/", "\\")
            if file_path:
                self.input_path_data_received.setText(file_path)

    def select_file(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Files (*)")
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0].replace("/", "\\")
            if file_path:
                self.file_input.setText(file_path)
                file_size = os.path.getsize(file_path)
                self.progress_bar.setMaximum(100)
                self.progress_bar.setValue(0)
                self.progress_bar.setFormat(f"File size: {file_size} bytes")

    def select_json_file(self, path_input):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Files (*.json)")
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0].replace("/", "\\")
            if file_path:
                path_input.setText(file_path)
                
    def send_file(self):
        file_path = self.file_input.text()
        if not file_path:
            QMessageBox.warning(self, "Warning", "No file selected.")
            return
        try:
            self.file_sender = FileSender(file_path, self.main_Serial)
            self.file_sender.progressUpdated.connect(lambda percentage: self.update_progress_bar(percentage, 100))
            self.progress_bar.setFormat("%p%")
            self.progress_bar.setValue(0)
            self.progress_bar.setMaximum(100)
            self.file_sender.start()
        except FileNotFoundError:
            QMessageBox.warning(self, "Warning", "File not found.")
        except PermissionError:
            QMessageBox.warning(self, "Warning", "Permission denied to open the file.")

    def update_progress_bar(self, sent_bytes, total_bytes):
        progress = int((sent_bytes / total_bytes) * 100)
        self.progress_bar.setValue(progress)

    def handle_key_press(self, event):
        if event.key() == Qt.Key_Return and event.modifiers() == Qt.ShiftModifier:
            # Handle Shift + Enter pressed: insert a new line
            cursor = self.command_input.textCursor()
            cursor.insertText("\n")
            self.command_input.setTextCursor(cursor)
        elif event.key() == Qt.Key_Return and event.modifiers() == Qt.NoModifier:
            # Handle Enter pressed: send the command
            self.send_command()
        else:
            # Let other key events be handled normally
            QTextEdit.keyPressEvent(self.command_input, event)

    def port_update(self):
        current_ports = [port.device for port in list_ports.comports()]
        self.serial_port_combo.clear()
        self.serial_port_combo.addItems(current_ports)
        QComboBox.showPopup(self.serial_port_combo)

    def _process_hex_data(self, data):
        """Process hex data and return formatted HTML string"""
        if not self.received_hex_data_checkbox.isChecked():
            return ""  # Return empty string if checkbox is unchecked
        
        try:
            # Extract hex data based on timestamp checkbox
            raw_hex = data[25:].replace(' ', '') if self.timeStamp_checkbox.isChecked() else data.replace(' ', '')
            hex_bytes = bytes.fromhex(raw_hex)
            
            # Decode with error handling
            decoded_str = hex_bytes.decode('ascii', errors='replace')
            
            # Add spaces between characters (except escape sequences)
            spaced = []
            for char in decoded_str:
                if char == '\r':
                    spaced.append('\\r ')
                elif char == '\n':
                    spaced.append('\\n ')
                elif char == '\\':
                    spaced.append('\\\\ ')
                else:
                    spaced.append(f'{char} ')
            
            return f'<span style="color: #198754;">{"".join(spaced).strip()}</span><br>'
        
        except Exception as e:
            # Return error message as HTML instead of direct insertion
            return f'<span style="color: #dc3545;">Invalid hex data: {e}</span><br>'

    def load_older_data(self):
        """Load previous data chunks when scrolling up"""
        if self.current_offset + self.visible_lines < len(self.full_data_store):
            scrollbar = self.received_data_textarea.verticalScrollBar()
            previous_scroll_value = scrollbar.value()
            lines_in_view = self.received_data_textarea.height() // self.received_data_textarea.fontMetrics().lineSpacing()
            top_line_index = self.current_offset + (previous_scroll_value // self.received_data_textarea.fontMetrics().lineSpacing())
            self.current_offset += lines_in_view // 2  # Overlap half the actual visible lines for better context
            self.update_display()
            new_scroll_value = (top_line_index - self.current_offset) * self.received_data_textarea.fontMetrics().lineSpacing()
            scrollbar.setValue(max(0, new_scroll_value))

    def load_newer_data(self):
        """Load next data chunks when scrolling down"""
        if self.current_offset > 0:
            scrollbar = self.received_data_textarea.verticalScrollBar()
            previous_scroll_value = scrollbar.value()
            lines_in_view = self.received_data_textarea.height() // self.received_data_textarea.fontMetrics().lineSpacing()
            top_line_index = self.current_offset + (previous_scroll_value // self.received_data_textarea.fontMetrics().lineSpacing())
            self.current_offset -= lines_in_view // 2  # Overlap half the actual visible lines for better context
            self.current_offset = max(0, self.current_offset)  # Ensure offset doesn't go below 0
            self.update_display()
            new_scroll_value = (top_line_index - self.current_offset) * self.received_data_textarea.fontMetrics().lineSpacing()
            scrollbar.setValue(max(0, new_scroll_value))

    def fetch_new_data(self):
        """Method to fetch new data, adjust implementation based on your data source."""
        if hasattr(self, 'data_receiver') and self.data_receiver:
            try:
                # Assuming your DataReceiver class has a fetch_data method
                new_data = self.data_receiver.fetch_latest_data()
                if new_data:
                    # Add new data to the display buffer
                    self.full_data_store.append(new_data)
                    if len(self.full_data_store) > self.buffer_size:
                        del self.full_data_store[0]
                else:
                    # If no new data is available, do nothing
                    pass
            except Exception as e:
                # logging.error(f"Error occurred while fetching new data: {e}")
                pass

    def batch_update_ui(self):
        """批量更新UI，减少刷新频率"""
        if not self.pending_updates:
            return
        
        # 更新性能统计
        current_time = time.time()
        self.performance_stats['update_count'] += len(self.pending_updates)
        
        # 每秒计算一次更新频率
        time_diff = current_time - self.performance_stats['last_stats_time']
        if time_diff >= 1.0:
            self.performance_stats['updates_per_second'] = self.performance_stats['update_count'] / time_diff
            self.performance_stats['update_count'] = 0
            self.performance_stats['last_stats_time'] = current_time
            
            # 根据更新频率自适应调整间隔
            if self.performance_stats['updates_per_second'] > 50:
                self.ui_update_interval = 0.2  # 高频时增加间隔
            elif self.performance_stats['updates_per_second'] > 20:
                self.ui_update_interval = 0.15
            else:
                self.ui_update_interval = 0.1  # 低频时减少间隔
        
        # 处理所有待更新的数据
        for data in self.pending_updates:
            self.full_data_store.append(data)
            self.hex_buffer.append(self._process_hex_data(data))
            
            # 文件日志记录（异步处理以减少阻塞）
            if self.checkbox_data_received.isChecked():
                file_path = self.input_path_data_received.text()
                # 使用线程池异步写入文件
                self.thread_pool.start(
                    lambda: common.print_write(data, file_path if file_path else None)
                )
        
        # 清空待更新队列
        self.pending_updates.clear()
        
        # 维护缓冲区大小
        while len(self.full_data_store) > self.buffer_size:
            del self.full_data_store[0]
            del self.hex_buffer[0]
        
        # 检查是否需要更新显示
        scrollbar = self.received_data_textarea.verticalScrollBar()
        at_bottom = scrollbar.maximum() - scrollbar.value() <= 60
        
        if at_bottom:
            self.current_offset = 0
            self.efficient_update_display()

    def efficient_update_display(self):
        """高效的UI更新方法"""
        # 计算显示范围
        end_idx = len(self.full_data_store) - self.current_offset
        start_idx = max(0, end_idx - self.visible_lines)
        
        # 如果没有新数据，直接返回
        if (hasattr(self, '_last_start_idx') and 
            start_idx == self._last_start_idx and 
            end_idx == self._last_end_idx):
            return
        
        self._last_start_idx = start_idx
        self._last_end_idx = end_idx
        
        # 禁用更新以提高性能
        self.received_data_textarea.setUpdatesEnabled(False)
        try:
            # 使用QTextDocument进行批量更新
            document = QTextDocument()
            
            # 保持原有的字体设置
            current_font = self.received_data_textarea.font()
            document.setDefaultFont(current_font)
            
            cursor = QTextCursor(document)
            
            # 获取数据切片
            text_lines = self.full_data_store[start_idx:end_idx]
            hex_lines = self.hex_buffer[start_idx:end_idx] if self.received_hex_data_checkbox.isChecked() else []
            
            # 批量插入文本
            for i, line in enumerate(text_lines):
                if line.strip():  # 只处理非空行
                    cursor.insertText(line + '\n')
                    
                    # 如果需要显示十六进制数据
                    if (self.received_hex_data_checkbox.isChecked() and 
                        i < len(hex_lines) and hex_lines[i].strip()):
                        cursor.insertHtml(hex_lines[i])
            
            # 一次性设置整个文档
            self.received_data_textarea.setDocument(document)
            
        finally:
            self.received_data_textarea.setUpdatesEnabled(True)
        
        # 维护滚动位置
        if self.current_offset == 0:
            scrollbar = self.received_data_textarea.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def update_main_textarea(self, data):
        # 初始化缓冲区（如果不存在）
        if not hasattr(self, 'full_data_store'):
            self.full_data_store = []
            self.hex_buffer = []
            self.buffer_size = 1000
            self.visible_lines = 100
            self.current_offset = 0
        
        # 将数据添加到待更新队列，而不是立即更新
        self.pending_updates.append(data)
        
        # 检查是否应该立即更新（基于时间或数量阈值）
        current_time = time.time()
        time_since_last_update = current_time - self.last_ui_update_time
        
        # 如果缓冲区满了或者时间间隔够了，立即更新
        if (len(self.pending_updates) >= 20 or 
            time_since_last_update >= self.ui_update_interval):
            
            if not self.update_timer.isActive():
                self.update_timer.start(10)  # 10ms后批量更新
                self.last_ui_update_time = current_time

    def show_search_dialog(self):
        if self.stacked_widget.currentIndex() == 0:
            dialog = SearchReplaceDialog(self.received_data_textarea, self)
        elif self.stacked_widget.currentIndex() == 1:
            dialog = SearchReplaceDialog(self.text_input_layout_2, self)
        elif self.stacked_widget.currentIndex() == 2:
            dialog = SearchReplaceDialog(self.text_input_layout_3, self)
        elif self.stacked_widget.currentIndex() == 3:
            dialog = SearchReplaceDialog(self.text_input_layout_4, self)
        dialog.show()

    def port_on(self):
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
                # Clear old connection
                self.port_button.clicked.connect(self.port_off)
                self.port_button.setText("Close Port")
                self.port_button.setShortcut("Ctrl+O")
                self.port_button.setToolTip("Shortcut: Ctrl+O")
                self.set_status_label("Open", "#198754")
                self.port_button.clicked.disconnect(self.port_on)
                self.port_button.clicked.connect(self.port_off)
                # Disable the serial port and baud rate combo boxes
                self.serial_port_combo.setEnabled(False)
                self.baud_rate_combo.setEnabled(False)
                self.stopbits_combo.setEnabled(False)
                self.parity_combo.setEnabled(False)
                self.bytesize_combo.setEnabled(False)
                self.flowcontrol_checkbox.setEnabled(False)
                self.command_input.setEnabled(True)
                self.send_button.setEnabled(True)
                self.prompt_button.setEnabled(True)
                self.prompt_batch_start_button.setEnabled(True)
                self.prompt_batch_stop_button.setEnabled(True)
                for button in self.buttons:
                    button.setEnabled(True)
                for input in self.input_fields:
                    input.setEnabled(True)

            self.data_receiver = DataReceiver(self.main_Serial)
            self.data_receiver.dataReceived.connect(self.update_main_textarea)
            self.data_receive_thread = QThread()
            self.data_receiver.moveToThread(self.data_receive_thread)
            self.data_receive_thread.started.connect(self.data_receiver.run)
            self.data_receive_thread.finished.connect(self.data_receiver.deleteLater)
            self.data_receiver.exceptionOccurred.connect(self.port_off)
            self.data_receiver.is_show_symbol = self.symbol_checkbox.isChecked()
            self.data_receiver.is_show_timeStamp = self.timeStamp_checkbox.isChecked()
            self.data_receiver.is_show_hex = self.received_hex_data_checkbox.isChecked()
            self.data_receive_thread.start()
        except Exception as e:
            common.custom_print(f"Error opening serial port: {e}")
            self.set_status_label("Failed", "#dc3545")

    def port_off(self):
        self.data_receiver.stop_thread()
        self.data_receive_thread.quit()
        # No wait for the thread to finish, it will finish itself
        # self.data_receive_thread.wait()

        try:
            self.main_Serial = common.port_off(self.main_Serial)
            if self.main_Serial is None:
                self.port_button.setText("Open Port")
                self.port_button.setShortcut("Ctrl+O")
                self.port_button.setToolTip("Shortcut: Ctrl+O")
                self.set_status_label("Closed", "#198754")
                self.port_button.clicked.disconnect()
                self.port_button.clicked.connect(self.port_on)

                self.serial_port_combo.setEnabled(True)
                self.baud_rate_combo.setEnabled(True)
                self.stopbits_combo.setEnabled(True)
                self.parity_combo.setEnabled(True)
                self.bytesize_combo.setEnabled(True)
                self.flowcontrol_checkbox.setEnabled(True)
                self.command_input.setEnabled(False)
                self.send_button.setEnabled(False)
                self.prompt_button.setEnabled(False)
                self.prompt_batch_start_button.setEnabled(False)
                self.prompt_batch_stop_button.setEnabled(False)
                for button in self.buttons:
                    button.setEnabled(False)
                for input in self.input_fields:
                    input.setEnabled(False)
            else:
                common.custom_print("⚙ Port Close Failed")
                self.port_button.setEnabled(True)
        except Exception as e:
            common.custom_print(f"Error closing serial port: {e}")
            self.set_status_label("Failed", "#dc3545")

    """
    Summary:
        Hotkeys click handler       
    """

    def clear_log(self):
        self.current_offset = 0
        self.full_data_store = []
        self.hex_buffer = []
        
        self.received_data_textarea.clear()
        if self.input_path_data_received.text():
            with open(self.input_path_data_received.text(), "w", encoding="utf-8") as f:
                f.write("")
        else:
            with open(
                common.get_absolute_path("tmps/temp.log"),
                "w",
                encoding="utf-8",
            ) as f:
                f.write("")

    def read_ATCommand(self):
        with open(
            self.path_ATCommand,
            "r",
            encoding="utf-8",
        ) as f:
            ATCommandFromFile = json.load(f).get("Commands")
            for i in range(1, len(self.input_fields) + 1):
                if i <= len(ATCommandFromFile):
                    self.checkbox[i - 1].setChecked(
                        ATCommandFromFile[i - 1].get("selected")
                    )
                    self.input_fields[i - 1].setText(
                        ATCommandFromFile[i - 1].get("command")
                    )
                    self.input_fields[i - 1].setCursorPosition(0)
                    self.checkbox_send_with_enters[i - 1].setChecked(
                        ATCommandFromFile[i - 1].get("withEnter")
                    )
                    self.interVal[i - 1].setText(
                        str(ATCommandFromFile[i - 1].get("interval"))
                    )
                else:
                    self.input_fields[i - 1].setText("")

    def update_ATCommand(self):
        result = common.update_AT_command(
            self.path_ATCommand, 
            self.config["MoreSettings"]["ATCRegex"])
        self.text_input_layout_2.setPlainText(result)

    def restore_ATCommand(self):
        last_non_empty_index = None
        for i in range(len(self.input_fields) - 1, -1, -1):
            if self.input_fields[i].text():
                last_non_empty_index = i
                break
        if last_non_empty_index is None:
            last_non_empty_index = 0
        
        self.text_input_layout_2.setPlainText(
            "\n".join([item.text() for item in self.input_fields[:last_non_empty_index + 1]])
        )
        
        command_list = []
        for i in range(last_non_empty_index + 1):
            command_info = {
                "selected": self.checkbox[i].isChecked(),
                "command": self.input_fields[i].text(),
                "interval": (
                    self.interVal[i].text() if self.interVal[i].text() else ""
                ),
                "withEnter": self.checkbox_send_with_enters[i].isChecked(),
            }
            command_list.append(command_info)
        with open(
            self.path_ATCommand,
            "w",
            encoding="utf-8",
        ) as f:
            json.dump({"Commands": command_list}, f, ensure_ascii=False, indent=4)

    def handle_radio_button_click(self, index):
        if self.radio_path_command_buttons[index].isChecked():
            if self.path_command_inputs[index].text():
                self.path_ATCommand = self.path_command_inputs[index].text()
                self.text_input_layout_2.setPlainText(
                    common.join_text(common.read_ATCommand(self.path_ATCommand))
                )
                # 保存当前选中的路径到配置文件
                self.save_paths_to_config()
            else:
                self.path_ATCommand = common.get_absolute_path("tmps/ATCommand.json")
        else:
            # common.custom_print(f"Radio button {index + 1} is unchecked.")
            pass

    def handle_hotkey_click(self, index: int, value: str = "", shortcut: str = ""):
        def hotkey_clicked():
            if value:
                self.port_write(value, self.main_Serial, True)
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
        # Handle button events
        if hasattr(self, "prompt_button") and watched == self.prompt_button:
            if watched == self.prompt_button:
                if event.type() == QEvent.MouseButtonDblClick:
                    if event.button() == Qt.RightButton:
                        self.handle_right_double_click()
                        return True
                elif event.type() == QEvent.MouseButtonPress:
                    if event.button() == Qt.LeftButton:
                        self.handle_left_click()
                        return True
                    elif event.button() == Qt.RightButton:
                        if event.modifiers() & Qt.ControlModifier:
                            self.handle_right_control_click()
                            return True
                        elif event.modifiers() & Qt.ShiftModifier:
                            self.handle_right_shift_click()
                            return True
                        else:
                            # Single right click
                            self.handle_right_click()
                            return True
                    elif event.button() == Qt.MiddleButton:
                        self.handle_middle_click()
                        return True

        # Handle wheel events for text area scrolling
        if watched == self.received_data_textarea and event.type() == QEvent.Wheel:
            self.handle_scroll_event(event)
            return True

        # Let the parent class handle other events
        return super().eventFilter(watched, event)

    def handle_scroll_event(self, event):
        """Detect scroll direction and position"""
        scrollbar = self.received_data_textarea.verticalScrollBar()

        # Scroll up detection
        if event.angleDelta().y() > 0 and scrollbar.value() <= scrollbar.singleStep():
            self.load_older_data()
        
        # Scroll down detection
        elif event.angleDelta().y() < 0 and scrollbar.value() >= scrollbar.maximum() - scrollbar.singleStep():
            # When reaching the bottom, attempt to fetch more new data
            self.fetch_new_data()
            
            # Reset the offset to ensure the latest content is displayed
            self.current_offset = 0
            self.update_display()
            
        # Else, do nothing
        else:
            pass

    def handle_left_click(self):
        if self.prompt_index >= 0 and self.prompt_index < len(self.input_fields) - 1:
            # Left button click to SEND
            self.port_write(
                self.input_prompt.text(),
                self.main_Serial,
                self.checkbox_send_with_enters[self.prompt_index].isChecked(),
            )
            self.checkbox[self.prompt_index].setChecked(True)
            self.prompt_index += 1
            self.input_prompt.setText(self.input_fields[self.prompt_index].text())
            self.input_prompt.setCursorPosition(0)
            self.input_prompt_index.setText(str(self.prompt_index + 1))
            # Set Input Prompt Index read-only
            self.input_prompt_index.setReadOnly(True)
        else:
            self.prompt_index = 0
            self.input_prompt_index.setText("1")
            self.input_prompt.setText(self.input_fields[0].text())
            self.input_prompt.setCursorPosition(0)
            self.input_prompt_index.setReadOnly(True)

    def handle_right_click(self):
        self.prompt_index += 1
        # Right button click to SKIP
        if self.prompt_index < len(self.input_fields) - 1:
            self.input_prompt.setText(self.input_fields[self.prompt_index].text())
            self.input_prompt.setCursorPosition(0)
            self.input_prompt_index.setText(str(self.prompt_index + 1))

    def handle_right_double_click(self):
        pass

    def handle_right_control_click(self):
        if self.prompt_index >= 0:
            self.prompt_index -= 1
            self.input_prompt.setText(self.input_fields[self.prompt_index].text())
            self.input_prompt_index.setText(str(self.prompt_index + 1))

    def handle_right_shift_click(self):
        common.custom_print("Right button click with Shift modifier")

    def handle_middle_click(self):
        if self.prompt_index >= 0:
            self.prompt_index -= 1
            self.input_prompt.setText(self.input_fields[self.prompt_index].text())
            self.input_prompt_index.setText(str(self.prompt_index + 1))

    def set_prompt_index(self):
        self.prompt_index = int(self.input_prompt_index.text()) - 1
        self.input_prompt.setText(self.input_fields[self.prompt_index].text())
        self.input_prompt.setCursorPosition(0)
        self.input_prompt_index.setReadOnly(True)

    def set_input_none(self):
        for i in range(len(self.input_fields)):
            self.input_fields[i].setText("")

    def set_checkbox_none(self):
        for i in range(len(self.checkbox)):
            self.checkbox[i].setChecked(False)

    def set_enter_none(self):
        status = not all(checkbox.isChecked() for checkbox in self.checkbox_send_with_enters)
        for checkbox in self.checkbox_send_with_enters:
            checkbox.setChecked(status)

    def set_interval_none(self):
        interVal = self.interVal[0].text()
        for i in range(len(self.interVal)):
            self.interVal[i].setText(interVal)

    def set_settings_groupbox_visible(self):
        for i in range(self.settings_layout.count()):
            widget = self.settings_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(not widget.isVisible())

    def set_command_groupbox_visible(self):
        for i in range(self.command_layout.count()):
            widget = self.command_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(not widget.isVisible())

    def set_file_groupbox_visible(self):
        for i in range(self.file_layout.count()):
            item = self.file_layout.itemAt(i)
            if isinstance(item, QHBoxLayout) or isinstance(item, QVBoxLayout):
                for j in range(item.count()):
                    widget = item.itemAt(j).widget()
                    if widget:
                        widget.setVisible(not widget.isVisible())
            else:
                widget = item.widget()
                if widget:
                    widget.setVisible(not widget.isVisible())

    def set_hotkeys_groupbox_visible(self):
        for i in range(self.hotkeys_layout.count()):
            widget = self.hotkeys_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(not widget.isVisible())

    def set_radio_groupbox_visible(self):
        if self.path_command_inputs[0].isVisible():
            # 收起状态
            self.expand_left_button.setIcon(QIcon("res/direction_left.png"))
            # 保存路径到配置文件
            self.save_paths_to_config()
            # 隐藏所有路径输入框
            for path_input in self.path_command_inputs:
                path_input.setVisible(False)
            # 设置最大宽度为50
            self.radio_scroll_area.setMaximumWidth(50)
        else:
            # 展开状态
            self.expand_left_button.setIcon(QIcon("res/direction_right.png"))
            # 显示所有路径输入框
            for path_input in self.path_command_inputs:
                path_input.setVisible(True)
            # 设置最大宽度为窗口宽度的1/3
            self.radio_scroll_area.setMaximumWidth(self.width() // 3)
            
    def save_paths_to_config(self):
        """保存路径到配置文件"""
        try:
            # 确保Paths部分存在
            if "Paths" not in self.config:
                self.config.add_section("Paths")
                
            # 保存所有路径
            for i in range(len(self.path_command_inputs)):
                path_key = f"Path_{i+1}"
                path_value = self.path_command_inputs[i].text()
                self.config.set("Paths", path_key, path_value)
                
            # 写入配置文件
            common.write_config(self.config)
        except Exception as e:
            logging.error(f"Error saving paths to config: {e}")

    # Filter selected commands
    def filter_selected_command(self):
        self.selected_commands = []
        for i in range(len(self.input_fields)):
            if self.checkbox[i].isChecked():
                command_info = {
                    "index": i,
                    "command": self.input_fields[i].text(),
                    "interval": self.interVal[i].text(),
                    "withEnter": self.checkbox_send_with_enters[i].isChecked(),
                }
                self.selected_commands.append(command_info)
        return self.selected_commands

    def handle_command_executed(self, index, command):
        # self.checkbox[index].setChecked(True)
        self.input_prompt_index.setText(str(index))
        self.input_prompt.setText(command)
        self.input_prompt.setCursorPosition(0)

    def handle_command_executed_total_times(self, total_times):
        self.input_prompt_batch_times.setText(str(total_times))

    def handle_prompt_batch_start(self):
        if not self.command_executor:
            try:
                self.total_times = int(self.input_prompt_batch_times.text())
            except ValueError:
                self.total_times = 1
            # If total times is 0, set it to 1
            if self.total_times == 0:
                self.total_times = 1
            self.command_executor = CommandExecutor(
                self.filter_selected_command(),
                self.main_Serial,
                self.total_times,
            )
            self.command_executor.commandExecuted.connect(self.handle_command_executed)
            self.command_executor.totalTimes.connect(
                self.handle_command_executed_total_times
            )
            self.command_executor.start()
            self.prompt_batch_start_button.setText("Pause")
            self.prompt_batch_start_button.clicked.disconnect()
            self.prompt_batch_start_button.clicked.connect(
                self.handle_prompt_batch_pause
            )

    def handle_prompt_batch_pause(self):
        if self.command_executor:
            self.command_executor.pause_thread()
            self.prompt_batch_start_button.setText("Resume")
            self.prompt_batch_start_button.clicked.disconnect()
            self.prompt_batch_start_button.clicked.connect(
                self.handle_prompt_batch_resume
            )

    def handle_prompt_batch_resume(self):
        if self.command_executor:
            self.command_executor.resume_thread()
            self.prompt_batch_start_button.setText("Pause")
            self.prompt_batch_start_button.clicked.disconnect()
            self.prompt_batch_start_button.clicked.connect(
                self.handle_prompt_batch_pause
            )

    def handle_prompt_batch_stop(self):
        if self.command_executor:
            self.command_executor.pause_thread()
            self.command_executor = None
            self.prompt_batch_start_button.setText("Start")
            self.prompt_batch_start_button.clicked.disconnect()
            self.prompt_batch_start_button.clicked.connect(
                self.handle_prompt_batch_start
            )

    def handle_total_checkbox_click(self, state):
        for checkbox in self.checkbox:
            checkbox.setChecked(state == 2)

    # Button Click Handler
    def handle_button_click(
        self, index, input_field, checkbox, checkbox_send_with_enter, interVal
    ):
        def button_clicked():
            if not self.last_one_click_time:
                self.last_one_click_time = time.time()
            self.port_write(
                input_field.text(),
                self.main_Serial,
                checkbox_send_with_enter.isChecked(),
            )
            checkbox.setChecked(True)
            self.prompt_index = index
            self.input_prompt_index.setText(str(index))
            self.input_prompt.setText(input_field.text())
            now_click_time = time.time()
            self.interVal[index - 2].setText(
                str(min(99, int(now_click_time - self.last_one_click_time) + 1))
            )
            self.last_one_click_time = now_click_time

        return button_clicked

    """
    Summary:
    Main window close event handler
    
    """

    def closeEvent(self, event):
        # Confirm exit dialog
        confirm_exit_dialog = ConfirmExitDialog(self)
        if confirm_exit_dialog.exec() == QDialog.Accepted:
            # Save configuration settings
            self.save_config(self.config)
            # Properly stop and wait for the data receive thread
            try:
                if hasattr(self, "data_receiver") and self.data_receiver:
                    self.data_receiver.stop_thread()
                if hasattr(self, "data_receive_thread") and self.data_receive_thread:
                    self.data_receive_thread.quit()
                    self.data_receive_thread.wait(2000)  # Wait up to 2 seconds
            except Exception as e:
                logging.error(f"Error stopping data receive thread: {e}")
            # Close serial port
            if self.main_Serial:
                self.port_off()
            # Signal all running threads to stop
            active_threads = self.thread_pool.activeThreadCount()
            while active_threads > 0:
                self.thread_pool.waitForDone(100)
                active_threads = self.thread_pool.activeThreadCount()
            event.accept()
        else:
            event.ignore()


def main():
    try:
        app = QApplication([])
        
        load_dotenv()
        version = os.getenv("VERSION", "1.0.0")
        
        # 创建启动画面
        splash_pixmap = QPixmap(400, 300)
        splash_pixmap.fill(QColor("#f0f0f0"))
        
        # 在启动画面上绘制内容
        painter = QPainter(splash_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制应用图标（如果存在）
        try:
            icon_pixmap = QPixmap("favicon.ico")
            if not icon_pixmap.isNull():
                scaled_icon = icon_pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                painter.drawPixmap(168, 80, scaled_icon)
        except:
            pass
        
        # 绘制应用名称
        painter.setPen(QColor("#333333"))
        font = QFont("Microsoft YaHei", 18, QFont.Bold)
        painter.setFont(font)
        text_rect = splash_pixmap.rect().adjusted(0, 150, 0, -120)
        painter.drawText(text_rect, Qt.AlignHCenter | Qt.AlignTop, f"SCOM v{version}")
        
        # 绘制加载文本
        font = QFont("Consolas", 12)
        painter.setFont(font)
        painter.setPen(QColor("#666666"))
        painter.drawText(50, 210, 300, 30, Qt.AlignCenter, "Starting SCOM...")

        # 绘制进度条背景
        painter.setPen(QColor("#cccccc"))
        painter.setBrush(QColor("#f8f8f8"))
        painter.drawRoundedRect(80, 240, 240, 8, 4, 4)
        
        painter.end()
        
        splash = QSplashScreen(splash_pixmap)
        splash.show()
        app.processEvents()
        
        # 更新启动画面消息
        def update_splash_message(message):
            splash.showMessage(
                f"{message}",
                Qt.AlignBottom | Qt.AlignCenter,
                QColor("#333333")
            )
            app.processEvents()
        
        # 分步骤加载
        update_splash_message("Initializing application...")
        app.processEvents()
        
        update_splash_message("Loading main interface...")
        widget = MyWidget()
        app.processEvents()
        
        update_splash_message("Applying styles...")
        widget.setStyleSheet(QSSLoader.load_stylesheet("styles/fish.qss"))
        app.processEvents()
        
        update_splash_message("Configuring window...")
        widget.setWindowTitle(f"SCOM v{version}")
        app.setWindowIcon(QIcon("favicon.ico"))
        widget.resize(1000, 900)
        app.processEvents()
        
        update_splash_message("Checking for updates...")
        app.processEvents()
        
        update_loader = UpdateInfoDialog.load_update_info_async()
        
        def on_update_finished(success, should_show_dialog):
            update_splash_message("Startup complete!")
            QTimer.singleShot(300, lambda: finish_startup(should_show_dialog))
        
        def finish_startup(should_show_dialog=False):
            widget.show()
            splash.finish(widget)
            
            # 如果检测到更新信息有变化，显示更新信息对话框
            if should_show_dialog:
                def show_update_dialog():
                    try:
                        update_dialog = UpdateInfoDialog(widget)
                        update_dialog.show()
                    except Exception as e:
                        print(f"显示更新信息对话框失败: {e}")
                
                # 延迟500毫秒后显示更新对话框，让主界面先完全显示
                QTimer.singleShot(500, show_update_dialog)
        
        # 连接完成信号
        update_loader.finished.connect(on_update_finished)
        
        # 设置超时机制，如果10秒内没有完成就强制关闭启动画面
        def force_close_splash():
            if update_loader.isRunning():
                print("Update info loading timeout, force closing splash screen")
                update_splash_message("Startup complete!")
                widget.show()
                splash.finish(widget)
        
        QTimer.singleShot(10000, force_close_splash)  # 10秒超时
        
        sys.exit(app.exec())
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        print(f"Startup failed: {e}")
        try:
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setText("Application failed to start")
            error_msg.setInformativeText(f"Error: {str(e)}")
            error_msg.setWindowTitle("Error")
            error_msg.exec()
        except:
            print("Unable to display error dialog")


if __name__ == "__main__":
    logging.basicConfig(
        filename="logs/error.log",
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    main()

