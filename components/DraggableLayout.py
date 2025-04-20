from PySide6.QtWidgets import QGridLayout
from PySide6.QtCore import Qt

class DraggableLayout(QGridLayout):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSpacing(10)
        self.setContentsMargins(10, 10, 10, 10)
        
    def addWidget(self, widget, row, column, rowSpan=1, columnSpan=1):
        super().addWidget(widget, row, column, rowSpan, columnSpan)
        
    def removeWidget(self, widget):
        super().removeWidget(widget)
        
    def itemAtPosition(self, row, column):
        return super().itemAtPosition(row, column)
        
    def indexOf(self, widget):
        return super().indexOf(widget)
        
    def count(self):
        return super().count()
        
    def itemAt(self, index):
        return super().itemAt(index)
        
    def takeAt(self, index):
        return super().takeAt(index)
        
    def addItem(self, item):
        super().addItem(item)
        
    def setAlignment(self, alignment):
        super().setAlignment(alignment)
        
    def setSpacing(self, spacing):
        super().setSpacing(spacing)
        
    def setContentsMargins(self, left, top, right, bottom):
        super().setContentsMargins(left, top, right, bottom) 