from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QPushButton, QLabel, QComboBox, QSpinBox, QColorDialog,
    QFontDialog, QCheckBox, QSlider, QTabWidget, QWidget,
    QMessageBox, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QPalette
import configparser
import os
from utils import common
from .QSSLoader import QSSLoader
from middileware.Logger import Logger

# 尝试获取logger实例，如果Logger未初始化则创建简单logger
try:
    logger = Logger.get_logger("StyleConfigDialog")
except RuntimeError:
    # 如果Logger中间件未初始化，创建简单的logger
    import logging
    logger = logging.getLogger("StyleConfigDialog")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

class ColorPreviewLabel(QLabel):
    """颜色预览标签"""
    def __init__(self, color="#000000"):
        super().__init__()
        self.color = color
        self.setFixedSize(40, 25)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                border: 2px solid #ddd;
                border-radius: 6px;
            }}
        """)
        self.setText("")

    def set_color(self, color):
        self.color = color
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                border: 2px solid #ddd;
                border-radius: 6px;
            }}
        """)

class FontPreviewLabel(QLabel):
    """字体预览标签"""
    def __init__(self):
        super().__init__("预览文本 Preview Text 123")
        self.setFixedHeight(40)
        self.setStyleSheet("""
            QLabel {
                border: 2px solid #ddd;
                padding: 8px;
                background-color: #ffffff;
                border-radius: 6px;
                color: #333333;
            }
        """)

