# desktop-app/view/editor.py
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QMainWindow, QAction, QWidget, QVBoxLayout, QSplitter

from widgets.timeline import TimelineWidget
from widgets.preview import PreviewWidget
from widgets.toolbox import ToolboxWidget

class EditorWindow(QMainWindow):
    settings_requested = pyqtSignal()  # displayed when user picks “Settings” from menu

    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.project = project  # a Project instance from models/project.py
        self.setWindowTitle(f"uMovie – Editing: {project.file_path or 'Untitled'}")
        self.resize(1200, 800)

        # 1) Extract models from project
        self.timeline_model = project.timeline
        self.player_model = project.player

        # 2) Instantiate sub‐widgets
        self.timeline_widget = TimelineWidget()
        self.preview_widget = PreviewWidget()
        self.toolbox_widget = ToolboxWidget()

        # 3) Hook models into widgets
        self.timeline_widget.set_model(self.timeline_model)
        self.preview_widget.set_player(self.player_model)

        # 4) Lay them out with a QSplitter
        hsplit = QSplitter(Qt.Horizontal)
        hsplit.addWidget(self.toolbox_widget)

        vsplit = QSplitter(Qt.Vertical)
        vsplit.addWidget(self.preview_widget)
        vsplit.addWidget(self.timeline_widget)
        vsplit.setSizes([600, 200])

        hsplit.addWidget(vsplit)
        hsplit.setStretchFactor(1, 4)
        hsplit.setSizes([150, 850])

        container = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(hsplit)
        container.setLayout(layout)
        self.setCentralWidget(container)

        # 5) Wire signals & slots between sub‐widgets
        self.timeline_widget.frame_requested.connect(self._on_frame_requested)
        self.timeline_widget.clip_selected.connect(self._on_clip_selected)
        self.preview_widget.playback_position_changed.connect(self._on_playback_moved)
        self.toolbox_widget.tool_selected.connect(self._on_tool_selected)
        # (We’ll describe these handler methods below.)

        # 6) Menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        save_action = QAction("Save Project", self)
        save_action.triggered.connect(self._save_project)
        file_menu.addAction(save_action)

        edit_menu = menubar.addMenu("Edit")
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.settings_requested.emit)
        edit_menu.addAction(settings_action)

    # 7) Slots to respond to sub‐widget signals
    def _on_frame_requested(self, frame_number: int):
        self.preview_widget.show_frame(frame_number)

    def _on_clip_selected(self, clip_id: int):
        # If in “Cut” mode, maybe call timeline_model.split_clip first.
        if self.timeline_model.current_tool == "Cut":
            self.timeline_model.split_clip(clip_id, self.timeline_model.playhead)
        # … then show the frame at that clip’s start on preview?
        clip = next(c for c in self.timeline_model.get_clips() if c["id"] == clip_id)
        self.preview_widget.show_frame(clip["start_frame"])

    def _on_playback_moved(self, frame_number: int):
        self.timeline_model.set_playhead(frame_number)
        self.timeline_widget.update()

    def _on_tool_selected(self, tool_name: str):
        self.timeline_model.set_current_tool(tool_name)
        self.timeline_widget.update()

    # 8) Menu action “Save Project”
    def _save_project(self):
        if not self.project.file_path:
            from PyQt5.QtWidgets import QFileDialog
            path, _ = QFileDialog.getSaveFileName(self, "Save uMovie Project", filter="uMovie (*.json)")
            if not path:
                return
            self.project.file_path = path

        self.project.save_to_file(self.project.file_path)
