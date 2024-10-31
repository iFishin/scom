import io
import os
import re
import sys
import time
import json
import serial


def force_decode(text: str) -> str:
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
        print(f"Error writing to log file: {e}")
        return False


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
        # 创建一个 Serial 对象但不打开串口连接
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
    except serial.SerialException as e:
        print(f"{port}口连接失败，可能是串口被占用。")
        print(e)
        return None

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
            print(f"Error closing serial port: {e}")


def port_write(
    command: str, port_serial: serial.Serial, sendWithEnter: bool = True
) -> None:
    """
    向串口写入命令

    参数：
    command (str): 要写入的命令
    port_serial (serial.Serial): 打开的串口对象
    sendWithEnter (bool): 是否添加回车换行（默认 True）
    """
    if port_serial is None:
        print("Serial port is not initialized.")
        return
    else:
        try:
            if sendWithEnter:
                command = command.rstrip()
                port_serial.write((command + "\r\n").encode("UTF-8"))
            else:
                port_serial.write(command.encode("UTF-8"))
        except Exception as e:
            print(f"Error writing to serial port: {e}")
            raise e


def port_read(port_serial: serial.Serial) -> str:
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
                    reply += port_serial.read_until(expected, size=size).decode(
                        "UTF-8", errors="ignore"
                    )
        except Exception as e:
            print(f"Error reading from serial port: {e}")
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
        print("Serial port is not initialized.")
        return ""
    else:
        try:
            line = port_serial.readline()
            if line:
                return line.decode("UTF-8", errors="ignore")
            else:
                return ""
        except Exception as e:
            print(f"Error reading a line from serial port: {e}")
            raise e


def echo(port_serial: serial.Serial) -> None:
    """
    发送 AT+QECHO=1 命令并读取响应

    参数：
    port_serial (serial.Serial): 串口对象
    """
    if port_serial is None:
        print("Serial port is not initialized.")
        return
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
        print("Serial port is not initialized.")
        return
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
                print(f"{line}")


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
        print(f"Error reading AT command file: {e}")


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
                            "interval": '',
                        }
                        for command in commands
                    ]
                },
                f,
                ensure_ascii=False,
                indent=4,
            )
    except IOError as e:
        print(f"Error writing AT command file: {e}")


def strip_AT_command(
    text: str, regex: str = r"(?i)(AT\+[^（）\n\t\\\r\u4e00-\u9fa5]+)"
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
            print("ATCommand.txt is empty. Exiting...")
            return ""
        else:
            with open(path_command_json, "w", encoding="utf-8") as f:
                write_ATCommand(path_command_json, strip_AT_command(text))
                result = "\n".join(strip_AT_command(text))
                return result
    except IOError as e:
        print(f"Error updating AT command file: {e}")


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
