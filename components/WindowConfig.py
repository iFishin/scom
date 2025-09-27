"""Window / UI layout configuration centralized component.

把所有窗口级别的默认值、尺寸和布局相关的参数集中管理，方便在不同模块间传递。
"""
from typing import Tuple

class WindowConfig:
    """集中管理窗口与布局相关的配置。

    初始化时可以传入一个 configparser.ConfigParser 对象（可选），从中读取用户配置并覆盖默认值。
    """
    def __init__(self, config=None):
        self.config = config

        # 默认主窗口大小
        self.default_width = int(self._get_config('UI', 'DefaultWidth', 1000))
        self.default_height = int(self._get_config('UI', 'DefaultHeight', 900))

        # Radio area 折叠时的最大宽度（像素）
        self.radio_collapsed_max_width = int(self._get_config('UI', 'RadioCollapsedMaxWidth', 100))

        # Radio area 展开时占窗口宽度的分母值（window_width // radio_expanded_divisor）
        self.radio_expanded_divisor = int(self._get_config('UI', 'RadioExpandedDivisor', 3))

        # 更多设置面板的推荐高度
        self.settings_more_widget_height = int(self._get_config('UI', 'SettingsMoreHeight', 240))

        # 默认路径槽位数量（与 Window 中的实现保持一致）
        self.default_path_slots = int(self._get_config('Paths', 'DefaultSlots', 16))

    def _get_config(self, section: str, option: str, default):
        try:
            if self.config and section in self.config and option in self.config[section]:
                return self.config[section][option]
        except Exception:
            pass
        return default

    def radio_expanded_width(self, parent_width: int) -> int:
        """根据父窗口宽度计算展开时 radio 区域的最大宽度。"""
        try:
            return max(200, parent_width // max(1, self.radio_expanded_divisor))
        except Exception:
            return parent_width // 3

    def as_dict(self) -> dict:
        return {
            'default_width': self.default_width,
            'default_height': self.default_height,
            'radio_collapsed_max_width': self.radio_collapsed_max_width,
            'radio_expanded_divisor': self.radio_expanded_divisor,
            'settings_more_widget_height': self.settings_more_widget_height,
            'default_path_slots': self.default_path_slots,
        }
