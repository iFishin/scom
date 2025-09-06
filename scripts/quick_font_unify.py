#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化的字体统一脚本
用于快速统一QSS文件中的字体设置
"""

import os
import sys
import shutil
import re


def quick_font_unify(qss_path="styles/fish.qss"):
    """快速字体统一"""
    if not os.path.exists(qss_path):
        print(f"❌ QSS文件不存在: {qss_path}")
        return False
    
    # 创建备份
    backup_path = f"{qss_path}.backup_{int(__import__('time').time())}"
    try:
        shutil.copy2(qss_path, backup_path)
        print(f"✅ 备份创建: {backup_path}")
    except Exception as e:
        print(f"❌ 备份创建失败: {e}")
        return False
    
    try:
        with open(qss_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 字体统一规则
        rules = [
            # 1. 统一混合字体为UI字体
            (
                r'font-family:\s*"Consolas",\s*"Microsoft YaHei"[^;]*;',
                'font-family: "Microsoft YaHei", "SimSun", "Segoe UI", "Roboto", sans-serif; /* UI_FONT_FAMILY */'
            ),
            
            # 2. 确保代码字体注释
            (
                r'(font-family:\s*"JetBrains Mono"[^;]*;)(?!\s*/\*)',
                r'\1 /* CODE_FONT_FAMILY */'
            ),
            
            # 3. 确保UI字体注释
            (
                r'(font-family:\s*"Microsoft YaHei"[^;]*;)(?!\s*/\*)',
                r'\1 /* UI_FONT_FAMILY */'
            ),
            
            # 4. 标准化常用字体大小并添加注释
            (r'font-size:\s*11px;(?!\s*/\*)', 'font-size: 11px; /* UI_FONT_SIZE_SMALL */'),
            (r'font-size:\s*13px;(?!\s*/\*)', 'font-size: 13px; /* UI_FONT_SIZE_NORMAL */'),
            (r'font-size:\s*14px;(?!\s*/\*)', 'font-size: 14px; /* UI_FONT_SIZE_MEDIUM */'),
            (r'font-size:\s*15px;(?!\s*/\*)', 'font-size: 15px; /* UI_FONT_SIZE_LARGE */'),
            (r'font-size:\s*16px;(?!\s*/\*)', 'font-size: 16px; /* UI_FONT_SIZE_XL */'),
            (r'font-size:\s*18px;(?!\s*/\*)', 'font-size: 18px; /* UI_FONT_SIZE_XXL */'),
            (r'font-size:\s*20px;(?!\s*/\*)', 'font-size: 20px; /* UI_FONT_SIZE_XXXL */'),
            (r'font-size:\s*24px;(?!\s*/\*)', 'font-size: 24px; /* UI_FONT_SIZE_HUGE */'),
            (r'font-size:\s*28px;(?!\s*/\*)', 'font-size: 28px; /* UI_FONT_SIZE_MEGA */'),
        ]
        
        changes = 0
        for pattern, replacement in rules:
            matches = len(re.findall(pattern, content))
            if matches > 0:
                content = re.sub(pattern, replacement, content)
                changes += matches
                print(f"✅ 应用规则: {matches} 处更改")
        
        # 保存文件
        with open(qss_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"🎉 字体统一完成! 总共 {changes} 处更改")
        return True
        
    except Exception as e:
        print(f"❌ 字体统一失败: {e}")
        # 恢复备份
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, qss_path)
            print("🔄 已从备份恢复")
        return False


def check_font_consistency(qss_path="styles/fish.qss"):
    """检查字体一致性"""
    if not os.path.exists(qss_path):
        print(f"❌ QSS文件不存在: {qss_path}")
        return
    
    try:
        with open(qss_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 统计字体使用
        font_families = re.findall(r'font-family:\s*([^;]+);', content)
        font_sizes = re.findall(r'font-size:\s*([^;]+);', content)
        
        ui_fonts = [f for f in font_families if 'Microsoft YaHei' in f and 'Consolas' not in f]
        code_fonts = [f for f in font_families if 'Consolas' in f or 'JetBrains Mono' in f]
        mixed_fonts = [f for f in font_families if 'Consolas' in f and 'Microsoft YaHei' in f]
        
        print("📊 字体使用统计")
        print("=" * 30)
        print(f"🎨 UI字体定义: {len(ui_fonts)} 处")
        print(f"💻 代码字体定义: {len(code_fonts)} 处")
        print(f"⚠️  混合字体定义: {len(mixed_fonts)} 处")
        print(f"📏 字体大小种类: {len(set(font_sizes))} 种")
        
        if mixed_fonts:
            print(f"\n⚠️  发现 {len(mixed_fonts)} 处混合字体，建议统一!")
            return False
        else:
            print("\n✅ 字体定义一致!")
            return True
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False


def main():
    """主函数"""
    print("🎨 字体统一工具")
    print("=" * 20)
    
    # 检查当前状态
    if check_font_consistency():
        print("\n字体已经统一，无需处理!")
    else:
        print("\n开始字体统一...")
        if quick_font_unify():
            print("\n重新检查...")
            check_font_consistency()


if __name__ == "__main__":
    main()
