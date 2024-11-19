import os
import sys
from PyQt5.QtWidgets import QFrame


class DragDropFrame(QFrame):
    def __init__(self, width, height, color):
        super().__init__()
        self.setAcceptDrops(True)
        self.setFixedSize(width, height)
        self.setStyleSheet(f"background-color: {color};")
        self.handler = None

    def setHandler(self, handler):
        self.handler = handler

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        self.handler(event)
