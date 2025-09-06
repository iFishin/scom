"""
打包配置工具 - 针对不同分发渠道的配置
"""

import os
import json
import shutil
from pathlib import Path


class PackageConfig:
    """打包配置管理"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.configs = {
            "safe": {
                "name": "安全版本",
                "description": "禁用自动更新，适合企业环境和避免报毒",
                "features": {
                    "auto_update": False,
                    "network_check": False,
                    "file_download": False,
                    "external_links": False,
                    "telemetry": False
                }
            },
            "standard": {
                "name": "标准版本",
                "description": "包含所有功能，适合个人用户",
                "features": {
                    "auto_update": True,
                    "network_check": True,
                    "file_download": False,  # 仍然禁用自动下载
                    "external_links": True,
                    "telemetry": False
                }
            },
            "enterprise": {
                "name": "企业版本",
                "description": "无网络功能，适合内网环境",
                "features": {
                    "auto_update": False,
                    "network_check": False,
                    "file_download": False,
                    "external_links": False,
                    "telemetry": False
                }
            }
        }
    
    def generate_config(self, config_type: str):
        """生成指定类型的配置文件"""
        if config_type not in self.configs:
            raise ValueError(f"不支持的配置类型: {config_type}")
        
        config = self.configs[config_type]
        
        # 生成运行时配置文件
        runtime_config = {
            "package_type": config_type,
            "features": config["features"],
            "build_info": {
                "version": "1.0.0",
                "build_date": "2025-08-31",
                "description": config["description"]
            }
        }
        
        # 保存配置文件
        config_file = self.base_dir / "package_config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(runtime_config, f, indent=2, ensure_ascii=False)
        
        print(f"已生成 {config['name']} 配置")
        print(f"配置文件: {config_file}")
        
        return runtime_config
    
    def patch_update_checker(self, config_type: str):
        """根据配置类型修补更新检查器"""
        if config_type == "safe" or config_type == "enterprise":
            # 创建禁用版本的更新检查器
            safe_checker_content = '''"""
安全版本的更新检查器 - 禁用所有网络功能
"""

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox


class SafeUpdateChecker(QObject):
    """安全的更新检查器 - 无网络功能"""
    update_available = Signal(str, str)
    check_failed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def check_for_updates(self, user_initiated=True):
        """禁用的更新检查"""
        if user_initiated:
            self.check_failed.emit("此版本已禁用自动更新功能\\n请手动访问项目页面获取更新")


class SafeUpdateDialog(QDialog):
    """安全版本的更新对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("更新检查")
        self.setFixedSize(400, 200)
        
        layout = QVBoxLayout()
        
        label = QLabel("此版本已禁用自动更新功能\\n\\n如需获取最新版本，请访问:\\nhttps://github.com/iFishin/scom")
        label.setWordWrap(True)
        layout.addWidget(label)
        
        button = QPushButton("确定")
        button.clicked.connect(self.close)
        layout.addWidget(button)
        
        self.setLayout(layout)
    
    def _show_update_available(self, version, notes):
        """兼容方法"""
        pass
    
    @staticmethod
    def check_updates_on_startup():
        """启动时检查更新（禁用版本）"""
        return None
'''
            
            # 写入安全版本的文件
            safe_file = self.base_dir / "components" / "SafeUpdateChecker_safe.py"
            with open(safe_file, "w", encoding="utf-8") as f:
                f.write(safe_checker_content)
            
            # 如果是安全版本，替换原文件
            if config_type == "safe":
                original_file = self.base_dir / "components" / "SafeUpdateChecker.py"
                shutil.copy(safe_file, original_file)
                print("已应用安全版本的更新检查器")
    
    def create_build_script(self, config_type: str):
        """创建构建脚本"""
        build_script = f'''@echo off
echo 构建 {self.configs[config_type]["name"]} 版本...

REM 生成配置
python build_config.py {config_type}

REM 清理之前的构建
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

REM 使用PyInstaller打包
pyinstaller SCOM.spec --clean --noconfirm

REM 复制配置文件到输出目录
copy package_config.json dist\\SCOM\\

echo 构建完成！
echo 输出目录: dist\\SCOM\\
pause
'''
        
        script_file = self.base_dir / f"build_{config_type}.bat"
        with open(script_file, "w", encoding="gbk") as f:
            f.write(build_script)
        
        print(f"已创建构建脚本: {script_file}")


def main():
    """主函数"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python build_config.py <config_type>")
        print("可用配置类型: safe, standard, enterprise")
        return
    
    config_type = sys.argv[1]
    
    builder = PackageConfig()
    
    try:
        # 生成配置
        config = builder.generate_config(config_type)
        
        # 修补更新检查器
        builder.patch_update_checker(config_type)
        
        # 创建构建脚本
        builder.create_build_script(config_type)
        
        print(f"\\n✅ {config['build_info']['description']} 配置已准备完成")
        print(f"使用 build_{config_type}.bat 开始构建")
        
    except Exception as e:
        print(f"❌ 配置生成失败: {e}")


if __name__ == "__main__":
    main()
