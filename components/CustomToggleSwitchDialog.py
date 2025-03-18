import sys
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QColor, QFont


class FancyToggleButton(QLabel):
    def __init__(self):
        super().__init__()
        self.setFixedSize(200, 100)
        self.is_checked = False
        self.setText("Toggle Me")
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet('''
            QLabel {
                background-color: #ccc;
                border: 2px solid #000;
                border-radius: 50px;
                font-size: 20px;
                color: #000;
                padding: 10px;
            }
        ''')
        self.setMouseTracking(True)
        self.animation = QPropertyAnimation(self, b'geometry')
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.InOutQuart)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_checked = not self.is_checked
            self.toggle_animation()

    def toggle_animation(self):
        if self.is_checked:
            self.setText("ON")
            target_geometry = self.geometry()
            target_geometry.translate(100, 0)
            self.animation.setEndValue(target_geometry)
            self.setStyleSheet('''
                QLabel {
                    background-color: #007BFF;
                    border: 2px solid #000;
                    border-radius: 50px;
                    font-size: 20px;
                    color: white;
                    padding: 10px;
                }
            ''')
        else:
            self.setText("Toggle Me")
            target_geometry = self.geometry()
            target_geometry.translate(-100, 0)
            self.animation.setEndValue(target_geometry)
            self.setStyleSheet('''
                QLabel {
                    background-color: #ccc;
                    border: 2px solid #000;
                    border-radius: 50px;
                    font-size: 20px;
                    color: #000;
                    padding: 10px;
                }
            ''')
        self.animation.start()


class CustomToggleSwitchDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fancy Toggle Button Example")
        self.resize(400, 400)

        main_layout = QVBoxLayout()
        toggle_button = FancyToggleButton()
        main_layout.addWidget(toggle_button)

        self.setLayout(main_layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = CustomToggleSwitchDialog()
    dialog.show()
    sys.exit(app.exec())
