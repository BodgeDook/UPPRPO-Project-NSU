import sys
from PyQt5.QtWidgets import QApplication
from .welcome_window import WelcomeWindowSigned

if __name__ == '__main__':
    app = QApplication(sys.argv)
    print("Application initialized")
    is_signed_in = True
    if is_signed_in:
        welcome_window = WelcomeWindowSigned()
    else:
        pass  # welcome_window = WelcomeWindowUnsigned()
    welcome_window.show()
    print("Window shown, starting event loop")
    sys.exit(app.exec_())

'''
to launch the application:
python -m ui.main
'''