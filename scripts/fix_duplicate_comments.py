#!/usr/bin/env python3
"""
修复QSS文件中的重复注释问题
"""

import re
import os
import sys

def fix_duplicate_comments():
    # 获取脚本所在目录的父目录路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    qss_file = os.path.join(parent_dir, "styles", "fish.qss")
    
    # 读取文件内容
    with open(qss_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 创建备份
    with open(f"{qss_file}.fix_backup", 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("正在修复重复注释...")
    
    # 修复重复的字体族注释
    content = re.sub(r'/\* UI_FONT_FAMILY \*/ /\* UI_FONT_FAMILY \*/', '/* UI_FONT_FAMILY */', content)
    content = re.sub(r'/\* CODE_FONT_FAMILY \*/ /\* CODE_FONT_FAMILY \*/', '/* CODE_FONT_FAMILY */', content)
    
    # 修复重复的字体大小注释
    size_patterns = [
        'UI_FONT_SIZE_SMALL',
        'UI_FONT_SIZE_NORMAL', 
        'UI_FONT_SIZE_MEDIUM',
        'UI_FONT_SIZE_LARGE',
        'UI_FONT_SIZE_XL',
        'UI_FONT_SIZE_XXL',
        'UI_FONT_SIZE_XXXL',
        'UI_FONT_SIZE_HUGE',
        'UI_FONT_SIZE_MEGA'
    ]
    
    for pattern in size_patterns:
        content = re.sub(rf'/\* {pattern} \*/ /\* {pattern} \*/', f'/* {pattern} */', content)
    
    # 写回文件
    with open(qss_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 已修复重复注释，备份保存为: {qss_file}.fix_backup")

if __name__ == "__main__":
    fix_duplicate_comments()
