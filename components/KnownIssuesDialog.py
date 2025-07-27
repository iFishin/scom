from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QPushButton,
    QHBoxLayout,
    QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl


class KnownIssuesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("knownIssuesDialog")
        self.setWindowTitle("Known Issues")
        self.setFixedSize(500, 220)
        self.setWindowFlag(Qt.FramelessWindowHint)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Information label
        info_label = QLabel(
            "Click the button below to view known issues and their solutions. "
        )
        info_label.setAlignment(Qt.AlignCenter)

        # Open button
        open_btn = QPushButton("View Known Issues")
        open_btn.clicked.connect(self.open_known_issues)
        open_btn.setFixedSize(150, 40)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        close_btn.setFixedSize(150, 40)

        # Button layout
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)
        btn_layout.addStretch()
        btn_layout.addWidget(open_btn)
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()

        # Combine layouts
        main_layout.addWidget(info_label)
        main_layout.addStretch()
        main_layout.addLayout(btn_layout)
        main_layout.addStretch()
        self.setLayout(main_layout)

        # Style settings
        self.setStyleSheet("""
            QDialog {
                background: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
            }
            QPushButton {
                background: #00A67C;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
            }
            QPushButton:hover { background: #008F6B; }
            QPushButton:pressed { background: #007755; }
            QLabel {
                font-family: 'Microsoft YaHei';
                font-size: 14px;
                color: #333;
            }
        """)

    def open_known_issues(self):
        """Open the Known Issues page on GitHub"""
        github_url = "https://github.com/iFishin/scom/blob/main/KNOWN_ISSUES.md"
        try:
            QDesktopServices.openUrl(QUrl(github_url))
        except Exception as e:
            self.show_error_message(f"Failed to open URL: {str(e)}")

    def show_error_message(self, message):
        """Display an error message dialog"""
        error_dialog = QDialog(self)
        error_dialog.setWindowTitle("Error")
        error_dialog.setFixedSize(300, 150)

        # Error dialog layout
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        # Error message label
        label = QLabel(message)
        label.setAlignment(Qt.AlignCenter)

        # Close button for error dialog
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(error_dialog.close)
        close_btn.setFixedSize(100, 35)

        layout.addWidget(label)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
        error_dialog.setLayout(layout)
        error_dialog.exec()
