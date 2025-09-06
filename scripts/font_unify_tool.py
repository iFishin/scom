#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
字体统一工具
用于统一QSS文件中的所有字体设置，确保一致性
"""

import os
import re
import shutil
from typing import Dict, List, Tuple


class FontUnifyTool:
    """字体统一工具类"""
    
    def __init__(self, qss_file_path: str = "../styles/fish.qss"):
        self.qss_file_path = qss_file_path
        self.backup_path = f"{qss_file_path}.font_backup"
        
        # 标准字体定义
        self.font_definitions = {
            # 字体族定义
            'UI_FONT_FAMILY': '"Microsoft YaHei", "SimSun", "Segoe UI", "Roboto", sans-serif',
            'CODE_FONT_FAMILY': '"JetBrains Mono", "Consolas", "Courier New", monospace',
            
            # 字体大小定义
            'UI_FONT_SIZE_SMALL': '11px',
            'UI_FONT_SIZE_NORMAL': '13px',
            'UI_FONT_SIZE_MEDIUM': '14px',
            'UI_FONT_SIZE_LARGE': '15px',
            'UI_FONT_SIZE_XL': '16px',
            'UI_FONT_SIZE_XXL': '18px',
            'UI_FONT_SIZE_XXXL': '20px',
            'UI_FONT_SIZE_HUGE': '24px',
            'UI_FONT_SIZE_MEGA': '28px',
        }
        
        # 字体替换规则
        self.font_family_patterns = [
            # 需要替换为UI字体的模式
            (r'font-family:\s*"Consolas",\s*"Microsoft YaHei"[^;]+;', 
             f'font-family: {self.font_definitions["UI_FONT_FAMILY"]}; /* UI_FONT_FAMILY */'),
            
            # 其他混合字体模式
            (r'font-family:\s*"[^"]+",\s*"Microsoft YaHei"[^;]+;',
             f'font-family: {self.font_definitions["UI_FONT_FAMILY"]}; /* UI_FONT_FAMILY */'),
             
            # 单独的Consolas字体（保留为代码字体）
            (r'font-family:\s*"Consolas"[^;]*;',
             f'font-family: {self.font_definitions["CODE_FONT_FAMILY"]}; /* CODE_FONT_FAMILY */'),
        ]
        
        # 字体大小标准化规则
        self.font_size_rules = {
            # 控件类型 -> 推荐字体大小
            'QLabel': 'UI_FONT_SIZE_NORMAL',
            'QPushButton': 'UI_FONT_SIZE_NORMAL', 
            'QLineEdit': 'UI_FONT_SIZE_MEDIUM',
            'QTextEdit': 'UI_FONT_SIZE_MEDIUM',
            'QComboBox': 'UI_FONT_SIZE_NORMAL',
            'QCheckBox': 'UI_FONT_SIZE_NORMAL',
            'QRadioButton': 'UI_FONT_SIZE_NORMAL',
            'QGroupBox': 'UI_FONT_SIZE_NORMAL',
            'QMenuBar': 'UI_FONT_SIZE_NORMAL',
            'QMenu': 'UI_FONT_SIZE_NORMAL',
            'QTabBar': 'UI_FONT_SIZE_MEDIUM',
            'QTableWidget': 'UI_FONT_SIZE_MEDIUM',
            'QListWidget': 'UI_FONT_SIZE_MEDIUM',
            'QTextBrowser': 'UI_FONT_SIZE_MEDIUM',
            'QHeaderView': 'UI_FONT_SIZE_MEDIUM',
            'QProgressBar': 'UI_FONT_SIZE_MEDIUM',
            'QToolTip': 'UI_FONT_SIZE_NORMAL',
            'QStatusBar': 'UI_FONT_SIZE_NORMAL',
        }
    
    def create_backup(self):
        """创建QSS文件备份"""
        try:
            shutil.copy2(self.qss_file_path, self.backup_path)
            print(f"✅ Created backup: {self.backup_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to create backup: {e}")
            return False
    
    def analyze_font_usage(self) -> Dict[str, List[str]]:
        """分析字体使用情况"""
        try:
            with open(self.qss_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            analysis = {
                'font_families': [],
                'font_sizes': [],
                'inconsistent_patterns': [],
                'missing_comments': []
            }
            
            # 查找所有字体族定义
            font_family_matches = re.findall(r'font-family:\s*([^;]+);', content, re.IGNORECASE)
            for match in font_family_matches:
                if match.strip() not in analysis['font_families']:
                    analysis['font_families'].append(match.strip())
            
            # 查找所有字体大小定义
            font_size_matches = re.findall(r'font-size:\s*([^;]+);', content, re.IGNORECASE)
            for match in font_size_matches:
                if match.strip() not in analysis['font_sizes']:
                    analysis['font_sizes'].append(match.strip())
            
            # 查找不一致的模式
            lines = content.split('\n')
            for i, line in enumerate(lines):
                # 检查是否有字体定义但缺少注释
                if 'font-family:' in line and '/* UI_FONT_FAMILY */' not in line and '/* CODE_FONT_FAMILY */' not in line:
                    analysis['missing_comments'].append(f"Line {i+1}: {line.strip()}")
                
                # 检查混合字体模式
                if 'font-family:' in line and 'Consolas' in line and 'Microsoft YaHei' in line:
                    analysis['inconsistent_patterns'].append(f"Line {i+1}: Mixed font pattern")
            
            return analysis
            
        except Exception as e:
            print(f"❌ Failed to analyze font usage: {e}")
            return {}
    
    def unify_fonts(self, interactive=True):
        """统一字体设置"""
        if not self.create_backup():
            return False
        
        try:
            with open(self.qss_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            changes_made = 0
            
            print("🔄 Starting font unification...")
            
            # 1. 替换字体族
            for pattern, replacement in self.font_family_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    if interactive:
                        print(f"\n📝 Found {len(matches)} instances of pattern: {pattern[:50]}...")
                        for match in matches[:3]:  # Show first 3 examples
                            print(f"   Example: {match[:80]}...")
                        if len(matches) > 3:
                            print(f"   ... and {len(matches) - 3} more")
                        
                        choice = input("Replace all? (y/n/s=skip): ").lower()
                        if choice == 's':
                            continue
                        elif choice != 'y':
                            continue
                    
                    content = re.sub(pattern, replacement, content)
                    changes_made += len(matches)
                    print(f"✅ Replaced {len(matches)} font family patterns")
            
            # 2. 更新全局字体定义
            global_font_pattern = r'\* \{\s*font-family:[^}]+\}'
            global_font_replacement = f"""* {{
    font-family: {self.font_definitions["UI_FONT_FAMILY"]}; /* UI_FONT_FAMILY */
    font-size: {self.font_definitions["UI_FONT_SIZE_MEDIUM"]}; /* UI_FONT_SIZE_MEDIUM */
    color: #333333;
    outline: none; /* 移除焦点轮廓 */
}}"""
            
            if re.search(global_font_pattern, content, re.DOTALL):
                content = re.sub(global_font_pattern, global_font_replacement, content, flags=re.DOTALL)
                changes_made += 1
                print("✅ Updated global font definition")
            
            # 3. 确保所有字体定义都有注释
            font_family_lines = re.findall(r'(.*font-family:\s*[^;]+;.*)', content)
            for line in font_family_lines:
                if '/* UI_FONT_FAMILY */' not in line and '/* CODE_FONT_FAMILY */' not in line:
                    # 判断是否为代码字体
                    if any(code_font in line for code_font in ['Consolas', 'Courier New', 'JetBrains Mono', 'monospace']):
                        new_line = line.replace(';', '; /* CODE_FONT_FAMILY */')
                    else:
                        new_line = line.replace(';', '; /* UI_FONT_FAMILY */')
                    
                    content = content.replace(line, new_line)
                    changes_made += 1
            
            # 4. 标准化特定控件的字体大小
            for widget, size_key in self.font_size_rules.items():
                size_value = self.font_definitions[size_key]
                
                # 匹配控件选择器的字体大小
                pattern = rf'({widget}[^{{]*\{{[^}}]*?)font-size:\s*[^;]+;([^}}]*\}})'
                replacement = rf'\1font-size: {size_value}; /* {size_key} */\2'
                
                matches = re.findall(pattern, content, re.DOTALL)
                if matches:
                    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
                    print(f"✅ Standardized font size for {widget} ({len(matches)} instances)")
                    changes_made += len(matches)
            
            # 保存更改
            if changes_made > 0:
                with open(self.qss_file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"\n🎉 Font unification completed! Made {changes_made} changes.")
                print(f"📁 Backup saved as: {self.backup_path}")
                return True
            else:
                print("✨ No changes needed - fonts are already unified!")
                # 删除不必要的备份
                if os.path.exists(self.backup_path):
                    os.remove(self.backup_path)
                return True
                
        except Exception as e:
            print(f"❌ Failed to unify fonts: {e}")
            # 恢复备份
            if os.path.exists(self.backup_path):
                shutil.copy2(self.backup_path, self.qss_file_path)
                print("🔄 Restored from backup")
            return False
    
    def restore_backup(self):
        """从备份恢复"""
        if os.path.exists(self.backup_path):
            try:
                shutil.copy2(self.backup_path, self.qss_file_path)
                print(f"✅ Restored from backup: {self.backup_path}")
                return True
            except Exception as e:
                print(f"❌ Failed to restore backup: {e}")
                return False
        else:
            print("❌ No backup file found")
            return False
    
    def generate_font_report(self):
        """生成字体使用报告"""
        analysis = self.analyze_font_usage()
        if not analysis:
            return
        
        print("\n" + "="*60)
        print("📊 FONT USAGE ANALYSIS REPORT")
        print("="*60)
        
        print(f"\n📋 Found {len(analysis['font_families'])} different font family definitions:")
        for i, font in enumerate(analysis['font_families'], 1):
            print(f"  {i}. {font}")
        
        print(f"\n📏 Found {len(analysis['font_sizes'])} different font sizes:")
        for i, size in enumerate(analysis['font_sizes'], 1):
            print(f"  {i}. {size}")
        
        if analysis['missing_comments']:
            print(f"\n⚠️  Found {len(analysis['missing_comments'])} lines without font type comments:")
            for comment in analysis['missing_comments'][:5]:  # Show first 5
                print(f"  {comment}")
            if len(analysis['missing_comments']) > 5:
                print(f"  ... and {len(analysis['missing_comments']) - 5} more")
        
        if analysis['inconsistent_patterns']:
            print(f"\n🔍 Found {len(analysis['inconsistent_patterns'])} inconsistent font patterns:")
            for pattern in analysis['inconsistent_patterns']:
                print(f"  {pattern}")
        
        print("\n📝 RECOMMENDED ACTIONS:")
        if len(analysis['font_families']) > 3:
            print("  • Run font unification to reduce font family variety")
        if analysis['missing_comments']:
            print("  • Add font type comments for better maintainability")
        if analysis['inconsistent_patterns']:
            print("  • Fix mixed font patterns for consistency")
        
        print("\n💡 FONT STANDARDS:")
        print("  • UI Elements: Microsoft YaHei, SimSun, Segoe UI, Roboto")
        print("  • Code/Console: JetBrains Mono, Consolas, Courier New")
        print("  • Standard sizes: 11px (small), 13px (normal), 14px (medium), 16px (large)")


def main():
    """主函数"""
    print("🎨 Font Unification Tool for QSS")
    print("=" * 40)
    
    tool = FontUnifyTool()
    
    while True:
        print("\n📋 Available actions:")
        print("1. Analyze current font usage")
        print("2. Generate font report")
        print("3. Unify fonts (interactive)")
        print("4. Unify fonts (automatic)")
        print("5. Restore from backup")
        print("6. Exit")
        
        choice = input("\nSelect action (1-6): ").strip()
        
        if choice == '1':
            analysis = tool.analyze_font_usage()
            print(f"\n📊 Analysis complete: {len(analysis)} categories analyzed")
            
        elif choice == '2':
            tool.generate_font_report()
            
        elif choice == '3':
            tool.unify_fonts(interactive=True)
            
        elif choice == '4':
            tool.unify_fonts(interactive=False)
            
        elif choice == '5':
            tool.restore_backup()
            
        elif choice == '6':
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice, please try again")


if __name__ == "__main__":
    main()
