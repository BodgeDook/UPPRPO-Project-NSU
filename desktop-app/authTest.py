from PyQt5.QtWidgets import QApplication
from models.auth import AuthModel
from controllers.auth import AuthController
from views.auth import AuthView

import sys

def main():
    app = QApplication(sys.argv)

    # 1) Instantiate the model
    model = AuthModel()

    # 2) Instantiate the controller, passing the model
    auth_controller = AuthController(model)

    # 3) Instantiate the view, passing the controller
    auth_window = AuthView(auth_controller)

    # 4) Show the auth window
    auth_window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
