from PySide6.QtCore import QThread, Signal, QMutex, QWaitCondition
from utils import common
from middileware.Logger import init_logging, Logger


class CommandExecutor(QThread):
    # Signal to emit index only
    commandExecuted = Signal(int)
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
        # initialize logger for this component; if global logger not initialized, create it
        try:
            self.logger = Logger.get_logger('CommandExecutor', 'command_executor.log')
        except RuntimeError:
            init_logging(app_name='SCOM')
            self.logger = Logger.get_logger('CommandExecutor', 'command_executor.log')
    # initialization complete (logging suppressed to only show errors)
        
    def execute_commands(self):
        for command_dict in self.commands:
            index = command_dict.get('index', 0)
            command = command_dict.get('command', '')
            interval = command_dict.get('interval', '')
            with_enter = command_dict.get('withEnder', False)
            # Pause handling: lock the mutex and wait while paused
            self.mutex.lock()
            try:
                while self.is_paused:
                    # wait will release the mutex and re-acquire it after wakeOne
                    self.cond.wait(self.mutex)
            finally:
                self.mutex.unlock()

            # Execute the command and emit detailed errors on failure
            try:
                # execution log suppressed; only errors will be logged
                common.port_write(command, self.serial_port, with_enter)
                self.commandExecuted.emit(index+1)
                # interval is treated as milliseconds now. If it's provided, try to parse it
                # as a number (may be string) representing ms. Fallback default is 3000 ms.
                if interval:
                    try:
                        ms = int(float(interval))
                    except Exception:
                        ms = 0
                    if ms > 0:
                        QThread.msleep(ms)
                else:
                    QThread.msleep(3000)
            except Exception as e:
                # Emit error detail, set error flag, and log exception with traceback
                self.error_occurred = True
                msg = f"Error executing command {index+1}: {e}"
                self.logger.exception(msg)
                self.commandExecuted.emit(-1)
                # QThread.sleep(2)
        # emit completion signal; error logging handled in exception path
        self.commandExecuted.emit(-1)
        if self.error_occurred:
            self.commandExecuted.emit(-1)

    def pause_thread(self):
        if not self.is_paused:
            self.mutex.lock()
            try:
                self.is_paused = True
            finally:
                self.mutex.unlock()
            # paused (logging suppressed)

    def resume_thread(self):
        self.mutex.lock()
        try:
            if self.is_paused:
                self.is_paused = False
                # wake all waiting threads (only one in this design)
                self.cond.wakeOne()
        finally:
            self.mutex.unlock()
            # resumed (logging suppressed)

    def run(self):
        # total times to run the commands
        for i in range(self.total_times):
            self.execute_commands()
            self.totalTimes.emit(self.total_times - i - 1)
            

    def clean_up(self):
        # Add any cleanup code here if needed
        pass