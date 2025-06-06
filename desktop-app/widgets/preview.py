# desktop-app/widgets/preview.py
from PyQt5.QtCore import pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QPainter, QImage
from PyQt5.QtWidgets import QWidget

class PreviewWidget(QWidget):
    playback_position_changed = pyqtSignal(int)  # “we advanced to frame X”

    def __init__(self, parent=None):
        super().__init__(parent)
        self._player = None      # will hold PlayerModel
        self._current_frame = 0
        self._current_image = None

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance_frame)

    def set_player(self, player_model):
        """
        player_model must provide:
          - total_frames: int
          - frame_rate: float
          - get_frame(frame_number) -> QImage
        """
        self._player = player_model
        interval = int(1000 / max(1, getattr(player_model, "frame_rate", 24)))
        self._timer.setInterval(interval)
        self._current_frame = 0
        self._update_frame()

    def show_frame(self, frame_number: int):
        if not self._player:
            return
        self._current_frame = frame_number
        self._update_frame()

    def play(self):
        if not self._player:
            return
        self._timer.start()

    def pause(self):
        self._timer.stop()

    def _advance_frame(self):
        if not self._player:
            return
        nxt = self._current_frame + 1
        if nxt >= self._player.total_frames:
            self._timer.stop()
            return
        self.show_frame(nxt)

    def _update_frame(self):
        if self._player:
            qimg = self._player.get_frame(self._current_frame)
            self._current_image = qimg
            self.update()
            self.playback_position_changed.emit(self._current_frame)

    def paintEvent(self, event):
        painter = QPainter(self)
        w, h = self.width(), self.height()
        painter.fillRect(0, 0, w, h, Qt.black)
        if self._current_image:
            scaled = self._current_image.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = (w - scaled.width()) // 2
            y = (h - scaled.height()) // 2
            painter.drawImage(x, y, scaled)
