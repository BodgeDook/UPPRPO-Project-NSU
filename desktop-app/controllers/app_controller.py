# from views.welcome import WelcomeWindow
# from views.editor import EditorWindow
# from views.settings import SettingsDialog
# # from views.auth import AuthDialog
# from controllers.auth import AuthController

# from PyQt5.QtWidgets import QDialog 

# class AppController:
#     def __init__(self):

#         self.welcome = WelcomeWindow()
#         self.editor = EditorWindow()
#         self.settings = SettingsDialog(parent=None)  # floating dialog
#         # self.auth = AuthDialog(parent=self.welcome)

#         # connect Welcome → open project/new project
#         self.welcome.open_project_requested.connect(self._open_editor)
#         self.welcome.new_project_requested.connect(self._open_editor)
#         # connect Welcome → login/register
#         self.welcome.login_requested.connect(self._show_login)
#         self.welcome.settings_requested.connect(self.settings.exec_)

#         # connect Editor → settings
#         # parent can be main editor window so dialog stays on top
#         # self.editor_settings_slot = lambda: self.settings.exec_()
#         self.editor.settings_requested.connect(self.settings.exec_)
#         self.editor.closed.connect(self.welcome.show)

#     def start(self):
#         self.welcome.show()

#     def _open_editor(self, project_path=None):
#         self.welcome.close()    # might need to change to hide()
#         # if editor already exists, close or switch project
#         if self.editor:
#             self.editor.close()
#         self.editor = EditorWindow(project=project_path)
#         # make sure closing *this* editor brings back the welcome screen
#         self.editor.closed.connect(self.welcome.show)
#         # wire settings and maybe logout back to welcome
#         self.editor.settings_requested.connect(self.settings.exec_)
#         self.editor.show()

#     # def _show_login(self):
#     #     # 1) Instantiate AuthController, passing the welcome window as parent
#     #     auth_ctrl = AuthController(parent=self.welcome)

#     #     # 2) Show the dialog modally and check the result
#     #     result = auth_ctrl.view.exec_()
#     #     if result == auth_ctrl.view.Accepted:
#     #         # user logged in successfully
#     #         print("User is now authenticated")
#     #     else:
#     #         print("Login cancelled or failed")
    
#     def _show_login(self):
#         auth = AuthController(parent=self.welcome)
#         if auth.exec_() == QDialog.Accepted:
#             print("Logged in!")
#         else:
#             print("Did not log in.")


# desktop-app/controllers/auth.py
from PyQt5.QtCore import QObject, pyqtSignal
# from models.auth import AuthService
from controllers.auth import AuthController
# from view.auth import LoginDialog

class AuthController(QObject):
    login_succeeded = pyqtSignal()  # let AppController know we can proceed
    login_failed = pyqtSignal(str)  # passes error message
    register_succeeded = pyqtSignal()
    register_failed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dialog = LoginDialog(parent=None)
        self.dialog.login_attempt.connect(self._on_login_attempt)
        self.dialog.register_attempt.connect(self._on_register_attempt)

        # connect our internal success/fail to close dialog or show error
        self.login_succeeded.connect(self.dialog.accept)
        self.login_failed.connect(self.dialog.notify_failure)
        self.register_succeeded.connect(self.dialog.accept)
        self.register_failed.connect(self.dialog.notify_failure)

    def show_login(self):
        return self.dialog.exec_()  # modal

    def _on_login_attempt(self, user, pwd):
        if AuthService.login(user, pwd):
            self.login_succeeded.emit()
        else:
            self.login_failed.emit("Invalid username or password.")

    def _on_register_attempt(self, user, pwd):
        if AuthService.register(user, pwd):
            self.register_succeeded.emit()
        else:
            self.register_failed.emit("Username already taken.")
