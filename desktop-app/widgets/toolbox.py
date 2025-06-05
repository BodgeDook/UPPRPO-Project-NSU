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

        tools = ["Select", "Cut", "Trim", "Razor"]
        for t in tools:
            btn = QPushButton(t)
            btn.clicked.connect(lambda checked, name=t: self.tool_selected.emit(name))
            layout.addWidget(btn)

        layout.addStretch(1)
