#!/usr/bin/env python3
"""
统一QSS文件中的字体定义
将所有分散的字体定义统一为标准化引用
"""

import re
import os
import sys

def unify_fonts():
    # 获取脚本所在目录的父目录路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    qss_file = os.path.join(parent_dir, "styles", "fish.qss")
    
    print(f"正在处理文件: {qss_file}")
    
    # 读取QSS文件
    with open(qss_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 创建备份
    backup_file = f"{qss_file}.backup"
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ 已创建备份: {backup_file}")
    
    # 定义标准字体
    ui_font_family = '"Microsoft YaHei", "SimSun", "Segoe UI", "Roboto", sans-serif'
    code_font_family = '"JetBrains Mono", "Consolas", "Courier New", monospace'
    
    # 字体族统一
    ui_font_patterns = [
        r'"Microsoft YaHei"[^;]*',
        r'"SimSun"[^;]*', 
        r'"Segoe UI"[^;]*',
        r'"Arial"[^;]*'
    ]
    
    code_font_patterns = [
        r'"JetBrains Mono"[^;]*',
        r'"Consolas"[^;]*',
        r'"Courier New"[^;]*',
        r'"Monaco"[^;]*'
    ]
    
    ui_font_count = 0
    code_font_count = 0
    
    # 统一UI字体
    for pattern in ui_font_patterns:
        matches = re.findall(pattern, content)
        if matches:
            ui_font_count += len(matches)
            content = re.sub(f'font-family: {pattern};', f'font-family: {ui_font_family}; /* UI_FONT_FAMILY */', content)
    
    # 统一代码字体
    for pattern in code_font_patterns:
        matches = re.findall(pattern, content)
        if matches:
            code_font_count += len(matches)
            content = re.sub(f'font-family: {pattern};', f'font-family: {code_font_family}; /* CODE_FONT_FAMILY */', content)
    
    # 字体大小统一
    size_map = {
        '11': 'UI_FONT_SIZE_SMALL',
        '12': 'UI_FONT_SIZE_SMALL+', 
        '13': 'UI_FONT_SIZE_NORMAL',
        '14': 'UI_FONT_SIZE_MEDIUM',
        '15': 'UI_FONT_SIZE_LARGE',
        '16': 'UI_FONT_SIZE_XL',
        '18': 'UI_FONT_SIZE_XXL',
        '20': 'UI_FONT_SIZE_XXXL',
        '24': 'UI_FONT_SIZE_HUGE',
        '28': 'UI_FONT_SIZE_MEGA'
    }
    
    size_count = 0
    for size, label in size_map.items():
        pattern = f'font-size: {size}px;'
        matches = content.count(pattern)
        if matches > 0:
            size_count += matches
            content = content.replace(pattern, f'font-size: {size}px; /* {label} */')
    
    # 写回文件
    with open(qss_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 字体统一完成:")
    print(f"   - UI字体引用: {ui_font_count}个")
    print(f"   - 代码字体引用: {code_font_count}个") 
    print(f"   - 字体大小注释: {size_count}个")

if __name__ == "__main__":
    unify_fonts()
