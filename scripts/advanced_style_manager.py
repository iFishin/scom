#!/usr/bin/env python3
"""
增强版样式管理工具
支持批量管理QSS样式，包括字体、颜色、大小等
"""

import re
import os
import json
import argparse
from datetime import datetime

class AdvancedStyleManager:
    def __init__(self, qss_file="../styles/fish.qss"):
        # 获取脚本所在目录的父目录路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)
        self.qss_file = os.path.join(parent_dir, "styles", "fish.qss")
        self.backup_dir = os.path.join(parent_dir, "styles", "backups")
        self.config_file = os.path.join(parent_dir, "styles", "style_config.json")
        
        # 确保备份目录存在
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # 样式配置模板
        self.default_config = {
            "fonts": {
                "ui_family": '"Microsoft YaHei", "SimSun", "Segoe UI", "Roboto", sans-serif',
                "code_family": '"JetBrains Mono", "Consolas", "Courier New", monospace',
                "mixed_family": '"Consolas", "Microsoft YaHei", "Courier New", monospace',
                "sizes": {
                    "small": 11,
                    "small+": 12,
                    "normal": 13,
                    "medium": 14,
                    "large": 15,
                    "xl": 16,
                    "xxl": 18,
                    "xxxl": 20,
                    "huge": 24,
                    "mega": 28
                }
            },
            "colors": {
                "primary": "#00a86b",
                "secondary": "#6c757d", 
                "success": "#28a745",
                "danger": "#dc3545",
                "warning": "#ffc107",
                "info": "#17a2b8",
                "light": "#f8f9fa",
                "dark": "#343a40",
                "blue": "#007bff"
            },
            "spacing": {
                "small": "3px",
                "normal": "6px",
                "medium": "12px",
                "large": "20px"
            },
            "border_radius": {
                "small": "4px",
                "normal": "6px",
                "medium": "8px",
                "large": "12px"
            }
        }
    
    def create_backup(self, reason="manual"):
        """创建备份文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{self.backup_dir}/fish_{timestamp}_{reason}.qss"
        
        with open(self.qss_file, 'r', encoding='utf-8') as f:
            content = f.read()
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 已创建备份: {backup_file}")
        return backup_file
    
    def load_config(self):
        """加载样式配置"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            self.save_config(self.default_config)
            return self.default_config.copy()
    
    def save_config(self, config):
        """保存样式配置"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def read_qss(self):
        """读取QSS文件"""
        with open(self.qss_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    def write_qss(self, content):
        """写入QSS文件"""
        with open(self.qss_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def apply_font_changes(self, config):
        """应用字体更改"""
        self.create_backup("font_change")
        content = self.read_qss()
        
        # 更新UI字体族
        ui_font = config['fonts']['ui_family']
        content = re.sub(
            r'font-family: "[^"]*"[^;]*; /\* UI_FONT_FAMILY \*/',
            f'font-family: {ui_font}; /* UI_FONT_FAMILY */',
            content
        )
        
        # 更新代码字体族
        code_font = config['fonts']['code_family']
        content = re.sub(
            r'font-family: "[^"]*"[^;]*; /\* CODE_FONT_FAMILY \*/',
            f'font-family: {code_font}; /* CODE_FONT_FAMILY */',
            content
        )
        
        # 更新混合字体族 (如果有使用的话)
        mixed_font = config['fonts']['mixed_family']
        content = re.sub(
            r'font-family: "[^"]*"[^;]*; /\* MIXED_FONT_FAMILY \*/',
            f'font-family: {mixed_font}; /* MIXED_FONT_FAMILY */',
            content
        )
        
        # 更新字体大小
        size_map = {
            'small': 'UI_FONT_SIZE_SMALL',
            'small+': 'UI_FONT_SIZE_SMALL\\+',
            'normal': 'UI_FONT_SIZE_NORMAL',
            'medium': 'UI_FONT_SIZE_MEDIUM',
            'large': 'UI_FONT_SIZE_LARGE',
            'xl': 'UI_FONT_SIZE_XL',
            'xxl': 'UI_FONT_SIZE_XXL',
            'xxxl': 'UI_FONT_SIZE_XXXL',
            'huge': 'UI_FONT_SIZE_HUGE',
            'mega': 'UI_FONT_SIZE_MEGA'
        }
        
        for size_key, size_value in config['fonts']['sizes'].items():
            if size_key in size_map:
                pattern = rf'font-size: \d+px; /\* {size_map[size_key]} \*/'
                size_comment = size_map[size_key].replace("\\\\", "\\")
                replacement = f'font-size: {size_value}px; /* {size_comment} */'
                content = re.sub(pattern, replacement, content)
        
        # 更新注释中的定义
        header_pattern = r'(=== 字体系统统一定义 ===.*?)(\*/)'
        def update_header(match):
            header_content = f"""=== 字体系统统一定义 ===