class StyleConfigDialog(QDialog):
    """样式配置对话框"""
    style_changed = Signal(dict)  # 样式改变信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.setWindowTitle("样式配置")
        self.setFixedSize(600, 500)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        
        # 样式配置数据
        self.style_config = {
            'font_family': 'Microsoft YaHei',
            'font_size': 14,
            'primary_color': '#00a86b',
            'secondary_color': '#6c757d',
            'background_color': '#f8f9fa',
            'text_color': '#333333',
            'accent_color': '#007bff',
            'success_color': '#28a745',
            'warning_color': '#ffc107',
            'danger_color': '#dc3545',
            'border_radius': 6,
            'theme_mode': 'light'
        }
        
        self.init_ui()
        self.load_config()
        
    def init_ui(self):
        """初始化UI"""
        # 应用当前应用程序的QSS样式
        try:
            qss_style = QSSLoader.load_stylesheet("styles/fish.qss")
            self.setStyleSheet(qss_style)
        except Exception as e:
            print(f"Failed to load QSS style: {e}")
        
        layout = QVBoxLayout(self)
        
        # 创建选项卡
        tab_widget = QTabWidget()
        
        # 字体设置选项卡
        font_tab = self.create_font_tab()
        tab_widget.addTab(font_tab, "字体设置")
        
        # 颜色主题选项卡
        color_tab = self.create_color_tab()
        tab_widget.addTab(color_tab, "颜色主题")
        
        # 外观设置选项卡
        appearance_tab = self.create_appearance_tab()
        tab_widget.addTab(appearance_tab, "外观设置")
        
        layout.addWidget(tab_widget)
        
        # 按钮组
        button_layout = QHBoxLayout()
        
        self.preview_button = QPushButton("预览")
        self.preview_button.clicked.connect(self.preview_style)
        
        self.apply_button = QPushButton("应用")
        self.apply_button.clicked.connect(self.apply_style)
        
        self.reset_button = QPushButton("重置")
        self.reset_button.clicked.connect(self.reset_to_default)
        
        self.ok_button = QPushButton("确定")
        self.ok_button.clicked.connect(self.accept_and_apply)
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.preview_button)
        button_layout.addWidget(self.apply_button)
        button_layout.addStretch()
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
    def create_font_tab(self):
        """创建字体设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 字体系列
        font_group = QGroupBox("字体设置")
        font_layout = QGridLayout(font_group)
        
        # 字体系列选择
        font_layout.addWidget(QLabel("字体系列:"), 0, 0)
        self.font_family_combo = QComboBox()
        self.font_family_combo.addItems([
            "Microsoft YaHei", "SimSun", "SimHei", "KaiTi", "FangSong",
            "Consolas", "Arial", "Times New Roman", "Courier New",
            "Helvetica", "Georgia", "Verdana"
        ])
        self.font_family_combo.currentTextChanged.connect(self.on_font_changed)
        font_layout.addWidget(self.font_family_combo, 0, 1)
        
        # 字体大小
        font_layout.addWidget(QLabel("字体大小:"), 1, 0)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 32)
        self.font_size_spin.setValue(14)
        self.font_size_spin.valueChanged.connect(self.on_font_changed)
        font_layout.addWidget(self.font_size_spin, 1, 1)
        
        # 字体预览
        font_layout.addWidget(QLabel("预览:"), 2, 0)
        self.font_preview = FontPreviewLabel()
        font_layout.addWidget(self.font_preview, 2, 1)
        
        # 字体选择按钮
        self.font_dialog_button = QPushButton("选择字体...")
        self.font_dialog_button.clicked.connect(self.select_font)
        font_layout.addWidget(self.font_dialog_button, 3, 0, 1, 2)
        
        layout.addWidget(font_group)
        layout.addStretch()
        
        return widget
        
    def create_color_tab(self):
        """创建颜色主题选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # 主题模式
        theme_group = QGroupBox("主题模式")
        theme_layout = QHBoxLayout(theme_group)
        
        self.theme_mode_combo = QComboBox()
        self.theme_mode_combo.addItems(["浅色主题", "深色主题", "自动"])
        self.theme_mode_combo.currentTextChanged.connect(self.on_theme_mode_changed)
        theme_layout.addWidget(QLabel("主题模式:"))
        theme_layout.addWidget(self.theme_mode_combo)
        theme_layout.addStretch()
        
        scroll_layout.addWidget(theme_group)
        
        # 颜色设置
        color_group = QGroupBox("颜色设置")
        color_layout = QGridLayout(color_group)
        
        # 定义颜色设置项
        color_items = [
            ("主色调", "primary_color", "#00a86b", "主要按钮、链接等"),
            ("次要色", "secondary_color", "#6c757d", "次要按钮、边框等"),
            ("强调色", "accent_color", "#007bff", "复选框、焦点等"),
            ("背景色", "background_color", "#f8f9fa", "窗口背景颜色"),
            ("文字色", "text_color", "#333333", "主要文字颜色"),
            ("成功色", "success_color", "#28a745", "成功状态颜色"),
            ("警告色", "warning_color", "#ffc107", "警告状态颜色"),
            ("危险色", "danger_color", "#dc3545", "错误、危险状态")
        ]
        
        self.color_buttons = {}
        self.color_previews = {}
        
        for i, (name, key, default_color, description) in enumerate(color_items):
            # 标签
            color_layout.addWidget(QLabel(f"{name}:"), i, 0)
            
            # 颜色预览
            preview = ColorPreviewLabel(default_color)
            self.color_previews[key] = preview
            color_layout.addWidget(preview, i, 1)
            
            # 颜色选择按钮
            button = QPushButton("选择")
            button.clicked.connect(lambda checked, k=key: self.select_color(k))
            self.color_buttons[key] = button
            color_layout.addWidget(button, i, 2)
            
            # 描述
            desc_label = QLabel(description)
            desc_label.setStyleSheet("color: #666; font-size: 11px;")
            color_layout.addWidget(desc_label, i, 3)
        
        scroll_layout.addWidget(color_group)
        
        # 预设主题
        preset_group = QGroupBox("预设主题")
        preset_layout = QHBoxLayout(preset_group)
        
        themes = [
            ("默认绿色", {"primary_color": "#00a86b", "accent_color": "#007bff"}),
            ("蓝色主题", {"primary_color": "#007bff", "accent_color": "#0056b3"}),
            ("紫色主题", {"primary_color": "#6f42c1", "accent_color": "#5a2d91"}),
            ("橙色主题", {"primary_color": "#fd7e14", "accent_color": "#e8590c"})
        ]
        
        for name, colors in themes:
            button = QPushButton(name)
            button.clicked.connect(lambda checked, c=colors: self.apply_preset_theme(c))
            preset_layout.addWidget(button)
        
        scroll_layout.addWidget(preset_group)
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        return widget
        
    def create_appearance_tab(self):
        """创建外观设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 圆角设置
        radius_group = QGroupBox("圆角设置")
        radius_layout = QGridLayout(radius_group)
        
        radius_layout.addWidget(QLabel("边框圆角:"), 0, 0)
        self.border_radius_spin = QSpinBox()
        self.border_radius_spin.setRange(0, 20)
        self.border_radius_spin.setValue(6)
        self.border_radius_spin.setSuffix("px")
        radius_layout.addWidget(self.border_radius_spin, 0, 1)
        
        layout.addWidget(radius_group)
        
        # 其他外观设置
        other_group = QGroupBox("其他设置")
        other_layout = QGridLayout(other_group)
        
        # 动画效果
        self.animation_checkbox = QCheckBox("启用动画效果")
        self.animation_checkbox.setChecked(True)
        other_layout.addWidget(self.animation_checkbox, 0, 0)
        
        # 阴影效果
        self.shadow_checkbox = QCheckBox("启用阴影效果")
        self.shadow_checkbox.setChecked(False)
        other_layout.addWidget(self.shadow_checkbox, 1, 0)
        
        layout.addWidget(other_group)
        layout.addStretch()
        
        return widget
        
    def on_font_changed(self):
        """字体改变时更新预览"""
        font = QFont(self.font_family_combo.currentText(), self.font_size_spin.value())
        self.font_preview.setFont(font)
        
    def select_font(self):
        """选择字体"""
        current_font = QFont(self.font_family_combo.currentText(), self.font_size_spin.value())
        font, ok = QFontDialog.getFont(current_font, self)
        if ok:
            self.font_family_combo.setCurrentText(font.family())
            self.font_size_spin.setValue(font.pointSize())
            self.on_font_changed()
            
    def select_color(self, color_key):
        """选择颜色"""
        current_color = QColor(self.style_config.get(color_key, "#000000"))
        color = QColorDialog.getColor(current_color, self, f"选择{color_key}")
        if color.isValid():
            color_hex = color.name()
            self.style_config[color_key] = color_hex
            self.color_previews[color_key].set_color(color_hex)
            
    def on_theme_mode_changed(self):
        """主题模式改变"""
        mode_map = {"浅色主题": "light", "深色主题": "dark", "自动": "auto"}
        self.style_config['theme_mode'] = mode_map[self.theme_mode_combo.currentText()]
        
    def apply_preset_theme(self, colors):
        """应用预设主题"""
        for key, value in colors.items():
            if key in self.style_config:
                self.style_config[key] = value
                if key in self.color_previews:
                    self.color_previews[key].set_color(value)
                    
    def collect_config(self):
        """收集当前配置"""
        self.style_config.update({
            'font_family': self.font_family_combo.currentText(),
            'font_size': self.font_size_spin.value(),
            'border_radius': self.border_radius_spin.value(),
            'animation_enabled': self.animation_checkbox.isChecked(),
            'shadow_enabled': self.shadow_checkbox.isChecked()
        })
        return self.style_config.copy()
        
    def preview_style(self):
        """预览样式"""
        config = self.collect_config()
        self.generate_and_apply_qss(config, preview=True)
        
    def apply_style(self):
        """应用样式"""
        config = self.collect_config()
        self.generate_and_apply_qss(config, preview=False)
        self.save_config()
        
    def accept_and_apply(self):
        """确定并应用"""
        self.apply_style()
        self.accept()
        
    def reset_to_default(self):
        """重置为默认值"""
        self.style_config = {
            'font_family': 'Microsoft YaHei',
            'font_size': 14,
            'primary_color': '#00a86b',
            'secondary_color': '#6c757d',
            'background_color': '#f8f9fa',
            'text_color': '#333333',
            'accent_color': '#007bff',
            'success_color': '#28a745',
            'warning_color': '#ffc107',
            'danger_color': '#dc3545',
            'border_radius': 6,
            'theme_mode': 'light',
            'animation_enabled': True,
            'shadow_enabled': False
        }
        self.load_ui_from_config()
        
    def load_ui_from_config(self):
        """从配置加载UI"""
        self.font_family_combo.setCurrentText(self.style_config.get('font_family', 'Microsoft YaHei'))
        self.font_size_spin.setValue(self.style_config.get('font_size', 14))
        self.border_radius_spin.setValue(self.style_config.get('border_radius', 6))
        self.animation_checkbox.setChecked(self.style_config.get('animation_enabled', True))
        self.shadow_checkbox.setChecked(self.style_config.get('shadow_enabled', False))
        
        # 更新颜色预览
        for key, preview in self.color_previews.items():
            color = self.style_config.get(key, "#000000")
            preview.set_color(color)
            
        # 更新主题模式
        mode_map = {"light": "浅色主题", "dark": "深色主题", "auto": "自动"}
        theme_mode = self.style_config.get('theme_mode', 'light')
        self.theme_mode_combo.setCurrentText(mode_map.get(theme_mode, "浅色主题"))
        
        self.on_font_changed()
        
    def load_config(self):
        """加载配置"""
        try:
            config = configparser.ConfigParser()
            config.read('config.ini', encoding='utf-8')
            
            if 'StyleSettings' in config:
                style_section = config['StyleSettings']
                for key in self.style_config:
                    if key in style_section:
                        value = style_section[key]
                        if key in ['font_size', 'border_radius']:
                            self.style_config[key] = int(value)
                        elif key in ['animation_enabled', 'shadow_enabled']:
                            self.style_config[key] = value.lower() == 'true'
                        else:
                            self.style_config[key] = value
                            
            self.load_ui_from_config()
            
        except Exception as e:
            logger.error(f"加载样式配置失败: {e}")
            
    def save_config(self):
        """保存配置"""
        try:
            config = configparser.ConfigParser()
            if os.path.exists('config.ini'):
                config.read('config.ini', encoding='utf-8')
                
            if 'StyleSettings' not in config:
                config.add_section('StyleSettings')
                
            style_section = config['StyleSettings']
            current_config = self.collect_config()
            
            for key, value in current_config.items():
                style_section[key] = str(value)
                
            with open('config.ini', 'w', encoding='utf-8') as f:
                config.write(f)
                
            logger.info("样式配置已保存")
            
        except Exception as e:
            logger.error(f"保存样式配置失败: {e}")
            
    def generate_and_apply_qss(self, config, preview=False):
        """生成并应用QSS样式"""
        try:
            # 生成QSS内容
            qss_content = self.generate_qss_content(config)
            
            # 保存为文件
            style_file = 'styles/custom_style.qss' if not preview else 'styles/preview_style.qss'
            os.makedirs('styles', exist_ok=True)
            
            with open(style_file, 'w', encoding='utf-8') as f:
                f.write(qss_content)
                
            # 应用样式
            if self.parent_widget:
                app = self.parent_widget.app if hasattr(self.parent_widget, 'app') else None
                if app:
                    app.setStyleSheet(qss_content)
                else:
                    self.parent_widget.setStyleSheet(qss_content)
                    
            if not preview:
                QMessageBox.information(self, "样式应用", "样式已成功应用！")
                
        except Exception as e:
            logger.error(f"应用样式失败: {e}")
            QMessageBox.warning(self, "错误", f"应用样式失败: {e}")
            
    def generate_qss_content(self, config):
        """生成QSS内容"""
        # 这里生成完整的QSS内容，基于用户配置
        qss_template = f"""
