from windows.welcome import WelcomeWindow
from windows.editor import EditorWindow
from windows.settings import SettingsDialog
from windows.login import LoginDialog

class AppController:
    def __init__(self):

        self.welcome = WelcomeWindow()
        self.editor = EditorWindow()
        self.settings = SettingsDialog(parent=None)  # floating dialog
        self.login = LoginDialog(parent=self.welcome)

        # connect Welcome → open project/new project
        self.welcome.open_project_requested.connect(self._open_editor)
        self.welcome.new_project_requested.connect(self._open_editor)
        # connect Welcome → login/register
        self.welcome.login_requested.connect(self.login.exec_)
        self.welcome.settings_requested.connect(self.settings.exec_)

        # connect Editor → settings
        # parent can be main editor window so dialog stays on top
        # self.editor_settings_slot = lambda: self.settings.exec_()
        self.editor.settings_requested.connect(self.settings.exec_)
        self.editor.closed.connect(self.welcome.show)

    def start(self):
        self.welcome.show()

    def _open_editor(self, project_path=None):
        # if editor already exists, close or switch project
        if self.editor:
            self.editor.close()
        self.editor = EditorWindow(project=project_path)
        # make sure closing *this* editor brings back the welcome screen
        self.editor.closed.connect(self.welcome.show)
        # wire settings and maybe logout back to welcome
        self.editor.settings_requested.connect(self.settings.exec_)
        self.editor.show()
        self.welcome.close()
