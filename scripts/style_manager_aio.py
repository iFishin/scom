#!/usr/bin/env python3
"""
SCOM 样式管理器 - All-in-One 版本
一个功能完整的QSS样式管理工具，支持：
- 样式优化和去重
- 字体统一管理
- 颜色主题切换
- 备份和恢复
- 批量查找替换
- 主题预设管理
- 交互式编辑
- 代码质量检查

作者：iFishin
版本：2.0.0
日期：2025-01-01
"""

import re
import os
import json
import argparse
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

class StyleOptimizer:
    """样式优化器 - 去除重复和冗余"""
    
    def __init__(self, content: str):
        self.content = content
        self.optimized_content = ""
        self.optimization_report = {}
    
    def remove_duplicate_rules(self) -> str:
        """去除重复的CSS规则"""
        # 提取所有CSS规则
        rules = {}
        rule_pattern = r'([^{]+)\s*{\s*([^}]+)\s*}'
        
        matches = re.findall(rule_pattern, self.content, re.MULTILINE | re.DOTALL)
        
        for selector, declarations in matches:
            selector = selector.strip()
            declarations = declarations.strip()
            
            # 如果选择器已存在，合并声明
            if selector in rules:
                existing_declarations = rules[selector]
                # 解析声明
                existing_props = self._parse_declarations(existing_declarations)
                new_props = self._parse_declarations(declarations)
                
                # 合并属性（新的覆盖旧的）
                existing_props.update(new_props)
                rules[selector] = self._format_declarations(existing_props)
            else:
                rules[selector] = declarations
        
        # 重建CSS
        optimized_rules = []
        for selector, declarations in rules.items():
            optimized_rules.append(f"{selector} {{\n    {declarations}\n}}")
        
        return "\n\n".join(optimized_rules)
    
    def _parse_declarations(self, declarations: str) -> Dict[str, str]:
        """解析CSS声明"""
        props = {}
        lines = declarations.split(';')
        for line in lines:
            line = line.strip()
            if ':' in line:
                prop, value = line.split(':', 1)
                props[prop.strip()] = value.strip()
        return props
    
    def _format_declarations(self, props: Dict[str, str]) -> str:
        """格式化CSS声明"""
        declarations = []
        for prop, value in props.items():
            declarations.append(f"{prop}: {value};")
        return "\n    ".join(declarations)
    
    def remove_empty_rules(self) -> str:
        """移除空规则"""
        # 移除空的CSS规则
        empty_rule_pattern = r'[^{]+{\s*}'
        content = re.sub(empty_rule_pattern, '', self.content, flags=re.MULTILINE)
        return content
    
    def optimize_comments(self) -> str:
        """优化注释"""
        # 保留重要注释，移除冗余注释
        content = self.content
        
        # 移除多余的空行
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        # 标准化注释格式
        content = re.sub(r'/\*\s*([^*]+)\s*\*/', r'/* \1 */', content)
        
        return content
    
    def optimize(self) -> Tuple[str, Dict[str, Any]]:
        """执行完整优化"""
        original_size = len(self.content)
        
        # 步骤1：移除空规则
        self.content = self.remove_empty_rules()
        
        # 步骤2：优化注释
        self.content = self.optimize_comments()
        
        # 步骤3：去除重复规则（注释：暂时跳过，因为可能破坏现有结构）
        # self.content = self.remove_duplicate_rules()
        
        optimized_size = len(self.content)
        compression_ratio = (original_size - optimized_size) / original_size * 100
        
        self.optimization_report = {
            "original_size": original_size,
            "optimized_size": optimized_size,
            "compression_ratio": compression_ratio,
            "lines_saved": self.content.count('\n') - self.content.count('\n')
        }
        
        return self.content, self.optimization_report

