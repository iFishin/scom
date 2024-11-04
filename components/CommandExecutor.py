from PySide6.QtCore import QThread, Signal, QMutex, QWaitCondition, QMutexLocker
from utils import common


class CommandExecutor(QThread):
    # Signal to emit index, command
    commandExecuted = Signal(int, str)
    totalTimes = Signal(int)

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
            index = command_dict.get('index', 0)
            command = command_dict.get('command', '')
            interval = command_dict.get('interval', '')
            with_enter = command_dict.get('withEnter', False)

            with QMutexLocker(self.mutex):
                if self.is_paused:
                    self.cond.wait(self.mutex)
            if not self.is_paused:
                try:
                    # Use common.port_write to execute the command
                    common.port_write(command, self.serial_port, with_enter)
                    self.commandExecuted.emit(index, command)
                    if interval:
                        QThread.sleep(int(interval))
                except Exception as e:
                    self.error_occurred = True
                # QThread.sleep(2)
        self.commandExecuted.emit(-1, "All commands completed.")
        if self.error_occurred:
            self.commandExecuted.emit(-1, "Some commands encountered errors.")

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
            self.totalTimes.emit(self.total_times - i - 1)
            

    def clean_up(self):
        # Add any cleanup code here if needed
        pass