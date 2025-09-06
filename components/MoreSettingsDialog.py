from utils.common import read_config, write_config
import os
import sys
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QScrollArea,
    QWidget,
    QCheckBox,
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QRect, Property
from PySide6.QtGui import QPainter, QColor, QLinearGradient

# QSSLoader现在已经集成了QuickStyleManager功能
from components.QSSLoader import QSSLoader


class ThemeToggleSwitch(QLabel):
    """简化版的主题切换开关"""
    def __init__(self):
        super().__init__()
        self.setFixedSize(60, 30)  # 较小的尺寸
        self._is_dark_theme = False  # False=亮色主题, True=暗色主题
        self._circle_pos = QPoint(3, 3)
        self.circle_size = 24
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)
        
        # 创建动画
        self.animation = QPropertyAnimation(self, b"circle_pos")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.OutQuart)
        
        # 初始化位置
        self.update_circle_position()
    
    def update_circle_position(self):
        """更新圆形按钮的位置"""
        y_center = (self.height() - self.circle_size) / 2
        if self._is_dark_theme:
            x_pos = self.width() - self.circle_size - 3
        else:
            x_pos = 3
        self._circle_pos = QPoint(x_pos, y_center)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制背景轨道
        track_rect = QRect(0, 0, self.width(), self.height())
        # 暗色主题时使用蓝色，亮色主题时使用灰色
        track_color = QColor("#2c3e50") if self._is_dark_theme else QColor("#e0e0e0")
        
        painter.setBrush(track_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(track_rect, self.height()/2, self.height()/2)
        
        # 绘制圆形按钮
        button_rect = QRect(
            self._circle_pos.x(), 
            self._circle_pos.y(), 
            self.circle_size, 
            self.circle_size
        )
        
        # 按钮渐变效果
        gradient = QLinearGradient(0, self._circle_pos.y(), 0, self._circle_pos.y() + self.circle_size)
        if self._is_dark_theme:
            # 暗色主题时按钮为深色
            gradient.setColorAt(0, QColor("#34495e"))
            gradient.setColorAt(0.5, QColor("#2c3e50"))
            gradient.setColorAt(1, QColor("#1a252f"))
        else:
            # 亮色主题时按钮为亮色
            gradient.setColorAt(0, QColor("#ffffff"))
            gradient.setColorAt(0.5, QColor("#f8f8f8"))
            gradient.setColorAt(1, QColor("#e8e8e8"))
        
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(button_rect)
        
        # 按钮边框
        border_color = QColor("#bdc3c7") if not self._is_dark_theme else QColor("#7f8c8d")
        painter.setPen(border_color)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(button_rect)
        
        # 绘制主题图标（太阳/月亮）
        icon_rect = QRect(
            self._circle_pos.x() + 6,
            self._circle_pos.y() + 6,
            12, 12
        )
        
        painter.setBrush(QColor("#f39c12") if not self._is_dark_theme else QColor("#f1c40f"))
        painter.setPen(Qt.NoPen)
        if self._is_dark_theme:
            # 绘制月亮
            painter.drawEllipse(icon_rect)
            # 绘制月亮的阴影部分
            shadow_rect = QRect(icon_rect.x() + 3, icon_rect.y(), 9, 12)
            painter.setBrush(QColor("#2c3e50"))
            painter.drawEllipse(shadow_rect)
        else:
            # 绘制太阳
            painter.drawEllipse(icon_rect)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_dark_theme = not self._is_dark_theme
            self.toggle_animation()
            self.theme_changed()  # 触发主题更改
    
    def toggle_animation(self):
        """执行切换动画"""
        y_center = (self.height() - self.circle_size) / 2
        
        if self._is_dark_theme:
            start_x = 3
            end_x = self.width() - self.circle_size - 3
        else:
            start_x = self.width() - self.circle_size - 3
            end_x = 3
            
        self.animation.setStartValue(QPoint(start_x, y_center))
        self.animation.setEndValue(QPoint(end_x, y_center))
        self.animation.start()
    
    def theme_changed(self):
        """主题切换处理"""
        try:
            # 使用QSSLoader进行主题切换
            qss_loader = QSSLoader()
            
            if qss_loader.is_style_manager_available():
                if self._is_dark_theme:
                    qss_loader.apply_dark_theme(create_backup=False)  # 实时切换时不创建备份
                    print("Switched to dark theme")
                else:
                    qss_loader.apply_light_theme(create_backup=False)  # 实时切换时不创建备份
                    print("Switched to light theme")
                
                # 实时应用主题，无需重启
                self.apply_theme_immediately()
            else:
                print("Warning: Style manager not available, cannot switch theme")
        except Exception as e:
            print(f"Theme switching failed: {e}")
    
    def apply_theme_immediately(self):
        """立即应用主题更改，无需重启"""
        try:
            from PySide6.QtWidgets import QApplication
            
            # 获取当前应用实例
            app = QApplication.instance()
            if app is not None:
                # 重新加载样式表
                qss_loader = QSSLoader()
                new_stylesheet = qss_loader.load_stylesheet("styles/fish.qss")
                
                # 方法1：应用到整个应用
                app.setStyleSheet(new_stylesheet)
                
                # 方法2：特别处理主窗口（通过parent()方法获取）
                parent_widget = self.parent()
                if parent_widget:
                    parent_widget.setStyleSheet(new_stylesheet)
                    self._force_update_widget(parent_widget)
                
                # 方法3：查找并更新所有窗口
                for widget in app.topLevelWidgets():
                    # 更新每个顶级窗口的样式表
                    widget.setStyleSheet(new_stylesheet)
                    self._force_update_widget(widget)
                
                # 方法4：强制重新处理所有事件，确保样式立即生效
                app.processEvents()
                
                # 方法5：使用repaint强制重绘
                for widget in app.topLevelWidgets():
                    try:
                        widget.repaint()
                        # 递归重绘所有子控件
                        for child in widget.findChildren(QWidget):
                            child.repaint()
                    except Exception:
                        pass
                
                print("Theme applied successfully")
            else:
                print("Warning: Cannot get application instance")
        except Exception as e:
            print(f"Failed to apply theme immediately: {e}")
    
    def _force_update_widget(self, widget):
        """强制更新单个控件及其所有子控件"""
        try:
            # 强制样式重新计算
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            
            # 安全调用update方法
            if hasattr(widget, 'update') and callable(widget.update):
                try:
                    widget.update()
                except TypeError:
                    # 如果update需要参数，跳过
                    pass
            
            # 递归更新所有子控件
            for child in widget.findChildren(QWidget):
                try:
                    child.style().unpolish(child)
                    child.style().polish(child)
                    if hasattr(child, 'update') and callable(child.update):
                        try:
                            child.update()
                        except TypeError:
                            # 如果update需要参数，跳过
                            pass
                except Exception:
                    # 忽略单个子控件的错误
                    continue
                
        except Exception as e:
            print(f"Failed to force update widget: {e}")
    
    def _update_child_widgets(self, parent):
        """递归更新所有子控件的样式"""
        try:
            for child in parent.findChildren(QWidget):
                child.style().unpolish(child)
                child.style().polish(child)
                child.update()
        except Exception as e:
            print(f"Failed to update child widgets: {e}")
    
    def is_dark_theme(self):
        """获取当前主题状态"""
        return self._is_dark_theme
    
    def set_dark_theme(self, is_dark):
        """设置主题状态"""
        if self._is_dark_theme != is_dark:
            self._is_dark_theme = is_dark
            self.update_circle_position()
            self.update()
    
    def get_circle_pos(self):
        return self._circle_pos
    
    def set_circle_pos(self, pos):
        self._circle_pos = pos
        self.update()
    
    circle_pos = Property(QPoint, get_circle_pos, set_circle_pos)


class MoreSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("More Settings")
        self.setFixedSize(450, 400)  # 稍微增大窗口以容纳主题切换
        self.parent = parent
        self.isReconstructUI = False
        
        self.config = read_config("config.ini")
        self.layout = QVBoxLayout()

        # 主题切换区域
        self.create_theme_section()

        # Scroll area setup
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Container widget for settings
        settings_container = QWidget()
        settings_layout = QVBoxLayout(settings_container)

        self.settings = dict(self.config.items("MoreSettings"))

        self.setting_inputs = {}

        # Create input fields for each setting
        for name, value in self.settings.items():
            label = QLabel(name)
            if value in ["True", "False"]:  # Check if the value is a boolean
                checkbox = QCheckBox()
                checkbox.setChecked(value == "True")
                settings_layout.addWidget(label)
                settings_layout.addWidget(checkbox)
                self.setting_inputs[name] = checkbox
            else:
                input_field = QLineEdit(value)
                settings_layout.addWidget(label)
                settings_layout.addWidget(input_field)
                self.setting_inputs[name] = input_field

        # Add the settings container to the scroll area
        scroll_area.setWidget(settings_container)

        # Add scroll area to the main layout
        self.layout.addWidget(scroll_area)

        # Add Save and Close buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(save_button)
        button_layout.addWidget(close_button)

        self.layout.addLayout(button_layout)
        self.setLayout(self.layout)

    def create_theme_section(self):
        """创建主题切换区域"""
        theme_widget = QWidget()
        theme_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
                margin: 5px;
            }
        """)
        
        theme_layout = QHBoxLayout(theme_widget)
        theme_layout.setContentsMargins(15, 10, 15, 10)
        
        # 主题标签和说明
        theme_info_layout = QVBoxLayout()
        
        theme_label = QLabel("应用主题")
        theme_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #495057;")
        
        theme_desc = QLabel("在亮色主题和暗色主题之间切换")
        theme_desc.setStyleSheet("font-size: 12px; color: #6c757d;")
        
        theme_info_layout.addWidget(theme_label)
        theme_info_layout.addWidget(theme_desc)
        theme_info_layout.addStretch()
        
        # 主题状态标签
        self.theme_status_label = QLabel("☀️ 亮色")
        self.theme_status_label.setStyleSheet("font-size: 12px; color: #495057; font-weight: bold;")
        
        # 主题切换开关
        self.theme_toggle = ThemeToggleSwitch()
        
        # 连接信号，更新状态标签
        def update_theme_status():
            if self.theme_toggle.is_dark_theme():
                self.theme_status_label.setText("🌙 暗色")
            else:
                self.theme_status_label.setText("☀️ 亮色")
        
        # 重写theme_changed方法以更新标签
        original_theme_changed = self.theme_toggle.theme_changed
        def enhanced_theme_changed():
            original_theme_changed()
            update_theme_status()
        self.theme_toggle.theme_changed = enhanced_theme_changed
        
        # 布局
        theme_layout.addLayout(theme_info_layout)
        theme_layout.addWidget(self.theme_status_label)
        theme_layout.addWidget(self.theme_toggle)
        
        self.layout.addWidget(theme_widget)

    def save_settings(self):
        # Update settings with input values
        new_settings = {}
        for name, input_field in self.setting_inputs.items():
            if isinstance(input_field, QCheckBox):  # Handle checkbox values
                new_settings[name] = "True" if input_field.isChecked() else "False"
            else:
                new_settings[name] = input_field.text()

        # Check if reconstructUI needs to be triggered
        if new_settings.get("maxrowsofbuttongroup") != self.settings.get("maxrowsofbuttongroup"):
            self.isReconstructUI = True

        # Update the config with new settings
        self.config["MoreSettings"] = new_settings
        write_config(self.config, "config.ini")
        self.parent.config = self.config

        # Reinitialize UI if needed
        if self.isReconstructUI:
            self.parent.modify_max_rows_of_button_group(int(new_settings.get("maxrowsofbuttongroup")))
        
        # self.close()
