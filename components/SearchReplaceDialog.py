import re
from PySide6 import QtWidgets, QtGui
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox, QDialog, QTextEdit,
    QMessageBox
)
from PySide6.QtGui import (
    QTextCursor, QTextCharFormat, QColor, QAction
)
from PySide6.QtCore import Qt

class SearchReplaceDialog(QDialog):
    def __init__(self, text_edit, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Search and Replace")
        self.text_edit = text_edit
        self.last_search = ""
        self.results = []
        self.current_result_index = -1
        self.case_sensitive_checkbox.setChecked(False)
        self.regex_checkbox.setChecked(False)
        self.whole_word_checkbox.setChecked(False)
        
        layout = QVBoxLayout(self)
        self.setMinimumWidth(500)

        # Search section
        search_layout = QHBoxLayout()
        self.search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.clear_highlights)
        self.search_button = QPushButton("Find")
        self.case_sensitive_checkbox = QCheckBox("Case sensitive")
        self.regex_checkbox = QCheckBox("Regex")
        self.whole_word_checkbox = QCheckBox("Whole word")

        search_layout.addWidget(self.search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        search_layout.addWidget(self.case_sensitive_checkbox)
        search_layout.addWidget(self.regex_checkbox)
        search_layout.addWidget(self.whole_word_checkbox)

        # Navigation buttons
        self.prev_button = QPushButton("↑")
        self.next_button = QPushButton("↓")
        search_layout.addWidget(self.prev_button)
        search_layout.addWidget(self.next_button)

        # Replace section
        replace_layout = QHBoxLayout()
        self.replace_label = QLabel("Replace:")
        self.replace_input = QLineEdit()
        self.replace_button = QPushButton("Replace")
        self.replace_all_button = QPushButton("Replace All")
        
        replace_layout.addWidget(self.replace_label)
        replace_layout.addWidget(self.replace_input)
        replace_layout.addWidget(self.replace_button)
        replace_layout.addWidget(self.replace_all_button)

        layout.addLayout(search_layout)
        layout.addLayout(replace_layout)

        # Connect signals
        self.search_button.clicked.connect(self.find_text)
        self.search_input.returnPressed.connect(self.find_text)
        self.prev_button.clicked.connect(self.prev_match)
        self.next_button.clicked.connect(self.next_match)
        self.replace_button.clicked.connect(self.replace)
        self.replace_all_button.clicked.connect(self.replace_all)

        # Initialize highlighting
        self.highlight_format = QTextCharFormat()
        self.highlight_format.setBackground(QColor(255, 255, 0))  # Yellow
        self.current_highlight_format = QTextCharFormat()
        self.current_highlight_format.setBackground(QColor(0, 255, 0))  # Green

    def get_flags(self):
        flags = 0
        if not self.case_sensitive_checkbox.isChecked():
            flags |= re.IGNORECASE
        if self.whole_word_checkbox.isChecked():
            return flags | re.UNICODE
        return flags

    def get_pattern(self):
        text = self.search_input.text()
        if not self.regex_checkbox.isChecked():
            text = re.escape(text)
        if self.whole_word_checkbox.isChecked():
            text = rf"\b{text}\b"
        return text

    def clear_highlights(self):
        self.text_edit.setExtraSelections([])

    def find_text(self):
        pattern = self.get_pattern()
        text = self.text_edit.toPlainText()
        flags = self.get_flags()

        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            QMessageBox.warning(self, "Regex Error", f"Invalid regular expression: {e}")
            return

        self.results = [match.span() for match in regex.finditer(text)]
        self.current_result_index = -1
        self.highlight_matches()

        if self.results:
            self.next_match()
        else:
            self.clear_highlights()

    def highlight_matches(self):
        selections = []
        cursor = self.text_edit.textCursor()
        current_pos = cursor.position()

        for i, (start, end) in enumerate(self.results):
            fmt = self.highlight_format
            if start <= current_pos <= end:
                fmt = self.current_highlight_format
                self.current_result_index = i

            selection = QtWidgets.QTextEdit.ExtraSelection()
            selection.format = fmt
            
            sel_cursor = self.text_edit.textCursor()
            sel_cursor.setPosition(start)
            sel_cursor.setPosition(end, QTextCursor.KeepAnchor)
            selection.cursor = sel_cursor
            selections.append(selection)

        self.text_edit.setExtraSelections(selections)

    def navigate_match(self, direction):
        if not self.results:
            return

        if self.current_result_index == -1:
            self.current_result_index = 0 if direction == 1 else len(self.results)-1
        else:
            self.current_result_index = (self.current_result_index + direction) % len(self.results)

        start, end = self.results[self.current_result_index]
        cursor = self.text_edit.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
        
        # Set the cursor to the current match
        self.text_edit.setTextCursor(cursor)
        self.text_edit.setFocus(Qt.TabFocusReason)
        self.text_edit.viewport().update()
        
        self.highlight_matches()
        

    def prev_match(self):
        self.navigate_match(-1)

    def next_match(self):
        self.navigate_match(1)

    def replace(self):
        if not self.results or self.current_result_index == -1:
            return

        start, end = self.results[self.current_result_index]
        cursor = self.text_edit.textCursor()
        cursor.beginEditBlock()

        # Get replacement text
        replacement = self.replace_input.text()
        if self.regex_checkbox.isChecked():
            try:
                match_text = self.text_edit.toPlainText()[start:end]
                replacement = re.sub(
                    self.get_pattern(),
                    replacement,
                    match_text,
                    flags=self.get_flags(),
                    count=1
                )
            except re.error as e:
                QMessageBox.warning(self, "Regex Error", f"Replacement error: {e}")
                return

        # Perform replacement
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
        cursor.insertText(replacement)
        cursor.endEditBlock()

        # Update results after replacement
        delta = len(replacement) - (end - start)
        self.results = [
            (s + delta if s > start else s, e + delta if e > start else e)
            for s, e in self.results
        ]

        self.find_text()  # Refresh search results

    def replace_all(self):
        text = self.text_edit.toPlainText()
        pattern = self.get_pattern()
        replacement = self.replace_input.text()
        flags = self.get_flags()

        try:
            new_text, count = re.subn(pattern, replacement, text, flags=flags)
        except re.error as e:
            QMessageBox.warning(self, "Regex Error", f"Replace all error: {e}")
            return

        if count > 0:
            cursor = self.text_edit.textCursor()
            cursor.beginEditBlock()
            cursor.select(QTextCursor.Document)
            cursor.insertText(new_text)
            cursor.endEditBlock()
            self.find_text()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        super().keyPressEvent(event)