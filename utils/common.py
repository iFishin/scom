import os
import re
import sys
import time
import json
import serial
import configparser
from datetime import datetime


class SerialPortNotInitializedError(Exception):
    pass

def get_absolute_path(file_name):
    """
    获取文件的绝对路径

    参数：
    file_name (str): 文件名
    
    返回：
    str: 文件的绝对路径
    """
    abs_path = None
    if hasattr(sys, "_MEIPASS"):
        base_path = os.path.join(sys._MEIPASS)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    base_path = os.path.abspath(os.path.join(base_path, ".."))
    abs_path = os.path.join(base_path, file_name)
    if os.path.exists(abs_path):
        return abs_path
    else:
        raise FileNotFoundError(f"File not found at path: {abs_path}")


def force_decode(text: bytes) -> str:
    """
    强制解码文本

    参数：
    text (bytes): 要解码的字节文本

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


def create_default_config() -> None:
    """
    创建默认配置文件

    参数：
    None

    返回：
    None
    """
    config_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    config_path = os.path.join(config_dir, "config.ini")
    default_config_path = os.path.join(config_dir, "config", "config_default")

    if not os.path.exists(config_path):
        if os.path.exists(default_config_path):
            try:
                with open(default_config_path, 'r', encoding='utf-8') as src, open(config_path, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            except IOError as e:
                custom_print(f"Error creating default config file: {e}")
                raise e
        else:
            raise FileNotFoundError(f"Default config file not found at {default_config_path}")


def read_config(config_path: str = None) -> configparser.ConfigParser:
    """
    读取配置文件，如果不存在则创建默认配置文件
    
    参数：
    config_path (str): 配置文件路径，默认为 None

    返回：
    configparser.ConfigParser: 配置文件对象
    """
    if config_path is None:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
    else:
        config_path = os.path.abspath(config_path)
    config = configparser.ConfigParser()
    config.optionxform = str

    if not os.path.exists(config_path):
        create_default_config()
        try:
            config.read(config_path, encoding="utf-8")
        except configparser.Error as e:
            custom_print(f"Error reading config file: {e}")
            raise e
    else:
        try:
            config.read(config_path, encoding="utf-8")
        except configparser.MissingSectionHeaderError as e:
            custom_print("Configuration file is corrupted or missing section headers.")
            create_default_config()
            try:
                config.read(config_path, encoding="utf-8")
            except configparser.Error as e:
                custom_print(f"Error reading config file: {e}")
                raise e
    
    return config


def write_config(config: configparser.ConfigParser, config_path: str = None) -> None:
    """
    写入配置文件

    参数：
    config (configparser.ConfigParser): 配置文件对象
    config_path (str): 配置文件路径，默认为 None

    返回：
    None
    """
    if config_path is None:
        config_path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.ini"))
    else:
        config_path = os.path.abspath(config_path)
    try:
        custom_print(f"Writing config file to {config_path}")
        with open(config_path, "w", encoding="utf-8") as configfile:
            config.write(configfile)
    except IOError as e:
        custom_print(f"Error writing config file: {e}")
        raise e


def log_write(res: str, log_file: str = None) -> bool:
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
        with open(os.path.join(log_file), "a", encoding="utf-8") as log_file_object:
            log_file_object.write("{}\n".format(res.strip()))
        return True
    except IOError as e:
        custom_print(f"Error writing to log file: {e}")
        raise e


def port_on(
    port: str,
    baudrate: int,
    stopbits=serial.STOPBITS_ONE,
    parity=serial.PARITY_NONE,
    bytesize=serial.EIGHTBITS,
    flowcontrol=None,
    dtr=False,
    rts=False,
) -> serial.Serial:
    """
    打开指定参数的串口

    参数：
    port (str): 串口名称
    baudrate (int): 波特率
    stopbits: 停止位（默认 serial.STOPBITS_ONE）
    parity: 校验位（默认 serial.PARITY_NONE）
    bytesize: 数据位（默认 serial.EIGHTBITS）
    flowcontrol: 流控制（默认 None）
    dtr: DTR 控制（默认 False）
    rts: RTS 控制（默认 False）

    返回：
    serial.Serial or None: 成功打开的串口对象或 None（如果打开失败）
    """
    try:
        ser = serial.Serial()
        ser.port = port
        ser.baudrate = baudrate
        ser.stopbits = stopbits
        ser.parity = parity
        ser.bytesize = bytesize
        if flowcontrol == "RTS/CTS":
            ser.rtscts = True
            ser.xonxoff = False
            ser.dsrdtr = False
        elif flowcontrol == "XON/XOFF":
            ser.xonxoff = True
            ser.rtscts = False
            ser.dsrdtr = False
        elif flowcontrol == "DSR/DTR":
            ser.dsrdtr = True
            ser.rtscts = False
            ser.xonxoff = False
        else:
            ser.rtscts = False
            ser.xonxoff = False
            ser.dsrdtr = False
        ser.rts = rts
        ser.dtr = dtr
        ser.open()
        return ser
    except Exception as e:
        custom_print(f"Error opening serial port: {e}")
        raise e


def port_off(port_serial: serial.Serial) -> None:
    """
    关闭打开的串口

    参数：
    port_serial (serial.Serial): 要关闭的串口对象

    返回：
    None
    """
    if port_serial:
        try:
            port_serial.close()
        except Exception as e:
            custom_print(f"Error closing serial port: {e}")
            raise e


def port_write(
    command: str,
    port_serial: serial.Serial,
    sendWithEnter: bool = True,
    sendWithOther: str = None,
) -> None:
    """
    向串口写入命令

    参数：
    command (str): 要写入的命令
    port_serial (serial.Serial): 打开的串口对象
    sendWithEnter (bool): 是否添加回车换行（默认 True）
    """
    if port_serial is None:
        raise SerialPortNotInitializedError("Serial port is not initialized.")
    else:
        try:
            if sendWithEnter:
                port_serial.write((command + "\r\n").encode("UTF-8"))
            else:
                if sendWithOther:
                    port_serial.write((command + sendWithOther).encode("UTF-8"))
                else:
                    port_serial.write(command.encode("UTF-8"))
        except Exception as e:
            custom_print(f"Error writing to serial port: {e}")
            raise e


def port_read(port_serial: serial.Serial, size: int = 1) -> str:
    """
    从串口读取数据

    参数：
    port_serial (serial.Serial): 串口对象
    size (int): 读取的最大字节数（默认 1）

    返回：
    str: 读取到的数据
    """
    if port_serial is None:
        raise SerialPortNotInitializedError("Serial port is not initialized.")
    else:
        try:
            data = bytearray()
            while port_serial.in_waiting > 0:
                data.extend(port_serial.read(size=port_serial.in_waiting or size))
                time.sleep(0.01)
            return data.decode("UTF-8", errors="ignore")
        except Exception as e:
            custom_print(f"Error reading from serial port: {e}")
            raise e


def port_read_hex(port_serial: serial.Serial, size: int = 1) -> str:
    """
    从串口读取数据并以带空格的大写十六进制形式返回

    参数：
    port_serial (serial.Serial): 串口对象
    size (int): 读取的最大字节数（默认 1）

    返回：
    str: 读取到的数据的十六进制表示，每个字节之间有一个空格且为大写
    """
    if port_serial is None:
        raise SerialPortNotInitializedError("Serial port is not initialized.")
    else:
        try:
            reply = bytearray()
            while port_serial.inWaiting() > 0:
                reply.extend(port_serial.read(size=size))
            if reply:
                hex_reply = " ".join(f"{byte:02X}" for byte in reply)
                return hex_reply
            else:
                return ""
        except Exception as e:
            custom_print(f"Error reading from serial port as hex: {e}")
            raise e


def port_read_until(
    port_serial: serial.Serial,
    expected: bytes = b"\r\n",
    size: int = None,
    is_show_symbol: bool = False,
) -> str:
    """
    从串口读取数据直到遇到指定字符

    参数：
    port_serial (serial.Serial): 串口对象
    expected (bytes): 期望遇到的字符（默认 b"\r\n"）
    size (int): 读取的最大字节数（默认 None）
    is_show_symbol (bool): 是否显示特殊字符（默认 False）

    返回：
    str: 读取到的数据
    """
    if port_serial is None:
        raise SerialPortNotInitializedError("Serial port is not initialized.")
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
                    reply += port_serial.read_until(expected, size=size).decode(
                        "UTF-8", errors="ignore"
                    )
        except Exception as e:
            custom_print(f"Error reading from serial port: {e}")
            raise e


def port_readline(port_serial: serial.Serial) -> str:
    """
    从串口按行读取数据

    参数：
    port_serial (serial.Serial): 串口对象

    返回：
    str: 读取到的一行数据，如果发生异常则上报
    """
    if port_serial is None:
        raise SerialPortNotInitializedError("Serial port is not initialized.")
    else:
        try:
            line = port_serial.readline()
            if line:
                return line.decode("UTF-8", errors="ignore")
            else:
                return ""
        except Exception as e:
            custom_print(f"Error reading a line from serial port: {e}")
            raise e


def port_readline_hex(port_serial: serial.Serial) -> str:
    """
    从串口按行读取数据并以带空格的大写十六进制形式返回

    参数：
    port_serial (serial.Serial): 串口对象

    返回：
    str: 读取到的一行数据的十六进制表示，每个字节之间有一个空格且为大写，如果发生异常则上报
    """
    if port_serial is None:
        raise SerialPortNotInitializedError("Serial port is not initialized.")
    else:
        try:
            line = port_serial.readline()
            if line:
                hex_line = " ".join(f"{byte:02X}" for byte in line)
                return hex_line
            else:
                return ""
        except Exception as e:
            custom_print(f"Error reading a line from serial port as hex: {e}")
            raise e


def echo(port_serial: serial.Serial) -> None:
    """
    发送 AT+QECHO=1 命令并读取响应

    参数：
    port_serial (serial.Serial): 串口对象
    """
    if port_serial is None:
        raise SerialPortNotInitializedError("Serial port is not initialized.")
    else:
        port_write("AT+QECHO=1\r\n", port_serial)
        port_read(port_serial)


def reset(port_serial: serial.Serial) -> None:
    """
    发送 AT+QRST 命令并读取响应

    参数：
    port_serial (serial.Serial): 串口对象
    """
    if port_serial is None:
        raise SerialPortNotInitializedError("Serial port is not initialized.")
    else:
        port_write("AT+RESTORE\r\n", port_serial)
        port_read(port_serial)


def print_write(text: str, log_file=None, isPrint=False) -> None:
    """
    打印并写入文本到日志

    参数：
    text (str): 要打印和写入日志的文本
    isPrint (bool): 是否打印文本（默认 False）
    """
    for line in text.strip().split("\n"):
        if line.strip():
            log_write(f"{line}", log_file=log_file)
            if isPrint:
                custom_print(f"{line}")


def custom_print(text: str, log_file: str = None, isPrint: bool = False) -> None:
    """
    自定义打印文本，带时间戳

    参数：
    text (str): 要打印的文本
    log_file (str): 日志文件路径，默认为 None
    isPrint (bool): 是否打印文本，默认为 False

    返回：
    None
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
    formatted_text = f"{timestamp} - {text}"
    if log_file is None:
        log_file = "logs/error.log"
    if isPrint:
        print_write(formatted_text, log_file=log_file, isPrint=isPrint)
    else:
        log_write(formatted_text, log_file=log_file)


