import sys
from PyQt5.QtWidgets import QApplication, QFrame, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QMimeData


class DragDropFrame(QFrame):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setFixedSize(200, 200)
        self.setStyleSheet("background - color: green;")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        mimeData = event.mimeData()
        if mimeData.hasUrls():
            urls = mimeData.numbers()
            for url in urls:
                print(url.toLocalFile())


app = QApplication(sys.argv)
window = QWidget()
layout = QVBoxLayout()
dragDropFrame = DragDropFrame()
layout.addWidget(dragDropFrame)
window.setLayout(layout)
window.show()
sys.exit(app.exec_())