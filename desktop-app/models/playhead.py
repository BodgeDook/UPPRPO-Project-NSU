from PyQt5.QtCore import QTimer, pyqtSignal, QObject

class Playhead(QObject):
    """
    Independent playhead. Fires positionChanged every frame.
    """
    positionChanged = pyqtSignal(int)  # current frame

    def __init__(self, fps: float = 30.0):
        super().__init__()
        self.fps = fps
        self._frame = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def _tick(self):
        self._frame += 1
        self.positionChanged.emit(self._frame)

    def play(self):
        interval_ms = int(1000.0 / self.fps)
        self._timer.start(interval_ms)

    def stop(self):
        self._timer.stop()

    def seek(self, frame: int):
        self._frame = frame
        self.positionChanged.emit(self._frame)

    @property
    def frame(self) -> int:
        return self._frame