def clear_terminal() -> None:
    """
    清空终端屏幕
    """
    if sys.platform.startswith("win"):
        os.system("cls")
    else:
        os.system("clear")


def join_text(text_list: list) -> str:
    """
    拼接数组成长文本

    参数：
    text_list (list): 要拼接的文本列表

    返回：
    str: 拼接后的长文本
    """
    return "\n".join(text_list)


def split_text(text: str) -> list:
    """
    拆分长文本为数组

    参数：
    text (str): 要拆分的长文本

    返回：
    list: 拆分后的文本数组
    """
    return text.split("\n")


def read_ATCommand(path_command_json: str) -> list:
    """
    读取 AT 命令文件

    参数：
    path_command_json (str): AT 命令文件路径

    返回：
    list: AT 命令列表
    """
    try:
        with open(path_command_json, "r", encoding="utf-8") as f:
            data = json.load(f)
            commands = [item["command"] for item in data.get("commands", [])]
            return commands
    except IOError as e:
        custom_print(f"Error reading AT command file: {e}")


def write_ATCommand(path_command_json: str, commands: list) -> None:
    """
    写入 AT 命令文件

    参数：
    path_command_json (str): AT 命令文件路径
    commands (list): AT 命令列表

    返回：
    None
    """
    try:
        with open(path_command_json, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "commands": [
                        {
                            "selected": False,
                            "command": command,
                            "withEnter": True,
                            "interval": "",
                        }
                        for command in commands
                    ]
                },
                f,
                ensure_ascii=False,
                indent=4,
            )
    except IOError as e:
        custom_print(f"Error writing AT command file: {e}")


