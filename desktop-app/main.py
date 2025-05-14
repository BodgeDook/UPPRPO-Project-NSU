import sys
from PyQt5.QtWidgets import QApplication
from app_controller import AppController

def main():
    app = QApplication(sys.argv)
    controller = AppController()
    controller.start()          # shows the welcome window
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
