import sys, os
from PyQt5.QtWidgets import QApplication
from controllers.app_controller import AppController

sys.path.append(os.path.dirname(__file__))

def main():
    app = QApplication(sys.argv)
    controller = AppController()
    controller.start()          # shows the welcome window
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