/* ===== 自定义样式配置 ===== */
* {{
    font-family: "{config['font_family']}";
    font-size: {config['font_size']}px;
    color: {config['text_color']};
    outline: none;
}}

QWidget {{
    background-color: {config['background_color']};
    color: {config['text_color']};
    selection-background-color: {config['accent_color']};
    selection-color: white;
}}

/* 按钮样式 */
QPushButton {{
    background-color: {config['primary_color']};
    color: white;
    border: 2px solid transparent;
    padding: 6px 12px;
    border-radius: {config['border_radius']}px;
    font-weight: 500;
    min-height: 16px;
}}

QPushButton:hover {{
    background-color: {self.adjust_color_brightness(config['primary_color'], -20)};
}}

QPushButton:pressed {{
    background-color: {self.adjust_color_brightness(config['primary_color'], -40)};
}}

/* 输入框样式 */
QLineEdit, QTextEdit, QPlainTextEdit {{
    border: 2px solid #ced4da;
    padding: 6px 10px;
    border-radius: {config['border_radius']}px;
    background-color: white;
    color: {config['text_color']};
    selection-background-color: {config['accent_color']};
    selection-color: white;
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {config['accent_color']};
}}

/* 复选框样式 */
QCheckBox::indicator:checked {{
    background-color: {config['accent_color']};
    border: 2px solid {config['accent_color']};
}}

