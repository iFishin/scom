import sys
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QRect, Property
from PySide6.QtGui import QPainter, QColor, QFont, QPainterPath


class FancyToggleButton(QLabel):
    def __init__(self):
        super().__init__()
        self.setFixedSize(120, 60)
        self._is_checked = False
        self._circle_pos = QPoint(10, 10)
        self.circle_size = 40
        self.setMouseTracking(True)
        
        # Create animation
        self.animation = QPropertyAnimation(self, b"circle_pos")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.update_style()

    def update_style(self):
        self.setStyleSheet(f'''
            QLabel {{
                background-color: {"#4CAF50" if self._is_checked else "#e0e0e0"};
                border: none;
                border-radius: 30px;
                font-size: 14px;
                color: {"white" if self._is_checked else "#666"};
                font-weight: bold;
            }}
        ''')

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 30, 30)
        painter.fillPath(path, QColor("#4CAF50" if self._is_checked else "#e0e0e0"))
            
        # Draw circle
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("white"))
        # Calculate vertical center position
        y_center = (self.height() - self.circle_size) / 2
        circle_pos = QPoint(self._circle_pos.x(), y_center)
        painter.drawEllipse(circle_pos, self.circle_size/2, self.circle_size/2)
        
        # Draw text
        painter.setPen(QColor("white" if self._is_checked else "#666"))
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, "ON" if self._is_checked else "OFF")

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_checked = not self._is_checked
            self.toggle_animation()

    def toggle_animation(self):
        # Calculate vertical center position
        y_center = (self.height() - self.circle_size) / 2
        if self._is_checked:
            self.animation.setStartValue(QPoint(10, y_center))
            self.animation.setEndValue(QPoint(self.width() - self.circle_size - 10, y_center))
        else:
            self.animation.setStartValue(QPoint(self.width() - self.circle_size + 10, y_center))
            self.animation.setEndValue(QPoint(10, y_center))
            
        self.animation.start()
        self.update_style()
        self.update()

    def get_circle_pos(self):
        return self._circle_pos

    def set_circle_pos(self, pos):
        self._circle_pos = pos
        self.update()

    circle_pos = Property(QPoint, get_circle_pos, set_circle_pos)


class CustomToggleSwitchDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Toggle Switch Example")
        self.setFixedSize(300, 250)
        self.setWindowFlag(Qt.FramelessWindowHint)
        
        # Set dialog style
        self.setStyleSheet("""
            QDialog {
                background-color: white;
                border-radius: 10px;
                border: 2px solid #888;
            }
            QPushButton {
                background-color: #6699cc;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5588bb;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Add title
        title = QLabel("Toggle Switch")
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)
        
        # Add toggle button
        toggle_button = FancyToggleButton()
        main_layout.addWidget(toggle_button, alignment=Qt.AlignCenter)
        
        # Add description
        description = QLabel("Click to toggle between ON and OFF states")
        description.setAlignment(Qt.AlignCenter)
        description.setStyleSheet("color: #666;")
        main_layout.addWidget(description)

        # Add close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.setFixedWidth(100)
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = CustomToggleSwitchDialog()
    dialog.show()
    sys.exit(app.exec())
