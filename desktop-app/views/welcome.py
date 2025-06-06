# from PyQt5.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QAction
# from PyQt5.QtCore import pyqtSignal

# class WelcomeWindow(QMainWindow):
#     # Declare signals the controller can connect to
#     open_project_requested = pyqtSignal(str)  # could send project path
#     new_project_requested = pyqtSignal()
#     login_requested = pyqtSignal()
#     settings_requested = pyqtSignal()


#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("Welcome")

#         # UI
#         layout = QVBoxLayout()
#         open_button = QPushButton("Open Project")
#         new_button = QPushButton("New Project")
#         login_button = QPushButton("Log In")

#         open_button.clicked.connect(lambda: self.open_project_requested.emit("dummy/path"))
#         new_button.clicked.connect(self.new_project_requested.emit)
#         login_button.clicked.connect(self.login_requested.emit)

#         container = QWidget()
#         layout.addWidget(open_button)
#         layout.addWidget(new_button)
#         layout.addWidget(login_button)
#         container.setLayout(layout)

#         self.setCentralWidget(container)

#         # Menu
#         menubar = self.menuBar()
#         file_menu = menubar.addMenu("File")
#         settings_action = QAction("Settings", self)
#         settings_action.triggered.connect(self.settings_requested.emit)
#         file_menu.addAction(settings_action)




# desktop-app/view/welcome.py
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton

class WelcomeWindow(QMainWindow):
    open_project_requested = pyqtSignal(str)  # path to an existing project file
    new_project_requested = pyqtSignal()      # create a brand-new project
    login_requested = pyqtSignal()            # open the login dialog

    def __init__(self):
        super().__init__()
        self.setWindowTitle("uMovie – Welcome")
        self.resize(400, 200)

        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)

        btn_open = QPushButton("Open Project…")
        btn_new  = QPushButton("Create New Project")
        btn_login = QPushButton("Log In / Register")

        layout.addWidget(btn_open)
        layout.addWidget(btn_new)
        layout.addWidget(btn_login)
        layout.addStretch(1)

        btn_open.clicked.connect(self._on_open_clicked)
        btn_new.clicked.connect(self.new_project_requested.emit)
        btn_login.clicked.connect(self.login_requested.emit)

        self.setCentralWidget(container)

    def _on_open_clicked(self):
        from PyQt5.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "Open uMovie Project", filter="uMovie (*.json)")
        if path:
            self.open_project_requested.emit(path)
