from PySide6.QtWidgets import QGroupBox, QApplication
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QDrag

class DraggableGroupBox(QGroupBox):
    def __init__(self, title="", parent=None):
        super().__init__(title, parent)
        self.setAcceptDrops(True)
        self.drag_start_position = None
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
            
        if not self.drag_start_position:
            return
            
        # 计算拖动距离
        distance = (event.pos() - self.drag_start_position).manhattanLength()
        if distance < QApplication.startDragDistance():
            return
            
        # 创建拖动对象
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self.title())
        drag.setMimeData(mime_data)
        
        # 执行拖动
        drag.exec_(Qt.MoveAction)
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()
            
    def dropEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
            # 交换位置
            source = event.source()
            if source and source != self:
                parent_layout = self.parent().layout()
                if parent_layout:
                    source_index = parent_layout.indexOf(source)
                    target_index = parent_layout.indexOf(self)
                    if source_index != -1 and target_index != -1:
                        parent_layout.removeWidget(source)
                        parent_layout.removeWidget(self)
                        parent_layout.addWidget(source, target_index // parent_layout.columnCount(),
                                              target_index % parent_layout.columnCount())
                        parent_layout.addWidget(self, source_index // parent_layout.columnCount(),
                                             source_index % parent_layout.columnCount())
        else:
            event.ignore()
        
    def mouseReleaseEvent(self, event):
        self.drag_start_position = None
        super().mouseReleaseEvent(event) 