class AllInOneStyleManager:
    """All-in-One 样式管理器"""
    
    def __init__(self, qss_file: Optional[str] = None):
        # 路径设置
        if qss_file:
            self.qss_file = qss_file
        else:
            script_dir = Path(__file__).parent
            parent_dir = script_dir.parent
            self.qss_file = parent_dir / "styles" / "fish.qss"
        
        self.qss_file = Path(self.qss_file)
        self.styles_dir = self.qss_file.parent
        self.backup_dir = self.styles_dir / "backups"
        self.themes_dir = self.styles_dir / "themes"
        self.config_file = self.styles_dir / "style_config.json"
        
        # 确保目录存在
        self.backup_dir.mkdir(exist_ok=True)
        self.themes_dir.mkdir(exist_ok=True)
        
        # 样式配置模板
        self.default_config = {
            "version": "2.0.0",
            "meta": {
                "created": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat(),
                "author": "iFishin",
                "description": "SCOM 应用样式配置"
            },
            "fonts": {
                "ui_family": '"Consolas", "SimSun", "Segoe UI", "Roboto", sans-serif',
                "code_family": '"JetBrains Mono", "Consolas", "Courier New", monospace',
                "sizes": {
                    "small": 11,
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
                "dark": "#495057",
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
            },
            "presets": {
                "default": "默认绿色主题",
                "dark": "深色主题",
                "blue": "蓝色主题",
                "purple": "紫色主题"
            }
        }
    
    def create_backup(self, reason: str = "manual") -> Path:
        """创建备份文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 计算文件哈希值
        with open(self.qss_file, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()[:8]
        
        backup_file = self.backup_dir / f"fish_{timestamp}_{reason}_{file_hash}.qss"
        
        shutil.copy2(self.qss_file, backup_file)
        
        # 创建备份元信息
        meta_file = backup_file.with_suffix('.json')
        meta_info = {
            "timestamp": timestamp,
            "reason": reason,
            "original_file": str(self.qss_file),
            "file_hash": file_hash,
            "size": backup_file.stat().st_size
        }
        
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(meta_info, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 已创建备份: {backup_file.name}")
        return backup_file
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份"""
        backups = []
        for backup_file in self.backup_dir.glob("*.qss"):
            meta_file = backup_file.with_suffix('.json')
            if meta_file.exists():
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta_info = json.load(f)
                meta_info['file'] = backup_file
                backups.append(meta_info)
            else:
                # 没有元信息的旧备份
                stat = backup_file.stat()
                backups.append({
                    "timestamp": datetime.fromtimestamp(stat.st_mtime).strftime("%Y%m%d_%H%M%S"),
                    "reason": "unknown",
                    "file": backup_file,
                    "size": stat.st_size
                })
        
        # 按时间排序
        backups.sort(key=lambda x: x['timestamp'], reverse=True)
        return backups
    
    def restore_backup(self, backup_file: Path) -> None:
        """恢复备份"""
        if not backup_file.exists():
            raise FileNotFoundError(f"备份文件不存在: {backup_file}")
        
        # 创建当前文件的备份
        self.create_backup("before_restore")
        
        # 恢复备份
        shutil.copy2(backup_file, self.qss_file)
        print(f"✅ 已恢复备份: {backup_file.name}")
    
    def load_config(self) -> Dict[str, Any]:
        """加载样式配置"""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 合并默认配置（处理新增的配置项）
            def merge_config(default: Dict, current: Dict) -> Dict:
                for key, value in default.items():
                    if key not in current:
                        current[key] = value
                    elif isinstance(value, dict) and isinstance(current[key], dict):
                        current[key] = merge_config(value, current[key])
                return current
            
            return merge_config(self.default_config.copy(), config)
        else:
            self.save_config(self.default_config)
            return self.default_config.copy()
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """保存样式配置"""
        config["meta"]["last_modified"] = datetime.now().isoformat()
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def read_qss(self) -> str:
        """读取QSS文件"""
        with open(self.qss_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    def write_qss(self, content: str) -> None:
        """写入QSS文件"""
        with open(self.qss_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def apply_font_changes(self, config: Dict[str, Any]) -> None:
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
        
        # 更新字体大小
        size_map = {
            'small': 'UI_FONT_SIZE_SMALL',
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
                replacement = f'font-size: {size_value}px; /* {size_map[size_key]} */'
                content = re.sub(pattern, replacement, content)
        
        # 更新注释中的字体定义
        header_pattern = r'(=== 字体系统统一定义 ===.*?)(\*/)'
        def update_header(match):
            sizes_text = ""
            for size_key, size_value in config['fonts']['sizes'].items():
                size_constant = size_map.get(size_key, f'UI_FONT_SIZE_{size_key.upper()}')
                sizes_text += f"{size_constant}: {size_value}px\n"
            
            header_content = f"""=== 字体系统统一定义 ===
UI_FONT_FAMILY: {ui_font}
CODE_FONT_FAMILY: {code_font}

{sizes_text}
注意：QSS不支持变量定义，修改字体时请统一修改所有引用处"""
            return header_content + "\n*/"
        
        content = re.sub(header_pattern, update_header, content, flags=re.DOTALL)
        
        self.write_qss(content)
        print("✅ 字体样式已更新")
    
    def apply_color_changes(self, config: Dict[str, Any]) -> None:
        """应用颜色更改"""
        self.create_backup("color_change")
        content = self.read_qss()
        
        # 定义当前主题色到新主题色的映射
        current_colors = {
            "#00a86b": config['colors']['primary'],    # 主色
            "#dc3545": config['colors']['danger'],     # 危险色
            "#ffc107": config['colors']['warning'],    # 警告色
            "#17a2b8": config['colors']['info'],       # 信息色
            "#28a745": config['colors']['success'],    # 成功色
            "#007bff": config['colors']['blue'],       # 蓝色
            "#6c757d": config['colors']['secondary'],  # 次要色
            "#f8f9fa": config['colors']['light'],      # 浅色
            "#495057": config['colors']['dark']        # 深色
        }
        
        # 批量替换颜色
        for old_color, new_color in current_colors.items():
            if old_color != new_color:  # 只有当颜色真的改变时才替换
                content = content.replace(old_color, new_color)
        
        self.write_qss(content)
        print("✅ 颜色样式已更新")
    
    def optimize_qss(self) -> Dict[str, Any]:
        """优化QSS文件"""
        self.create_backup("before_optimization")
        content = self.read_qss()
        
        optimizer = StyleOptimizer(content)
        optimized_content, report = optimizer.optimize()
        
        self.write_qss(optimized_content)
        
        print("✅ QSS文件已优化")
        print(f"   原始大小: {report['original_size']} 字符")
        print(f"   优化后大小: {report['optimized_size']} 字符")
        print(f"   压缩率: {report['compression_ratio']:.1f}%")
        
        return report
    
    def create_theme_preset(self, theme_name: str, config: Dict[str, Any]) -> None:
        """创建主题预设"""
        preset_file = self.themes_dir / f"{theme_name}.json"
        
        # 只保存主题相关的配置
        theme_config = {
            "name": theme_name,
            "description": f"{theme_name}主题",
            "created": datetime.now().isoformat(),
            "fonts": config['fonts'],
            "colors": config['colors'],
            "spacing": config.get('spacing', {}),
            "border_radius": config.get('border_radius', {})
        }
        
        with open(preset_file, 'w', encoding='utf-8') as f:
            json.dump(theme_config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 主题预设已保存: {theme_name}")
    
    def apply_theme_preset(self, theme_name: str) -> None:
        """应用主题预设"""
        preset_file = self.themes_dir / f"{theme_name}.json"
        
        if not preset_file.exists():
            print(f"❌ 主题预设不存在: {theme_name}")
            return
        
        with open(preset_file, 'r', encoding='utf-8') as f:
            theme_config = json.load(f)
        
        # 加载当前配置
        config = self.load_config()
        
        # 更新配置
        config['fonts'] = theme_config['fonts']
        config['colors'] = theme_config['colors']
        if 'spacing' in theme_config:
            config['spacing'] = theme_config['spacing']
        if 'border_radius' in theme_config:
            config['border_radius'] = theme_config['border_radius']
        
        self.create_backup(f"theme_{theme_name}")
        self.apply_font_changes(config)
        self.apply_color_changes(config)
        self.save_config(config)
        
        print(f"✅ 已应用主题: {theme_name}")
    
    def bulk_find_replace(self, find_text: str, replace_text: str, regex: bool = False) -> int:
        """批量查找替换"""
        self.create_backup("bulk_replace")
        content = self.read_qss()
        
        if regex:
            count = len(re.findall(find_text, content))
            content = re.sub(find_text, replace_text, content)
        else:
            count = content.count(find_text)
            content = content.replace(find_text, replace_text)
        
        self.write_qss(content)
        print(f"✅ 批量替换完成: '{find_text}' -> '{replace_text}' ({count}次)")
        return count
    
    def analyze_qss(self) -> Dict[str, Any]:
        """分析QSS文件"""
        content = self.read_qss()
        
        # 基本统计
        lines = content.split('\n')
        total_lines = len(lines)
        non_empty_lines = len([line for line in lines if line.strip()])
        comment_lines = len([line for line in lines if line.strip().startswith('/*') or '/*' in line])
        
        # CSS规则统计
        selectors = re.findall(r'([^{]+)\s*{', content)
        total_rules = len(selectors)
        
        # 字体使用统计
        font_families = re.findall(r'font-family:\s*([^;]+);', content)
        font_sizes = re.findall(r'font-size:\s*(\d+px);', content)
        
        # 颜色使用统计
        colors = re.findall(r'#[0-9a-fA-F]{6}', content)
        color_freq = {}
        for color in colors:
            color_freq[color] = color_freq.get(color, 0) + 1
        
        # 文件大小
        file_size = self.qss_file.stat().st_size
        
        analysis = {
            "file_info": {
                "path": str(self.qss_file),
                "size_bytes": file_size,
                "size_kb": round(file_size / 1024, 2)
            },
            "content_stats": {
                "total_lines": total_lines,
                "non_empty_lines": non_empty_lines,
                "comment_lines": comment_lines,
                "code_lines": non_empty_lines - comment_lines
            },
            "css_stats": {
                "total_rules": total_rules,
                "unique_selectors": len(set(selector.strip() for selector in selectors))
            },
            "font_stats": {
                "font_families_used": len(set(font_families)),
                "font_sizes_used": len(set(font_sizes)),
                "common_sizes": list(set(font_sizes))
            },
            "color_stats": {
                "unique_colors": len(set(colors)),
                "most_used_colors": sorted(color_freq.items(), key=lambda x: x[1], reverse=True)[:10]
            }
        }
        
        return analysis
    
    def show_analysis(self) -> None:
        """显示分析结果"""
        analysis = self.analyze_qss()
        
        print("📊 QSS文件分析报告")
        print("=" * 50)
        print(f"文件路径: {analysis['file_info']['path']}")
        print(f"文件大小: {analysis['file_info']['size_kb']} KB")
        print()
        print("📝 内容统计:")
        print(f"   总行数: {analysis['content_stats']['total_lines']}")
        print(f"   非空行数: {analysis['content_stats']['non_empty_lines']}")
        print(f"   注释行数: {analysis['content_stats']['comment_lines']}")
        print(f"   代码行数: {analysis['content_stats']['code_lines']}")
        print()
        print("🎨 CSS统计:")
        print(f"   CSS规则数: {analysis['css_stats']['total_rules']}")
        print(f"   唯一选择器: {analysis['css_stats']['unique_selectors']}")
        print()
        print("📝 字体统计:")
        print(f"   使用的字体族: {analysis['font_stats']['font_families_used']}")
        print(f"   使用的字体大小: {analysis['font_stats']['font_sizes_used']}")
        print(f"   常用大小: {', '.join(analysis['font_stats']['common_sizes'][:5])}")
        print()
        print("🎯 颜色统计:")
        print(f"   唯一颜色数: {analysis['color_stats']['unique_colors']}")
        print("   最常用颜色:")
        for color, count in analysis['color_stats']['most_used_colors'][:5]:
            print(f"     {color}: {count}次")
    
    def show_current_config(self) -> None:
        """显示当前配置"""
        config = self.load_config()
        
        print("🎨 当前样式配置:")
        print("=" * 50)
        print(f"版本: {config.get('version', 'unknown')}")
        print(f"最后修改: {config.get('meta', {}).get('last_modified', 'unknown')}")
        print()
        print("📝 字体设置:")
        print(f"   UI字体族: {config['fonts']['ui_family']}")
        print(f"   代码字体族: {config['fonts']['code_family']}")
        print()
        print("📏 字体大小:")
        for size_name, size_value in config['fonts']['sizes'].items():
            print(f"   {size_name}: {size_value}px")
        print()
        print("🎯 颜色主题:")
        for color_name, color_value in config['colors'].items():
            print(f"   {color_name}: {color_value}")
    
    def list_themes(self) -> List[str]:
        """列出可用主题"""
        themes = []
        for theme_file in self.themes_dir.glob("*.json"):
            themes.append(theme_file.stem)
        return sorted(themes)
    
    def create_built_in_themes(self) -> None:
        """创建内置主题"""
        themes = {
            "dark": {
                "name": "dark",
                "description": "深色主题",
                "colors": {
                    "primary": "#4caf50",
                    "secondary": "#757575",
                    "success": "#8bc34a",
                    "danger": "#f44336",
                    "warning": "#ff9800",
                    "info": "#2196f3",
                    "light": "#2d2d2d",
                    "dark": "#1a1a1a",
                    "blue": "#2196f3"
                }
            },
            "blue": {
                "name": "blue", 
                "description": "蓝色主题",
                "colors": {
                    "primary": "#007bff",
                    "secondary": "#6c757d",
                    "success": "#28a745",
                    "danger": "#dc3545",
                    "warning": "#ffc107",
                    "info": "#17a2b8",
                    "light": "#f8f9fa",
                    "dark": "#495057",
                    "blue": "#0056b3"
                }
            },
            "purple": {
                "name": "purple",
                "description": "紫色主题", 
                "colors": {
                    "primary": "#6f42c1",
                    "secondary": "#6c757d",
                    "success": "#28a745",
                    "danger": "#dc3545",
                    "warning": "#ffc107",
                    "info": "#17a2b8",
                    "light": "#f8f9fa",
                    "dark": "#495057",
                    "blue": "#007bff"
                }
            }
        }
        
        config = self.load_config()
        for theme_name, theme_data in themes.items():
            theme_config = {
                "name": theme_name,
                "description": theme_data["description"],
                "created": datetime.now().isoformat(),
                "fonts": config['fonts'],  # 使用当前字体设置
                "colors": theme_data["colors"]
            }
            
            preset_file = self.themes_dir / f"{theme_name}.json"
            with open(preset_file, 'w', encoding='utf-8') as f:
                json.dump(theme_config, f, indent=2, ensure_ascii=False)
        
        print("✅ 内置主题已创建: dark, blue, purple")
    
    def interactive_editor(self) -> None:
        """交互式编辑器"""
        config = self.load_config()
        
        while True:
            print("\n🔧 SCOM 样式管理器 - All-in-One 版本")
            print("=" * 60)
            print("1.  📝 修改字体族")
            print("2.  📏 修改字体大小")
            print("3.  🎯 修改颜色主题")
            print("4.  👀 查看当前配置")
            print("5.  📊 分析QSS文件")
            print("6.  ⚡ 优化QSS文件")
            print("7.  💾 应用更改")
            print("8.  🎨 保存为主题预设")
            print("9.  🔄 加载主题预设")
            print("10. 📦 创建内置主题")
            print("11. 💽 管理备份")
            print("12. 🔍 批量查找替换")
            print("13. 📋 查看主题列表")
            print("14. 🚀 快速主题切换")
            print("15. 📁 打开样式目录")
            print("0.  🚪 退出")
            
            choice = input("\n请选择操作 (0-15): ").strip()
            
            try:
                if choice == '1':
                    self._edit_fonts(config)
                elif choice == '2':
                    self._edit_font_sizes(config)
                elif choice == '3':
                    self._edit_colors(config)
                elif choice == '4':
                    self.show_current_config()
                elif choice == '5':
                    self.show_analysis()
                elif choice == '6':
                    self.optimize_qss()
                elif choice == '7':
                    self.apply_font_changes(config)
                    self.apply_color_changes(config)
                    self.save_config(config)
                    print("✅ 所有更改已应用到QSS文件")
                elif choice == '8':
                    self._save_theme_preset(config)
                elif choice == '9':
                    self._load_theme_preset()
                    config = self.load_config()  # 重新加载配置
                elif choice == '10':
                    self.create_built_in_themes()
                elif choice == '11':
                    self._manage_backups()
                elif choice == '12':
                    self._bulk_find_replace()
                elif choice == '13':
                    self._show_theme_list()
                elif choice == '14':
                    self._quick_theme_switch()
                    config = self.load_config()  # 重新加载配置
                elif choice == '15':
                    print(f"📁 样式目录: {self.styles_dir}")
                    os.startfile(self.styles_dir)  # Windows
                elif choice == '0':
                    print("👋 再见!")
                    break
                else:
                    print("❌ 无效选择，请重试")
            
            except KeyboardInterrupt:
                print("\n\n🛑 操作被用户中断")
            except Exception as e:
                print(f"❌ 操作失败: {e}")
    
    def _edit_fonts(self, config: Dict[str, Any]) -> None:
        """编辑字体"""
        print("\n📝 当前字体族:")
        print(f"UI字体: {config['fonts']['ui_family']}")
        print(f"代码字体: {config['fonts']['code_family']}")
        
        font_type = input("修改哪种字体? (ui/code): ").strip().lower()
        if font_type in ['ui', 'code']:
            current_font = config['fonts'][f'{font_type}_family']
            print(f"当前{font_type}字体: {current_font}")
            new_font = input("输入新的字体族 (留空保持不变): ").strip()
            if new_font:
                config['fonts'][f'{font_type}_family'] = new_font
                print(f"✅ {font_type}字体已更新为: {new_font}")
    
    def _edit_font_sizes(self, config: Dict[str, Any]) -> None:
        """编辑字体大小"""
        print("\n📏 当前字体大小:")
        for size_name, size_value in config['fonts']['sizes'].items():
            print(f"{size_name}: {size_value}px")
        
        size_name = input("修改哪个大小? ").strip()
        if size_name in config['fonts']['sizes']:
            current_size = config['fonts']['sizes'][size_name]
            print(f"当前{size_name}大小: {current_size}px")
            try:
                new_size = input(f"输入{size_name}的新大小 (留空保持不变): ").strip()
                if new_size:
                    new_size = int(new_size)
                    config['fonts']['sizes'][size_name] = new_size
                    print(f"✅ {size_name}大小已更新为{new_size}px")
            except ValueError:
                print("❌ 请输入有效数字")
    
    def _edit_colors(self, config: Dict[str, Any]) -> None:
        """编辑颜色"""
        print("\n🎯 当前颜色:")
        for color_name, color_value in config['colors'].items():
            print(f"{color_name}: {color_value}")
        
        color_name = input("修改哪个颜色? ").strip()
        if color_name in config['colors']:
            current_color = config['colors'][color_name]
            print(f"当前{color_name}颜色: {current_color}")
            new_color = input(f"输入{color_name}的新颜色值 (留空保持不变): ").strip()
            if new_color:
                # 验证颜色格式
                if new_color.startswith('#') and len(new_color) == 7:
                    config['colors'][color_name] = new_color
                    print(f"✅ {color_name}颜色已更新为: {new_color}")
                else:
                    print("❌ 请输入有效的颜色值 (格式: #RRGGBB)")
    
    def _save_theme_preset(self, config: Dict[str, Any]) -> None:
        """保存主题预设"""
        theme_name = input("输入主题名称: ").strip()
        if theme_name:
            self.create_theme_preset(theme_name, config)
    
    def _load_theme_preset(self) -> None:
        """加载主题预设"""
        themes = self.list_themes()
        if themes:
            print("\n🎨 可用主题:")
            for i, theme in enumerate(themes, 1):
                print(f"{i}. {theme}")
            try:
                choice_idx = int(input("选择主题序号: ")) - 1
                if 0 <= choice_idx < len(themes):
                    self.apply_theme_preset(themes[choice_idx])
            except ValueError:
                print("❌ 请输入有效数字")
        else:
            print("❌ 没有找到主题预设")
    
    def _manage_backups(self) -> None:
        """管理备份"""
        backups = self.list_backups()
        if not backups:
            print("❌ 没有找到备份文件")
            return
        
        print("\n💽 备份管理:")
        print("1. 查看备份列表")
        print("2. 恢复备份")
        print("3. 删除备份")
        
        choice = input("选择操作 (1-3): ").strip()
        
        if choice == '1':
            print(f"\n📋 共找到 {len(backups)} 个备份:")
            for i, backup in enumerate(backups[:10], 1):  # 只显示最近10个
                print(f"{i}. {backup['timestamp']} - {backup['reason']} ({backup.get('size', 0)} bytes)")
        
        elif choice == '2':
            print(f"\n📋 选择要恢复的备份:")
            for i, backup in enumerate(backups[:10], 1):
                print(f"{i}. {backup['timestamp']} - {backup['reason']}")
            try:
                choice_idx = int(input("选择备份序号: ")) - 1
                if 0 <= choice_idx < len(backups) and choice_idx < 10:
                    self.restore_backup(backups[choice_idx]['file'])
            except ValueError:
                print("❌ 请输入有效数字")
        
        elif choice == '3':
            # 删除旧备份
            if len(backups) > 10:
                old_backups = backups[10:]
                print(f"🗑️ 找到 {len(old_backups)} 个旧备份")
                if input("是否删除旧备份? (y/N): ").lower() == 'y':
                    for backup in old_backups:
                        backup['file'].unlink()
                        meta_file = backup['file'].with_suffix('.json')
                        if meta_file.exists():
                            meta_file.unlink()
                    print(f"✅ 已删除 {len(old_backups)} 个旧备份")
            else:
                print("🎉 备份数量合理，无需清理")
    
    def _bulk_find_replace(self) -> None:
        """批量查找替换"""
        find_text = input("输入要查找的文本: ").strip()
        if not find_text:
            return
        
        replace_text = input("输入替换文本: ").strip()
        use_regex = input("使用正则表达式? (y/N): ").lower() == 'y'
        
        if input(f"确认替换 '{find_text}' -> '{replace_text}'? (y/N): ").lower() == 'y':
            count = self.bulk_find_replace(find_text, replace_text, use_regex)
            if count == 0:
                print("⚠️ 未找到匹配的文本")
    
    def _show_theme_list(self) -> None:
        """显示主题列表"""
        themes = self.list_themes()
        if themes:
            print("\n🎨 可用主题列表:")
            for theme in themes:
                preset_file = self.themes_dir / f"{theme}.json"
                try:
                    with open(preset_file, 'r', encoding='utf-8') as f:
                        theme_config = json.load(f)
                    description = theme_config.get('description', '无描述')
                    print(f"  • {theme}: {description}")
                except:
                    print(f"  • {theme}: 无描述")
        else:
            print("❌ 没有找到主题预设")
    
    def _quick_theme_switch(self) -> None:
        """快速主题切换"""
        themes = self.list_themes()
        if not themes:
            print("❌ 没有找到主题预设")
            return
        
        print("\n🚀 快速主题切换:")
        for i, theme in enumerate(themes, 1):
            print(f"{i}. {theme}")
        
        try:
            choice_idx = int(input("选择主题序号: ")) - 1
            if 0 <= choice_idx < len(themes):
                self.apply_theme_preset(themes[choice_idx])
        except ValueError:
            print("❌ 请输入有效数字")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='SCOM 样式管理器 - All-in-One 版本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python style_manager_aio.py --interactive               # 交互模式
  python style_manager_aio.py --show                      # 显示当前配置
  python style_manager_aio.py --analyze                   # 分析QSS文件
  python style_manager_aio.py --optimize                  # 优化QSS文件
  python style_manager_aio.py --theme dark                # 应用暗色主题
  python style_manager_aio.py --backup                    # 创建备份
  python style_manager_aio.py --create-themes             # 创建内置主题
  python style_manager_aio.py --find "#007bff" --replace "#ff6b6b"  # 批量替换
        """
    )
    
    parser.add_argument('--qss-file', type=str, help='指定QSS文件路径')
    parser.add_argument('--show', action='store_true', help='显示当前配置')
    parser.add_argument('--analyze', action='store_true', help='分析QSS文件')
    parser.add_argument('--optimize', action='store_true', help='优化QSS文件')
    parser.add_argument('--interactive', action='store_true', help='启动交互模式')
    parser.add_argument('--theme', type=str, help='应用指定主题')
    parser.add_argument('--backup', action='store_true', help='创建备份')
    parser.add_argument('--create-themes', action='store_true', help='创建内置主题')
    parser.add_argument('--list-themes', action='store_true', help='列出可用主题')
    parser.add_argument('--list-backups', action='store_true', help='列出备份文件')
    parser.add_argument('--find', type=str, help='查找文本')
    parser.add_argument('--replace', type=str, help='替换文本')
    parser.add_argument('--regex', action='store_true', help='使用正则表达式')
    parser.add_argument('--version', action='version', version='SCOM 样式管理器 v2.0.0')
    
    args = parser.parse_args()
    
    try:
        manager = AllInOneStyleManager(args.qss_file)
        
        if args.show:
            manager.show_current_config()
        elif args.analyze:
            manager.show_analysis()
        elif args.optimize:
            manager.optimize_qss()
        elif args.interactive:
            manager.interactive_editor()
        elif args.theme:
            manager.apply_theme_preset(args.theme)
        elif args.backup:
            manager.create_backup("manual")
        elif args.create_themes:
            manager.create_built_in_themes()
        elif args.list_themes:
            themes = manager.list_themes()
            if themes:
                print("🎨 可用主题:")
                for theme in themes:
                    print(f"  • {theme}")
            else:
                print("❌ 没有找到主题预设")
        elif args.list_backups:
            backups = manager.list_backups()
            if backups:
                print(f"💽 备份列表 (共{len(backups)}个):")
                for backup in backups[:10]:
                    print(f"  • {backup['timestamp']} - {backup['reason']}")
            else:
                print("❌ 没有找到备份文件")
        elif args.find and args.replace:
            count = manager.bulk_find_replace(args.find, args.replace, args.regex)
            if count == 0:
                print("⚠️ 未找到匹配的文本")
        else:
            print("🎨 SCOM 样式管理器 - All-in-One 版本 v2.0.0")
            print("作者: iFishin")
            print()
            print("功能特性:")
            print("  ✨ 样式优化和去重")
            print("  🎯 颜色主题管理")
            print("  📝 字体统一配置")
            print("  💽 备份和恢复")
            print("  🔍 批量查找替换")
            print("  📊 文件分析报告")
            print("  🎨 主题预设管理")
            print("  🔧 交互式编辑")
            print()
            print("使用 --help 查看完整帮助信息")
            print("使用 --interactive 启动交互模式")
    
    except FileNotFoundError as e:
        print(f"❌ 文件不存在: {e}")
    except PermissionError as e:
        print(f"❌ 权限不足: {e}")
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
