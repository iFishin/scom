import os
import sys
import re
import time
import datetime
import json
import serial
import configparser
from middileware.Logger import Logger
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
from components.ConfigManager import read_config as read_app_config, write_config as write_app_config
from components.QSSLoader import QSSLoader
from components.DataReceiver import DataReceiver
from components.FileSender import FileSender
from components.CommandExecutor import CommandExecutor
from components.SearchReplaceDialog import SearchReplaceDialog
from components.HotkeysConfigDialog import HotkeysConfigDialog
from components.MoreSettingsDialog import MoreSettingsDialog
from components.LayoutConfigDialog import LayoutConfigDialog
from components.StyleConfigDialog import StyleConfigDialog
from components.AboutDialog import AboutDialog
from components.KnownIssuesDialog import KnownIssuesDialog
from components.HelpDialog import HelpDialog
from components.SafeUpdateChecker import SafeUpdateDialog, SafeUpdateChecker
from components.ConfirmExitDialog import ConfirmExitDialog
from components.LengthCalculateDialog import LengthCalculateDialog
from components.StringAsciiConvertDialog import StringAsciiConvertDialog
from components.StringGenerateDialog import StringGenerateDialog
from components.CustomToggleSwitchDialog import CustomToggleSwitchDialog
from components.DictRecorder import DictRecorderWindow
from components.DraggableGroupBox import DraggableGroupBox
from components.ErrorDialog import ErrorDialog
from components.ATCommandManager import ATCommandManager
from dotenv import load_dotenv
import os

# 创建全局logger实例
logger = Logger(
    app_name="Window",
    log_dir="logs",
    max_bytes=10 * 1024 * 1024,
    backup_count=3
).get_logger("Window")