def strip_AT_command(
    text: str, regex: str = r"(?i)(AT\+[^（）<>\n\t\\\r\u4e00-\u9fa5]+)"
) -> list:
    """
    提取 AT 命令

    参数：
    text (str): 包含 AT 命令的文本
    regex (str): 正则表达式（默认 r"(?i)(AT\+[^（）\n\t\\\r\u4e00-\u9fa5]+)"）

    返回：
    list: 提取的 AT 命令列表
    """
    return re.findall(regex, text)


def update_AT_command(path_command_json: str) -> str:
    """
    更新 AT 命令文件，去除无效内容

    参数：
    path_command_json (str): AT 命令文件路径

    返回：
    str: 更新后的 AT 命令内容
    """
    try:
        text = "\n".join(read_ATCommand(path_command_json))
        if not text:
            custom_print("ATCommand.txt is empty. Exiting...")
            return ""
        else:
            with open(path_command_json, "w", encoding="utf-8") as f:
                write_ATCommand(path_command_json, strip_AT_command(text))
                result = "\n".join(strip_AT_command(text))
                return result
    except IOError as e:
        custom_print(f"Error updating AT command file: {e}")


def remove_TimeStamp(text: str, regex: str = r"\[20(.*?)\]") -> str:
    """
    去除文本中的时间戳

    参数：
    text (str): 输入文本
    regex (str): 正则表达式（默认 r"\[20(.*?)\]"）

    返回：
    str: 去除时间戳后的文本
    """
    return re.sub(regex, "", text)
