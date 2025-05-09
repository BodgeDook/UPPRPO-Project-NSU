import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QVBoxLayout

from auth_window import AuthWindow, AuthViewModel, AuthModel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Main Window")
        self.resize(400, 300)

        self.second_window = None  # Keep a reference to avoid garbage collection

        self.button = QPushButton("Login", self)
        self.button.clicked.connect(self.open_secondary_window)

        # self.button = QPushButton("NewProject", self)
        # self.button.clicked.connect(self.open_main_window)

    def open_secondary_window(self):
        if not self.second_window or not self.second_window.isVisible():
            model = AuthModel()
            view_model = AuthViewModel(model)
            self.second_window = AuthWindow(view_model)
            self.second_window.show()  # Show the new window

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec_())
