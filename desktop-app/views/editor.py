# desktop-app/view/editor.py

from PyQt5.QtWidgets import (
    QMainWindow,
    QAction,
    QFileDialog,
    QWidget,
    QSplitter,
    QVBoxLayout,
)
from PyQt5.QtCore import Qt, pyqtSignal

from widgets.timeline import TimelineWidget
from widgets.preview import PreviewWidget
from widgets.toolbox import ToolboxWidget


class EditorWindow(QMainWindow):
    """
    Main editor window. Now adds an “Import Asset” action under File → Import Asset,
    which copies a video into the project’s assets folder and updates the timeline.
    """

    settings_requested = pyqtSignal()

    def __init__(self, project):
        super().__init__()
        self.project = project  # instance of models/project.py → Project
        self.setWindowTitle(f"uMovie – {project.metadata.get('name', '')}")
        self.resize(1200, 800)

        # ─── 1) Grab models from project ───
        self.timeline_model = self.project.timeline_model
        self.player = self.project.player

        # ─── 2) Instantiate sub‐widgets ───
        self.timeline_widget = TimelineWidget(self)
        self.preview_widget = PreviewWidget(self)
        self.toolbox_widget = ToolboxWidget(self)

        # Tell preview to use our PlayerModel
        if self.player:
            self.preview_widget.set_player(self.player)

        # Tell timeline to use our TimelineModel
        if self.timeline_model:
            self.timeline_widget.set_model(self.timeline_model)
            # Listen for data changes so the widget repaints
            self.timeline_model.dataChanged.connect(self.timeline_widget.update)

        # ─── 3) Layout with splitters ───
        h_split = QSplitter(Qt.Horizontal)
        h_split.addWidget(self.toolbox_widget)

        v_right_split = QSplitter(Qt.Vertical)
        v_right_split.addWidget(self.preview_widget)
        v_right_split.addWidget(self.timeline_widget)
        v_right_split.setSizes([600, 200])

        h_split.addWidget(v_right_split)
        h_split.setStretchFactor(1, 4)
        h_split.setSizes([150, 850])

        container = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(h_split)
        container.setLayout(layout)
        self.setCentralWidget(container)

        # ─── 4) Wire signals between sub‐widgets ───
        self.timeline_widget.frame_requested.connect(self._on_timeline_frame_requested)
        self.preview_widget.playback_position_changed.connect(
            self._on_playback_position_changed
        )
        self.toolbox_widget.tool_selected.connect(self._on_tool_selected)

        # ─── 5) Menu Bar: File, Edit ───
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")

        # “Import Asset” → open file dialog, copy asset, register clip
        import_action = QAction("Import Asset", self)
        import_action.triggered.connect(self._import_asset)
        file_menu.addAction(import_action)

        # “Save Project” → let Project.save() persist JSON
        save_action = QAction("Save Project", self)
        save_action.triggered.connect(self._save_project)
        file_menu.addAction(save_action)

        # “Settings” under Edit
        edit_menu = menubar.addMenu("Edit")
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.settings_requested.emit)
        edit_menu.addAction(settings_action)

    # ─────────────────────────────────────────────────────────────────────────────
    # Slots that respond to sub‐widget signals:
    # ─────────────────────────────────────────────────────────────────────────────

    def _on_timeline_frame_requested(self, frame_number: int):
        self.preview_widget.show_frame(frame_number)

    def _on_playback_position_changed(self, frame_number: int):
        # update playhead in model → timeline repaints
        self.timeline_model.set_playhead(frame_number)

    def _on_tool_selected(self, tool_name: str):
        self.timeline_model.set_current_tool(tool_name)

    # ─────────────────────────────────────────────────────────────────────────────
    # New: Import and Save logic
    # ─────────────────────────────────────────────────────────────────────────────

    def _import_asset(self):
        """
        Show a QFileDialog to pick a video file. 
        Then call project.add_asset(...) to copy + register it.
        Finally, rebind preview to the new player and force timeline repaint.
        """
        file_filter = "Video Files (*.mp4 *.mov *.mkv *.avi);;All Files (*)"
        src_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video Asset to Import", filter=file_filter
        )
        if not src_path:
            return  # user cancelled

        # Delegate to Project to copy + register the clip
        new_clip = self.project.add_asset(src_path)

        # Rebind the preview widget to the new PlayerModel (which was updated)
        self.preview_widget.set_player(self.project.player)

        # Ensure timeline sees the new clip immediately
        # (Project.add_asset already did timeline_model.add_clip_dict and emitted dataChanged)

    def _save_project(self):
        """
        Delegate to Project.save() to write project.json and clip‐list.
        """
        self.project.save()
