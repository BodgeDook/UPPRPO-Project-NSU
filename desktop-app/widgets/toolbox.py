# desktop-app/widgets/toolbox.py
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton

class ToolboxWidget(QWidget):
    tool_selected = pyqtSignal(str)  # “Select”, “Cut”, “Trim”, etc.

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(150)

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addStretch(1)
