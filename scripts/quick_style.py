#!/usr/bin/env python3
"""
快速样式管理工具
提供常用的样式批量管理功能
"""

import re
import os
import argparse
from datetime import datetime

class QuickStyleManager:
    def __init__(self, qss_file="../styles/fish.qss"):
        # 获取脚本所在目录的父目录路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)
        self.qss_file = os.path.join(parent_dir, "styles", "fish.qss")
        
    def backup(self):
        """创建备份"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"styles/fish_{timestamp}.qss.backup"
        
        with open(self.qss_file, 'r', encoding='utf-8') as f:
            content = f.read()
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Backup created: {backup_file}")
        return backup_file
    
    def change_primary_color(self, new_color):
        """批量更改主要颜色"""
        self.backup()
        
        with open(self.qss_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换所有主要颜色引用
        old_colors = ['#00a86b', '#008c5a', '#006f4a']
        
        for old_color in old_colors:
            content = content.replace(old_color, new_color)
        
        with open(self.qss_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Primary color changed to: {new_color}")
    
    def change_ui_font(self, new_font):
        """批量更改UI字体"""
        self.backup()
        
        with open(self.qss_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换所有UI字体引用
        pattern = r'font-family: "[^"]*"[^;]*; /\* UI_FONT_FAMILY \*/'
        replacement = f'font-family: {new_font}; /* UI_FONT_FAMILY */'
        content = re.sub(pattern, replacement, content)
        
        with open(self.qss_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"UI font changed to: {new_font}")
    
    def change_code_font(self, new_font):
        """批量更改代码字体"""
        self.backup()
        
        with open(self.qss_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换所有代码字体引用
        pattern = r'font-family: "[^"]*"[^;]*; /\* CODE_FONT_FAMILY \*/'
        replacement = f'font-family: {new_font}; /* CODE_FONT_FAMILY */'
        content = re.sub(pattern, replacement, content)
        
        with open(self.qss_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Code font changed to: {new_font}")
    
    def scale_all_fonts(self, scale_factor):
        """按比例缩放所有字体大小"""
        self.backup()
        
        with open(self.qss_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找并替换所有字体大小
        def scale_size(match):
            old_size = int(match.group(1))
            new_size = max(8, int(old_size * scale_factor))
            return f"font-size: {new_size}px; {match.group(2)}"
        
        pattern = r'font-size: (\d+)px; (/\* UI_FONT_SIZE_[^*]*\*/)'
        content = re.sub(pattern, scale_size, content)
        
        with open(self.qss_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"All fonts scaled {scale_factor}x")
    
    def find_replace(self, find_text, replace_text, regex=False):
        """查找替换"""
        self.backup()
        
        with open(self.qss_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if regex:
            content = re.sub(find_text, replace_text, content)
        else:
            content = content.replace(find_text, replace_text)
        
        with open(self.qss_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Replacement completed: '{find_text}' -> '{replace_text}'")
    
    def apply_dark_theme(self, create_backup=True):
        """应用暗色主题"""
        if create_backup:
            self.backup()
        
        with open(self.qss_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("Applying dark theme...")
        
        # 更全面的暗色主题颜色映射
        color_map = {
            # 主要背景色
            '#f8f9fa': '#2c3e50',  # 主背景 light -> dark blue
            'background-color: white;': 'background-color: #34495e;',  # 输入框等白色背景
            '#ffffff': '#34495e',   # 其他白色引用
            
            # 边框和分割线
            '#e9ecef': '#4a5568',   # 浅灰边框 -> 中灰
            '#dee2e6': '#718096',   # 边框灰 -> 更亮的灰
            '#ced4da': '#a0aec0',   # 输入框边框
            
            # 文字颜色 (深色背景需要浅色文字)
            '#495057': '#e2e8f0',   # 深色文字 -> 浅色文字
            '#333333': '#f7fafc',   # 很深的文字 -> 很浅的文字
            '#212529': '#f7fafc',   # 最深的文字 -> 最浅的文字
            '#343a40': '#e2e8f0',   # 深灰文字 -> 浅灰文字
            
            # 悬停和焦点状态
            '#80bdff': '#4299e1',   # 蓝色焦点边框 (稍微调暗)
            '#e3f2fd': '#2d3748',   # 悬停背景 (蓝色) -> 深灰
            
            # 禁用状态
            '#adb5bd': '#718096',   # 禁用文字颜色
            
            # 保持主题色不变 (绿色主题)
            # '#00a86b': '#00a86b',  # 主题绿色保持
            # '#007bff': '#007bff',  # 主题蓝色保持
        }
        
        # 批量替换颜色
        for old_color, new_color in color_map.items():
            if old_color.startswith('background-color:'):
                # 特殊处理background-color属性
                content = content.replace(old_color, new_color)
            else:
                # 普通颜色替换
                content = content.replace(old_color, new_color)
        
        # 特殊处理：确保选择背景色在暗色主题下可见
        content = content.replace('selection-background-color: #007bff;', 'selection-background-color: #4299e1;')
        
        with open(self.qss_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("Dark theme applied successfully")
        if create_backup:
            print("Tip: If some elements still show as light, please restart the application")
    
    def apply_light_theme(self, create_backup=True):
        """应用亮色主题（恢复默认）"""
        if create_backup:
            self.backup()
        
        with open(self.qss_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("Applying light theme...")
        
        # 亮色主题颜色映射（暗色的完全逆向）
        color_map = {
            # 恢复主要背景色
            '#2c3e50': '#f8f9fa',
            'background-color: #34495e;': 'background-color: white;',
            '#34495e': '#ffffff',
            
            # 恢复边框和分割线
            '#4a5568': '#e9ecef',
            '#718096': '#dee2e6',
            '#a0aec0': '#ced4da',
            
            # 恢复文字颜色
            '#e2e8f0': '#495057',
            '#f7fafc': '#333333',
            
            # 恢复悬停和焦点状态
            '#4299e1': '#80bdff',
            '#2d3748': '#e3f2fd',
            
            # 恢复禁用状态
            '#718096': '#adb5bd',  # 这个需要特殊处理，因为上面也用了
        }
        
        # 批量替换颜色
        for old_color, new_color in color_map.items():
            if old_color.startswith('background-color:'):
                content = content.replace(old_color, new_color)
            else:
                content = content.replace(old_color, new_color)
        
        # 恢复选择背景色
        content = content.replace('selection-background-color: #4299e1;', 'selection-background-color: #007bff;')
        
        # 特殊处理：解决 #718096 的冲突
        # 先把所有的 #718096 改回 #dee2e6，然后再处理禁用状态的特殊情况
        content = content.replace('#718096', '#dee2e6')
        # 禁用状态的文字颜色需要单独处理
        content = re.sub(r'color: #dee2e6;([^}]*disabled)', r'color: #adb5bd;\1', content)
        
        with open(self.qss_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("Light theme applied successfully")
        if create_backup:
            print("Tip: If some elements still show as dark, please restart the application")

def main():
    parser = argparse.ArgumentParser(description='快速样式管理工具')
    parser.add_argument('--primary-color', help='更改主要颜色')
    parser.add_argument('--ui-font', help='更改UI字体')
    parser.add_argument('--code-font', help='更改代码字体')
    parser.add_argument('--scale-fonts', type=float, help='缩放所有字体 (如: 1.2)')
    parser.add_argument('--find', help='查找文本')
    parser.add_argument('--replace', help='替换文本')
    parser.add_argument('--regex', action='store_true', help='使用正则表达式')
    parser.add_argument('--dark-theme', action='store_true', help='应用暗色主题')
    parser.add_argument('--light-theme', action='store_true', help='应用亮色主题')
    parser.add_argument('--backup', action='store_true', help='仅创建备份')
    
    args = parser.parse_args()
    
    manager = QuickStyleManager()
    
    if args.primary_color:
        manager.change_primary_color(args.primary_color)
    elif args.ui_font:
        manager.change_ui_font(args.ui_font)
    elif args.code_font:
        manager.change_code_font(args.code_font)
    elif args.scale_fonts:
        manager.scale_all_fonts(args.scale_fonts)
    elif args.find and args.replace:
        manager.find_replace(args.find, args.replace, args.regex)
    elif args.dark_theme:
        manager.apply_dark_theme()
    elif args.light_theme:
        manager.apply_light_theme()
    elif args.backup:
        manager.backup()
    else:
        print("🚀 快速样式管理工具")
        print()
        print("常用操作:")
        print("  python Scripts/quick_style.py --primary-color '#ff6b6b'     # 更改主要颜色为红色")
        print("  python Scripts/quick_style.py --ui-font '\"Arial\", sans-serif'  # 更改UI字体")
        print("  python Scripts/quick_style.py --code-font '\"Monaco\", monospace' # 更改代码字体")
        print("  python Scripts/quick_style.py --scale-fonts 1.2             # 所有字体放大20%")
        print("  python Scripts/quick_style.py --dark-theme                  # 应用暗色主题")
        print("  python Scripts/quick_style.py --light-theme                 # 应用亮色主题")
        print("  python Scripts/quick_style.py --backup                      # 创建备份")
        print()
        print("批量替换:")
        print("  python Scripts/quick_style.py --find '#007bff' --replace '#e74c3c'  # 替换颜色")
        print("  python Scripts/quick_style.py --find 'border-radius: \\d+px' --replace 'border-radius: 10px' --regex  # 正则替换")

if __name__ == "__main__":
    main()
