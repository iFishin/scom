import io
import os
import re
import sys
import time
import serial
from serial.tools import list_ports
import datetime
import threading
import logging



tmp_log = "./tmps/temp.log"
command_txt = "./utils/ATCommand.txt"

def force_decode(text):
    """
    强制解码文本

    参数：
    text (str): 要解码的文本

    返回：
    str: 解码后的文本
    """
    encoding_list = ["utf-8", "gbk", "big5", "latin1"]
    for encoding in encoding_list:
        try:
            return text.decode(encoding)
        except UnicodeDecodeError:
            continue
    return text.decode("utf-8", "ignore")

def log_write(res, log_file=None):
    """
    将结果写入临时日志文件

    参数：
    res (str): 要写入的结果
    log_file (str): 日志文件路径，默认为 None

    返回：
    bool: 写入成功返回 True，否则返回 False
    """
    if log_file is None:
        log_file = "./tmps/temp.log"
    try:
        with open(log_file, "a+", encoding="utf-8") as file_object:
            file_object.write("{}\n".format(res.strip()))
        return True
    except IOError as e:
        print(f"Error writing to log file: {e}")
        return False

def response_write(res):
    """
    处理响应写入（目前为空实现，可根据需要添加功能）

    参数：
    res (str): 响应结果
    """
    pass

def port_select():
    """
    选择可用的串口

    返回：
    str: 选择的串口设备名称
    """
    port_list = list_ports.comports()
    if not port_list:
        print("未检测到串口，请检查串口连接")
        sys.exit()
    logging.info("请选择串口，默认第一个：")
    for index, port in enumerate(port_list):
        logging.info(f"{index + 1}: {port.device}")
    while True:
        try:
            port_index = input("请输入序号：")
            if port_index == "":
                return port_list[0].device
            elif 0 <= int(port_index) - 1 < len(port_list):
                return port_list[int(port_index) - 1].device
            else:
                print("输入错误，请重新输入")
        except ValueError:
            print("输入错误，请重新输入")

def baudrate_select():
    """
    选择波特率

    返回：
    int: 选择的波特率值
    """
    logging.info("请选择波特率，默认第一个：")
    baudrate_list = [115200, 921600]
    for index, baudrate in enumerate(baudrate_list):
        logging.info(f"{index + 1}: {baudrate}")
    while True:
        try:
            baudrate_index = input("请输入序号：")
            if baudrate_index == "":
                return baudrate_list[0]
            elif 0 <= int(baudrate_index) - 1 < len(baudrate_list):
                return baudrate_list[int(baudrate_index) - 1]
            else:
                print("输入错误，请重新输入")
        except ValueError:
            print("输入错误，请重新输入")

def port_on(port, baudrate, stopbits=serial.STOPBITS_ONE, parity=serial.PARITY_NONE, bytesize=serial.EIGHTBITS, flowcontrol=None):
    """
    打开指定参数的串口

    参数：
    port (str): 串口名称
    baudrate (int): 波特率
    stopbits: 停止位（默认 serial.STOPBITS_ONE）
    parity: 校验位（默认 serial.PARITY_NONE）
    bytesize: 数据位（默认 serial.EIGHTBITS）
    flowcontrol: 流控制（默认 None）

    返回：
    serial.Serial or None: 成功打开的串口对象或 None（如果打开失败）
    """
    try:
        if flowcontrol == "RTS/CTS":
            port_serial = serial.Serial(port, baudrate, stopbits=stopbits, parity=parity, bytesize=bytesize, rtscts=True, timeout=0.1)
        elif flowcontrol == "XON/XOFF":
            port_serial = serial.Serial(port, baudrate, stopbits=stopbits, parity=parity, bytesize=bytesize, xonxoff=True, timeout=0.1)
        else:
            port_serial = serial.Serial(port, baudrate, stopbits=stopbits, parity=parity, bytesize=bytesize, timeout=0.1)
        return port_serial
    except serial.SerialException as e:
        print(f"{port}口连接失败，可能是串口被占用。")
        print(e)
        return None

def port_off(port_serial):
    """
    关闭打开的串口

    参数：
    port_serial (serial.Serial): 要关闭的串口对象

    返回：
    None
    """
    if port_serial and port_serial.is_open:
        try:
            port_serial.close()
        except Exception as e:
            print(f"Error closing serial port: {e}")

def port_write(command, port_open, sendWithEnter=True):
    """
    向串口写入命令

    参数：
    command (str): 要写入的命令
    port_open (serial.Serial): 打开的串口对象
    sendWithEnter (bool): 是否添加回车换行（默认 True）
    """
    if port_open is None:
        print("Serial port is not initialized.")
        return
    else:
        try:
            if sendWithEnter:
                command = command.rstrip()
                port_open.write((command + "\r\n").encode("UTF-8"))
            else:
                port_open.write(command.encode("UTF-8"))
        except Exception as e:
            print(f"Error writing to serial port: {e}")
            raise e

