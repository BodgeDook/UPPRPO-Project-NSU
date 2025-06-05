# desktop-app/widgets/timeline.py
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPainter, QColor, QRect
from PyQt5.QtWidgets import QWidget

class TimelineWidget(QWidget):
    frame_requested = pyqtSignal(int)  # “user clicked at some frame X”
    clip_selected = pyqtSignal(int)    # “user clicked on clip with ID X”

    def __init__(self, parent=None):
        super().__init__(parent)
        self._model = None
        self.setMinimumHeight(100)

    def set_model(self, timeline_model):
        """
        timeline_model must provide:
          - total_frames: int
          - get_clips() → List[{'id': int, 'start_frame': int, 'end_frame': int, …}]
          - current_tool (string)
          - split_clip(clip_id, at_frame)
          - playhead (int) and an optional signal dataChanged
        """
        self._model = timeline_model
        # If the model emits dataChanged, automatically repaint
        try:
            self._model.dataChanged.connect(self.update)
        except AttributeError:
            pass
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        w, h = self.width(), self.height()
        painter.fillRect(0, 0, w, h, QColor(40, 40, 40))

        if not self._model or self._model.total_frames <= 0:
            return

        total = self._model.total_frames

        def frame_to_x(f):
            return int(f / total * w)

        # Draw each clip
        for clip in self._model.get_clips():
            start_x = frame_to_x(clip["start_frame"])
            end_x = frame_to_x(clip["end_frame"])
            rect = QRect(start_x, 10, max(end_x - start_x, 2), h - 20)
            painter.fillRect(rect, QColor(200, 120, 60))
            painter.setPen(QColor(0, 0, 0))
            painter.drawRect(rect)

        # Draw playhead
        ph = frame_to_x(self._model.playhead)
        painter.setPen(QColor(255, 0, 0))
        painter.drawLine(ph, 0, ph, h)

    def mousePressEvent(self, event):
        if not self._model or self._model.total_frames <= 0:
            return
        w = self.width()
        total = self._model.total_frames
        x = event.x()
        clicked_frame = int(x / w * total)

        # If the tool is “Cut,” split that clip first
        if self._model.current_tool == "Cut":
            for clip in self._model.get_clips():
                if clip["start_frame"] <= clicked_frame <= clip["end_frame"]:
                    self._model.split_clip(clip["id"], clicked_frame)
                    self.clip_selected.emit(clip["id"])
                    return

        # Otherwise, just request that frame for preview
        self.frame_requested.emit(clicked_frame)

        # Also detect if a clip was clicked
        for clip in self._model.get_clips():
            if clip["start_frame"] <= clicked_frame <= clip["end_frame"]:
                self.clip_selected.emit(clip["id"])
                return
