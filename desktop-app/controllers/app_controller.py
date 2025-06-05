# desktop-app/controllers/app_controller.py

from PyQt5.QtWidgets import QApplication
from views.welcome import WelcomeWindow
from views.editor import EditorWindow
from views.settings import SettingsDialog
from views.auth import AuthView  # If you show auth from here, otherwise import your AuthController and AuthView where needed
# If you have a separate AuthController inside controllers/auth.py, you can instantiate it in main.py or here.

from models.project import Project  # Your own Project class for loading/creating

class AppController:
    def __init__(self):
        # 1) Create the “Welcome” screen
        self.welcome = WelcomeWindow()

        # 2) Initially, no editor is open
        self.editor = None

        # 3) Create a single SettingsDialog (modal). We’ll only exec_() it when needed.
        self.settings = SettingsDialog(parent=None)

        # 4) (Optional) if you launch login from AppController, you might instantiate AuthController/AuthView here.
        #    But since you have an AuthView already, you could also do that from main.py.
        #    For now, leave it out, or do:
        # from controllers.auth import AuthController
        # from view.auth import AuthView
        # model = AuthModel()
        # self.auth_ctrl = AuthController(model)
        # self.auth_view = AuthView(self.auth_ctrl)

        # — Connect WelcomeWindow signals to our slots —
        self.welcome.open_project_requested.connect(self._open_editor)
        self.welcome.new_project_requested.connect(self._open_editor)
        self.welcome.login_requested.connect(self._show_login)

        # If you want Settings from Welcome (rare), you could also do:
        # self.welcome.settings_requested.connect(lambda: self.settings.exec_())

    def start(self):
        """ Show the welcome screen when the app starts. """
        self.welcome.show()

    def _show_login(self):
        """
        If you want to handle login/register here, do something like:
          auth_model = AuthModel()
          self.auth_ctrl = AuthController(auth_model)
          self.auth_view = AuthView(self.auth_ctrl)
          self.auth_view.show()
        Or, if you already did that in __init__, simply:
          self.auth_view.show()
        """
        # Example (uncomment if you wired AuthView here):
        # self.auth_view.show()
        pass

    def _open_editor(self, project_path=None):
        """
        Called when the user clicks “Open Project” or “New Project” on the welcome screen.

        If project_path is None → new project; otherwise → load from file.
        """

        # 1) If there is already an EditorWindow open, close it first
        if self.editor:
            self.editor.close()
            self.editor = None

        # 2) Load/create the Project model
        if project_path:
            project = Project.load_from_file(project_path)
        else:
            project = Project.create_new()  # however you create an empty project

        # 3) Instantiate EditorWindow with the project
        self.editor = EditorWindow(project=project)

        # 4) Whenever the user clicks “Settings” inside the editor, pop up our single SettingsDialog
        self.editor.settings_requested.connect(self.settings.exec_)

        # 5) Show the editor and hide the welcome screen
        self.editor.show()
        self.welcome.close()
