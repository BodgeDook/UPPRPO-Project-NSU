# desktop-app/widgets/preview.py
# from PyQt5.QtCore import pyqtSignal, Qt, QTimer
# from PyQt5.QtGui import QPainter, QImage
# from PyQt5.QtWidgets import QWidget

# class PreviewWidget(QWidget):
#     playback_position_changed = pyqtSignal(int)  # “we advanced to frame X”

#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self._player = None      # will hold PlayerModel
#         self._current_frame = 0
#         self._current_image = None

#         self._timer = QTimer(self)
#         self._timer.timeout.connect(self._advance_frame)

#     def set_player(self, player_model):
#         """
#         player_model must provide:
#           - total_frames: int
#           - frame_rate: float
#           - get_frame(frame_number) -> QImage
#         """
#         self._player = player_model
#         interval = int(1000 / max(1, getattr(player_model, "frame_rate", 24)))
#         self._timer.setInterval(interval)
#         self._current_frame = 0
#         self._update_frame()

#     def show_frame(self, frame_number: int):
#         if not self._player:
#             return
#         self._current_frame = frame_number
#         self._update_frame()

#     def play(self):
#         if not self._player:
#             return
#         self._timer.start()

#     def pause(self):
#         self._timer.stop()

#     def _advance_frame(self):
#         if not self._player:
#             return
#         nxt = self._current_frame + 1
#         if nxt >= self._player.total_frames:
#             self._timer.stop()
#             return
#         self.show_frame(nxt)

#     def _update_frame(self):
#         if self._player:
#             qimg = self._player.get_frame(self._current_frame)
#             self._current_image = qimg
#             self.update()
#             self.playback_position_changed.emit(self._current_frame)

#     def paintEvent(self, event):
#         painter = QPainter(self)
#         w, h = self.width(), self.height()
#         painter.fillRect(0, 0, w, h, Qt.black)
#         if self._current_image:
#             scaled = self._current_image.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
#             x = (w - scaled.width()) // 2
#             y = (h - scaled.height()) // 2
#             painter.drawImage(x, y, scaled)



import sys
from pathlib import Path

from PyQt5.QtCore    import Qt, QUrl, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QSlider,
    QVBoxLayout, QFileDialog, QStyle, QMessageBox
)
from PyQt5.QtMultimedia         import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets  import QVideoWidget


