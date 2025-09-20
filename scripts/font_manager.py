#!/usr/bin/env python3
"""
字体管理工具
用于统一修改QSS文件中的字体设置
"""

import re
import os
import argparse
import sys

# 确保可以访问父目录的文件
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class FontManager:
    def __init__(self, qss_file="../styles/fish.qss"):
        # 获取脚本所在目录的父目录路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)
        self.qss_file = os.path.join(parent_dir, "styles", "fish.qss")
        self.backup_file = f"{self.qss_file}.backup"
        
    def backup_if_needed(self):
        """创建备份文件（如果不存在）"""
        if not os.path.exists(self.backup_file):
            with open(self.qss_file, 'r', encoding='utf-8') as f:
                content = f.read()
            with open(self.backup_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 已创建备份: {self.backup_file}")
    
    def read_content(self):
        """读取QSS文件内容"""
        with open(self.qss_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    def write_content(self, content):
        """写入QSS文件内容"""
        with open(self.qss_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def change_ui_font_family(self, new_font_family):
        """修改UI字体族"""
        self.backup_if_needed()
        content = self.read_content()
        
        # 修改顶部定义注释
        pattern = r'UI_FONT_FAMILY: "[^"]*"[^,]*'
        replacement = f'UI_FONT_FAMILY: {new_font_family}'
        content = re.sub(pattern, replacement, content)
        
        # 修改所有UI_FONT_FAMILY引用
        pattern = r'font-family: "[^"]*"[^;]*; /\* UI_FONT_FAMILY \*/'
        replacement = f'font-family: {new_font_family}; /* UI_FONT_FAMILY */'
        content = re.sub(pattern, replacement, content)
        
        self.write_content(content)
        print(f"✅ 已将UI字体族更改为: {new_font_family}")
    
    def change_code_font_family(self, new_font_family):
        """修改代码字体族"""
        self.backup_if_needed()
        content = self.read_content()
        
        # 修改顶部定义注释
        pattern = r'CODE_FONT_FAMILY: "[^"]*"[^,]*'
        replacement = f'CODE_FONT_FAMILY: {new_font_family}'
        content = re.sub(pattern, replacement, content)
        
        # 修改所有CODE_FONT_FAMILY引用
        pattern = r'font-family: "[^"]*"[^;]*; /\* CODE_FONT_FAMILY \*/'
        replacement = f'font-family: {new_font_family}; /* CODE_FONT_FAMILY */'
        content = re.sub(pattern, replacement, content)
        
        self.write_content(content)
        print(f"✅ 已将代码字体族更改为: {new_font_family}")
    
    def change_font_size(self, size_level, new_size):
        """修改指定级别的字体大小"""
        self.backup_if_needed()
        content = self.read_content()
        
        size_levels = {
            'small': 'UI_FONT_SIZE_SMALL',
            'small+': 'UI_FONT_SIZE_SMALL+',
            'normal': 'UI_FONT_SIZE_NORMAL', 
            'medium': 'UI_FONT_SIZE_MEDIUM',
            'large': 'UI_FONT_SIZE_LARGE',
            'xl': 'UI_FONT_SIZE_XL',
            'xxl': 'UI_FONT_SIZE_XXL',
            'xxxl': 'UI_FONT_SIZE_XXXL',
            'huge': 'UI_FONT_SIZE_HUGE',
            'mega': 'UI_FONT_SIZE_MEGA'
        }
        
        if size_level not in size_levels:
            print(f"❌ 无效的字体大小级别: {size_level}")
            print(f"   有效级别: {', '.join(size_levels.keys())}")
            return
        
        level_name = size_levels[size_level]
        
        # 修改顶部定义注释
        pattern = rf'{level_name}: \d+px'
        replacement = f'{level_name}: {new_size}px'
        content = re.sub(pattern, replacement, content)
        
        # 修改所有对应的引用
        pattern = rf'font-size: \d+px; /\* {level_name} \*/'
        replacement = f'font-size: {new_size}px; /* {level_name} */'
        content = re.sub(pattern, replacement, content)
        
        self.write_content(content)
        print(f"✅ 已将 {level_name} 更改为: {new_size}px")
    
    def global_font_scale(self, scale_factor):
        """全局缩放所有字体大小"""
        self.backup_if_needed()
        content = self.read_content()
        
        # 查找所有字体大小并计算新值
        def scale_size(match):
            old_size = int(match.group(1))
            new_size = max(8, int(old_size * scale_factor))  # 最小8px
            return f"font-size: {new_size}px; {match.group(2)}"
        
        # 替换所有带注释的字体大小
        pattern = r'font-size: (\d+)px; (/\* UI_FONT_SIZE_[^*]*\*/)'
        content = re.sub(pattern, scale_size, content)
        
        # 同时更新顶部定义
        def scale_definition(match):
            old_size = int(match.group(2))
            new_size = max(8, int(old_size * scale_factor))
            return f"{match.group(1)}: {new_size}px"
        
        pattern = r'(UI_FONT_SIZE_[^:]+): (\d+)px'
        content = re.sub(pattern, scale_definition, content)
        
        self.write_content(content)
        print(f"✅ 已将所有字体大小缩放 {scale_factor}x")
    
    def show_current_fonts(self):
        """显示当前字体设置"""
        content = self.read_content()
        
        print("📋 当前字体设置:")
        print()
        
        # 查找字体族定义
        ui_font = re.search(r'UI_FONT_FAMILY: ([^\n]+)', content)
        code_font = re.search(r'CODE_FONT_FAMILY: ([^\n]+)', content)
        
        if ui_font:
            print(f"🖥️  UI字体族: {ui_font.group(1)}")
        if code_font:
            print(f"💻 代码字体族: {code_font.group(1)}")
        
        print()
        print("📏 字体大小设置:")
        
        # 查找字体大小定义
        size_patterns = [
            (r'UI_FONT_SIZE_SMALL: (\d+)px', '🔸 小字体'),
            (r'UI_FONT_SIZE_SMALL\+: (\d+)px', '🔸 小字体+'),
            (r'UI_FONT_SIZE_NORMAL: (\d+)px', '🔹 标准字体'),
            (r'UI_FONT_SIZE_MEDIUM: (\d+)px', '🔷 中等字体'),
            (r'UI_FONT_SIZE_LARGE: (\d+)px', '🔶 大字体'),
            (r'UI_FONT_SIZE_XL: (\d+)px', '🟠 特大字体'),
            (r'UI_FONT_SIZE_XXL: (\d+)px', '🟡 超大字体'),
            (r'UI_FONT_SIZE_XXXL: (\d+)px', '🟢 极大字体'),
            (r'UI_FONT_SIZE_HUGE: (\d+)px', '🔵 巨大字体'),
            (r'UI_FONT_SIZE_MEGA: (\d+)px', '🟣 超巨大字体'),
        ]
        
        for pattern, name in size_patterns:
            match = re.search(pattern, content)
            if match:
                print(f"   {name}: {match.group(1)}px")

def main():
    parser = argparse.ArgumentParser(description='QSS字体管理工具')
    parser.add_argument('--show', action='store_true', help='显示当前字体设置')
    parser.add_argument('--ui-font', type=str, help='修改UI字体族')
    parser.add_argument('--code-font', type=str, help='修改代码字体族') 
    parser.add_argument('--size', type=str, help='修改字体大小级别')
    parser.add_argument('--value', type=int, help='新的字体大小值')
    parser.add_argument('--scale', type=float, help='全局字体缩放比例')
    
    args = parser.parse_args()
    
    fm = FontManager()
    
    if args.show:
        fm.show_current_fonts()
    elif args.ui_font:
        fm.change_ui_font_family(args.ui_font)
    elif args.code_font:
        fm.change_code_font_family(args.code_font)
    elif args.size and args.value:
        fm.change_font_size(args.size, args.value)
    elif args.scale:
        fm.global_font_scale(args.scale)
    else:
        print("🔧 QSS字体管理工具")
        print()
        print("使用示例:")
        print("  python Scripts/font_manager.py --show                    # 显示当前字体设置")
        print("  python Scripts/font_manager.py --ui-font '\"Arial\", sans-serif'  # 修改UI字体")
        print("  python Scripts/font_manager.py --code-font '\"Monaco\", monospace' # 修改代码字体")
        print("  python Scripts/font_manager.py --size normal --value 14  # 修改标准字体大小为14px")
        print("  python Scripts/font_manager.py --scale 1.2               # 所有字体放大1.2倍")
        print()
        print("字体大小级别: small, small+, normal, medium, large, xl, xxl, xxxl, huge, mega")

if __name__ == "__main__":
    main()