def port_read(port_serial):
    """
    从串口读取数据

    参数：
    port_serial (serial.Serial): 串口对象

    返回：
    str: 读取到的数据
    """
    if port_serial is None:
        print("Serial port is not initialized.")
        return ""
    else:
        reply = ""
        try:
            time.sleep(0.5)
            while port_serial.inWaiting() > 0:
                reply += port_serial.read(size=1).decode("UTF-8", errors="ignore")
        except UnicodeDecodeError as e:
            print(f"Error decoding byte. Skipping... {e}")
        except Exception as e:
            print(f"Error reading from serial port: {e}")
        return reply
    
def port_read_until(port_serial, expected=b"\r\n", size=None, is_show_symbol=False):
    """
    从串口读取数据直到遇到指定字符

    参数：
    port_serial (serial.Serial): 串口对象
    expected (str): 预期的字符（默认为换行符）

    返回：
    str: 读取到的数据
    """
    if port_serial is None:
        print("Serial port is not initialized.")
        return ""
    else:
        reply = ""
        try:
            while True:
                if reply.endswith(expected.decode("UTF-8")):
                    if is_show_symbol:
                        return repr(reply)[1:-1]
                    else:
                        return reply
                else:
                    reply += port_serial.read_until(expected, size=size).decode("UTF-8", errors="ignore")
        except Exception as e:
            print(f"Error reading from serial port: {e}")
            raise e
            return ""

def port_readline(serial_port):
    """
    从串口按行读取数据

    参数：
    serial_port (serial.Serial): 串口对象

    返回：
    str: 读取到的一行数据，如果发生异常则上报
    """
    if serial_port is None:
        print("Serial port is not initialized.")
        return ""
    else:
        try:
            line = serial_port.readline()
            if line:
                return line.decode("UTF-8", errors="ignore")
            else:
                return ""
        except Exception as e:
            print(f"Error reading a line from serial port: {e}")
            raise e

def echo(UART_Serial):
    """
    发送 AT+QECHO=1 命令并读取响应

    参数：
    UART_Serial (serial.Serial): 串口对象
    """
    if UART_Serial is None:
        print("Serial port is not initialized.")
        return
    else:
        port_write("AT+QECHO=1\r\n", UART_Serial)
        port_read(UART_Serial)

def reset(UART_Serial):
    """
    发送 AT+QRST 命令并读取响应

    参数：
    UART_Serial (serial.Serial): 串口对象
    """
    if UART_Serial is None:
        print("Serial port is not initialized.")
        return
    else:
        port_write("AT+RESTORE\r\n", UART_Serial)
        port_read(UART_Serial)

def print_write(text, log_file=None):
    """
    打印并写入文本到日志

    参数：
    text (str): 要打印和写入日志的文本
    """
    for line in text.strip().split("\n"):
        if line.strip():
            print(f"{line}")
            log_write(f"{line}", log_file=log_file)

def clear_terminal():
    """
    清空终端屏幕
    """
    if sys.platform.startswith('win'):
        os.system('cls')
    else:
        os.system('clear')

def strip_AT_command(text):
    """
    提取 AT 命令

    参数：
    text (str): 包含 AT 命令的文本

    返回：
    list: 提取的 AT 命令列表
    """
    return re.findall(r"(?i)(AT\+[^（）\n\t\\\r\u4e00-\u9fa5]+)", text)

def update_AT_command():
    """
    更新 AT 命令文件，去除无效内容

    返回：
    str: 更新后的 AT 命令内容
    """
    try:
        with open(command_txt, "r", encoding="utf-8") as f:
            text = f.read()
        if not text:
            print("ATCommand.txt is empty. Exiting...")
            return
        with open(command_txt, "w", encoding="utf-8") as f:
            result = "\n".join(strip_AT_command(text))
            f.write(result)
            return result
    except IOError as e:
        print(f"Error updating AT command file: {e}")

def remove_TimeStamp(text):
    """
    去除文本中的时间戳

    参数：
    text (str): 输入文本

    返回：
    str: 去除时间戳后的文本
    """
    return re.sub(r"\[20(.*?)\]", "", text)

def restore_AT_command():
    """
    还原 AT 命令文件，去除特殊字符

    参数：
    None
    """
    try:
        with open(command_txt, "r", encoding="utf-8") as f:
            text = f.read()
        if not text:
            print("ATCommand.txt is empty. Exiting...")
            sys.exit()
        text =  text.replace("$", "").replace("￥", "").replace("`", "")
        with open(command_txt, "w", encoding="utf-8") as f:
            f.write(text)
    except IOError as e:
        print(f"Error restoring AT command file: {e}")

def execute_AT_command(uart_serial):
    """
    执行 AT 命令文件中的命令

    参数：
    uart_serial (serial.Serial): 串口对象
    """
    try:
        with open ('./utils/ATCommand.txt', 'r', encoding='utf-8') as f:
            ATCommandFromFile = f.read().strip().split('\n')

        def send_command(command):
            if "`" in command:
                return
            elif "$" in command or "￥" in command:
                command = command.replace("$", "").replace("￥", "")
                port_write(command, uart_serial)
                time.sleep(10)
            else:
                # 如果是最后一个命令，等待 3 秒
                if command == ATCommandFromFile[-1]:
                    time.sleep(3)
                port_write(command, uart_serial)

        for item in ATCommandFromFile:
            threading.Thread(target=send_command, args=(item,)).start()
    except IOError as e:
        print(f"Error reading AT command file: {e}")