class VideoPlayer(QWidget):
    playback_position_changed = pyqtSignal(int)  # “we advanced to frame X” — to be connected

    def __init__(self, source: Path | None = None, parent=None) -> None:
        super().__init__(parent)
        self._player = None      # will hold PlayerModel
        self._current_path: Path | None = None
        # self.setWindowTitle("Minimal PyQt5 Player")

        # --- Qt Multimedia backend -----------------------------------------
        self.player = QMediaPlayer(self)
        self.player.setNotifyInterval(40)  # update slider every ~40 ms

        # --- Video surface --------------------------------------------------
        self.video_widget = QVideoWidget(self)
        self.player.setVideoOutput(self.video_widget)

        # --- Play / Pause button -------------------------------------------
        self.play_btn = QPushButton(self)
        self.play_btn.setEnabled(False)
        self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_btn.clicked.connect(self.toggle_play_pause)

        # --- Scrub / Position slider ---------------------------------------
        self.scrub = QSlider(Qt.Horizontal, self)
        self.scrub.setEnabled(False)
        self.scrub.setRange(0, 0)               # real range set on media load
        self.scrub.sliderMoved.connect(self.scrub_moved)
        self.scrub.sliderPressed.connect(self._remember_if_was_playing)

        # --- Layout ---------------------------------------------------------
        layout = QVBoxLayout(self)
        layout.addWidget(self.video_widget)
        layout.addWidget(self.scrub)
        layout.addWidget(self.play_btn, alignment=Qt.AlignHCenter)
        self.setLayout(layout)

        # --- Wire QMediaPlayer signals -------------------------------------
        self.player.durationChanged.connect(self._update_duration)
        self.player.positionChanged.connect(self._update_position)
        self.player.stateChanged.connect(self._update_ui_state)

        # --- Frame coms -----------------------------------------------------
        self._fps = 30.0
        self.player.mediaStatusChanged.connect(self._probe_fps)

        # --- Load first clip (optional) -------------------------------------
        if source is not None:
            self.open_clip(source)
        # else:
        #     self._prompt_open()

    # ----------------------------------------------------------------------
    # Public helpers
    # ----------------------------------------------------------------------
    def open_clip(self, path: Path) -> None:
        if not path.exists():
            QMessageBox.critical(self, "File not found", str(path))
            return
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(str(path))))
        self.play_btn.setEnabled(True)
        self.scrub.setEnabled(True)

    def set_player(self, player_model):
        """
        player_model must provide:
          - total_frames: int
          - frame_rate: float
          - get_frame(frame_number) -> QImage
        """
        self._player = player_model
        # interval = int(1000 / max(1, getattr(player_model, "frame_rate", 24)))
        # self._timer.setInterval(interval)
        # self._current_frame = 0
        # self._update_frame()
    
    def show_source(self, path: Path, pos_ms: int) -> None:
        """Switch file only if needed, then seek."""
        if self._current_path != path:
            self._current_path = path
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(str(path))))
            # allow play/pause button & slider to activate
            self.play_btn.setEnabled(True)
            self.scrub.setEnabled(True)

        # whether it was a new clip or not, jump to the requested position
        self.player.blockSignals(True)          # don’t recurse via positionChanged
        self.player.setPosition(pos_ms)
        self.player.blockSignals(False)
        # emit frame index so timeline stays in sync
        frame = int(round(pos_ms / 1000 * self._fps))
        self.playback_position_changed.emit(frame)

    # ----------------------------------------------------------------------
    # Slots
    # ----------------------------------------------------------------------
    def toggle_play_pause(self) -> None:
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def scrub_moved(self, position: int) -> None:
        """Seek **only** when paused to respect the ‘no seeking while playing’ rule."""
        if self.player.state() != QMediaPlayer.PlayingState:
            self.player.setPosition(position)
    
    # ------------------------------------------------------------------
    # Grab FPS once the media is loaded
    # ------------------------------------------------------------------
    def _probe_fps(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.LoadedMedia:
            # Try to read the stream’s declared frame-rate; fall back to default
            # fps = self.player.metaData().value(QMediaMetaData.VideoFrameRate)
            # if fps:
            #     self._fps = float(fps)
            # Ask for the single key directly (PyQt 5 API)
            try:
                fps_val = self.player.metaData("VideoFrameRate")
                if fps_val:                         # might be '' or None
                    self._fps = float(fps_val)
            except (TypeError, ValueError):
                # leave self._fps at its default if Qt returns “unknown”
                pass

    # ------------------------------------------------------------------
    # Position updates – emit frame number here
    # ------------------------------------------------------------------
    def _update_position(self, pos_ms: int) -> None:
        # keep the slider in sync
        if not self.scrub.isSliderDown():
            self.scrub.blockSignals(True)
            self.scrub.setValue(pos_ms)
            self.scrub.blockSignals(False)

        # convert milliseconds → frame index and emit
        frame = int(round((pos_ms / 1000.0) * self._fps))
        self.playback_position_changed.emit(frame)

    # ----------------------------------------------------------------------
    # Internal glue
    # ----------------------------------------------------------------------
    def _update_duration(self, duration: int) -> None:
        self.scrub.setRange(0, duration)

    def _update_position(self, pos: int) -> None:
        # Only update slider if the user is not actively dragging it
        if not self.scrub.isSliderDown():
            self.scrub.blockSignals(True)
            self.scrub.setValue(pos)
            self.scrub.blockSignals(False)

    def _update_ui_state(self, state: QMediaPlayer.State) -> None:
        icon = QStyle.SP_MediaPause if state == QMediaPlayer.PlayingState else QStyle.SP_MediaPlay
        self.play_btn.setIcon(self.style().standardIcon(icon))
        # Disable slider while playing so the user can’t seek
        self.scrub.setEnabled(state != QMediaPlayer.PlayingState)

    def _remember_if_was_playing(self) -> None:
        """
        If you decide later that clicking the slider should automatically pause,
        you can store state here.  For now it’s a stub (kept for clarity).
        """
        pass

    def _prompt_open(self) -> None:
        fname, _ = QFileDialog.getOpenFileName(
            self, "Open video", "", "Videos (*.mp4 *.mov *.avi *.mkv);;All files (*.*)"
        )
        if fname:
            self.open_clip(Path(fname))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    source_arg = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    player = VideoPlayer(source_arg)
    player.resize(960, 540)
    player.show()
    sys.exit(app.exec_())