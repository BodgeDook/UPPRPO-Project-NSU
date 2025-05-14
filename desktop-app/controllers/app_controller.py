from views.welcome import WelcomeWindow
from views.editor import EditorWindow
from views.settings import SettingsDialog
# from views.auth import AuthDialog
from controllers.auth import AuthController


class AppController:
    def __init__(self):

        self.welcome = WelcomeWindow()
        self.editor = EditorWindow()
        self.settings = SettingsDialog(parent=None)  # floating dialog
        # self.auth = AuthDialog(parent=self.welcome)

        # connect Welcome → open project/new project
        self.welcome.open_project_requested.connect(self._open_editor)
        self.welcome.new_project_requested.connect(self._open_editor)
        # connect Welcome → login/register
        self.welcome.login_requested.connect(self._show_login)
        self.welcome.settings_requested.connect(self.settings.exec_)

        # connect Editor → settings
        # parent can be main editor window so dialog stays on top
        # self.editor_settings_slot = lambda: self.settings.exec_()
        self.editor.settings_requested.connect(self.settings.exec_)
        self.editor.closed.connect(self.welcome.show)

    def start(self):
        self.welcome.show()

    def _open_editor(self, project_path=None):
        self.welcome.close()    # might need to change to hide()
        # if editor already exists, close or switch project
        if self.editor:
            self.editor.close()
        self.editor = EditorWindow(project=project_path)
        # make sure closing *this* editor brings back the welcome screen
        self.editor.closed.connect(self.welcome.show)
        # wire settings and maybe logout back to welcome
        self.editor.settings_requested.connect(self.settings.exec_)
        self.editor.show()

    # def _show_login(self):
    #     # 1) Instantiate AuthController, passing the welcome window as parent
    #     auth_ctrl = AuthController(parent=self.welcome)

    #     # 2) Show the dialog modally and check the result
    #     result = auth_ctrl.view.exec_()
    #     if result == auth_ctrl.view.Accepted:
    #         # user logged in successfully
    #         print("User is now authenticated")
    #     else:
    #         print("Login cancelled or failed")
    
    def _show_login(self):
        auth = AuthController(parent=self.welcome)
        if auth.exec_() == QDialog.Accepted:
            print("Logged in!")
        else:
            print("Did not log in.")