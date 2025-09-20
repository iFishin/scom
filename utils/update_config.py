"""
更新检测配置管理
提供灵活的更新检测配置选项
"""

import json
import os
from typing import Dict, Any


class UpdateConfig:
    """更新配置管理器"""
    
    def __init__(self, config_file: str = "update_config.json"):
        self.config_file = config_file
        self.default_config = {
            "auto_check_enabled": True,
            "check_frequency_days": 7,  # 7天检查一次
            "check_on_startup": True,
            "use_proxy": False,
            "proxy_urls": [
                "https://gh-proxy.com/",
                "https://mirror.ghproxy.com/"
            ],
            "timeout_seconds": 10,
            "last_check_time": None,
            "last_known_version": None,
            "download_method": "manual",  # manual 或 auto
            "notification_enabled": True
        }
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded_config = json.load(f)
                    # 合并默认配置和加载的配置
                    config = self.default_config.copy()
                    config.update(loaded_config)
                    return config
            else:
                return self.default_config.copy()
        except Exception as e:
            print(f"加载更新配置失败: {e}")
            return self.default_config.copy()
    
    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存更新配置失败: {e}")
    
    def get(self, key: str, default=None):
        """获取配置值"""
        return self.config.get(key, default)
    
    def set(self, key: str, value):
        """设置配置值"""
        self.config[key] = value
        self.save_config()
    
    def disable_auto_check(self):
        """禁用自动检查（减少报毒风险）"""
        self.set("auto_check_enabled", False)
        self.set("check_on_startup", False)
    
    def enable_manual_only(self):
        """仅启用手动检查"""
        self.set("auto_check_enabled", False)
        self.set("check_on_startup", False)
        self.set("download_method", "manual")
        self.set("notification_enabled", False)
    
    def reset_to_safe_defaults(self):
        """重置为安全的默认配置"""
        safe_config = {
            "auto_check_enabled": False,
            "check_frequency_days": 30,
            "check_on_startup": False,
            "use_proxy": False,
            "timeout_seconds": 5,
            "download_method": "manual",
            "notification_enabled": False
        }
        self.config.update(safe_config)
        self.save_config()


# 使用示例
if __name__ == "__main__":
    config = UpdateConfig()
    
    # 查看当前配置
    print("当前配置:")
    for key, value in config.config.items():
        print(f"  {key}: {value}")
    
    # 设置为安全模式
    print("\n设置为安全模式...")
    config.reset_to_safe_defaults()
    
    print("\n安全模式配置:")
    for key, value in config.config.items():
        print(f"  {key}: {value}")