class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        # Get User Data Directory
        self.app_data_dir = common.ensure_user_directories()
        # Init constants for the widget
        self.main_Serial = None
        self.hotkey_buttons = []
        self.shortcuts = []
        self.prompt_index = -1
        self.total_times = 0
        self.is_stop_batch = False
        self.last_one_click_time = None
        self.path_ATCommand = os.path.join(self.app_data_dir, "tmps", "ATCommand.json")
        self.received_data_textarea_scrollBottom = True

        # 初始化AT命令管理器
        self.at_command_manager = ATCommandManager(self)
        self.thread_pool = QThreadPool()
        self.data_receiver = None
        self.command_executor = None

        ## Update main text area - 优化的缓冲区管理
        self.full_data_store = []  # Complete history
        self.hex_buffer = []  # 用于存储十六进制数据
        self.raw_data_buffer = []  # 用于存储原始数据
        self.buffer_size = 2000  # Maximum stored lines
        self.visible_lines = 500  # 可见行数
        self.current_offset = 0  # Scroll position tracker

        ## 添加UI更新优化相关变量
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.batch_update_ui)
        self.update_timer.setSingleShot(True)
        self.pending_updates = []
        self.last_ui_update_time = time.time()
        self.ui_update_interval = 0.1  # 100ms最小更新间隔

        ## 性能监控和缓冲区配置
        self.performance_stats = {
            'updates_per_second': 0,
            'last_stats_time': time.time(),
            'update_count': 0,
        }

        # 增大缓冲区以减少数据丢失
        self.buffer_size = 10000  # 从2000增加到10000
        self.visible_lines = 500
        self.max_pending_updates = 20  # 限制待处理更新的最大数量，从200降低到20
        # Before init the UI, read the Configurations of SCOM from the config.ini
        # Use the centralized ConfigManager to fully control config lifecycle
        try:
            self.config = read_app_config("config.ini")
        except Exception:
            # fallback to existing common.read_config if something unexpected happens
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
    def add_settings_button_group(self):
        # Create settings_button_group
        self.settings_button_group = QGroupBox("Prompt Button Group")
        settings_button_layout = QGridLayout(self.settings_button_group)
        settings_button_layout.setColumnStretch(1, 3)

        self.prompt_button = QPushButton("Prompt")
        self.prompt_button.setObjectName("prompt_button")
        self.prompt_button.setToolTip(
            "Left button clicked to Execute; Right button clicked to Switch Next"
        )
        self.prompt_button.installEventFilter(self)
        self.prompt_button.setEnabled(False)

        self.input_prompt = QLineEdit()
        self.input_prompt.setObjectName("input_prompt")
        self.input_prompt.setPlaceholderText("COMMAND: click the LEFT BUTTON to start")

        self.input_prompt_index = QLineEdit()
        self.input_prompt_index.setObjectName("input_prompt_index")
        self.input_prompt_index.setPlaceholderText("Idx")
        self.input_prompt_index.setToolTip("Double click to edit")
        self.input_prompt_index.setReadOnly(True)
        self.input_prompt_index.setMaximumWidth(self.width() * 0.1)
        self.input_prompt_index.mouseDoubleClickEvent = (
            lambda event=None: self.input_prompt_index.setReadOnly(False)
        )
        self.input_prompt_index.editingFinished.connect(self.set_prompt_index)

        self.prompt_batch_start_button = QPushButton("Start")
        self.prompt_batch_start_button.setObjectName("prompt_batch_start_button")
        self.prompt_batch_start_button.setEnabled(False)
        self.prompt_batch_start_button.clicked.connect(self.handle_prompt_batch_start)

        self.prompt_batch_stop_button = QPushButton("Stop")
        self.prompt_batch_stop_button.setObjectName("prompt_batch_stop_button")
        self.prompt_batch_stop_button.setEnabled(False)
        self.prompt_batch_stop_button.clicked.connect(self.handle_prompt_batch_stop)

        self.input_prompt_batch_times = QLineEdit()
        self.input_prompt_batch_times.setObjectName("input_prompt_batch_times")
        self.input_prompt_batch_times.setPlaceholderText("Total Times")

        settings_button_layout.addWidget(self.prompt_button, 0, 0, 1, 1)
        settings_button_layout.addWidget(self.input_prompt, 0, 1, 1, 4)
        settings_button_layout.addWidget(self.input_prompt_index, 0, 5, 1, 1)
        settings_button_layout.addWidget(self.prompt_batch_start_button, 1, 0, 1, 1)
        settings_button_layout.addWidget(self.input_prompt_batch_times, 1, 1, 1, 3)
        settings_button_layout.addWidget(self.prompt_batch_stop_button, 1, 4, 1, 2)

        self.input_prompt.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

    def modify_max_rows_of_button_group(self, max_rows):
        """修改按钮组的最大行数，只操作button_groupbox内部"""
        # 清理现有的动态控件
        self.clear_dynamic_controls()

        # 获取现有布局或新建
        if not self.button_groupbox.layout():
            button_layout = QGridLayout(self.button_groupbox)
            button_layout.setColumnStretch(2, 2)
        else:
            button_layout = self.button_groupbox.layout()

        # 存储屏幕宽度
        self.screen_width = QApplication.primaryScreen().size().width()
        
        # 重置按钮列表（不删除现有的，让 Qt 自己管理）
        self.checkbox = []
        self.buttons = []
        self.input_fields = []
        self.checkbox_hex = []  # 新增：十六进制复选框列表
        self.checkbox_send_with_enders = []
        self.interVal = []
        
        # 添加列标题
        if not hasattr(self, 'total_checkbox') or not self.total_checkbox.parent():
            self.total_checkbox = QCheckBox()
            button_layout.addWidget(self.total_checkbox, 1, 0)
            self.total_checkbox.stateChanged.connect(self.handle_total_checkbox_click)
            
            label_sender = QLabel("Sender")
            label_sender.setToolTip("nothing")
            label_input_field = QLabel("Input")
            label_input_field.setToolTip("Double click to Clear")
            label_input_field.mouseDoubleClickEvent = lambda event: self.set_input_none()
            label_hex = QLabel("Hex")
            label_hex.setToolTip("Send as hexadecimal data")
            label_hex.setAlignment(Qt.AlignCenter)
            label_hex.mouseDoubleClickEvent = lambda event: self.set_hex_none()
            label_hex.mouseDoubleClickEvent = lambda event: self.set_hex_none()
            label_ender = QLabel("Ender")
            label_ender.setToolTip("Double click to Clear")
            label_ender.mouseDoubleClickEvent = lambda event: self.set_enter_none()
            label_ms = QLabel("ms")
            label_ms.setToolTip("Double click to Clear")
            label_ms.setAlignment(Qt.AlignCenter)
            label_ms.mouseDoubleClickEvent = lambda event: self.set_interval_none()
            
            button_layout.addWidget(label_sender, 1, 1, alignment=Qt.AlignCenter)
            button_layout.addWidget(label_input_field, 1, 2, alignment=Qt.AlignCenter)
            button_layout.addWidget(label_hex, 1, 3, alignment=Qt.AlignCenter)
            button_layout.addWidget(label_ender, 1, 4, alignment=Qt.AlignCenter)
            button_layout.addWidget(label_ms, 1, 5, alignment=Qt.AlignRight)

        isEnable = self.main_Serial is not None

        # Create new button row
        for i in range(1, max_rows + 1):
            checkbox = QCheckBox()
            checkbox.mouseDoubleClickEvent = lambda event: self.set_checkbox_none()
            button = QPushButton(f"Send {i}")
            input_field = QLineEdit()
            input_field.setMinimumWidth(self.screen_width * 0.08)
            checkbox_hex = QCheckBox()
            checkbox_hex.setChecked(False)
            checkbox_hex.setToolTip("Send data as hexadecimal")
            checkbox_send_with_ender = QCheckBox()
            checkbox_send_with_ender.setChecked(True)
            input_interval = QLineEdit()
            input_interval.setMaximumWidth(self.screen_width * 0.025)
            # Maximum of SLEEP interval is fixed to 99999, about 99s
            input_interval.setValidator(QIntValidator(0, 99999))
            input_interval.setPlaceholderText("ms")
            input_interval.setAlignment(Qt.AlignCenter)

            # 为输入框添加键盘导航功能
            input_field.keyPressEvent = self.create_input_field_key_handler(input_field, i-1)

            button_layout.addWidget(checkbox, i+1, 0)
            button_layout.addWidget(button, i+1, 1)
            button_layout.addWidget(input_field, i+1, 2)
            button_layout.addWidget(checkbox_hex, i+1, 3)
            button_layout.addWidget(checkbox_send_with_ender, i+1, 4)
            button_layout.addWidget(input_interval, i+1, 5)

            self.checkbox.append(checkbox)
            self.buttons.append(button)
            self.input_fields.append(input_field)
            self.checkbox_hex.append(checkbox_hex)
            self.checkbox_send_with_enders.append(checkbox_send_with_ender)
            self.interVal.append(input_interval)

            button.setEnabled(isEnable)
            input_field.setEnabled(isEnable)
            input_field.returnPressed.connect(
                self.handle_button_click(
                    i,
                    input_field,
                    checkbox,
                    checkbox_hex,
                    checkbox_send_with_ender,
                    input_interval,
                )
            )
            button.clicked.connect(
                self.handle_button_click(
                    i,
                    input_field,
                    checkbox,
                    checkbox_hex,
                    checkbox_send_with_ender,
                    input_interval,
                )
            )

    def create_input_field_key_handler(self, input_field, index):
        """为输入框创建键盘事件处理器"""
        def key_press_handler(event):
            if event.key() == Qt.Key_Up:
                # 上方向键：聚焦到上一个输入框
                if index > 0:
                    self.input_fields[index - 1].setFocus()
                    self.input_fields[index - 1].selectAll()
                return
            elif event.key() == Qt.Key_Down:
                # 下方向键：聚焦到下一个输入框
                if index < len(self.input_fields) - 1:
                    self.input_fields[index + 1].setFocus()
                    self.input_fields[index + 1].selectAll()
                return
            else:
                # 其他按键使用默认处理
                QLineEdit.keyPressEvent(input_field, event)
        return key_press_handler

    def setup_input_navigation(self):
        """设置输入框导航功能（也可以从外部调用来激活第一个输入框）"""
        if len(self.input_fields) > 0:
            self.input_fields[0].setFocus()
            self.input_fields[0].selectAll()

    def clear_dynamic_controls(self):
        """安全地清理动态创建的控件（保留第一行的settings_button_group）"""
        if not hasattr(self, "button_groupbox") or not self.button_groupbox.layout():
            return
            
        layout = self.button_groupbox.layout()
        
        # 收集需要删除的控件（从第2行开始，保留第0行的settings_button_group）
        widgets_to_remove = []
        
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                # 检查控件的网格位置
                row, col, rowspan, colspan = layout.getItemPosition(i)
                if row > 0 and widget != self.settings_button_group:  # 保留第0行和settings_button_group
                    widgets_to_remove.append(widget)
        
        # 安全删除控件
        for widget in widgets_to_remove:
            if widget and not widget.isHidden():
                widget.setParent(None)
                widget.deleteLater()
        
    def init_UI(self):
        # Pre actions before the initialization of the UI.
        self.pre_init_UI()
        
        # Create menu bar
        self.menu_bar = QMenuBar()

        # Create Settings menu
        self.settings_menu = self.menu_bar.addMenu("Settings")

        self.save_settings_action = self.settings_menu.addAction("Save Config")
        self.save_settings_action.setShortcut("Ctrl+Shift+S")
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
        self.style_config_action = self.settings_menu.addAction("Style Configuration")
        self.style_config_action.setShortcut("Ctrl+T")
        self.style_config_action.triggered.connect(self.show_style_config)
        
        # Crete Tools menu
        self.tools_menu = self.menu_bar.addMenu("Tools")
        
        self.calculate_length_action = self.tools_menu.addAction("Calculate Length")
        self.calculate_length_action.triggered.connect(self.calculate_length)
        self.generate_string_action = self.tools_menu.addAction("Generate String")
        self.generate_string_action.triggered.connect(self.generate_string)
        self.string_ascii_convert_action = self.tools_menu.addAction("String - ASCII Converter")
        self.string_ascii_convert_action.triggered.connect(self.string_ascii_convert)
        self.custom_toggle_switch_action = self.tools_menu.addAction("Record MODE")
        self.custom_toggle_switch_action.triggered.connect(self.custom_toggle_switch)
        
        # Create About menu
        self.about_menu = self.menu_bar.addMenu("About")

        self.help_menu_action = self.about_menu.addAction("Help")
        self.help_menu_action.setShortcut("Ctrl+/")
        self.help_menu_action.triggered.connect(self.show_help_info)

        self.update_info_action = self.about_menu.addAction("Update Info")
        self.update_info_action.setShortcut("Ctrl+U")
        self.update_info_action.triggered.connect(self.show_update_info)

        self.known_issues_action = self.about_menu.addAction("Known Issues")
        self.known_issues_action.triggered.connect(self.show_known_issues_info)
        self.known_issues_action.setShortcut("Ctrl+K")

        self.about_menu_action = self.about_menu.addAction("About")
        self.about_menu_action.setShortcut("Ctrl+I")
        self.about_menu_action.triggered.connect(self.show_about_info)

        # Create a flag to indicate whether the thread should stop
        self.stop_ports_update_thread = False
        self.stop_textarea_update_thread = True

        # 重新设计的简洁ComboBox - 使用占位符和标签设计
        self.serial_port_label = QLabel("Port:")
        self.serial_port_combo = QComboBox()
        self.serial_port_combo.addItems([port.device for port in list_ports.comports()])
        if self.serial_port_combo.count() == 0:
            self.serial_port_combo.addItem("No devices found")
        self.serial_port_combo.setObjectName("clean_settings_combo")
        self.serial_port_combo.setToolTip("Select serial communication port")
        # Use the default showPopup method
        self.serial_port_combo.showPopup = self.port_update

        self.baud_rate_label = QLabel("BaudRate:")
        self.baud_rate_combo = QComboBox()
        baud_rates = [
            "50", "75", "110", "134", "150", "200", "300", "600", "1200", "1800",
            "2400", "4800", "7200", "9600", "14400", "19200", "28800", "38400",
            "57600", "76800", "115200", "128000", "153600", "230400", "256000",
            "460800", "500000", "576000", "921600", "1000000", "1152000", "1500000",
            "2000000", "2500000", "3000000", "3500000", "4000000", "4500000",
            "5000000", "5500000", "6000000", "6500000", "7000000", "7500000", "8000000"
        ]
        self.baud_rate_combo.addItems(baud_rates)
        self.baud_rate_combo.setCurrentText("115200")
        self.baud_rate_combo.setObjectName("clean_settings_combo")
        self.baud_rate_combo.setToolTip("Select baud rate for serial communication")
        
        # 更多设置的ComboBox - 集成标签到选项中
        self.stopbits_combo = QComboBox()
        self.stopbits_combo.addItems(["StopBits: 1", "StopBits: 1.5", "StopBits: 2"])
        self.stopbits_combo.setCurrentText("StopBits: 1")
        self.stopbits_combo.setObjectName("more_settings_combo")
        self.stopbits_combo.setToolTip("Configure stop bits for serial communication")

        self.parity_combo = QComboBox()
        self.parity_combo.addItems(["Parity: None", "Parity: Even", "Parity: Odd", "Parity: Mark", "Parity: Space"])
        self.parity_combo.setCurrentText("Parity: None")
        self.parity_combo.setObjectName("more_settings_combo")
        self.parity_combo.setToolTip("Configure parity checking for serial communication")

        self.bytesize_combo = QComboBox()
        self.bytesize_combo.addItems(["ByteSize: 5", "ByteSize: 6", "ByteSize: 7", "ByteSize: 8"])
        self.bytesize_combo.setCurrentText("ByteSize: 8")
        self.bytesize_combo.setObjectName("more_settings_combo")
        self.bytesize_combo.setToolTip("Configure data bits per byte for serial communication")

        self.flowcontrol_combo = QComboBox()
        self.flowcontrol_combo.addItems(["FlowControl: None", "FlowControl: RTS/CTS", "FlowControl: XON/XOFF", "FlowControl: DSR/DTR"])
        self.flowcontrol_combo.setCurrentText("FlowControl: None")
        self.flowcontrol_combo.setObjectName("more_settings_combo")
        self.flowcontrol_combo.setToolTip("Configure flow control for serial communication")

        self.dtr_checkbox = QCheckBox("DTR")
        self.dtr_checkbox.setObjectName("settings_checkbox")
        self.dtr_checkbox.setToolTip("Data Terminal Ready - Control DTR pin state")
        self.dtr_checkbox.stateChanged.connect(self.dtr_state_changed)

        self.rts_checkbox = QCheckBox("RTS")
        self.rts_checkbox.setObjectName("settings_checkbox")
        self.rts_checkbox.setToolTip("Request To Send - Control RTS pin state")
        self.rts_checkbox.stateChanged.connect(self.rts_state_changed)

        self.checkbox_send_with_ender = QCheckBox("SendWithEnder")
        self.checkbox_send_with_ender.setObjectName("settings_checkbox")
        self.checkbox_send_with_ender.setToolTip("Automatically append line ending characters")
        self.checkbox_send_with_ender.setChecked(True)

        self.control_char_checkbox = QCheckBox("Show\\r\\n")
        self.control_char_checkbox.setObjectName("settings_checkbox")
        self.control_char_checkbox.setToolTip("Display control characters (carriage return and line feed)")
        self.control_char_checkbox.stateChanged.connect(self.control_char_state_changed)

        self.timeStamp_checkbox = QCheckBox("TimeStamp")
        self.timeStamp_checkbox.setObjectName("settings_checkbox")
        self.timeStamp_checkbox.setToolTip("Add timestamp to received data")
        self.timeStamp_checkbox.stateChanged.connect(self.timeStamp_state_changed)

        self.received_hex_data_checkbox = QCheckBox("RecvHex")
        self.received_hex_data_checkbox.setObjectName("settings_checkbox")
        self.received_hex_data_checkbox.setToolTip("Display received data in hexadecimal format")
        self.received_hex_data_checkbox.stateChanged.connect(
            self.received_hex_data_state_changed
        )

        self.input_path_data_received = QLineEdit()
        self.input_path_data_received.setText(
            common.safe_resource_path("tmps/temp.log")
        )
        self.input_path_data_received.setPlaceholderText("Log file path - double click to select")
        self.input_path_data_received.setReadOnly(True)
        self.input_path_data_received.mouseDoubleClickEvent = (
            self.select_received_file
        )
        self.checkbox_data_received = QCheckBox("Save Log")
        self.checkbox_data_received.setObjectName("settings_checkbox")
        self.checkbox_data_received.setToolTip("Save received data to file")
        self.checkbox_data_received.stateChanged.connect(
            self.handle_data_received_checkbox
        )

        self.port_button = QPushButton("Open Port")
        self.port_button.clicked.connect(self.port_on)
        self.port_button.setShortcut("Ctrl+O")
        self.port_button.setToolTip("Shortcut: Ctrl+O")

        self.toggle_button = QPushButton()
        self.toggle_button.setObjectName("icon_button")
        self.toggle_button.setToolTip("Show More Options")
        self.toggle_button.setIcon(QIcon(common.safe_resource_path("res/expander-down.png")))
        self.toggle_button_is_expanded = False
        self.toggle_button.clicked.connect(self.show_more_options)

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setObjectName("status_label")
        self.set_status_label("Closed", "disconnected")

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
        self.expand_button.setObjectName("icon_button")
        self.expand_button.setIcon(
            QIcon(common.safe_resource_path("res/expand.png"))
        )  # You need to have an icon for this
        self.expand_button.setCheckable(True)
        self.expand_button.setChecked(False)
        self.expand_button.clicked.connect(self.expand_command_input)

        self.send_button = QPushButton("Send")
        self.send_button.setEnabled(False)
        self.send_button.clicked.connect(self.send_command)

        # Add SendAsHex checkbox for command input
        self.command_send_as_hex_checkbox = QCheckBox("Hex")
        self.command_send_as_hex_checkbox.setObjectName("command_hex_checkbox")
        self.command_send_as_hex_checkbox.setChecked(False)
        self.command_send_as_hex_checkbox.setToolTip("Send command as hexadecimal data")

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
        
        # 重新设计的清晰布局 - 标签+控件的经典设计
        self.settings_layout.addWidget(self.serial_port_label, 0, 0, 1, 1, alignment=Qt.AlignRight)
        self.settings_layout.addWidget(self.serial_port_combo, 0, 1, 1, 1)
        self.settings_layout.addWidget(self.baud_rate_label, 1, 0, 1, 1, alignment=Qt.AlignRight)
        self.settings_layout.addWidget(self.baud_rate_combo, 1, 1, 1, 1)
        self.settings_layout.addWidget(self.port_button, 0, 2, 1, 2)
        self.settings_layout.addWidget(self.status_label, 1, 2, 1, 1)
        self.settings_layout.addWidget(self.toggle_button, 1, 3, 1, 1) 
        
        # 设置列拉伸比例，使布局更协调
        self.settings_layout.setColumnStretch(0, 0)  # 标签列固定宽度
        self.settings_layout.setColumnStretch(1, 2)  # ComboBox列可拉伸
        self.settings_layout.setColumnStretch(2, 1)  # 按钮列固定宽度
        self.settings_layout.setColumnStretch(3, 0)  # 切换按钮列固定宽度

        # 创建可折叠的配置区域容器
        self.settings_more_widget = QWidget()
        self.settings_more_widget.setObjectName("settings_more_widget")
        self.settings_more_layout = QGridLayout(self.settings_more_widget)
        self.settings_more_layout.setContentsMargins(12, 12, 12, 12)
        self.settings_more_layout.setSpacing(15)

        # 设置更大的行间距和列间距，避免重叠
        self.settings_more_layout.setVerticalSpacing(18)
        self.settings_more_layout.setHorizontalSpacing(25)

        # 设置列的拉伸比例 - 简洁的3列设计
        self.settings_more_layout.setColumnStretch(0, 1)  # 第1列
        self.settings_more_layout.setColumnStretch(1, 1)  # 第2列  
        self.settings_more_layout.setColumnStretch(2, 1)  # 第3列
        
        # 串口配置参数 - 直接使用ComboBox，无需标签
        # 第一行：3个主要串口参数ComboBox
        self.settings_more_layout.addWidget(self.stopbits_combo, 1, 0, 1, 1)
        self.settings_more_layout.addWidget(self.parity_combo, 1, 1, 1, 1)
        self.settings_more_layout.addWidget(self.bytesize_combo, 1, 2, 1, 1)
        
        # 第二行：FlowControl ComboBox 跨前两列
        self.settings_more_layout.addWidget(self.flowcontrol_combo, 2, 0, 1, 2)

        # 第三行和第四行：复选框 - 3列布局，2行排列
        self.settings_more_layout.addWidget(self.dtr_checkbox, 3, 0, 1, 1)
        self.settings_more_layout.addWidget(self.rts_checkbox, 3, 1, 1, 1)
        self.settings_more_layout.addWidget(self.control_char_checkbox, 3, 2, 1, 1)
        self.settings_more_layout.addWidget(self.timeStamp_checkbox, 4, 0, 1, 1)
        self.settings_more_layout.addWidget(self.checkbox_send_with_ender, 4, 1, 1, 1)
        self.settings_more_layout.addWidget(self.received_hex_data_checkbox, 4, 2, 1, 1)

        # 文件保存区域布局 - 重新排列，去掉QLabel
        self.settings_more_layout.addWidget(self.input_path_data_received, 5, 0, 1, 2)  # 跨两列
        self.settings_more_layout.addWidget(self.checkbox_data_received, 5, 2, 1, 1)

        # 调整固定高度适应优化的布局，增加高度避免重叠
        self.settings_more_widget.setFixedHeight(240)  # 进一步增加高度以适应新的边距和内边距
        self.settings_more_widget.setVisible(False)
        
        self.settings_layout.addWidget(self.settings_more_widget, 2, 0, 1, 4)  # 跨越所有列

        # Create a group box for the command section
        self.command_groupbox = QGroupBox("Command")
        self.command_groupbox.mouseDoubleClickEvent = (
            lambda event: self.set_command_groupbox_visible()
        )
        self.command_layout = QHBoxLayout(self.command_groupbox)
        self.command_layout.addWidget(self.command_input)
        self.command_layout.addWidget(self.expand_button)
        self.command_layout.addWidget(self.command_send_as_hex_checkbox)
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
        
        # Add settings button group
        self.add_settings_button_group()

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
        self.right_layout.addWidget(self.settings_button_group)
        self.right_layout.addWidget(self.button_scroll_area)

        # Create a layout_1 for the widget
        layout_1 = QHBoxLayout()
        layout_1.addLayout(self.left_layout)
        layout_1.addLayout(self.right_layout)

        layout_2 = QVBoxLayout()
        
        # 创建ATCommand页面的标题栏，包含状态和保存按钮
        at_command_header = QHBoxLayout()
        self.label_layout_2 = QLabel("")
        self.label_layout_2.setObjectName("page_title")
        # 允许鼠标悬停显示完整路径
        self.label_layout_2.setToolTip("")
        self.label_layout_2.setMaximumWidth(300)
        self.label_layout_2.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        
        layout_2.addLayout(at_command_header)
        
        self.text_input_layout_2 = QTextEdit()
        self.text_input_layout_2.setDocument(QTextDocument(None))
        self.text_input_layout_2.setLineWrapMode(QTextEdit.WidgetWidth)
        self.text_input_layout_2.setObjectName("text_input_layout_2")
        self.text_input_layout_2.setAcceptRichText(False)
        
        # 监听文本变化
        self.text_input_layout_2.textChanged.connect(self.on_at_command_text_changed)
        
        layout_2_main = QHBoxLayout()
        layout_2_main.addWidget(self.text_input_layout_2)
        
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

        # 展开/收起按钮保持原有设置
        self.expand_left_button = QPushButton()
        self.expand_left_button.setFixedWidth(30)
        self.expand_left_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.expand_left_button.setObjectName("icon_button")
        self.expand_left_button.setIcon(QIcon(common.safe_resource_path("res/direction_left.png")))
        self.expand_left_button.clicked.connect(self.set_radio_groupbox_visible)

        # 文件状态标签
        self.at_file_status_label = QLabel("")
        self.at_file_status_label.setObjectName("file_status_label")
        
        # 整合的保存按钮（同时保存路径配置和AT命令文件）
        self.integrated_save_button = QPushButton()
        self.integrated_save_button.setObjectName("icon_button")
        self.integrated_save_button.setFixedSize(30, 30)
        self.integrated_save_button.setIcon(QIcon(common.safe_resource_path("res/save.png")))
        self.integrated_save_button.setToolTip("Save path configuration and AT command file (Ctrl+S)")
        self.integrated_save_button.clicked.connect(self.save_integrated_function)
        self.integrated_save_button.setEnabled(False)
        
        at_command_header.addWidget(self.label_layout_2)
        at_command_header.addStretch()
        at_command_header.addWidget(self.at_file_status_label)
        # at_command_header.addWidget(self.integrated_save_button)

        # 导入按钮
        self.import_button = QPushButton()
        self.import_button.setObjectName("icon_button")
        self.import_button.setFixedSize(30, 30)
        self.import_button.setIcon(QIcon(common.safe_resource_path("res/import.png")))
        self.import_button.setToolTip("Import AT command file")
        self.import_button.clicked.connect(self.import_at_command_file)

        # 将按钮添加到左侧容器
        left_buttons_layout.addWidget(self.integrated_save_button)
        left_buttons_layout.addWidget(self.import_button)
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
        for i in range(16):
            path_key = f"Path_{i+1}"
            path_value = self.config.get("Paths", path_key, fallback="")
            self.path_configs.append(path_value)

        for i in range(16):
            radio_button = QRadioButton(f"Path {i + 1}")
            radio_button.toggled.connect(
                lambda state, x=i: self.handle_radio_button_click(x)
            )
            path_input = QLineEdit()
            path_input.mouseDoubleClickEvent = lambda event, pi=path_input: (
                self.select_json_file(pi) if event else None
            )
            path_input.setPlaceholderText("Path, double click to select")
            path_input.setVisible(False)
            
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
        self.text_input_layout_3.setObjectName("text_input_layout_3")
        self.text_input_layout_3.setAcceptRichText(False)

        layout_4 = QVBoxLayout()
        self.label_layout_4 = QLabel("No TimeStamp")
        self.text_input_layout_4 = QTextEdit()
        self.text_input_layout_4.setDocument(QTextDocument(None))
        self.text_input_layout_4.setLineWrapMode(QTextEdit.WidgetWidth)
        layout_4.addWidget(self.label_layout_4)
        layout_4.addWidget(self.text_input_layout_4)
        self.text_input_layout_4.setObjectName("text_input_layout_4")
        self.text_input_layout_4.setAcceptRichText(False)
        
        layout_5 = QVBoxLayout()
        self.dict_recorder_window = DictRecorderWindow()
        layout_5.addWidget(self.dict_recorder_window)

        # Create a button section for switching other layouts
        self.button1 = QPushButton("Main")
        self.button1.setToolTip("Shortcut: F1")
        self.button1.setObjectName("nav_button_active")
        self.button1.setDefault(True)
        self.button1.clicked.connect(lambda: self.show_page(0))

        self.button2 = QPushButton("ATCommand")
        self.button2.setToolTip("Shortcut: F2")
        self.button2.setObjectName("nav_button")
        self.button2.clicked.connect(lambda: self.show_page(1))

        self.button3 = QPushButton("Log")
        self.button3.setToolTip("Shortcut: F3")
        self.button3.setObjectName("nav_button")
        self.button3.clicked.connect(lambda: self.show_page(2))

        self.button4 = QPushButton("NoTimeStamp")
        self.button4.setToolTip("Shortcut: F4")
        self.button4.setObjectName("nav_button")
        self.button4.clicked.connect(lambda: self.show_page(3))
        
        self.button5 = QPushButton("DictRecorder")
        self.button5.setToolTip("Shortcut: F5")
        self.button5.setObjectName("nav_button")
        self.button5.clicked.connect(lambda: self.show_page(4))
        
        self.button6 = QPushButton("DictExecuter")
        self.button6.setToolTip("Shortcut: F6")
        self.button6.setObjectName("nav_button")
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
        
        # 设置初始状态 - 路径选项框收起，宽度调整为100以显示更多内容
        self.radio_scroll_area.setMaximumWidth(100)
        self.expand_left_button.setIcon(QIcon(common.safe_resource_path("res/direction_left.png")))
        
        # 初始化AT命令文件状态
        self.at_command_manager.set_file_path(self.path_ATCommand)
        # 尝试加载现有文件内容，如果文件不存在则设置为空
        if os.path.exists(self.path_ATCommand):
            content, error_msg = self.at_command_manager.load_file(self.path_ATCommand)
            if not error_msg:
                # 文件加载成功，但不更新UI（UI此时可能还没准备好）
                pass
            else:
                # 文件加载失败，设置为空状态
                self.at_command_manager.original_content = ""
                self.at_command_manager.current_content = ""
        else:
            # 文件不存在，设置为空状态
            self.at_command_manager.original_content = ""
            self.at_command_manager.current_content = ""
        self.update_at_command_status()
        
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
            # 设置主要ComboBox值（直接值，无需标签前缀）
            port_value = config.get("Set", "Port")
            self.serial_port_combo.setCurrentText(port_value)
            baudrate_value = config.get("Set", "BaudRate")
            self.baud_rate_combo.setCurrentText(baudrate_value)
            # 设置更多设置ComboBox值 - 使用带标签的格式
            stopbits_value = config.get("Set", "StopBits")
            self.stopbits_combo.setCurrentText(f"StopBits: {stopbits_value}")
            parity_value = config.get("Set", "Parity")
            self.parity_combo.setCurrentText(f"Parity: {parity_value}")
            bytesize_value = config.get("Set", "ByteSize")
            self.bytesize_combo.setCurrentText(f"ByteSize: {bytesize_value}")
            flowcontrol_value = config.get("Set", "FlowControl")
            self.flowcontrol_combo.setCurrentText(f"FlowControl: {flowcontrol_value}")
            self.dtr_checkbox.setChecked(config.getboolean("Set", "DTR"))
            self.rts_checkbox.setChecked(config.getboolean("Set", "RTS"))
            self.checkbox_send_with_ender.setChecked(
                config.getboolean("Set", "SendWithEnter")
            )
            self.control_char_checkbox.setChecked(config.getboolean("Set", "ShowSymbol"))
            self.timeStamp_checkbox.setChecked(config.getboolean("Set", "TimeStamp"))
            self.received_hex_data_checkbox.setChecked(
                config.getboolean("Set", "ReceivedHex")
            )
            self.input_path_data_received.setText(config.get("Set", "PathDataReceived"))
            self.checkbox_data_received.setChecked(
                config.getboolean("Set", "IsSaveDataReceived")
            )
            self.file_input.setText(config.get("Set", "PathFileSend"))
            
            # 加载命令发送hex模式配置
            try:
                self.command_send_as_hex_checkbox.setChecked(
                    config.getboolean("Set", "CommandSendAsHex")
                )
            except (configparser.NoSectionError, configparser.NoOptionError):
                self.command_send_as_hex_checkbox.setChecked(False)
            
            # 加载路径配置
            if "Paths" in config:
                for i in range(1, 16):
                    path_key = f"Path_{i}"
                    if path_key in config["Paths"]:
                        path_value = config["Paths"][path_key]
                        if i <= len(self.path_command_inputs):
                            self.path_command_inputs[i-1].setText(path_value)
        except configparser.NoSectionError as e:
            logger.error(f"Error applying config: {e}")
        except configparser.NoOptionError as e:
            logger.error(f"Error applying config: {e}")

        # Hotkeys
        # for i in range(1, 9):
        #     hotkey_text = config.get("Hotkeys", f"Hotkey_{i}", fallback="")
        #     self.hotkey_buttons[i - 1].setText(hotkey_text)
        #     hotkey_value = config.get("HotkeyValues", f"HotkeyValue_{i}", fallback="")
        #     self.hotkey_buttons[i - 1].clicked.connect(
        #         self.handle_hotkey_click(i, hotkey_value)
        #     )

    # 辅助方法：从集成标签的ComboBox中提取实际值
    def get_stopbits_value(self):
        """从StopBits ComboBox中提取实际的停止位值"""
        text = self.stopbits_combo.currentText()
        return text.split(": ")[1] if ": " in text else text

    def get_parity_value(self):
        """从Parity ComboBox中提取实际的校验位值"""
        text = self.parity_combo.currentText()
        return text.split(": ")[1] if ": " in text else text

    def get_bytesize_value(self):
        """从ByteSize ComboBox中提取实际的字节大小值"""
        text = self.bytesize_combo.currentText()
        return text.split(": ")[1] if ": " in text else text

    def get_flowcontrol_value(self):
        """从FlowControl ComboBox中提取实际的流控制值"""
        text = self.flowcontrol_combo.currentText()
        return text.split(": ")[1] if ": " in text else text

    def get_serial_port_value(self):
        """从Port ComboBox中获取端口值"""
        return self.serial_port_combo.currentText()

    def get_baud_rate_value(self):
        """从BaudRate ComboBox中获取波特率值"""
        return self.baud_rate_combo.currentText()

    def save_config(self, config):
        try:
            # Set
            config.set("Set", "Port", self.get_serial_port_value())
            config.set("Set", "BaudRate", self.get_baud_rate_value())
            config.set("Set", "StopBits", self.get_stopbits_value())
            config.set("Set", "Parity", self.get_parity_value())
            config.set("Set", "ByteSize", self.get_bytesize_value())
            config.set("Set", "FlowControl", self.get_flowcontrol_value())
            config.set("Set", "DTR", str(self.dtr_checkbox.isChecked()))
            config.set("Set", "RTS", str(self.rts_checkbox.isChecked()))
            config.set(
                "Set", "SendWithEnter", str(self.checkbox_send_with_ender.isChecked())
            )
            config.set("Set", "ShowSymbol", str(self.control_char_checkbox.isChecked()))
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
            
            # 保存命令发送hex模式配置
            config.set("Set", "CommandSendAsHex", str(self.command_send_as_hex_checkbox.isChecked()))
            
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

            logger.info("Saving config to config.ini")
            common.write_config(config)
        except Exception as e:
            logger.error(f"Error saving config: {e}")

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
                logger.error(f"Invalid shortcut: {hotkey_shortcut}")

        # Ensure each button is only connected once
        for button in self.hotkey_buttons:
            hotkey_value = self.config.get("HotkeyValues", f"HotkeyValue_{self.hotkey_buttons.index(button) + 1}", fallback="")
            button.clicked.connect(self.handle_hotkey_click(self.hotkey_buttons.index(button) + 1, hotkey_value))

    def show_page(self, index):
        # 如果正在切换到或从ATCommand页面，处理保存逻辑
        current_index = self.stacked_widget.currentIndex()
        
        # 从ATCommand页面切换出去时的处理
        if current_index == 1 and index != 1:
            if self.handle_at_command_page_leave():
                return  # 用户取消了切换
        
        # 切换到ATCommand页面时的处理
        if index == 1:
            self.handle_at_command_page_enter()
        elif index == 2 or current_index == 2:
            # Log页面 - 从日志文件读取完整日志（优先使用输入框里的路径），失败时回退到组件内容
            log_path = ""
            try:
                if hasattr(self, 'input_path_data_received'):
                    log_path = self.input_path_data_received.text()
                else:
                    log_path = self.config.get('Set', 'PathDataReceived', fallback='')

                if log_path and os.path.exists(log_path):
                    with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                else:
                    # 回退到接收组件中的内容
                    content = self.received_data_textarea.toPlainText()
            except Exception as e:
                logger.error(f"Error reading log file {log_path}: {e}")
                content = self.received_data_textarea.toPlainText()

            self.text_input_layout_3.setPlainText(content)

        elif index == 3 or current_index == 3:
            # NoTimeStamp页面 - 基于日志文件内容去除时间戳后显示
            log_path = ""
            try:
                if hasattr(self, 'input_path_data_received'):
                    log_path = self.input_path_data_received.text()
                else:
                    log_path = self.config.get('Set', 'PathDataReceived', fallback='')

                if log_path and os.path.exists(log_path):
                    with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                else:
                    content = self.received_data_textarea.toPlainText()
            except Exception as e:
                logger.error(f"Error reading log file {log_path}: {e}")
                content = self.received_data_textarea.toPlainText()

            try:
                no_ts = common.remove_TimeStamp(content, self.config["MoreSettings"]["TimestampRegex"])
            except Exception as e:
                logger.error(f"Error removing timestamp: {e}")
                no_ts = content

            self.text_input_layout_4.setPlainText(no_ts)
        elif index == 4 or current_index == 4:
            pass
            
        self.stacked_widget.setCurrentIndex(index)
        self.update_button_style(index)
    
    def handle_at_command_page_enter(self):
        """处理进入ATCommand页面的逻辑"""
        try:
            # 更新AT命令管理器的文件路径
            self.at_command_manager.set_file_path(self.path_ATCommand)
            
            # 如果文本框为空，尝试加载文件
            if self.text_input_layout_2.toPlainText() == "":
                content, error_msg = self.at_command_manager.load_file(self.path_ATCommand)
                if error_msg:
                    # 显示错误对话框
                    ErrorDialog.show_error(
                        parent=self,
                        title="Failed to Read AT Command File",
                        message=f"Unable to read AT command file: {self.path_ATCommand}",
                        details=error_msg
                    )
                    # 如果文件不存在，询问是否创建默认文件
                    if "File does not exist" in error_msg or "文件不存在" in error_msg:
                        self.offer_create_default_file()
                else:
                    self.text_input_layout_2.setPlainText(content)
            else:
                # 如果文本框有内容，同步更新管理器的原始内容和当前内容
                current_content = self.text_input_layout_2.toPlainText()
                self.at_command_manager.original_content = current_content
                self.at_command_manager.current_content = current_content
                self.at_command_manager.is_modified = False
        except Exception as e:
            logger.error(f"Error handling AT command page enter: {e}")
    
    def handle_at_command_page_leave(self) -> bool:
        """
        处理离开ATCommand页面的逻辑
        
        Returns:
            bool: True表示用户取消了切换，False表示可以继续切换
        """
        try:
            # 更新当前内容到管理器
            current_content = self.text_input_layout_2.toPlainText()
            self.at_command_manager.update_content(current_content)
            
            # 检查是否有未保存的更改
            if self.at_command_manager.has_unsaved_changes():
                choice = self.at_command_manager.prompt_save_changes()
                
                if choice == "cancel":
                    return True  # 用户取消，不切换页面
                elif choice == "save":
                    # 保存文件
                    success, error_msg = self.at_command_manager.save_file()
                    if not success:
                        ErrorDialog.show_error(
                            parent=self,
                            title="Save Failed",
                            message="Failed to save AT command file",
                            details=error_msg
                        )
                        return True  # 保存失败，不切换页面
                    else:
                        # 保存成功，更新配置
                        self.save_paths_to_config()
                elif choice == "discard":
                    # 丢弃更改，重新加载原始内容
                    original_content, _ = self.at_command_manager.load_file(self.path_ATCommand)
                    self.text_input_layout_2.setPlainText(original_content)
                # choice == "no_changes" 时不需要处理
            
            return False  # 可以继续切换页面
            
        except Exception as e:
            logger.error(f"Error handling AT command page leave: {e}")
            return False
    
    def offer_create_default_file(self):
        """询问用户是否创建默认文件"""
        from PySide6.QtWidgets import QMessageBox
        
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setWindowTitle("File Not Found")
        msg_box.setText(f"AT command file does not exist: {self.path_ATCommand}")
        msg_box.setInformativeText("Would you like to create a new file with default commands?")
        
        create_button = msg_box.addButton("Create Default File", QMessageBox.AcceptRole)
        skip_button = msg_box.addButton("Skip", QMessageBox.RejectRole)
        
        msg_box.setDefaultButton(create_button)
        msg_box.exec()
        
        if msg_box.clickedButton() == create_button:
            success, error_msg = self.at_command_manager.create_default_file(self.path_ATCommand)
            if success:
                # 加载新创建的文件内容
                content, _ = self.at_command_manager.load_file(self.path_ATCommand)
                self.text_input_layout_2.setPlainText(content)
                
                # 显示成功信息
                ErrorDialog.show_info(
                    parent=self,
                    title="File Created Successfully",
                    message=f"Default AT command file created: {self.path_ATCommand}",
                    details="The file contains some basic AT command examples that you can modify as needed."
                )
                # 将新创建的文件设置到管理器并刷新显示（更新文件名标签）
                try:
                    self.at_command_manager.set_file_path(self.path_ATCommand)
                except Exception:
                    pass
                try:
                    self.update_at_command_status()
                except Exception:
                    pass
            else:
                ErrorDialog.show_error(
                    parent=self,
                    title="File Creation Failed",
                    message="Unable to create default AT command file",
                    details=error_msg
                )
    
    def save_at_command_file(self):
        """手动保存AT命令文件"""
        try:
            current_content = self.text_input_layout_2.toPlainText()
            self.at_command_manager.update_content(current_content)
            
            success, error_msg = self.at_command_manager.save_file()
            if success:
                # 保存配置
                self.save_paths_to_config()
                # 更新状态显示
                self.update_at_command_status()
            else:
                ErrorDialog.show_error(
                    parent=self,
                    title="Save Failed",
                    message="Failed to save AT command file",
                    details=error_msg
                )
        except Exception as e:
            logger.error(f"Error saving AT command file manually: {e}")
    
    def on_at_command_text_changed(self):
        """AT命令文本变化时的处理"""
        try:
            if hasattr(self, 'at_command_manager'):
                current_content = self.text_input_layout_2.toPlainText()
                self.at_command_manager.update_content(current_content)
                self.update_at_command_status()
        except Exception as e:
            logger.error(f"Error handling AT command text change: {e}")
    
    def update_at_command_status(self):
        """更新AT命令文件状态显示"""
        try:
            if hasattr(self, 'at_command_manager'):
                file_info = self.at_command_manager.get_file_info()
                
                # 更新状态标签
                if file_info["is_modified"]:
                    self.at_file_status_label.setText("● Unsaved")
                    self.at_file_status_label.setProperty("status", "modified")
                    self.integrated_save_button.setEnabled(True)
                else:
                    self.at_file_status_label.setText("Saved")
                    self.at_file_status_label.setProperty("status", "saved")
                    self.integrated_save_button.setEnabled(False)
                
                # 更新文件名标签（显示 basename，tooltip 显示完整路径）
                try:
                    file_path = file_info.get("file_path", "")
                    if file_path:
                        basename = os.path.basename(file_path)
                        self.label_layout_2.setText(basename)
                        self.label_layout_2.setToolTip(file_path)
                    else:
                        self.label_layout_2.setText("No file")
                        self.label_layout_2.setToolTip("")
                except Exception:
                    # 保持原样，不影响主要状态更新
                    pass

                # 刷新样式
                self.at_file_status_label.style().unpolish(self.at_file_status_label)
                self.at_file_status_label.style().polish(self.at_file_status_label)
                
        except Exception as e:
            logger.error(f"Error updating AT command status: {e}")

    def update_button_style(self, index):
        buttons = [self.button1, self.button2, self.button3, self.button4, self.button5, self.button6]
        for i, button in enumerate(buttons):
            if i == index:
                button.setObjectName("nav_button_active")
            else:
                button.setObjectName("nav_button")
            # 强制刷新样式
            button.style().unpolish(button)
            button.style().polish(button)

    def keyPressEvent(self, event):
        # 处理全局快捷键
        if event.key() == Qt.Key_S and event.modifiers() == Qt.ControlModifier:
            # Ctrl+S 保存AT命令文件（只在ATCommand页面有效）
            if self.stacked_widget.currentIndex() == 1:
                self.save_integrated_function()
                return
        elif event.key() == Qt.Key_F1:
            self.show_page(0)
        elif event.key() == Qt.Key_F2:
            self.show_page(1)
        elif event.key() == Qt.Key_F3:
            self.show_page(2)
        elif event.key() == Qt.Key_F4:
            self.show_page(3)
        elif event.key() == Qt.Key_Right:
            # 右方向键：聚焦到第一个输入框（仅在主页面且没有其他控件聚焦时）
            if (self.stacked_widget.currentIndex() == 0 and 
                hasattr(self, 'input_fields') and 
                len(self.input_fields) > 0 and
                not any(field.hasFocus() for field in self.input_fields)):
                self.setup_input_navigation()
        else:
            # 调用父类的keyPressEvent来处理其他按键
            super().keyPressEvent(event)

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
        
    def show_style_config(self):
        self.style_config_dialog = StyleConfigDialog(self)
        self.style_config_dialog.show()
        
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
        self.custom_toggle_switch_dialog = CustomToggleSwitchDialog(self)
        self.custom_toggle_switch_dialog.show()

    def show_help_info(self):
        help_dialog = HelpDialog()
        help_dialog.exec()

    def show_update_info(self):
        update_dialog = SafeUpdateDialog(self)
        update_dialog.exec()
        
    def show_known_issues_info(self):
        known_issues_dialog = KnownIssuesDialog(self)
        known_issues_dialog.exec()

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

    def control_char_state_changed(self, state):
        if self.main_Serial:
            if state == 2:
                self.data_receiver.is_show_control_char = True
            else:
                self.data_receiver.is_show_control_char = False
        else:
            self.control_char_checkbox.setChecked(state)

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
        # 切换更多设置区域的可见性
        is_visible = self.settings_more_widget.isVisible()
        self.settings_more_widget.setVisible(not is_visible)
        
        # 更新按钮图标和状态
        if is_visible:
            # 当前可见，即将隐藏
            self.toggle_button.setIcon(QIcon(common.safe_resource_path("res/expander-down.png")))
            self.toggle_button_is_expanded = False
        else:
            # 当前隐藏，即将显示
            self.toggle_button.setIcon(QIcon(common.safe_resource_path("res/fork.png")))
            self.toggle_button_is_expanded = True

    def expand_command_input(self):
        self.command_input.setFixedHeight(100)
        self.command_input.setLineWrapMode(QTextEdit.WidgetWidth)
        self.expand_button.setIcon(QIcon(common.safe_resource_path("res/collapse.png")))
        self.expand_button.setChecked(True)
        self.expand_button.clicked.connect(self.collapse_command_input)

    def collapse_command_input(self):
        self.command_input.setFixedHeight(35)
        self.command_input.setLineWrapMode(QTextEdit.WidgetWidth)
        self.expand_button.setIcon(QIcon(common.safe_resource_path("res/expand.png")))
        self.expand_button.setChecked(False)
        self.expand_button.clicked.connect(self.expand_command_input)

    def set_status_label(self, text, color):
        self.status_label.setText(text)
        
        # 根据颜色设置状态属性，使用QSS中定义的样式
        color_to_status = {
            "#198754": "connected",   # 绿色 - 已连接
            "#6c757d": "disconnected", # 灰色 - 已断开
            "#dc3545": "error",       # 红色 - 错误状态
            "#ffc107": "warning",     # 黄色 - 警告状态
            "#17a2b8": "info"         # 青色 - 信息状态
        }
        
        # 如果传入的是状态字符串，直接使用；如果是颜色值，转换为状态
        if color in ["connected", "disconnected", "error", "warning", "info"]:
            status = color
        else:
            status = color_to_status.get(color, "disconnected")
        
        logger.debug(f"Setting status label color to: {color}")
        self.status_label.setProperty("status", status)
        
        # 强制刷新样式
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def port_write(self, command, serial_port, send_with_ender):
        try:
            Ender = self.config.get("MoreSettings", "Ender", fallback="0D0A")

            if send_with_ender:
                common.port_write(command, serial_port, ender=Ender)
            else:
                common.port_write(command, serial_port, ender='')
            self.data_receiver.is_new_data_written = True
            
            # If `ShowCommandEcho` is enabled, show the command in the received data area
            if self.config.getboolean("MoreSettings", "ShowCommandEcho"):
                command_withTimestamp = '(' + common.get_current_time() + ')--> ' + command
                # 只直接添加到显示区域，不加到 full_data_store 避免重复
                self.received_data_textarea.append(command_withTimestamp)
                # self.apply_style(command)
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            self.set_status_label("Failed", "error")

    def port_write_hex(self, hex_command, serial_port, send_with_ender):
        """发送十六进制数据到串口"""
        try:
            # 检查串口是否可用
            if not serial_port or not serial_port.is_open:
                logger.error("Serial port is not available or not open")
                self.set_status_label("Port Error", "error")
                return
            
            # 将十六进制字符串转换为字节
            try:
                hex_bytes = common.hex_str_to_bytes(hex_command)
            except ValueError as e:
                # 如果十六进制格式无效，记录错误并返回
                logger.error(f"Invalid hex format: {hex_command}, error: {e}")
                self.set_status_label("Hex Error", "error")
                return
            
            # 处理结束符
            Ender = self.config.get("MoreSettings", "Ender", fallback="0D0A")

            if send_with_ender and Ender:
                try:
                    ender_bytes = common.hex_str_to_bytes(Ender)
                    serial_port.write(hex_bytes + ender_bytes)
                except ValueError:
                    # 如果结束符格式无效，仅发送数据
                    serial_port.write(hex_bytes)
            else:
                serial_port.write(hex_bytes)
            
            # 标记有新数据写入
            if hasattr(self, 'data_receiver') and self.data_receiver:
                self.data_receiver.is_new_data_written = True
            
            # 处理命令回显 - 支持不同的显示格式
            if self.config.getboolean("MoreSettings", "ShowCommandEcho"):
                # 创建格式化的十六进制显示
                hex_display = ' '.join([f'{b:02X}' for b in hex_bytes])
                
                # 如果包含结束符，也显示结束符
                if send_with_ender and Ender:
                    try:
                        ender_bytes = common.hex_str_to_bytes(Ender)
                        ender_display = ' '.join([f'{b:02X}' for b in ender_bytes])
                        hex_display += f" {ender_display}"
                    except ValueError:
                        pass  # 忽略无效的结束符
                
                # 构造回显消息
                command_withTimestamp = f'({common.get_current_time()})-->[HEX] {hex_display}'
                
                # 只直接添加到显示区域，不加到 full_data_store 避免重复
                if hasattr(self, 'received_data_textarea'):
                    self.received_data_textarea.append(command_withTimestamp)
                
        except Exception as e:
            logger.error(f"Error sending hex command: {e}")
            self.set_status_label("Failed", "error")

    def send_command(self):
        command = self.command_input.toPlainText()
        if not command:
            return
        
        # 使用新的hex复选框状态
        send_as_hex = self.command_send_as_hex_checkbox.isChecked()
        
        if send_as_hex:
            try:
                # 使用统一的 port_write_hex 方法
                self.port_write_hex(
                    command,
                    self.main_Serial,
                    self.checkbox_send_with_ender.isChecked()
                )
                return
                
            except ValueError as e:
                QMessageBox.warning(self, "HEX Conversion Error", f"Error converting to HEX: {str(e)}")
                return
            except Exception as e:
                QMessageBox.warning(self, "Send Error", f"Error sending HEX command: {str(e)}")
                return
        
        # 普通文本发送模式
        self.port_write(command, self.main_Serial, self.checkbox_send_with_ender.isChecked())

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

    def create_json_template(self, file_path, file_name):
        """创建JSON文件模板"""
        template = {
            "name": file_name,
            "description": "AT Command configuration file",
            "version": "1.0",
            "created": datetime.datetime.now().isoformat(),
            "author": "SCOM User",
            "settings": {
                "baudrate": "115200",
                "timeout": 1.0,
                "encoding": "utf-8"
            },
            "Commands": [
                {
                    "name": "Reset Device",
                    "command": "AT+QRST",
                    "description": "Reset the device",
                    "expected_response": "OK",
                    "timeout": 5
                },
                {
                    "name": "Get Version",
                    "command": "AT+QVERSION",
                    "description": "Get firmware version",
                    "expected_response": "OK",
                    "timeout": 3
                }
            ]
        }
        return template

    def select_received_file(self, event=None):
        file_dialog = QFileDialog()
        # 禁用内置覆盖确认，选择已有文件时不弹出覆盖提示；仅在新建文件时显示提示
        file_dialog.setOption(QFileDialog.DontConfirmOverwrite, True)
        file_dialog.setFileMode(QFileDialog.AnyFile)
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)  # 允许保存/新建文件
        file_dialog.setNameFilter("Text Files (*.txt *.log);;All Files (*)")
        file_dialog.setDefaultSuffix("log")  # 默认后缀
        file_dialog.setWindowTitle("Select or Create Log File")

        # 设置默认文件名
        import datetime
        default_name = f"received_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_dialog.selectFile(default_name)

        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0].replace("/", "\\")
            if file_path:
                # 确保文件目录存在（如果有父目录）
                import os
                dir_name = os.path.dirname(file_path)
                if dir_name:
                    os.makedirs(dir_name, exist_ok=True)

                created = False
                # 如果文件不存在，创建一个空文件
                if not os.path.exists(file_path):
                    try:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write("")  # 创建空文件
                        created = True
                    except Exception as e:
                        QMessageBox.warning(self, "Warning", f"Cannot create file: {str(e)}")
                        return

                # 只在新建时提示，已存在文件直接使用路径
                if created:
                    QMessageBox.information(self, "File Created",
                        f"New log file created:\n{file_path}")

                self.input_path_data_received.setText(file_path)

    def select_file(self, file_type="send"):
        """通用文件选择方法
        
        Args:
            file_type: 文件选择的用途类型
                - "send": 选择要发送的文件（默认全类型）
                - "log": 选择日志文件保存位置
                - "json": 选择JSON配置文件
                - "at_command": 导入AT命令文件
        """
        # 定义不同文件类型的配置
        file_type_configs = {
            "send": {
                "mode": QFileDialog.ExistingFile,
                "accept_mode": QFileDialog.AcceptOpen,
                "filters": "All Files (*)",
                "title": "Select File to Send",
                "default_suffix": None,
                "allow_create": False,
                "callback": self._on_send_file_selected
            },
            "log": {
                "mode": QFileDialog.AnyFile,
                "accept_mode": QFileDialog.AcceptSave,
                "filters": "Text Files (*.txt *.log);;JSON Files (*.json);;All Files (*)",
                "title": "Select or Create Log File",
                "default_suffix": "log",
                "allow_create": True,
                "callback": self._on_log_file_selected
            },
            "json": {
                "mode": QFileDialog.AnyFile,
                "accept_mode": QFileDialog.AcceptSave,
                "filters": "JSON Files (*.json);;Text Files (*.txt);;All Files (*)",
                "title": "Select or Create JSON Configuration File",
                "default_suffix": "json",
                "allow_create": True,
                "callback": self._on_json_file_selected
            },
            "at_command": {
                "mode": QFileDialog.ExistingFile,
                "accept_mode": QFileDialog.AcceptOpen,
                "filters": "JSON Files (*.json);;Text Files (*.txt *.log);;All Files (*)",
                "title": "Import AT Command File",
                "default_suffix": None,
                "allow_create": False,
                "callback": self._on_at_command_file_selected
            }
        }
        
        # 获取配置
        config = file_type_configs.get(file_type, file_type_configs["send"])
        
        # 创建文件对话框
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(config["mode"])
        file_dialog.setAcceptMode(config["accept_mode"])
        file_dialog.setNameFilter(config["filters"])
        file_dialog.setWindowTitle(config["title"])
        
        if config["default_suffix"]:
            file_dialog.setDefaultSuffix(config["default_suffix"])
        
        # 如果允许创建新文件，禁用内置覆盖确认
        if config["allow_create"]:
            file_dialog.setOption(QFileDialog.DontConfirmOverwrite, True)
        
        # 执行对话框
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0].replace("/", "\\")
            if file_path and config["callback"]:
                config["callback"](file_path, config["allow_create"])
    
    def _on_send_file_selected(self, file_path: str, allow_create: bool):
        """处理发送文件选择完成的回调"""
        self.file_input.setText(file_path)
        try:
            file_size = os.path.getsize(file_path)
            self.progress_bar.setMaximum(100)
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat(f"File size: {file_size} bytes")
        except OSError as e:
            QMessageBox.warning(self, "Warning", f"Cannot get file size: {str(e)}")
            self.progress_bar.setFormat("File size: Unknown")
    
    def _on_log_file_selected(self, file_path: str, allow_create: bool):
        """处理日志文件选择完成的回调"""
        # 确保文件目录存在
        dir_name = os.path.dirname(file_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        
        created = False
        # 如果文件不存在，创建一个空文件
        if not os.path.exists(file_path) and allow_create:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("")
                created = True
            except Exception as e:
                QMessageBox.warning(self, "Warning", f"Cannot create file: {str(e)}")
                return
        
        # 只在新建时提示
        if created:
            QMessageBox.information(self, "File Created", f"New log file created:\n{file_path}")
        
        self.input_path_data_received.setText(file_path)
    
    def _on_json_file_selected(self, file_path: str, allow_create: bool):
        """处理JSON文件选择完成的回调"""
        # 确保文件目录存在
        dir_name = os.path.dirname(file_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        
        created = False
        # 如果文件不存在，创建JSON模板
        if not os.path.exists(file_path) and allow_create:
            try:
                import json
                import datetime
                file_name = os.path.basename(file_path).replace('.json', '')
                template = self.create_json_template(file_path, file_name)
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(template, f, indent=2, ensure_ascii=False)
                created = True
            except Exception as e:
                QMessageBox.warning(self, "Warning", f"Cannot create file: {str(e)}")
                return
        
        # 只在新建时提示
        if created:
            QMessageBox.information(self, "File Created", f"New JSON configuration file created:\n{file_path}")
        
        # 如果有保存的 path_input 对象，使用它；否则不处理
        if hasattr(self, '_json_file_input') and self._json_file_input:
            self._json_file_input.setText(file_path)
            self._json_file_input = None  # 清除临时变量
    
    def _on_at_command_file_selected(self, file_path: str, allow_create: bool):
        """处理AT命令文件选择完成的回调"""
        # 查找第一个空的路径输入框
        empty_index = None
        for idx, pi in enumerate(getattr(self, 'path_command_inputs', [])):
            if not pi.text().strip():
                empty_index = idx
                break
        
        if empty_index is None:
            ErrorDialog.show_error(
                parent=self,
                title="Import Failed",
                message="No empty path slots available",
                details="All path slots are occupied. Please clear a slot before importing."
            )
            return
        
        # 校验文件存在
        if not os.path.exists(file_path):
            ErrorDialog.show_error(
                parent=self,
                title="Import Failed",
                message="Selected file does not exist",
                details=f"File: {file_path}"
            )
            return
        
        # 写入到第一个空槽位并保存配置
        self.path_command_inputs[empty_index].setText(file_path)
        self.save_paths_to_config()
        
        QMessageBox.information(
            self,
            "Import Successful",
            f"Imported file to Path_{empty_index + 1}:\n{file_path}"
        )

    def select_json_file(self, path_input=None):
        """选择或创建JSON配置文件的包装方法
        
        Args:
            path_input: 可选的QLineEdit控件，用于显示选择的文件路径
        """
        # 临时保存 path_input，在回调中使用
        self._json_file_input = path_input
        # 调用通用方法，使用 "json" 类型
        self.select_file(file_type="json")
                
    def import_at_command_file(self):
        """从文件系统导入AT命令文件并写入第一个空的路径槽位

        - 打开文件选择对话（仅选择已存在文件）
        - 如果存在空槽位（path_command_inputs 中文本为空），将选中文件路径写入第一个空槽位并保存配置
        - 如果所有槽位都已被占用，使用 ErrorDialog 提示失败
        """
        # 调用通用方法，使用 "at_command" 类型
        self.select_file(file_type="at_command")
                
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
        if current_ports:
            self.serial_port_combo.addItems(current_ports)
        else:
            self.serial_port_combo.addItem("No devices found")
        QComboBox.showPopup(self.serial_port_combo)

    def _process_hex_data(self, hex_data: str) -> str:
        """
        将字节数据转换为两部分：
        第一部分：十六进制值
        第二部分：对应的字符（包括控制字符的转义形式）

        Args:
            data (bytes): 字节数据

        Returns:
            tuple[str, str]: 包含两部分的元组，第一部分是十六进制值，第二部分是对应字符
        """
        try:
            # 将十六进制字符串转换为字节数组
            hex_bytes = bytes.fromhex(hex_data)

            # 第一行：十六进制值
            hex_line =  "Received: "
            char_line = "ASCII   : "

            for byte in hex_bytes:
                # 十六进制部分，固定宽度为两位大写十六进制
                hex_line += f"{byte:02X} "

                # 字符部分，处理控制字符和可打印字符
                if 32 <= byte <= 126:  # 可打印ASCII字符
                    char_line += f"{chr(byte)}  "  # 每个字符后加两个空格对齐
                elif byte == 0x0D:  # \r
                    char_line += "\\r "
                elif byte == 0x0A:  # \n
                    char_line += "\\n "
                elif byte == 0x09:  # \t
                    char_line += "\\t "
                elif byte == 0x08:  # \b
                    char_line += "\\b "
                elif byte == 0x07:  # \a
                    char_line += "\\a "
                elif byte == 0x0C:  # \f
                    char_line += "\\f "
                elif byte == 0x0B:  # \v
                    char_line += "\\v "
                elif byte == 0x00:  # \0
                    char_line += "\\0 "
                else:  # 不可打印字符
                    char_line += f"\\x{byte:02x} "

            # 确保两行长度一致（填充空格）
            hex_line = hex_line.strip()
            char_line = char_line.strip()
            max_length = max(len(hex_line), len(char_line))
            hex_line = hex_line.ljust(max_length)
            char_line = char_line.ljust(max_length)

            # 返回两行格式化结果
            return hex_line, char_line

        except ValueError as e:
            return f"Invalid hex data: {str(e)}\n"

    def load_older_data(self):
        """Load previous data chunks when scrolling up"""
        lines_in_view = self.received_data_textarea.height() // self.received_data_textarea.fontMetrics().lineSpacing()
        if self.current_offset + lines_in_view < len(self.full_data_store):
            # 增加 current_offset
            self.current_offset += lines_in_view // 2  # 向上滚动，增加偏移量
            self.current_offset = min(self.current_offset, len(self.full_data_store) - lines_in_view)  # 确保不超出范围
            self.efficient_update_display()

    def load_newer_data(self):
        """Load next data chunks when scrolling down"""
        if self.current_offset > 0:
            scrollbar = self.received_data_textarea.verticalScrollBar()
            previous_scroll_value = scrollbar.value()
            lines_in_view = self.received_data_textarea.height() // self.received_data_textarea.fontMetrics().lineSpacing()
            top_line_index = self.current_offset + (previous_scroll_value // self.received_data_textarea.fontMetrics().lineSpacing())
            self.current_offset -= lines_in_view // 2  # Overlap half the actual visible lines for better context
            self.current_offset = max(0, self.current_offset)  # Ensure offset doesn't go below 0
            self.efficient_update_display()
            new_scroll_value = (top_line_index - self.current_offset) * self.received_data_textarea.fontMetrics().lineSpacing()
            # scrollbar.setValue(max(0, new_scroll_value))

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
                # logger.error(f"Error occurred while fetching new data: {e}")
                pass

    def _flush_accumulator(self):
        """强制刷新累积缓冲区中的数据（超时处理）"""
        if not hasattr(self, 'data_accumulator') or not self.data_accumulator:
            return
        
        # 获取当前时间作为数据起始时间
        current_time = datetime.datetime.now()
        
        # 将累积的数据作为一个完整的数据包处理，添加特殊标记表示这是超时数据
        accumulated_data = bytes(self.data_accumulator)
        self.data_accumulator = bytearray()  # 清空缓冲区
        
        # 添加到待处理队列，使用特殊标记 (data, time, is_timeout=True)
        if not hasattr(self, 'pending_updates'):
            self.pending_updates = []
        
        # 用三元组标记这是超时数据，需要直接处理而不是重新进入累积流程
        self.pending_updates.append((accumulated_data, current_time, True))
        
        # 触发UI更新
        if not hasattr(self, 'update_timer'):
            self.update_timer = QTimer()
            self.update_timer.setSingleShot(True)
            self.update_timer.timeout.connect(self.batch_update_ui)
        
        if not self.update_timer.isActive():
            self.update_timer.start(10)  # 很快就更新，因为这是强制刷新

    def batch_update_ui(self):
        """批量更新UI，pending_updates只存储(bytes, start_time)，每条日志都带精确时间戳。"""
        if not self.pending_updates:
            return

        # 数据丢失检测
        if len(self.pending_updates) > 100:
            logger.warning(f"Too many pending updates ({len(self.pending_updates)} items), potential data loss risk")

        # 性能统计
        current_time = time.time()
        self.performance_stats['update_count'] += len(self.pending_updates)
        time_diff = current_time - self.performance_stats['last_stats_time']
        if time_diff >= 1.0:
            self.performance_stats['updates_per_second'] = self.performance_stats['update_count'] / time_diff
            self.performance_stats['update_count'] = 0
            self.performance_stats['last_stats_time'] = current_time
            if self.performance_stats['updates_per_second'] > 50:
                self.ui_update_interval = 0.05  # 高速数据时更频繁更新，从0.2改为0.05
            elif self.performance_stats['updates_per_second'] > 20:
                self.ui_update_interval = 0.08  # 从0.15改为0.08
            else:
                self.ui_update_interval = 0.1

        # 获取串口配置
        try:
            baudrate = int(self.baud_rate_combo.currentText())
        except ValueError:
            baudrate = 115200  # 默认波特率

        try:
            stop_bits = float(self.get_stopbits_value())
        except ValueError:
            stop_bits = 1  # 默认停止位

        try:
            bytesize = int(self.get_bytesize_value())
        except ValueError:
            bytesize = 8  # 默认数据位

        parity = self.get_parity_value()
        parity_bits = 1 if parity != "None" else 0  # 如果有校验位，则加1

        # 计算每字节的位数，如默认8N1配置：1起始位 + 8数据位 + 1停止位 + 0校验位 = 10位
        bits_per_byte = 1 + bytesize + stop_bits + parity_bits

        # 处理所有待更新的数据
        for update_item in self.pending_updates:
            # 检查是否是超时数据（三元组）还是普通数据（二元组）
            if len(update_item) == 3:
                data_bytes, start_time, is_timeout = update_item
            else:
                data_bytes, start_time = update_item
                is_timeout = False
            
            # 获取结束符
            ender = self.config.get("MoreSettings", "Ender", fallback="\r\n")
            end_bytes = common.hex_str_to_bytes(ender) if ender else b""

            # 如果是超时数据或没有结束符，直接处理整个数据
            if is_timeout or not end_bytes:
                segments = [data_bytes]
                # print(f"直接处理数据:{segments} 超时={is_timeout}, 无结束符={not end_bytes}, 数据长度={len(data_bytes)}")
            else:
                # 使用累积缓冲区来处理跨数据包的消息
                if not hasattr(self, 'data_accumulator'):
                    self.data_accumulator = bytearray()
                
                # 初始化累积定时器（如果不存在）
                if not hasattr(self, 'accumulator_timer'):
                    self.accumulator_timer = QTimer()
                    self.accumulator_timer.setSingleShot(True)
                    self.accumulator_timer.timeout.connect(self._flush_accumulator)
                
                # 将新数据添加到累积缓冲区
                self.data_accumulator.extend(data_bytes)
                
                # 按结束符分割数据
                temp_data = bytes(self.data_accumulator)
                segments = temp_data.split(end_bytes)
                
                # 最后一个段可能是不完整的，保留在缓冲区中
                if len(segments) > 1:
                    # 保留最后一个不完整的段
                    incomplete_segment = segments[-1]
                    segments = segments[:-1]  # 移除不完整的段
                    
                    # 清空累积缓冲区，保留不完整的段
                    self.data_accumulator = bytearray(incomplete_segment)
                    
                    # 停止之前的定时器
                    self.accumulator_timer.stop()
                    
                    # 如果有不完整的段，启动超时定时器
                    if incomplete_segment:
                        self.accumulator_timer.start(30)

                    # 为完整的段添加结束符（用于正确显示）
                    complete_segments = []
                    for seg in segments:
                        # 不过滤空段，保留空行（它们可能是有意义的数据）
                        complete_segments.append(seg + end_bytes)
                    segments = complete_segments
                else:
                    # 没有找到完整的消息，启动或重启超时定时器
                    self.accumulator_timer.stop()
                    self.accumulator_timer.start(30)
                    segments = []
                
            # 调试信息 - 可以临时启用来诊断问题
            # if segments:
            #     for i, seg in enumerate(segments):
            #         print(f"段 {i}: {repr(seg[:100])}{'...' if len(seg) > 100 else ''}")
            # else:
            #     if hasattr(self, 'data_accumulator') and self.data_accumulator:
            #         print(f"累积缓冲区内容: {repr(bytes(self.data_accumulator)[:100])}")
                
            # print(f"Segments: {segments} | Data Bytes: {data_bytes} | End Bytes: {end_bytes}")
            byte_offset = 0  # 字节偏移量，用于计算每段的起始时间戳
            
            
            # 1. 如果要串口数据以十六进制显示
            if self.received_hex_data_checkbox.isChecked():
                for i, seg in enumerate(segments):

                    ## 解析十六进制数据
                    hex_line, char_line = self._process_hex_data(seg.hex())

                    ## 构建显示行
                    if self.timeStamp_checkbox.isChecked():
                        ### 计算时间戳
                        seg_start_time = common.calculate_timestamp(start_time, byte_offset, bits_per_byte / baudrate)
                        ts = seg_start_time.strftime("%Y-%m-%d_%H:%M:%S.%f")[:-3]
                        byte_offset += len(seg) + (len(end_bytes) if i < len(segments) - 1 else 0)

                        display_line = f"[{ts}]{hex_line}"
                        display_line += f"\n[{ts}]{char_line}"
                    else:
                        display_line = f"{hex_line}"
                        display_line += f"\n{char_line}"

                    ## 添加到缓冲区（移除直接append到UI，统一由efficient_update_display处理）
                    self.full_data_store.append(display_line)

                    ## 文件日志记录，同步写入
                    if self.checkbox_data_received.isChecked():
                        file_path = self.input_path_data_received.text()
                        common.print_write(display_line, file_path)
            
            
            # 2. 如果要显示控制字符
            elif self.control_char_checkbox.isChecked():
                for i, seg in enumerate(segments):
                    if self.timeStamp_checkbox.isChecked():
                        # 计算时间戳
                        seg_start_time = common.calculate_timestamp(start_time, byte_offset, bits_per_byte / baudrate)
                        ts = seg_start_time.strftime("%Y-%m-%d_%H:%M:%S.%f")[:-3]
                        byte_offset += len(seg) + (len(end_bytes) if i < len(segments) - 1 else 0)

                        display_line = f"[{ts}]{common.force_decode(seg, handle_control_char='escape')}"
                    else:
                        display_line = common.force_decode(seg, handle_control_char='escape')

                    # 添加到缓冲区，不过滤空行，保留所有数据
                    self.full_data_store.append(display_line)

                    # 文件日志记录，同步写入
                    if self.checkbox_data_received.isChecked():
                        file_path = self.input_path_data_received.text()
                        common.print_write(display_line, file_path)
                

            # 3. 否则，直接按照串口数据格式来显示
            else:
                for i, seg in enumerate(segments):
                    if self.timeStamp_checkbox.isChecked():
                        # 计算时间戳
                        seg_start_time = common.calculate_timestamp(start_time, byte_offset, bits_per_byte / baudrate)
                        ts = seg_start_time.strftime("%Y-%m-%d_%H:%M:%S.%f")[:-3]
                        byte_offset += len(seg) + (len(end_bytes) if i < len(segments) - 1 else 0)

                        display_line = f"[{ts}]{common.force_decode(seg, handle_control_char='interpret')}"
                    else:
                        display_line = f"{common.force_decode(seg, handle_control_char='interpret')}"

                    # 添加到缓冲区，不过滤空行，保留所有数据
                    self.full_data_store.append(display_line)

                    # 文件日志记录，同步写入
                    if self.checkbox_data_received.isChecked():
                        file_path = self.input_path_data_received.text()
                        common.print_write(display_line, file_path)

        self.pending_updates.clear()

        # 维护缓冲区大小
        if len(self.full_data_store) > self.buffer_size:
            excess = len(self.full_data_store) - self.buffer_size
            del self.full_data_store[:excess]
            
            # 安全地删除hex_buffer，确保索引不越界
            if hasattr(self, 'hex_buffer') and len(self.hex_buffer) > excess:
                del self.hex_buffer[:excess]
            elif hasattr(self, 'hex_buffer'):
                self.hex_buffer.clear()  # 如果长度不一致，清空重建

            # 调整 current_offset，保持当前显示内容不被挤到后面
            self.current_offset = max(0, self.current_offset - excess)

        # 更新显示（只有在触底时才更新）
        self.efficient_update_display()
        
    def efficient_update_display(self):
        """高效的UI更新方法"""
        # 获取滚动条
        scrollbar = self.received_data_textarea.verticalScrollBar()
        scroll_value = scrollbar.value()
        max_scroll_value = scrollbar.maximum()

        # 判断是否快要触底（比如10像素以内）
        will_at_bottom = max_scroll_value - scroll_value <= 20

        # 如果快要触底，更新显示范围以显示最新数据
        if will_at_bottom:
            self.current_offset = 0  # 重置偏移量，显示最新数据
        else:
            # 如果没有触底，保持 current_offset 不变
            return  # 不更新显示内容

        # 计算显示范围
        end_idx = len(self.full_data_store) - self.current_offset
        end_idx = max(0, end_idx)
        start_idx = max(0, end_idx - min(self.visible_lines, len(self.full_data_store)))
        text_lines = self.full_data_store[start_idx:end_idx]
        
        # 不过滤空行，保留原始数据的完整性
        # text_lines = [line for line in text_lines if line.strip()]

        # 更新滚动条范围
        # scrollbar.setMaximum(len(self.full_data_store) * self.received_data_textarea.fontMetrics().lineSpacing())

        # 打印调试信息
        # print(f"efficient_update_display: start_idx={start_idx}, end_idx={end_idx}, current_offset={self.current_offset}, will_at_bottom={will_at_bottom}")

        # 如果没有新数据，直接返回
        if (hasattr(self, '_last_start_idx') and 
            start_idx == self._last_start_idx and 
            end_idx == self._last_end_idx):
            return

        # 保存上次索引用于增量更新判断
        prev_start = getattr(self, '_last_start_idx', None)
        prev_end = getattr(self, '_last_end_idx', None)

        self._last_start_idx = start_idx
        self._last_end_idx = end_idx

        # 禁用更新以提高性能
        self.received_data_textarea.setUpdatesEnabled(False)
        try:
            current_font = self.received_data_textarea.font()

            # 如果还没有持久化文档或视图范围发生了复杂变化，重建文档
            need_rebuild = False
            if not hasattr(self, '_display_document'):
                need_rebuild = True
            else:
                # 如果请求的 start 与上次不同，或者出现回退（prev_end > end_idx），需要重建
                if prev_start is None or start_idx != prev_start or (prev_end is not None and prev_end > end_idx):
                    need_rebuild = True

            if need_rebuild:
                # 重建整个文档（第一次或范围不连续时）
                self._display_document = QTextDocument()
                self._display_document.setDefaultFont(current_font)
                cursor = QTextCursor(self._display_document)
                for i, line in enumerate(text_lines):
                    clean_line = line.rstrip('\n\r')
                    cursor.insertText(clean_line)
                    if i < len(text_lines) - 1:
                        cursor.insertText('\n')
                self.received_data_textarea.setDocument(self._display_document)
            else:
                # 尝试增量追加：当 start_idx 与 prev_start 相同且 end_idx > prev_end
                if prev_end is not None and end_idx > prev_end:
                    # 新增的行在 text_lines 中的起始位置
                    new_from = prev_end - start_idx
                    if new_from < 0:
                        # 退化为重建以避免不一致
                        self._display_document = QTextDocument()
                        self._display_document.setDefaultFont(current_font)
                        cursor = QTextCursor(self._display_document)
                        for i, line in enumerate(text_lines):
                            clean_line = line.rstrip('\n\r')
                            cursor.insertText(clean_line)
                            if i < len(text_lines) - 1:
                                cursor.insertText('\n')
                        self.received_data_textarea.setDocument(self._display_document)
                    else:
                        cursor = QTextCursor(self._display_document)
                        cursor.movePosition(QTextCursor.End)
                        new_lines = text_lines[new_from:]
                        for idx, line in enumerate(new_lines):
                            clean_line = line.rstrip('\n\r')
                            # 如果文档不是空的并且当前不是首行，先插入换行
                            if cursor.position() != 0 or (idx > 0):
                                cursor.insertText('\n')
                            cursor.insertText(clean_line)
                else:
                    # 没有新增内容可追加，或无法增量处理，安全重建
                    self._display_document = QTextDocument()
                    self._display_document.setDefaultFont(current_font)
                    cursor = QTextCursor(self._display_document)
                    for i, line in enumerate(text_lines):
                        clean_line = line.rstrip('\n\r')
                        cursor.insertText(clean_line)
                        if i < len(text_lines) - 1:
                            cursor.insertText('\n')
                    self.received_data_textarea.setDocument(self._display_document)
        finally:
            self.received_data_textarea.setUpdatesEnabled(True)

        # 如果快要触底，自动滚动到底部
        if will_at_bottom:
            # 如果是增量追加情况下，document 未被替换，可以立即滚到底
            if prev_start == start_idx and prev_end is not None and end_idx > prev_end:
                self.received_data_textarea.verticalScrollBar().setValue(self.received_data_textarea.verticalScrollBar().maximum())
            else:
                # 否则延后到事件循环末尾再滚动，确保布局完成
                QTimer.singleShot(0, lambda: self.received_data_textarea.verticalScrollBar().setValue(self.received_data_textarea.verticalScrollBar().maximum()))

    def update_main_textarea(self, raw_data: bytes):
        """
        接收串口线程传来的原始bytes数据，计算精确起始时间戳，加入pending_updates，等待批量UI刷新。
        """
        # 初始化缓冲区（如果不存在）
        if not hasattr(self, 'full_data_store'):
            self.full_data_store = []
            self.hex_buffer = []
            self.buffer_size = 10000  # 使用更大的缓冲区
            self.visible_lines = 500
            self.current_offset = 0
        if not hasattr(self, 'pending_updates'):
            self.pending_updates = []
        if not hasattr(self, 'last_ui_update_time'):
            self.last_ui_update_time = time.time()
        if not hasattr(self, 'ui_update_interval'):
            self.ui_update_interval = 0.1
        if not hasattr(self, 'update_timer'):
            self.update_timer = QTimer()
            self.update_timer.setSingleShot(True)
            self.update_timer.timeout.connect(self.batch_update_ui)

        # 获取原始数据打印
        # print(f"Received raw data: {raw_data}")

        # 计算数据起始时间戳（基于波特率和数据长度）
        baudrate = 115200  # 默认波特率
        try:
            baudrate = int(self.baud_rate_combo.currentText())
        except Exception:
            pass
        # 1字节=10bit（含起止位），耗时=10/baudrate
        byte_count = len(raw_data)
        duration = byte_count * 10.0 / baudrate
        end_time = time.time()
        start_time = end_time - duration if duration < 1 else end_time - min(duration, 1)
        # 用datetime对象，方便格式化
        start_dt = datetime.datetime.fromtimestamp(start_time)

        # 只存储(bytes, start_time)元组
        self.pending_updates.append((raw_data, start_dt))
        
        # 调试pending_updates内容
        # print(f"Pending updates: {self.pending_updates}")

        # 检查是否应该立即更新（基于时间或数量阈值）
        current_time = time.time()
        time_since_last_update = current_time - self.last_ui_update_time
        
        # 详细调试信息
        # print(f"调试信息: len(pending_updates)={len(self.pending_updates)}, "
        #       f"time_since_last_update={time_since_last_update:.3f}, "
        #       f"ui_update_interval={self.ui_update_interval}, "
        #       f"max_pending_updates={self.max_pending_updates}")
        
        # 降低触发阈值，确保数据能及时显示
        condition1 = len(self.pending_updates) >= 1  # 改为1，有数据就更新
        condition2 = time_since_last_update >= 0.01  # 降低到10ms
        condition3 = len(self.pending_updates) > self.max_pending_updates
        
        # print(f"触发条件: 数量>=1: {condition1}, 时间间隔>=0.01: {condition2}, 超过最大缓存: {condition3}")
        
        should_update = condition1 or condition2 or condition3
        
        if should_update:
            # 直接调用batch_update_ui，不使用定时器
            self.batch_update_ui()
            self.last_ui_update_time = current_time
        else:
            # 动态调整阈值，但保持在合理范围内
            self.max_pending_updates = max(5, min(50, len(self.pending_updates) * 3))

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
        # Check if log path is empty but save log is enabled
        if self.checkbox_data_received.isChecked() and not self.input_path_data_received.text().strip():
            ErrorDialog.show_warning(
                parent=self,
                title="Log Path Empty",
                message="Cannot open serial port",
                details="The 'Save Log' option is enabled but no log file path is specified. Please provide a log file path before opening the port."
            )
            return
        
        serial_port = self.get_serial_port_value()
        baud_rate = int(self.get_baud_rate_value())
        stop_bits = float(self.get_stopbits_value())
        parity = self.get_parity_value()
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
        byte_size = int(self.get_bytesize_value())
        flow_control = self.get_flowcontrol_value()

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
                self.set_status_label("Open", "connected")
                self.port_button.clicked.disconnect(self.port_on)
                self.port_button.clicked.connect(self.port_off)
                # Disable the serial port and baud rate combo boxes
                self.serial_port_combo.setEnabled(False)
                self.baud_rate_combo.setEnabled(False)
                self.stopbits_combo.setEnabled(False)
                self.parity_combo.setEnabled(False)
                self.bytesize_combo.setEnabled(False)
                self.flowcontrol_combo.setEnabled(False)
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
            self.data_receiver.is_show_control_char = self.control_char_checkbox.isChecked()
            self.data_receiver.is_show_timeStamp = self.timeStamp_checkbox.isChecked()
            self.data_receiver.is_show_hex = self.received_hex_data_checkbox.isChecked()
            self.data_receive_thread.start()
        except Exception as e:
            logger.error(f"Error opening serial port: {e}")
            self.set_status_label("Failed", "error")

    def port_off(self):
        self.data_receiver.stop_thread()
        self.data_receive_thread.quit()
        # No wait for the thread to finish, it will finish itself
        # self.data_receive_thread.wait()

        # 清空数据累积缓冲区
        if hasattr(self, 'data_accumulator'):
            self.data_accumulator = bytearray()
            
        # 停止累积定时器
        if hasattr(self, 'accumulator_timer'):
            self.accumulator_timer.stop()

        try:
            self.main_Serial = common.port_off(self.main_Serial)
            if self.main_Serial is None:
                self.port_button.setText("Open Port")
                self.port_button.setShortcut("Ctrl+O")
                self.port_button.setToolTip("Shortcut: Ctrl+O")
                self.set_status_label("Closed", "disconnected")
                self.port_button.clicked.disconnect()
                self.port_button.clicked.connect(self.port_on)

                self.serial_port_combo.setEnabled(True)
                self.baud_rate_combo.setEnabled(True)
                self.stopbits_combo.setEnabled(True)
                self.parity_combo.setEnabled(True)
                self.bytesize_combo.setEnabled(True)
                self.flowcontrol_combo.setEnabled(True)
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
                logger.error("Port Close Failed")
                self.port_button.setEnabled(True)
        except Exception as e:
            logger.error(f"Error closing serial port: {e}")
            self.set_status_label("Failed", "error")

    """
    Summary:
        Hotkeys click handler       
    """

    def clear_log(self):
        self.current_offset = 0
        self.full_data_store = []
        self.hex_buffer = []
        
        # 清空数据累积缓冲区
        if hasattr(self, 'data_accumulator'):
            self.data_accumulator = bytearray()
        
        # 停止累积定时器
        if hasattr(self, 'accumulator_timer'):
            self.accumulator_timer.stop()
        
        self.received_data_textarea.clear()
        
        # 清除日志文件逻辑，改为如果在moresettings中选中了Clear_Log_With_File则一并清除文件
        if self.config.getboolean("MoreSettings", "Clear_Log_With_File", fallback=False):
            if self.input_path_data_received.text():
                with open(self.input_path_data_received.text(), "w", encoding="utf-8") as f:
                    f.write("")
            else:
                with open(
                    common.get_resource_path("tmps/temp.log"),
                    "w",
                    encoding="utf-8",
                ) as f:
                    f.write("")

    def read_ATCommand(self):
        try:
            if not os.path.exists(self.path_ATCommand):
                ErrorDialog.show_error(
                    parent=self,
                    title="文件不存在",
                    message=f"AT命令文件不存在: {self.path_ATCommand}",
                    details="请检查文件路径是否正确，或者创建一个新的AT命令文件。"
                )
                return
                
            with open(
                self.path_ATCommand,
                "r",
                encoding="utf-8",
            ) as f:
                data = json.load(f)
                ATCommandFromFile = data.get("Commands", [])
                
                for i in range(1, len(self.input_fields) + 1):
                    if i <= len(ATCommandFromFile):
                        self.checkbox[i - 1].setChecked(
                            bool(ATCommandFromFile[i - 1].get("selected"))
                        )
                        self.input_fields[i - 1].setText(
                            ATCommandFromFile[i - 1].get("command") or ""
                        )
                        self.input_fields[i - 1].setCursorPosition(0)
                        self.checkbox_send_with_enders[i - 1].setChecked(
                            ATCommandFromFile[i - 1].get("withEnder", True)
                        )
                        self.checkbox_hex[i - 1].setChecked(
                            ATCommandFromFile[i - 1].get("hex", False)
                        )
                        self.interVal[i - 1].setText(
                            str(ATCommandFromFile[i - 1].get("interval") or 0)
                        )
                    else:
                        self.input_fields[i - 1].setText("")
                        
        except json.JSONDecodeError as e:
            ErrorDialog.show_error(
                parent=self,
                title="JSON格式错误",
                message=f"AT命令文件格式错误: {self.path_ATCommand}",
                details=f"JSON解析错误: {str(e)}"
            )
        except UnicodeDecodeError as e:
            ErrorDialog.show_error(
                parent=self,
                title="文件编码错误",
                message=f"无法读取AT命令文件: {self.path_ATCommand}",
                details=f"文件编码错误: {str(e)}\n请确保文件使用UTF-8编码保存。"
            )
        except Exception as e:
            ErrorDialog.show_error(
                parent=self,
                title="读取文件失败",
                message=f"读取AT命令文件时发生错误: {self.path_ATCommand}",
                details=f"错误详情: {str(e)}"
            )

    def update_ATCommand(self):
        result = common.update_AT_command(
            self.path_ATCommand, 
            self.config["MoreSettings"]["AtCommandRegex"])
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
                "hex": self.checkbox_hex[i].isChecked(),
                "withEnder": self.checkbox_send_with_enders[i].isChecked(),
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
                new_path = self.path_command_inputs[index].text()
                
                # 检查是否切换到了不同的文件
                if new_path != self.path_ATCommand:
                    # 处理当前文件的未保存更改
                    if hasattr(self, 'at_command_manager') and self.at_command_manager.has_unsaved_changes():
                        choice = self.at_command_manager.prompt_save_changes()
                        
                        if choice == "cancel":
                            # 用户取消，恢复原来的选择
                            for i, button in enumerate(self.radio_path_command_buttons):
                                if self.path_command_inputs[i].text() == self.path_ATCommand:
                                    button.setChecked(True)
                                    return
                        elif choice == "save":
                            # 保存当前文件
                            success, error_msg = self.at_command_manager.save_file()
                            if not success:
                                ErrorDialog.show_error(
                                    parent=self,
                                    title="保存失败",
                                    message="保存当前AT命令文件失败",
                                    details=error_msg
                                )
                                return
                    
                    # 切换到新文件
                    self.path_ATCommand = new_path
                    self.at_command_manager.set_file_path(new_path)
                    
                    # 加载新文件内容
                    content, error_msg = self.at_command_manager.load_file(new_path)
                    if error_msg:
                        # 显示错误对话框
                        ErrorDialog.show_error(
                            parent=self,
                            title="读取AT命令文件失败",
                            message=f"无法读取选择的AT命令文件: {new_path}",
                            details=error_msg
                        )
                        # 清空文本框
                        self.text_input_layout_2.clear()
                    else:
                        self.text_input_layout_2.setPlainText(content)
                    
                    # 保存当前选中的路径到配置文件
                    self.save_paths_to_config()
                    # 刷新文件名显示
                    self.update_at_command_status()
            else:
                self.path_ATCommand = common.get_resource_path("tmps/ATCommand.json")
                self.at_command_manager.set_file_path(self.path_ATCommand)
        else:
            logger.warning(f"Radio button {index + 1} is unchecked.")

    def handle_hotkey_click(self, index: int, value: str = "", shortcut: str = ""):
        def hotkey_clicked():
            if value:
                self.port_write(value, self.main_Serial, self.checkbox_send_with_ender.isChecked())
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
        """Detect scroll direction and update current_offset"""
        scrollbar = self.received_data_textarea.verticalScrollBar()
        scroll_value = scrollbar.value()
        max_scroll_value = scrollbar.maximum()

        # 打印调试信息
        # print(f"Scroll event: value={scroll_value}, max={max_scroll_value}, current_offset={self.current_offset}")

        # 滚动到顶部时加载旧数据
        if event.angleDelta().y() > 0 and scroll_value <= scrollbar.singleStep():
            self.load_older_data()

        # 滚动到底部时加载新数据
        elif event.angleDelta().y() < 0 and scroll_value >= max_scroll_value - scrollbar.singleStep():
            self.fetch_new_data()
            self.current_offset = 0  # 重置偏移量以显示最新内容
            self.efficient_update_display()

        # 中间滚动时同步更新 current_offset
        else:
            # 计算当前顶部行的索引
            top_line_index = scroll_value // self.received_data_textarea.fontMetrics().lineSpacing()
            # 更新 current_offset
            self.current_offset = max(0, len(self.full_data_store) - top_line_index - self.visible_lines)
            # print(f"Updated current_offset: {self.current_offset}")

    def handle_left_click(self):
        if self.prompt_index >= 0 and self.prompt_index < len(self.input_fields) - 1:
            # Left button click to SEND
            self.port_write(
                self.input_prompt.text(),
                self.main_Serial,
                self.checkbox_send_with_enders[self.prompt_index].isChecked(),
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
        logger.debug("Right button click with Shift modifier")

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
        status = not all(checkbox.isChecked() for checkbox in self.checkbox_send_with_enders)
        for checkbox in self.checkbox_send_with_enders:
            checkbox.setChecked(status)

    def set_hex_none(self):
        """切换所有十六进制复选框的状态"""
        if hasattr(self, 'checkbox_hex'):
            status = not all(checkbox.isChecked() for checkbox in self.checkbox_hex)
            for checkbox in self.checkbox_hex:
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
            self.expand_left_button.setIcon(QIcon(common.safe_resource_path("res/direction_left.png")))
            # 保存路径到配置文件
            self.save_paths_to_config()
            # 隐藏所有路径输入框
            for path_input in self.path_command_inputs:
                path_input.setVisible(False)
            # 设置收缩时的宽度为120，能显示更多内容
            self.radio_scroll_area.setMaximumWidth(100)
        else:
            # 展开状态
            self.expand_left_button.setIcon(QIcon(common.safe_resource_path("res/direction_right.png")))
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
            logger.error(f"Error saving paths to config: {e}")
    
    def save_integrated_function(self):
        """整合的保存功能：同时保存路径配置和AT命令文件"""
        try:
            # 1. 保存路径配置
            self.save_paths_to_config()
            
            # 2. 保存AT命令文件
            current_content = self.text_input_layout_2.toPlainText()
            self.at_command_manager.update_content(current_content)
            success, message = self.at_command_manager.save_file()
            
            if success:
                # 更新状态显示
                self.update_at_command_status()
                logger.info("Integrated save completed successfully")
            else:
                logger.error(f"Failed to save AT command file: {message}")
                # 可以考虑显示错误消息给用户
                from components.ErrorDialog import ErrorDialog
                ErrorDialog.show_error(self, "Save Failed", f"Failed to save AT command file: {message}")
                
        except Exception as e:
            logger.error(f"Error in integrated save function: {e}")
            from components.ErrorDialog import ErrorDialog
            ErrorDialog.show_error(self, "Save Error", f"An error occurred while saving: {str(e)}")

    # Filter selected commands
    def filter_selected_command(self):
        self.selected_commands = []
        for i in range(len(self.input_fields)):
            if self.checkbox[i].isChecked():
                command_info = {
                    "index": i,
                    "command": self.input_fields[i].text(),
                    "interval": self.interVal[i].text(),
                    "hex": self.checkbox_hex[i].isChecked(),
                    "withEnder": self.checkbox_send_with_enders[i].isChecked(),
                }
                self.selected_commands.append(command_info)
        return self.selected_commands

    def handle_command_executed(self, index):
        # index: 1-based command index, or -1 for completion/error
        try:
            self.input_prompt_index.setText(str(index))
            if index == -1:
                # show completion marker
                self.input_prompt.setText("")
            else:
                idx0 = int(index) - 1
                if 0 <= idx0 < len(self.input_fields):
                    cmd = self.input_fields[idx0].text()
                    self.input_prompt.setText(cmd)
                else:
                    # index out of range: clear input
                    self.input_prompt.setText("")
            self.input_prompt.setCursorPosition(0)
        except Exception:
            # defensive: avoid raising from signal handler
            pass

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
        self, index, input_field, checkbox, checkbox_hex, checkbox_send_with_ender, interVal
    ):
        def button_clicked():
            if not self.last_one_click_time:
                self.last_one_click_time = time.time()
            
            # 根据 checkbox_hex 的状态决定发送方式
            if checkbox_hex.isChecked():
                self.port_write_hex(
                    input_field.text(),
                    self.main_Serial,
                    checkbox_send_with_ender.isChecked(),
                )
            else:
                self.port_write(
                    input_field.text(),
                    self.main_Serial,
                    checkbox_send_with_ender.isChecked(),
                )
            
            checkbox.setChecked(True)
            self.prompt_index = index
            self.input_prompt_index.setText(str(index))
            self.input_prompt.setText(input_field.text())
            now_click_time = time.time()
            delta_ms = int((now_click_time - self.last_one_click_time) * 1000)
            # Limit the maximum display value to avoid excessive values (adjust the upper limit here if needed)
            self.interVal[index - 2].setText(str(min(99999, delta_ms)))
            self.last_one_click_time = now_click_time

        return button_clicked

    """
    Summary:
    Main window close event handler
    
    """

    def closeEvent(self, event):
        logger.info("Application close event triggered")
        
        # Confirm exit dialog
        confirm_exit_dialog = ConfirmExitDialog(self)
        if confirm_exit_dialog.exec() == QDialog.Accepted:
            logger.info("User confirmed application exit")
            
            # Save configuration settings
            logger.info("Saving configuration settings...")
            self.save_config(self.config)
            logger.info("Configuration settings saved successfully")
            
            # 停止累积定时器
            if hasattr(self, 'accumulator_timer'):
                logger.info("Stopping accumulator timer...")
                self.accumulator_timer.stop()
                logger.info("Accumulator timer stopped")
                
            # Properly stop and wait for the data receive thread
            try:
                if hasattr(self, "data_receiver") and self.data_receiver:
                    logger.info("Stopping data receiver thread...")
                    self.data_receiver.stop_thread()
                    logger.info("Data receiver thread stop signal sent")
                if hasattr(self, "data_receive_thread") and self.data_receive_thread:
                    logger.info("Waiting for data receive thread to finish...")
                    self.data_receive_thread.quit()
                    if self.data_receive_thread.wait(2000):  # Wait up to 2 seconds
                        logger.info("Data receive thread finished successfully")
                    else:
                        logger.warning("Data receive thread did not finish within timeout")
            except Exception as e:
                logger.error(f"Error stopping data receive thread: {e}")
                
            # Close serial port
            if self.main_Serial:
                logger.info("Closing serial port...")
                self.port_off()
                logger.info("Serial port closed")
            else:
                logger.info("No serial port to close")
                
            # Signal all running threads to stop
            active_threads = self.thread_pool.activeThreadCount()
            if active_threads > 0:
                logger.info(f"Waiting for {active_threads} active threads to finish...")
                while active_threads > 0:
                    self.thread_pool.waitForDone(100)
                    active_threads = self.thread_pool.activeThreadCount()
                logger.info("All threads finished successfully")
            else:
                logger.info("No active threads to wait for")
                
            logger.info("Application exit completed successfully")
            event.accept()
        else:
            logger.info("User cancelled application exit")
            event.ignore()


def main():
    try:
       
        # 添加控制台输出
        logger.info("Application starting...")
        
        app = QApplication([])
        
        # 加载环境变量
        env_path = common.get_resource_path(".env")
        if os.path.exists(env_path):
            load_dotenv(env_path)
        version = os.getenv("VERSION", "1.0.0")
        
        # 创建启动画面
        splash_pixmap = QPixmap(400, 300)
        splash_pixmap.fill(QColor("#f0f0f0"))
        
        # 在启动画面上绘制内容
        painter = QPainter(splash_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制应用图标（使用资源路径函数）
        try:
            icon_path = common.get_resource_path("favicon.ico")
            if os.path.exists(icon_path):
                icon_pixmap = QPixmap(icon_path)
                if not icon_pixmap.isNull():
                    scaled_icon = icon_pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    painter.drawPixmap(168, 80, scaled_icon)
        except Exception as e:
            logger.warning(f"Could not load icon: {e}")
        
        # 绘制应用名称
        painter.setPen(QColor("#333333"))
        font = QFont("Consolas", 18, QFont.Bold)
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
        try:
            style_path = common.safe_resource_path("styles/fish.qss")
            if os.path.exists(style_path):
                widget.setStyleSheet(QSSLoader.load_stylesheet(style_path))
            else:
                logger.warning("Style file not found, using default style")
        except Exception as e:
            logger.warning(f"Could not load stylesheet: {e}")
        app.processEvents()
        
        update_splash_message("Configuring window...")
        widget.setWindowTitle(f"SCOM v{version}")
        
        # 设置应用图标
        try:
            icon_path = common.safe_resource_path("favicon.ico")
            if os.path.exists(icon_path):
                app.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            logger.warning(f"Could not set window icon: {e}")
        
        widget.resize(1000, 900)
        app.processEvents()
        
        update_splash_message("Checking for updates...")
        app.processEvents()
        
        # 更新检查（添加异常处理）
        try:
            from components.SafeUpdateChecker import SafeUpdateChecker
            update_checker = SafeUpdateChecker.check_updates_on_startup()

            if update_checker:  # 如果返回了检查器实例，说明启用了启动时检查
                def on_update_finished(version, notes):
                    update_splash_message("Startup complete!")
                    QTimer.singleShot(300, lambda: finish_startup(True, version, notes))

                def on_check_failed(error_msg):
                    update_splash_message("Startup complete!")
                    QTimer.singleShot(300, lambda: finish_startup(False))

                update_checker.update_available.connect(on_update_finished)
                update_checker.check_failed.connect(on_check_failed)
            else:
                # 用户禁用了启动时检查
                update_splash_message("Startup complete!")
                QTimer.singleShot(300, lambda: finish_startup(False))

        except Exception as e:
            logger.warning(f"Update check failed: {e}")
            update_splash_message("Startup complete!")
            QTimer.singleShot(300, lambda: finish_startup(False))

        def finish_startup(has_update=False, version=None, notes=None):
            widget.show()
            splash.finish(widget)

            # 如果检测到更新，显示更新信息对话框
            if has_update:
                def show_update_dialog():
                    try:
                        update_dialog = SafeUpdateDialog(widget)
                        update_dialog._show_update_available(version, notes)
                        update_dialog.show()
                    except Exception as e:
                        logger.warning(f"Failed to show update dialog: {e}")

                # 延迟500毫秒后显示更新对话框，让主界面先完全显示
                QTimer.singleShot(500, show_update_dialog)

        # 设置超时机制，如果10秒内没有完成就强制关闭启动画面
        def force_close_splash():
            try:
                if 'update_checker' in locals() and hasattr(update_checker, 'isRunning') and update_checker.isRunning():
                    logger.info("Update info loading timeout, force closing splash screen")
                update_splash_message("Startup complete!")
                widget.show()
                splash.finish(widget)
            except Exception as e:
                logger.error(f"Error in force_close_splash: {e}")

        QTimer.singleShot(10000, force_close_splash)  # 10秒超时
        
        sys.exit(app.exec())
        
    except Exception as e:
        error_msg = f"Application startup failed: {str(e)}\n"
        error_msg += f"Python executable: {sys.executable}\n"
        error_msg += f"Working directory: {os.getcwd()}\n"
        error_msg += f"Frozen: {getattr(sys, 'frozen', False)}\n"
        error_msg += f"Sys.path: {sys.path[:3]}...\n"  # 只显示前3个路径
        
        logger.error(error_msg)
        logger.error(error_msg)
        
        # 尝试显示错误对话框
        try:
            error_app = QApplication([])
            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Critical)
            error_dialog.setText("Application failed to start")
            error_dialog.setDetailedText(error_msg)
            error_dialog.setWindowTitle("SCOM Startup Error")
            error_dialog.exec()
        except Exception as dialog_error:
            logger.error(f"Unable to display error dialog: {dialog_error}")
        
        sys.exit(1)

if __name__ == "__main__":
    logger = Logger(
            app_name="Window",
            log_dir="logs",
            max_bytes=10 * 1024 * 1024,
            backup_count=3
    ).get_logger("Window")

    main()

