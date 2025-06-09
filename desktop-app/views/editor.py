# desktop-app/view/editor.py
import os

from pathlib import Path
from PyQt5.QtWidgets import (
    QMainWindow,
    QAction,
    QFileDialog,
    QWidget,
    QSplitter,
    QVBoxLayout,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QScrollArea
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import QUrl

from widgets.preview import VideoPlayer  
# from widgets.preview import PreviewWidget
from widgets.timeline import TimelineWidget
from widgets.toolbox import ToolboxWidget
from models.render import PlayerModel


class EditorWindow(QMainWindow):
    """
    Main editor window. Now adds an “Import Asset” action under File → Import Asset,
    which copies a video into the project’s assets folder and updates the timeline.
    """

    settings_requested = pyqtSignal()

    def __init__(self, project):
        super().__init__()
        self.setAcceptDrops(True)
        self.project = project  # instance of models/project.py → Project
        self.setWindowTitle(f"uMovie – {project.metadata.get('name', '')}")
        self.resize(1200, 800)

        # ─── 1) Grab models from project ───
        self.timeline_model = self.project.timeline_model
        self.player = self.project.player

        # ─── 2) Instantiate sub‐widgets ───
        # self.preview_widget = PreviewWidget(self)
        self.toolbox_widget = ToolboxWidget(self)
        self.timeline_widget = TimelineWidget(self)
        self.video_player = VideoPlayer(parent=self) 

        # Tell preview to use our PlayerModel
        if self.player:
            # self.preview_widget.set_player(self.player)
            self.video_player.set_player(self.player)

        # Tell timeline to use our TimelineModel
        if self.timeline_model:
            self.timeline_widget.set_model(self.timeline_model)
            # Listen for data changes so the widget repaints
            self.timeline_model.dataChanged.connect(self.timeline_widget.update)
            # whenever the playhead moves, redraw preview at that frame
            # self.timeline_model.dataChanged.connect(
            #     lambda: self.preview_widget.show_frame(self.timeline_model.playhead)
            # )
        # keep timeline playhead and preview in sync
        self.video_player.playback_position_changed.connect(
            self.timeline_widget._model.set_playhead
        )
        self.timeline_widget.frame_requested.connect(
            lambda f: self.video_player.player.setPosition(int(f / self.video_player._fps * 1000))
        )

        # ─── 3) Layout with splitters ───
        # Top split: toolbox (1/2) and preview (1/2)
        top_split = QSplitter(Qt.Horizontal)
        top_split.addWidget(self.toolbox_widget)
        # top_split.addWidget(self.preview_widget)
        top_split.addWidget(self.video_player)
        # Set initial sizes: toolbox 1 part, preview 1 parts
        top_split.setStretchFactor(0, 1)
        top_split.setStretchFactor(1, 2)

        # Main split: top_split above a scrollable timeline
        main_split = QSplitter(Qt.Vertical)
        main_split.addWidget(top_split)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.timeline_widget)
        main_split.addWidget(scroll)
        # Set initial sizes: top 1 part, bottom 1 part (equal halves)
        main_split.setStretchFactor(0, 1)
        main_split.setStretchFactor(1, 1)

        container = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(main_split)
        container.setLayout(layout)
        self.setCentralWidget(container)

        # ─── 4) Wire signals between sub‐widgets ───
        self.timeline_widget.frame_requested.connect(self._on_timeline_frame_requested)
        # self.player.playback_position_changed.connect(self.timeline_widget._model.set_playhead)
        # self.preview_widget.playback_position_changed.connect(
        #     self._on_playback_position_changed
        # )
        self.toolbox_widget.tool_selected.connect(self._on_tool_selected)
        # — New: asset selection —
        self.currently_selected_asset = None
        self.toolbox_widget.asset_selected.connect(self._on_asset_selected)

        # Populate initial asset list
        self.toolbox_widget.set_assets(self.project.list_assets())
 

        # ─── 5) Menu Bar: File, Edit ───
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")

        # “Import Asset” → open file dialog, copy asset, register clip
        # import_action = QAction("Import Asset", self)
        # import_action.triggered.connect(self._import_asset)
        # file_menu.addAction(import_action)

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

    # def _on_timeline_frame_requested(self, frame_number: int):
    #     self.preview_widget.show_frame(frame_number)
    # def _on_timeline_frame_requested(self, frame_number: int):
    #     # If the user picked an asset, place it here
    #     if self.currently_selected_asset:
    #         self.project.add_clip_from_asset(self.currently_selected_asset, frame_number)
    #         # update UI and clear selection
    #         self.preview_widget.set_player(self.project.player)
    #         self.preview_widget.show_frame(frame_number)
    #         self.currently_selected_asset = None
    #         # toolbox still shows all assets
    #     else:
    #         # normal preview scrub
    #         self.preview_widget.show_frame(frame_number)

    # def _on_timeline_frame_requested(self, frame_number: int):
    #     # 1) Move playhead
    #     self.timeline_model.set_playhead(frame_number)

    #     # 2) Place pending asset (if any)
    #     if self.currently_selected_asset:
    #         self.project.add_clip_from_asset(self.currently_selected_asset, frame_number)
    #         self.toolbox_widget.clear_selection()      # hypothetical helper
    #         self.currently_selected_asset = None

    #     # 3) Seek preview to the new global frame
    #     self.video_player.player.setPosition(
    #         int(frame_number / self.video_player._fps * 1000)
    #     )

    def _on_timeline_frame_requested(self, frame: int) -> None:
        self.timeline_model.set_playhead(frame)

        src = self.project.source_at_frame(frame)
        if src is None:
            # no clip under the head → blank screen
            self.video_player.player.setMedia(QMediaContent())  # unload
            return

        path, pos_ms = src
        self.video_player.show_source(Path(path), pos_ms)

    # def _on_timeline_frame_requested(self, frame_number: int):
    #     # always move the playhead first
    #     self.timeline_model.set_playhead(frame_number)

    #     # if we’re in “placing new asset” mode, that logic stays the same…
    #     if self.currently_selected_asset:
    #         self.project.add_clip_from_asset(self.currently_selected_asset, frame_number)
    #         self.currently_selected_asset = None

    #     # now figure out which clip (if any) lives under the head
    #     clip = self.project.get_clip_at_frame(frame_number)
    #     if clip:
    #         # compute local frame within that clip
    #         local = frame_number - clip["start_frame"]
    #         asset_rel = clip["asset_rel_path"]
    #         abs_path = os.path.join(self.project.project_dir, asset_rel)

    #         # if it’s a different asset than we’re already previewing, swap players
    #         if (
    #             not self.project.player.video_path
    #             or os.path.normpath(self.project.player.video_path) != os.path.normpath(abs_path)
    #         ):
    #             new_player = PlayerModel(abs_path)
    #             self.project.player = new_player
    #             self.preview_widget.set_player(new_player)

    #         # finally show the local frame
    #         self.preview_widget.show_frame(local)
    #     else:
    #         # no clip under the head → show a black frame
    #         blank = PlayerModel.blank()
    #         self.project.player = blank
    #         self.preview_widget.set_player(blank)
    #         self.preview_widget.show_frame(0)

    def _on_asset_selected(self, asset_rel_path: str):
        """User clicked an asset in the toolbox—enter “placement” mode."""
        self.currently_selected_asset = asset_rel_path
        # Optionally, change cursor or highlight the timeline

    def _on_playback_position_changed(self, frame_number: int):
        # update playhead in model → timeline repaints
        self.timeline_model.set_playhead(frame_number)

    def _on_tool_selected(self, tool_name: str):
        self.timeline_model.set_current_tool(tool_name)
    
    def _advance_playhead(self, frame: int) -> None:
        """
        Connected to VideoPlayer.playback_position_changed so
        the timeline keeps up *and* we can jump clips on the fly.
        """
        self.timeline_model.blockSignals(True)
        self.timeline_model.set_playhead(frame)
        self.timeline_model.blockSignals(False)

        src = self.project.source_at_frame(frame)
        if src:
            path, pos_ms = src
            self.video_player.show_source(Path(path), pos_ms)

    # ─────────────────────────────────────────────────────────────────────────────
    # New: Import and Save logic
    # ─────────────────────────────────────────────────────────────────────────────

    # def _import_asset(self):
    #     """
    #     Show a QFileDialog to pick a video file. 
    #     Then call project.add_asset(...) to copy + register it.
    #     Finally, rebind preview to the new player and force timeline repaint.
    #     """
    #     file_filter = "Video Files (*.mp4 *.mov *.mkv *.avi);;All Files (*)"
    #     src_path, _ = QFileDialog.getOpenFileName(
    #         self, "Select Video Asset to Import", filter=file_filter
    #     )
    #     if not src_path:
    #         return  # user cancelled

    #     # Delegate to Project to copy + register the clip
    #     new_clip = self.project.add_asset(src_path)

    #     # update the Toolbox’s asset list
    #     self.toolbox_widget.set_assets(self.project.list_assets())
    #     # Rebind the preview widget to the new PlayerModel (which was updated)
    #     # self.preview_widget.set_player(self.project.player)
    #     file_url = QUrl.fromLocalFile(os.path.join(
    #         self.project.project_dir,
    #         asset_rel_path
    #     ))
    #     self.media_player.setMedia(QMediaContent(file_url))
    #     # seek to the very start
    #     self.media_player.pause()
    #     self.media_player.setPosition(0)

    #     # Ensure timeline sees the new clip immediately
    #     # (Project.add_asset already did timeline_model.add_clip_dict and emitted dataChanged)

    # def _import_asset(self):
    #     src_path, _ = QFileDialog.getOpenFileName(…)
    #     if not src_path:
    #         return

    #     # 1) Copy into assets & register clip
    #     new_clip = self.project.add_asset(src_path)
    #     asset_rel = new_clip["asset_rel_path"]
    #     abs_path  = os.path.join(self.project.project_dir, asset_rel)

    #     # 2) Load into QMediaPlayer
    #     url = QUrl.fromLocalFile(abs_path)
    #     self.media_player.setMedia(QMediaContent(url))
    #     self.media_player.pause()
    #     self.media_player.setPosition(0)

    #     # 3) Update UI
    #     self.toolbox_widget.set_assets(self.project.list_assets())
    #     # (Timeline repaint is automatic via dataChanged)

    # ─────────────────────────────────────────────────────────────────────────────
    # Import Asset  (File → Import Asset)
    # ─────────────────────────────────────────────────────────────────────────────
    def _import_asset(self) -> None:
        """
        Temporary stub: lets the app start without errors.
        Replace with the real import logic when you’re ready.
        """
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "Not implemented yet",
            "Asset import hasn’t been rebuilt after the preview refactor."
        )

    def _save_project(self):
        """
        Delegate to Project.save() to write project.json and clip-list.
        """
        self.project.save()
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Drag-and-Drop
    # ─────────────────────────────────────────────────────────────────────────────

    def dragEnterEvent(self, event):
        # only accept if it’s a file drop
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        urls = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if not urls:
            return

        # 1) Copy every dropped file into assets/
        new_clips = []
        for path in urls:
            clip = self.project.add_asset(path)      # your model handles copying
            new_clips.append(clip)

        # 2) Refresh the toolbox so the sidebar shows the new items
        self.toolbox_widget.set_assets(self.project.list_assets())

        # 3) Automatically cue the first dropped clip in the preview (optional)
        if len(new_clips) == 1:
            rel = new_clips[0]["asset_rel_path"]
            abs_path = os.path.join(self.project.project_dir, rel)
            self.video_player.show_source(Path(abs_path), pos_ms=0)
            
        event.acceptProposedAction()
    
    # def dropEvent(self, event):
    #     # for each dropped URL...
    #     for url in event.mimeData().urls():
    #         path = url.toLocalFile()
    #         if not path:
    #             continue

    #         # delegate to your model
    #         # this will copy the file into assets/ and update your timeline model
    #         self.project.add_asset(path)

    #     # update the Toolbox’s asset list
    #     self.toolbox_widget.set_assets(self.project.list_assets())

    #     # re-bind your preview to show the new PlayerModel
    #     # self.preview_widget.set_player(self.project.player)
    #     file_url = QUrl.fromLocalFile(os.path.join(
    #         self.project.project_dir,
    #         asset_rel_path
    #     ))
    #     self.media_player.setMedia(QMediaContent(file_url))
    #     # seek to the very start
    #     self.media_player.pause()
    #     self.media_player.setPosition(0)

    #     # your TimelineModel.emit dataChanged, so the widget repaints
    #     event.acceptProposedAction()
