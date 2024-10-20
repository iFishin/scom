import re
from PySide6 import QtCore, QtWidgets, QtGui


class SearchReplaceDialog(QtWidgets.QDialog):
    def __init__(self, text_edit, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Search and Replace")
        self.text_edit = text_edit

        layout = QtWidgets.QVBoxLayout(self)

        # Search section
        search_layout = QtWidgets.QHBoxLayout()
        self.search_label = QtWidgets.QLabel("Search:")
        self.search_input = QtWidgets.QLineEdit()
        self.search_button = QtWidgets.QPushButton("Find")
        self.case_sensitive_checkbox = QtWidgets.QCheckBox("Case Sensitive")
        self.regex_checkbox = QtWidgets.QCheckBox("Regex")
        search_layout.addWidget(self.search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        search_layout.addWidget(self.case_sensitive_checkbox)
        search_layout.addWidget(self.regex_checkbox)

        # Replace section
        replace_layout = QtWidgets.QHBoxLayout()
        self.replace_label = QtWidgets.QLabel("Replace:")
        self.replace_input = QtWidgets.QLineEdit()
        self.replace_button = QtWidgets.QPushButton("Replace")
        self.replace_all_button = QtWidgets.QPushButton("Replace All")
        replace_layout.addWidget(self.replace_label)
        replace_layout.addWidget(self.replace_input)
        replace_layout.addWidget(self.replace_button)
        replace_layout.addWidget(self.replace_all_button)

        layout.addLayout(search_layout)
        layout.addLayout(replace_layout)

        self.search_button.clicked.connect(self.find_text)
        self.search_input.returnPressed.connect(self.find_text)
        self.replace_button.clicked.connect(self.replace_text)
        self.replace_all_button.clicked.connect(self.replace_all_text)

        self.up_button = QtWidgets.QPushButton("↑")
        self.down_button = QtWidgets.QPushButton("↓")
        search_layout.addWidget(self.up_button)
        search_layout.addWidget(self.down_button)

        self.up_button.clicked.connect(self.move_to_previous_result)
        self.down_button.clicked.connect(self.move_to_next_result)

        self.current_result_index = -1
        self.results = []

    def find_text(self):
        self.text_edit.setExtraSelections([])
        text_to_find = self.search_input.text()
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            cursor.setPosition(cursor.selectionEnd())
        self.text_edit.setTextCursor(cursor)

        doc = self.text_edit.document()
        found = False
        self.results = []
        regex_flags = 0
        if not self.case_sensitive_checkbox.isChecked():
            regex_flags |= re.IGNORECASE
        if self.regex_checkbox.isChecked():
            regex_str = re.compile(text_to_find, regex_flags)
        else:
            regex_str = re.compile(re.escape(text_to_find), regex_flags)
        text = doc.toPlainText()
        for match in regex_str.finditer(text):
            start = match.start()
            end = match.end()
            self.results.append(start)
            self.results.append(end)
            found = True
        if found:
            self.current_result_index = 0
            new_cursor = QtGui.QTextCursor(doc)
            new_cursor.setPosition(self.results[self.current_result_index])
            new_cursor.setPosition(self.results[self.current_result_index + 1], QtGui.QTextCursor.KeepAnchor)
            self.text_edit.setTextCursor(new_cursor)
            self.highlight_text(text_to_find)
        else:
            self.current_result_index = -1
            self.results = []

    def replace_text(self):
        if self.current_result_index != -1 and len(self.results) > self.current_result_index + 1:
            cursor = self.text_edit.textCursor()
            start = self.results[self.current_result_index]
            end = self.results[self.current_result_index + 1]
            cursor.setPosition(start)
            cursor.setPosition(end, QtGui.QTextCursor.KeepAnchor)
            cursor.insertText(self.replace_input.text())
            self.find_text()
            # Adjust the current result index to avoid out of range error
            if self.current_result_index >= len(self.results):
                self.current_result_index = len(self.results) - 2
            self.results[self.current_result_index] = start
            self.results[self.current_result_index + 1] = start + len(self.replace_input.text())

    def replace_all_text(self):
        text_to_find = self.search_input.text()
        replacement_text = self.replace_input.text()
        cursor = self.text_edit.textCursor()
        cursor.beginEditBlock()
        doc = self.text_edit.document()
        regex_flags = 0
        if not self.case_sensitive_checkbox.isChecked():
            regex_flags |= re.IGNORECASE
        if self.regex_checkbox.isChecked():
            regex_str = re.compile(text_to_find, regex_flags)
        else:
            regex_str = re.compile(re.escape(text_to_find), regex_flags)
        text = doc.toPlainText()
        for match in regex_str.finditer(text):
            start = match.start()
            end = match.end()
            cursor.setPosition(start)
            cursor.setPosition(end, QtGui.QTextCursor.KeepAnchor)
            cursor.insertText(replacement_text)
            # Adjust the positions of the remaining matches
            shift = len(replacement_text) - (end - start)
            for i in range(len(self.results)):
                if self.results[i] > start:
                    self.results[i] += shift
        cursor.endEditBlock()
        self.find_text()

    def move_to_previous_result(self):
        if self.results and len(self.results) > self.current_result_index + 1:
            self.current_result_index = (self.current_result_index - 2) % len(self.results)
            cursor = QtGui.QTextCursor(self.text_edit.document())
            start = self.results[self.current_result_index]
            end = self.results[self.current_result_index + 1]
            cursor.setPosition(start)
            cursor.setPosition(end, QtGui.QTextCursor.KeepAnchor)
            self.text_edit.setTextCursor(cursor)

    def move_to_next_result(self):
        if self.results and len(self.results) > self.current_result_index + 1:
            self.current_result_index = (self.current_result_index + 2) % len(self.results)
            cursor = QtGui.QTextCursor(self.text_edit.document())
            start = self.results[self.current_result_index]
            end = self.results[self.current_result_index + 1]
            cursor.setPosition(start)
            cursor.setPosition(end, QtGui.QTextCursor.KeepAnchor)
            self.text_edit.setTextCursor(cursor)

    def highlight_text(self, text):
        selections = []
        format = QtGui.QTextCharFormat()
        format.setBackground(QtGui.QColor("yellow"))
        regex_flags = 0
        if not self.case_sensitive_checkbox.isChecked():
            regex_flags |= re.IGNORECASE
        if self.regex_checkbox.isChecked():
            regex = re.compile(text, regex_flags)
        else:
            regex = re.compile(re.escape(text), regex_flags)
        for match in regex.finditer(self.text_edit.toPlainText()):
            start = match.start()
            end = match.end()
            selection = QtWidgets.QTextEdit.ExtraSelection()
            selection.format = format
            selection.cursor = QtGui.QTextCursor(self.text_edit.document())
            selection.cursor.setPosition(start)
            selection.cursor.setPosition(end, QtGui.QTextCursor.KeepAnchor)
            selections.append(selection)
        self.text_edit.setExtraSelections(selections)