/* 分组框样式 */
QGroupBox {{
    border: 2px solid #dee2e6;
    border-radius: {config['border_radius']}px;
    padding: 18px 8px 8px 8px;
    margin-top: 12px;
    background-color: white;
    font-weight: 500;
    color: {config['text_color']};
}}

QGroupBox::title {{
    color: {config['text_color']};
    background-color: {config['background_color']};
    border-radius: {config['border_radius']}px;
    font-weight: 600;
    padding: 3px 10px;
    left: 8px;
    top: 4px;
}}

/* 下拉框样式 */
QComboBox {{
    border: 2px solid #ced4da;
    padding: 6px 10px;
    border-radius: {config['border_radius']}px;
    background-color: white;
    color: {config['text_color']};
}}

QComboBox:focus {{
    border-color: {config['accent_color']};
}}

/* 特殊按钮样式 */
QPushButton[buttonStyle="danger"] {{
    background-color: {config['danger_color']};
}}

QPushButton[buttonStyle="warning"] {{
    background-color: {config['warning_color']};
    color: {config['text_color']};
}}

QPushButton[buttonStyle="secondary"] {{
    background-color: {config['secondary_color']};
}}

/* 导航按钮样式 */
QPushButton#nav_button_active {{
    color: {config['primary_color']};
    border-bottom: 3px solid {config['primary_color']};
}}

QPushButton#nav_button {{
    color: {config['secondary_color']};
}}

QPushButton#nav_button:hover {{
    color: {config['primary_color']};
}}
"""
        return qss_template
        
    def adjust_color_brightness(self, color_hex, amount):
        """调整颜色亮度"""
        try:
            color = QColor(color_hex)
            h, s, v, a = color.getHsv()
            v = max(0, min(255, v + amount))
            color.setHsv(h, s, v, a)
            return color.name()
        except:
            return color_hex
