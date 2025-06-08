# desktop-app/controllers/app_controller.py

import os
from PyQt5.QtWidgets import QFileDialog, QInputDialog
from PyQt5.QtCore import QStandardPaths

from views.welcome import WelcomeWindow
from views.editor import EditorWindow
from views.settings import SettingsDialog
from models.project import Project


class AppController:
    def __init__(self):
        self.welcome = WelcomeWindow()
        self.editor = None
        self.settings = SettingsDialog(parent=None)

        # Wire welcome signals:
        self.welcome.open_project_requested.connect(self._open_editor)
        self.welcome.new_project_requested.connect(self._new_project)
        self.welcome.login_requested.connect(self._show_login)

    def start(self):
        self.welcome.show()

    def _show_login(self):
        # Launch your AuthView if you wired it here; otherwise, handle elsewhere
        pass

    def _new_project(self):
        """
        Called when the user clicks “New Project”. 
        We prompt them for a project folder under dev-cache (or a default location).
        """

        default_loc = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dev-cache")
        # # default_loc = os.path.join(os.path.dirname(__file__), "dev-cache")
        os.makedirs(default_loc, exist_ok=True)

        # proj_dir = QFileDialog.getExistingDirectory(
        #     None,
        #     "Select (or create) a new project folder under dev-cache",
        #     default_loc,
        #     QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        # )
        # if not proj_dir:
        #     return  # user cancelled

        # 1) Show a modal text input dialog
        name, ok = QInputDialog.getText(
            None,                      # no parent widget
            "New Project",             # dialog window title
            "Enter a name for your new project:"  # prompt text
        )

        # 2) Check if the user clicked “OK” and entered something
        if not ok or not name.strip():
            return  # they cancelled or gave an empty name

        # 3) Use that name to create your folder
        proj_dir = os.path.join(default_loc, name.strip())
        os.makedirs(proj_dir, exist_ok=True)

        # 4) Hand off to your model and view
        project = Project.create_new(proj_dir)
        self._open_editor(project_dir=proj_dir)

    def _open_editor(self, project_dir=None):
        """
        project_dir is either:
          1) a folder containing project.json (when loading), or
          2) a folder we just created (with no clips yet).
        """
        if self.editor:
            self.editor.close()
            self.editor = None

        # If project_dir has project.json, load; otherwise, assume create_new was already called
        json_path = os.path.join(project_dir, "project.json")
        if os.path.exists(json_path):
            project = Project.load_from_file(json_path)
        else:
            # In case we ended up here directly (shouldn't usually happen), create new:
            project = Project.create_new(project_dir)

        self.editor = EditorWindow(project=project)
        self.editor.settings_requested.connect(self.settings.exec_)
        self.editor.show()
        self.welcome.close()