UI_FONT_FAMILY: {ui_font}
CODE_FONT_FAMILY: {code_font}
MIXED_FONT_FAMILY: {mixed_font} (仅用于注释参考)

UI_FONT_SIZE_SMALL: {config['fonts']['sizes']['small']}px
UI_FONT_SIZE_SMALL+: {config['fonts']['sizes']['small+']}px
UI_FONT_SIZE_NORMAL: {config['fonts']['sizes']['normal']}px
UI_FONT_SIZE_MEDIUM: {config['fonts']['sizes']['medium']}px
UI_FONT_SIZE_LARGE: {config['fonts']['sizes']['large']}px
UI_FONT_SIZE_XL: {config['fonts']['sizes']['xl']}px
UI_FONT_SIZE_XXL: {config['fonts']['sizes']['xxl']}px
UI_FONT_SIZE_XXXL: {config['fonts']['sizes']['xxxl']}px
UI_FONT_SIZE_HUGE: {config['fonts']['sizes']['huge']}px
UI_FONT_SIZE_MEGA: {config['fonts']['sizes']['mega']}px

注意：QSS不支持变量定义，MIXED_FONT_FAMILY仅用于注释参考
修改字体时，请统一修改上述定义对应的所有引用处"""
            return header_content + "\n*/"
        
        content = re.sub(header_pattern, update_header, content, flags=re.DOTALL)
        
        self.write_qss(content)
        print("✅ 字体样式已更新")
    
    def apply_color_changes(self, config):
        """应用颜色更改"""
        self.create_backup("color_change")
        content = self.read_qss()
        
        # 定义颜色替换映射
        color_replacements = {
            config['colors']['primary']: ['#00a86b'],
            config['colors']['danger']: ['#dc3545'],
            config['colors']['warning']: ['#ffc107'],
            config['colors']['info']: ['#17a2b8'],
            config['colors']['success']: ['#28a745'],
            config['colors']['blue']: ['#007bff'],
            config['colors']['secondary']: ['#6c757d'],
            config['colors']['light']: ['#f8f9fa'],
            config['colors']['dark']: ['#343a40']
        }
        
        # 批量替换颜色
        for new_color, old_colors in color_replacements.items():
            for old_color in old_colors:
                content = content.replace(old_color, new_color)
        
        self.write_qss(content)
        print("✅ 颜色样式已更新")
    
    def apply_spacing_changes(self, config):
        """应用间距更改"""
        self.create_backup("spacing_change")
        content = self.read_qss()
        
        # 这里可以添加间距的批量替换逻辑
        # 由于间距涉及很多具体的像素值，需要更精确的替换策略
        
        print("✅ 间距样式已更新")
    
    def create_theme_preset(self, theme_name, config):
        """创建主题预设"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)
        preset_file = os.path.join(parent_dir, "styles", "themes", f"{theme_name}.json")
        themes_dir = os.path.join(parent_dir, "styles", "themes")
        os.makedirs(themes_dir, exist_ok=True)
        
        with open(preset_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 主题预设已保存: {preset_file}")
    
    def apply_theme_preset(self, theme_name):
        """应用主题预设"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)
        preset_file = os.path.join(parent_dir, "styles", "themes", f"{theme_name}.json")
        
        if not os.path.exists(preset_file):
            print(f"❌ 主题预设不存在: {preset_file}")
            return
        
        with open(preset_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        self.create_backup(f"theme_{theme_name}")
        self.apply_font_changes(config)
        self.apply_color_changes(config)
        self.save_config(config)
        
        print(f"✅ 已应用主题: {theme_name}")
    
    def bulk_find_replace(self, find_text, replace_text, regex=False):
        """批量查找替换"""
        self.create_backup("bulk_replace")
        content = self.read_qss()
        
        if regex:
            content = re.sub(find_text, replace_text, content)
        else:
            content = content.replace(find_text, replace_text)
        
        self.write_qss(content)
        print(f"✅ 批量替换完成: '{find_text}' -> '{replace_text}'")
    
    def show_current_config(self):
        """显示当前配置"""
        config = self.load_config()
        
        print("🎨 当前样式配置:")
        print()
        print("📝 字体设置:")
        print(f"   UI字体族: {config['fonts']['ui_family']}")
        print(f"   代码字体族: {config['fonts']['code_family']}")
        print(f"   混合字体族: {config['fonts']['mixed_family']}")
        print()
        print("📏 字体大小:")
        for size_name, size_value in config['fonts']['sizes'].items():
            print(f"   {size_name}: {size_value}px")
        print()
        print("🎯 颜色主题:")
        for color_name, color_value in config['colors'].items():
            print(f"   {color_name}: {color_value}")
    
    def interactive_editor(self):
        """交互式编辑器"""
        config = self.load_config()
        
        while True:
            print("\n🔧 样式管理器 - 交互模式")
            print("1. 修改字体族")
            print("2. 修改字体大小")
            print("3. 修改颜色主题")
            print("4. 查看当前配置")
            print("5. 应用更改")
            print("6. 保存为主题预设")
            print("7. 加载主题预设")
            print("8. 退出")
            
            choice = input("\n请选择操作 (1-8): ").strip()
            
            if choice == '1':
                print("\n当前字体族:")
                print(f"UI字体: {config['fonts']['ui_family']}")
                print(f"代码字体: {config['fonts']['code_family']}")
                font_type = input("修改哪种字体? (ui/code): ").strip().lower()
                if font_type in ['ui', 'code']:
                    new_font = input("输入新的字体族: ").strip()
                    if new_font:
                        config['fonts'][f'{font_type}_family'] = new_font
                        print(f"✅ {font_type}字体已更新")
            
            elif choice == '2':
                print("\n当前字体大小:")
                for size_name, size_value in config['fonts']['sizes'].items():
                    print(f"{size_name}: {size_value}px")
                size_name = input("修改哪个大小? ").strip()
                if size_name in config['fonts']['sizes']:
                    try:
                        new_size = int(input(f"输入{size_name}的新大小: "))
                        config['fonts']['sizes'][size_name] = new_size
                        print(f"✅ {size_name}大小已更新为{new_size}px")
                    except ValueError:
                        print("❌ 请输入有效数字")
            
            elif choice == '3':
                print("\n当前颜色:")
                for color_name, color_value in config['colors'].items():
                    print(f"{color_name}: {color_value}")
                color_name = input("修改哪个颜色? ").strip()
                if color_name in config['colors']:
                    new_color = input(f"输入{color_name}的新颜色值: ").strip()
                    if new_color:
                        config['colors'][color_name] = new_color
                        print(f"✅ {color_name}颜色已更新")
            
            elif choice == '4':
                self.show_current_config()
            
            elif choice == '5':
                self.apply_font_changes(config)
                self.apply_color_changes(config)
                self.save_config(config)
                print("✅ 所有更改已应用到QSS文件")
            
            elif choice == '6':
                theme_name = input("输入主题名称: ").strip()
                if theme_name:
                    self.create_theme_preset(theme_name, config)
            
            elif choice == '7':
                script_dir = os.path.dirname(os.path.abspath(__file__))
                parent_dir = os.path.dirname(script_dir)
                themes_dir = os.path.join(parent_dir, "styles", "themes")
                if os.path.exists(themes_dir):
                    themes = [f[:-5] for f in os.listdir(themes_dir) if f.endswith('.json')]
                    if themes:
                        print("\n可用主题:")
                        for i, theme in enumerate(themes, 1):
                            print(f"{i}. {theme}")
                        try:
                            choice_idx = int(input("选择主题序号: ")) - 1
                            if 0 <= choice_idx < len(themes):
                                self.apply_theme_preset(themes[choice_idx])
                                config = self.load_config()  # 重新加载配置
                        except ValueError:
                            print("❌ 请输入有效数字")
                    else:
                        print("❌ 没有找到主题预设")
                else:
                    print("❌ 主题目录不存在")
            
            elif choice == '8':
                print("👋 再见!")
                break
            
            else:
                print("❌ 无效选择，请重试")

def main():
    parser = argparse.ArgumentParser(description='增强版QSS样式管理工具')
    parser.add_argument('--show', action='store_true', help='显示当前配置')
    parser.add_argument('--interactive', action='store_true', help='启动交互模式')
    parser.add_argument('--theme', type=str, help='应用指定主题')
    parser.add_argument('--backup', action='store_true', help='创建备份')
    parser.add_argument('--find', type=str, help='查找文本')
    parser.add_argument('--replace', type=str, help='替换文本')
    parser.add_argument('--regex', action='store_true', help='使用正则表达式')
    
    args = parser.parse_args()
    
    manager = AdvancedStyleManager()
    
    if args.show:
        manager.show_current_config()
    elif args.interactive:
        manager.interactive_editor()
    elif args.theme:
        manager.apply_theme_preset(args.theme)
    elif args.backup:
        manager.create_backup("manual")
    elif args.find and args.replace:
        manager.bulk_find_replace(args.find, args.replace, args.regex)
    else:
        print("🎨 增强版样式管理工具")
        print()
        print("使用示例:")
        print("  python Scripts/advanced_style_manager.py --show              # 显示当前配置")
        print("  python Scripts/advanced_style_manager.py --interactive       # 交互模式")
        print("  python Scripts/advanced_style_manager.py --theme dark        # 应用暗色主题")
        print("  python Scripts/advanced_style_manager.py --backup            # 创建备份")
        print("  python Scripts/advanced_style_manager.py --find '#007bff' --replace '#ff6b6b'  # 批量替换")

if __name__ == "__main__":
    main()
