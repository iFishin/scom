
import os
import sys
import re
import shutil

class QSSLoader:
    def __init__(self):
        # 初始化时添加Scripts目录到路径并导入QuickStyleManager
        self._setup_style_manager()
        
        # 字体管理相关
        self.font_definitions = {
            'UI_FONT_FAMILY': '"Microsoft YaHei", "SimSun", "Segoe UI", "Roboto", sans-serif',
            'CODE_FONT_FAMILY': '"JetBrains Mono", "Consolas", "Courier New", monospace',
            'UI_FONT_SIZE_SMALL': '11px',
            'UI_FONT_SIZE_NORMAL': '13px',
            'UI_FONT_SIZE_MEDIUM': '14px',
            'UI_FONT_SIZE_LARGE': '15px',
            'UI_FONT_SIZE_XL': '16px',
        }

    def _setup_style_manager(self):
        """设置样式管理器"""
        # 添加Scripts目录到路径以便导入QuickStyleManager
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        scripts_dir = os.path.join(script_dir, 'Scripts')
        if scripts_dir not in sys.path:
            sys.path.append(scripts_dir)

        try:
            from quick_style import QuickStyleManager
            self.style_manager = QuickStyleManager()
        except ImportError:
            print("Warning: Cannot import QuickStyleManager, theme switching may not work properly")
            self.style_manager = None

    @staticmethod
    def load_stylesheet(style: str) -> str:
        """加载样式表文件"""
        with open(style, "r", encoding="UTF-8") as file:
            return file.read()
    
    def apply_dark_theme(self, create_backup=True):
        """应用暗色主题"""
        if self.style_manager:
            try:
                self.style_manager.apply_dark_theme(create_backup=create_backup)
                return True
            except Exception as e:
                print(f"Failed to apply dark theme: {e}")
                return False
        else:
            print("Warning: Style manager not available")
            return False
    
    def apply_light_theme(self, create_backup=True):
        """应用亮色主题"""
        if self.style_manager:
            try:
                self.style_manager.apply_light_theme(create_backup=create_backup)
                return True
            except Exception as e:
                print(f"Failed to apply light theme: {e}")
                return False
        else:
            print("Warning: Style manager not available")
            return False
    
    def is_style_manager_available(self):
        """检查样式管理器是否可用"""
        return self.style_manager is not None
    
    def check_font_consistency(self, qss_path="styles/fish.qss"):
        """检查字体一致性"""
        try:
            content = self.load_stylesheet(qss_path)
            
            # 统计字体使用
            font_families = re.findall(r'font-family:\s*([^;]+);', content)
            font_sizes = re.findall(r'font-size:\s*([^;]+);', content)
            
            ui_fonts = [f for f in font_families if 'Microsoft YaHei' in f and 'Consolas' not in f]
            code_fonts = [f for f in font_families if 'Consolas' in f or 'JetBrains Mono' in f]
            mixed_fonts = [f for f in font_families if 'Consolas' in f and 'Microsoft YaHei' in f]
            
            return {
                'ui_fonts': len(ui_fonts),
                'code_fonts': len(code_fonts),
                'mixed_fonts': len(mixed_fonts),
                'font_size_varieties': len(set(font_sizes)),
                'is_consistent': len(mixed_fonts) == 0
            }
        except Exception as e:
            print(f"Font consistency check failed: {e}")
            return None
    
    def unify_fonts(self, qss_path="styles/fish.qss", create_backup=True):
        """统一字体设置"""
        if not os.path.exists(qss_path):
            print(f"QSS file not found: {qss_path}")
            return False
        
        # 创建备份
        if create_backup:
            backup_path = f"{qss_path}.font_backup_{int(__import__('time').time())}"
            try:
                shutil.copy2(qss_path, backup_path)
                print(f"Font backup created: {backup_path}")
            except Exception as e:
                print(f"Failed to create font backup: {e}")
                return False
        
        try:
            content = self.load_stylesheet(qss_path)
            
            # 字体统一规则
            rules = [
                # 统一混合字体为UI字体
                (
                    r'font-family:\s*"Consolas",\s*"Microsoft YaHei"[^;]*;',
                    f'font-family: {self.font_definitions["UI_FONT_FAMILY"]}; /* UI_FONT_FAMILY */'
                ),
                # 确保字体注释
                (
                    r'(font-family:\s*"JetBrains Mono"[^;]*;)(?!\s*/\*)',
                    r'\1 /* CODE_FONT_FAMILY */'
                ),
                (
                    r'(font-family:\s*"Microsoft YaHei"[^;]*;)(?!\s*/\*)',
                    r'\1 /* UI_FONT_FAMILY */'
                ),
            ]
            
            changes = 0
            for pattern, replacement in rules:
                matches = len(re.findall(pattern, content))
                if matches > 0:
                    content = re.sub(pattern, replacement, content)
                    changes += matches
            
            # 保存文件
            with open(qss_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"Font unification completed: {changes} changes made")
            return True
            
        except Exception as e:
            print(f"Font unification failed: {e}")
            return False
    
    def get_font_report(self, qss_path="styles/fish.qss"):
        """获取字体使用报告"""
        consistency = self.check_font_consistency(qss_path)
        if not consistency:
            return "Font report generation failed"
        
        report = f"""
📊 Font Usage Report
==================
🎨 UI Fonts: {consistency['ui_fonts']} instances
💻 Code Fonts: {consistency['code_fonts']} instances
⚠️  Mixed Fonts: {consistency['mixed_fonts']} instances
📏 Font Size Varieties: {consistency['font_size_varieties']}
✅ Consistency Status: {'Consistent' if consistency['is_consistent'] else 'Needs unification'}

💡 Recommended Actions:
"""
        if not consistency['is_consistent']:
            report += "  • Run font unification to fix mixed font patterns\n"
        if consistency['font_size_varieties'] > 10:
            report += "  • Consider standardizing font sizes\n"
        if consistency['is_consistent']:
            report += "  • Fonts are already unified!\n"
        
        return report
