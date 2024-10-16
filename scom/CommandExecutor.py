from PySide6.QtCore import *
from utils import common


class CommandExecutor(QThread):
    # Signal to emit command and its output
    commandExecuted = Signal(str, str)

    def __init__(self, commands, serial_port, total_times):
        super().__init__()
        self.commands = commands
        self.serial_port = serial_port
        self.total_times = total_times
        self.is_paused = False
        self.mutex = QMutex()
        self.cond = QWaitCondition()
        self.error_occurred = False
        
    def execute_commands(self):
        for command_dict in self.commands:
            command = command_dict.get('command', '')
            interval = command_dict.get('interval', '')
            with_enter = command_dict.get('withEnter', False)

            with QMutexLocker(self.mutex):
                if self.is_paused:
                    self.cond.wait(self.mutex)
            if not self.is_paused:
                try:
                    # Use common.port_write to execute the command
                    output = common.port_write(command, self.serial_port, with_enter)
                    if interval:
                        QThread.sleep(int(interval))
                except Exception as e:
                    output = str(e)
                    self.error_occurred = True
                self.commandExecuted.emit(command, output)
                QThread.sleep(2)
        self.commandExecuted.emit("", "All commands completed.")
        if self.error_occurred:
            self.commandExecuted.emit("", "Some commands encountered errors.")

    def pause_thread(self):
        if not self.is_paused:
            with QMutexLocker(self.mutex):
                self.is_paused = True

    def resume_thread(self):
        with QMutexLocker(self.mutex):
            if self.is_paused:
                self.is_paused = False
                self.cond.wakeOne()

    def run(self):
        # total times to run the commands
        for i in range(self.total_times):
            self.execute_commands()

    def clean_up(self):
        # Add any cleanup code here if needed
        pass