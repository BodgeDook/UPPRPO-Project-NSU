# desktop-app/widgets/toolbox.py
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt5.QtWidgets import QLabel, QListWidget

class ToolboxWidget(QWidget):
    tool_selected = pyqtSignal(str)  # “Select”, “Cut”, “Trim”, etc.
    asset_selected = pyqtSignal(str)  # emits the asset_rel_path

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(200)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # — Tools —
        layout.addWidget(QLabel("Tools"))
        tools = ["Select", "Cut", "Trim", "Razor"]
        for t in tools:
            btn = QPushButton(t)
            btn.clicked.connect(lambda _, name=t: self.tool_selected.emit(name))
            layout.addWidget(btn)

        layout.addSpacing(10)
        # — Assets —
        layout.addWidget(QLabel("Assets"))
        self.asset_list = QListWidget()
        self.asset_list.itemClicked.connect(
            lambda item: self.asset_selected.emit(item.text())
        )
        layout.addWidget(self.asset_list)

        layout.addStretch(1)
    
    def set_assets(self, asset_rel_list):
        """Repopulate the asset list."""
        self.asset_list.clear()
        for rel in asset_rel_list:
            self.asset_list.addItem(rel)