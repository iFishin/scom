"""
AT命令管理器
提供智能的AT命令文件管理功能，包括自动保存、变更检测等
"""

import os
import json
import datetime
from typing import Dict, List, Tuple, Optional
from middileware.Logger import Logger
from components.ErrorDialog import ErrorDialog

logger = Logger(
    app_name="ATCommandManager",
    log_dir="logs",
    max_bytes=10 * 1024 * 1024,
    backup_count=3
).get_logger("ATCommandManager")

class ATCommandManager:
    """AT命令管理器类"""
    
    def __init__(self, parent=None):
        """
        初始化AT命令管理器
        
        Args:
            parent: 父窗口对象
        """
        self.parent = parent
        self.current_file_path = ""
        self.original_content = ""  # 原始文件内容
        self.current_content = ""   # 当前编辑内容
        self.is_modified = False    # 是否已修改
        self.auto_save_enabled = True  # 是否启用自动保存
        
    def set_file_path(self, file_path: str):
        """设置当前文件路径并重置状态"""
        self.current_file_path = file_path
        # 重置修改状态
        self.is_modified = False
        
    def load_file(self, file_path: str) -> Tuple[str, str]:
        """
        加载AT命令文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            tuple: (文件内容, 错误信息)
        """
        try:
            if not os.path.exists(file_path):
                error_msg = f"文件不存在: {file_path}"
                return "", error_msg
            
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                commands = [item.get("command", "") for item in data.get("Commands", [])]
                content = "\n".join(commands)
                
                # 记录原始内容
                self.original_content = content
                self.current_content = content
                self.current_file_path = file_path
                self.is_modified = False
                
                return content, ""
                
        except json.JSONDecodeError as e:
            error_msg = f"JSON格式错误: {str(e)}"
            return "", error_msg
        except UnicodeDecodeError as e:
            error_msg = f"文件编码错误: {str(e)}"
            return "", error_msg
        except Exception as e:
            error_msg = f"读取文件失败: {str(e)}"
            return "", error_msg
    
    def update_content(self, new_content: str):
        """
        更新当前内容
        
        Args:
            new_content: 新的内容
        """
        self.current_content = new_content
        self.is_modified = (self.current_content != self.original_content)
        
    def has_unsaved_changes(self) -> bool:
        """检查是否有未保存的更改"""
        return self.is_modified
        
    def save_file(self, file_path: str = None, content: str = None) -> Tuple[bool, str]:
        """
        保存AT命令文件
        
        Args:
            file_path: 文件路径，如果为None则使用当前路径
            content: 要保存的内容，如果为None则使用当前内容
            
        Returns:
            tuple: (是否成功, 错误信息)
        """
        try:
            save_path = file_path or self.current_file_path
            save_content = content or self.current_content
            
            if not save_path:
                return False, "未指定保存路径"
            
            # 确保目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # 将文本内容转换为JSON格式
            commands = [line.strip() for line in save_content.split('\n')]
            
            # 读取现有文件的元数据（如果存在）
            existing_data = {}
            if os.path.exists(save_path):
                try:
                    with open(save_path, "r", encoding="utf-8") as f:
                        existing_data = json.load(f)
                except:
                    pass
            
            # 构建新的数据结构
            json_data = {
                "name": existing_data.get("name", os.path.basename(save_path)),
                "description": existing_data.get("description", "AT Command configuration file"),
                "version": existing_data.get("version", "1.0"),
                "created": existing_data.get("created", datetime.datetime.now().isoformat()),
                "modified": datetime.datetime.now().isoformat(),
                "author": existing_data.get("author", "SCOM User"),
                "settings": existing_data.get("settings", {
                    "baudrate": "115200",
                    "timeout": 1.0,
                    "encoding": "utf-8"
                }),
                "Commands": []
            }
            
            # 构建Commands数组，保留现有的扩展属性
            existing_commands = existing_data.get("Commands", [])
            for i, command in enumerate(commands):
                if i < len(existing_commands):
                    # 保留现有命令的其他属性
                    cmd_data = existing_commands[i].copy()
                    cmd_data["command"] = command
                else:
                    # 新命令使用默认属性
                    cmd_data = {
                        "name": f"Command {i + 1}",
                        "command": command,
                        "description": "",
                        "expected_response": "OK",
                        "timeout": 3,
                        "selected": False,
                        "withEnder": True,
                        "hex": False,
                        "interval": 0
                    }
                json_data["Commands"].append(cmd_data)
            
            # 写入文件
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=4, ensure_ascii=False)
            
            # 更新状态
            self.original_content = save_content
            self.current_content = save_content
            self.is_modified = False
            
            logger.info(f"AT command file saved successfully: {save_path}")
            return True, ""
            
        except Exception as e:
            error_msg = f"保存文件失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def prompt_save_changes(self) -> str:
        """
        提示用户保存更改
        
        Returns:
            str: 用户选择 ("save", "discard", "cancel")
        """
        if not self.has_unsaved_changes():
            return "no_changes"
        
        from PySide6.QtWidgets import QMessageBox
        
        msg_box = QMessageBox(self.parent)
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setWindowTitle("Unsaved Changes")
        msg_box.setText("The current AT command file has unsaved changes")
        msg_box.setInformativeText("Do you want to save these changes?")
        
        save_button = msg_box.addButton("Save", QMessageBox.AcceptRole)
        discard_button = msg_box.addButton("Don't Save", QMessageBox.DestructiveRole)
        cancel_button = msg_box.addButton("Cancel", QMessageBox.RejectRole)
        
        msg_box.setDefaultButton(save_button)
        msg_box.exec()
        
        clicked_button = msg_box.clickedButton()
        if clicked_button == save_button:
            return "save"
        elif clicked_button == discard_button:
            return "discard"
        else:
            return "cancel"
    
    def create_default_file(self, file_path: str) -> Tuple[bool, str]:
        """
        创建默认的AT命令文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            tuple: (是否成功, 错误信息)
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 默认命令列表
            default_commands = [
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
            
            # 构建JSON数据
            json_data = {
                "name": os.path.basename(file_path),
                "description": "AT Command configuration file",
                "version": "1.0",
                "created": datetime.datetime.now().isoformat(),
                "author": "SCOM User",
                "settings": {
                    "baudrate": "115200",
                    "timeout": 1.0,
                    "encoding": "utf-8"
                },
                "Commands": []
            }
            
            # 添加默认命令
            for i, command in enumerate(default_commands):
                json_data["Commands"].append({
                    "name": f"Command {i + 1}",
                    "command": command,
                    "description": f"Default AT command {i + 1}",
                    "expected_response": "OK",
                    "timeout": 3,
                    "selected": True,
                    "withEnder": True,
                    "hex": False,
                    "interval": 0
                })
            
            # 写入文件
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=4, ensure_ascii=False)
            
            # 更新状态
            content = "\n".join(default_commands)
            self.original_content = content
            self.current_content = content
            self.current_file_path = file_path
            self.is_modified = False
            
            logger.info(f"Created default AT command file: {file_path}")
            return True, ""
            
        except Exception as e:
            error_msg = f"创建默认文件失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_file_info(self) -> Dict:
        """获取当前文件信息"""
        return {
            "file_path": self.current_file_path,
            "is_modified": self.is_modified,
            "original_length": len(self.original_content.split('\n')) if self.original_content else 0,
            "current_length": len(self.current_content.split('\n')) if self.current_content else 0,
            "auto_save_enabled": self.auto_save_enabled
        }
