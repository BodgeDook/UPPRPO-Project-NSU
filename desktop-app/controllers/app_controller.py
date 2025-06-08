import os
from PyQt5.QtWidgets import QFileDialog, QDialog, QVBoxLayout
from PyQt5.QtCore import QStandardPaths

from views.welcome import WelcomeWindow
from views.editor import EditorWindow
from views.settings import SettingsDialog
from views.auth import AuthView
from controllers.auth import AuthController
from models.auth import AuthModel
from models.project import Project


class AppController:
    def __init__(self):
        self.welcome = WelcomeWindow()
        self.editor = None
        self.settings = SettingsDialog(parent=None)
        self.auth_model = AuthModel()
        self.auth_controller = AuthController(self.auth_model)

        # Wire welcome signals
        self.welcome.open_project_requested.connect(self._open_editor)
        self.welcome.new_project_requested.connect(self._new_project)
        self.welcome.login_requested.connect(self._show_login)

        # Connect auth success to show WelcomeWindow
        self.auth_controller.auth_successful.connect(self._handle_auth_success)

    def start(self):
        self.welcome.show()

    def _show_login(self):
        dialog = QDialog(self.welcome)
        dialog.setWindowTitle("Login / Register")
        layout = QVBoxLayout()
        auth_view = AuthView(self.auth_controller)
        layout.addWidget(auth_view)
        dialog.setLayout(layout)
        dialog.exec_()

    def _handle_auth_success(self):
        if os.getenv("DEVELOP_MACHINE"):
            print("Authentication successful, returning to WelcomeWindow")
        self.welcome.show()  # Ensure WelcomeWindow is visible

    def _new_project(self):
        default_loc = os.path.join(os.path.dirname(__file__), "dev-cache")
        os.makedirs(default_loc, exist_ok=True)

        proj_dir = QFileDialog.getExistingDirectory(
            None,
            "Select (or create) a new project folder under dev-cache",
            default_loc,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )
        if not proj_dir:
            return

        project = Project.create_new(proj_dir)
        self._open_editor(project_dir=proj_dir)

    def _open_editor(self, project_dir=None):
        if self.editor:
            self.editor.close()
            self.editor = None

        if not project_dir:
            if os.getenv("DEVELOP_MACHINE"):
                print("No project directory provided, returning to WelcomeWindow")
            self.welcome.show()
            return

        try:
            json_path = os.path.join(project_dir, "project.json")
            if os.path.exists(json_path):
                project = Project.load_from_file(json_path)
            else:
                project = Project.create_new(project_dir)
            self.editor = EditorWindow(project=project)
            self.editor.settings_requested.connect(self.settings.exec_)
            self.editor.show()
            self.welcome.close()
        except Exception as e:
            if os.getenv("DEVELOP_MACHINE"):
                print(f"Failed to open editor: {e}")
            self.welcome.show()