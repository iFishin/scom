from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt

class ConfirmExitDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirm Exit")
        self.setModal(True)
        self.setLayout(QVBoxLayout())

        # 设置图标
        self.setWindowIcon(QIcon('favicon.ico'))
        
        icon_label = QLabel()
        icon = QIcon('favicon.ico').pixmap(100, 100)
        icon_label.setPixmap(icon)
        icon_label.setAlignment(Qt.AlignCenter)
        self.layout().addWidget(icon_label)

        label = QLabel("Are you sure you want to exit?")
        self.layout().addWidget(label)

        button_layout = QHBoxLayout()
        self.layout().addLayout(button_layout)

        yes_button = QPushButton("Yes")
        yes_button.clicked.connect(self.accept)
        button_layout.addWidget(yes_button)

        no_button = QPushButton("No")
        no_button.clicked.connect(self.reject)
        button_layout.addWidget(no_button)