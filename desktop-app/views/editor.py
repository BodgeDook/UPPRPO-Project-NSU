from PyQt5.QtWidgets import QMainWindow, QAction, QTextEdit
from PyQt5.QtCore import pyqtSignal

class EditorWindow(QMainWindow):
    settings_requested = pyqtSignal()
    closed = pyqtSignal()

    def __init__(self, project=None):
        super().__init__()
        self.setWindowTitle("Video Editor")
        self.resize(1000, 700)

        # Example: timeline + preview stub
        self.editor = QTextEdit()
        self.editor.setPlaceholderText(f"Project loaded: {project or 'New Project'}")
        self.setCentralWidget(self.editor)

        # Menu
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.settings_requested.emit)
        file_menu.addAction(settings_action)
    
    def closeEvent(self, event):
        # Emit our “closed” signal, then run the normal close logic
        self.closed.emit()
        super().closeEvent(event)
