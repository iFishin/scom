import sys
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QRect, Property
from PySide6.QtGui import QPainter, QColor, QFont, QPainterPath


class FancyToggleButton(QLabel):
    def __init__(self):
        super().__init__()
        self.setFixedSize(80, 40)  # 更合适的尺寸比例
        self._is_checked = False
        self._circle_pos = QPoint(5, 5)  # 初始位置
        self.circle_size = 30  # 圆形按钮大小
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)  # 设置手型光标
        
        # Create animation
        self.animation = QPropertyAnimation(self, b"circle_pos")
        self.animation.setDuration(250)  # 稍微慢一点的动画
        self.animation.setEasingCurve(QEasingCurve.OutQuart)  # 更流畅的缓动
        
        # 初始化位置
        self.update_circle_position()

    def update_circle_position(self):
        """更新圆形按钮的位置"""
        y_center = (self.height() - self.circle_size) / 2
        if self._is_checked:
            x_pos = self.width() - self.circle_size - 5
        else:
            x_pos = 5
        self._circle_pos = QPoint(x_pos, y_center)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制背景轨道
        track_rect = QRect(0, 0, self.width(), self.height())
        track_color = QColor("#4CAF50") if self._is_checked else QColor("#e0e0e0")
        
        # 绘制阴影效果
        shadow_rect = QRect(2, 2, self.width() - 2, self.height() - 2)
        painter.setBrush(QColor(0, 0, 0, 30))  # 半透明黑色阴影
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(shadow_rect, self.height()/2, self.height()/2)
        
        # 绘制主背景
        painter.setBrush(track_color)
        painter.drawRoundedRect(track_rect, self.height()/2, self.height()/2)
        
        # 绘制内部轨道（凹陷效果）
        inner_rect = QRect(3, 3, self.width() - 6, self.height() - 6)
        inner_color = QColor("#45a049") if self._is_checked else QColor("#d0d0d0")
        painter.setBrush(inner_color)
        painter.drawRoundedRect(inner_rect, (self.height()-6)/2, (self.height()-6)/2)
        
        # 绘制圆形按钮
        button_rect = QRect(
            self._circle_pos.x(), 
            self._circle_pos.y(), 
            self.circle_size, 
            self.circle_size
        )
        
        # 按钮阴影
        shadow_button_rect = QRect(
            self._circle_pos.x() + 1, 
            self._circle_pos.y() + 1, 
            self.circle_size, 
            self.circle_size
        )
        painter.setBrush(QColor(0, 0, 0, 50))
        painter.drawEllipse(shadow_button_rect)
        
        # 按钮渐变效果
        from PySide6.QtGui import QLinearGradient
        gradient = QLinearGradient(0, self._circle_pos.y(), 0, self._circle_pos.y() + self.circle_size)
        gradient.setColorAt(0, QColor("#ffffff"))
        gradient.setColorAt(0.5, QColor("#f8f8f8"))
        gradient.setColorAt(1, QColor("#e8e8e8"))
        
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(button_rect)
        
        # 按钮边框
        painter.setPen(QColor("#d0d0d0"))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(button_rect)
        
        # 绘制状态指示点（可选）
        if self._is_checked:
            indicator_rect = QRect(
                self._circle_pos.x() + self.circle_size//2 - 3,
                self._circle_pos.y() + self.circle_size//2 - 3,
                6, 6
            )
            painter.setBrush(QColor("#4CAF50"))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(indicator_rect)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_checked = not self._is_checked
            self.toggle_animation()

    def toggle_animation(self):
        """执行切换动画"""
        y_center = (self.height() - self.circle_size) / 2
        
        if self._is_checked:
            start_x = 5
            end_x = self.width() - self.circle_size - 5
        else:
            start_x = self.width() - self.circle_size - 5
            end_x = 5
            
        self.animation.setStartValue(QPoint(start_x, y_center))
        self.animation.setEndValue(QPoint(end_x, y_center))
        self.animation.start()

    def mousePressEvent(self, event):
        """鼠标按下效果"""
        if event.button() == Qt.LeftButton:
            # 可以添加按下时的视觉反馈
            self.update()

    def enterEvent(self, event):
        """鼠标悬停效果"""
        self.update()

    def leaveEvent(self, event):
        """鼠标离开效果"""
        self.update()

    def is_checked(self):
        """获取开关状态"""
        return self._is_checked
    
    def set_checked(self, checked):
        """设置开关状态"""
        if self._is_checked != checked:
            self._is_checked = checked
            self.update_circle_position()
            self.update()

    def get_circle_pos(self):
        return self._circle_pos

    def set_circle_pos(self, pos):
        self._circle_pos = pos
        self.update()

    circle_pos = Property(QPoint, get_circle_pos, set_circle_pos)


class CustomToggleSwitchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enhanced Toggle Switch")
        self.setFixedSize(350, 300)
        self.setWindowFlag(Qt.FramelessWindowHint)
        
        # Set dialog style
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border: 2px solid #dee2e6;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(25)
        
        # Add title
        title = QLabel("Enhanced Toggle Switch")
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #495057; margin-bottom: 10px;")
        main_layout.addWidget(title)
        
        # Add multiple toggle buttons for demonstration
        toggle_layout = QVBoxLayout()
        toggle_layout.setSpacing(20)
        
        # First toggle with label
        toggle1_layout = QHBoxLayout()
        toggle1_label = QLabel("Feature 1:")
        toggle1_label.setStyleSheet("color: #6c757d; font-weight: bold;")
        self.toggle1 = FancyToggleButton()
        toggle1_layout.addWidget(toggle1_label)
        toggle1_layout.addStretch()
        toggle1_layout.addWidget(self.toggle1)
        toggle_layout.addLayout(toggle1_layout)
        
        # Second toggle with label
        # toggle2_layout = QHBoxLayout()
        # toggle2_label = QLabel("Feature 2:")
        # toggle2_label.setStyleSheet("color: #6c757d; font-weight: bold;")
        # self.toggle2 = FancyToggleButton()
        # self.toggle2.set_checked(True)  # 默认开启
        # toggle2_layout.addWidget(toggle2_label)
        # toggle2_layout.addStretch()
        # toggle2_layout.addWidget(self.toggle2)
        # toggle_layout.addLayout(toggle2_layout)
        
        main_layout.addLayout(toggle_layout)
        
        # Add description
        description = QLabel("Click the switches to toggle between ON and OFF states.\nNotice the smooth animation and visual feedback.")
        description.setAlignment(Qt.AlignCenter)
        description.setStyleSheet("color: #6c757d; line-height: 1.4;")
        main_layout.addWidget(description)

        # Add buttons
        button_layout = QHBoxLayout()
        
        reset_button = QPushButton("Reset All")
        reset_button.setFixedWidth(120)
        reset_button.clicked.connect(self.reset_toggles)
        
        close_button = QPushButton("Close")
        close_button.setFixedWidth(120)
        close_button.clicked.connect(self.close)
        
        button_layout.addWidget(reset_button)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
    
    def reset_toggles(self):
        """重置所有开关"""
        self.toggle1.set_checked(False)
        # self.toggle2.set_checked(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = CustomToggleSwitchDialog()
    dialog.show()
    sys.exit(app.exec())
