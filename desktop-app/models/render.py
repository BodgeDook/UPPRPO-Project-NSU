# models/render.py
from PyQt5.QtGui import QImage
from cpp_renderer import CppRenderer

renderer = CppRenderer("some/path.mp4")
n = renderer.get_total_frames()       # returns 1000
fps = renderer.get_frame_rate()       # returns 24.0
buf, w, h = renderer.decode_frame(42) # returns a black frame of size 640×360

class PlayerModel:
    """
    Wraps your C++/FFmpeg code. Must provide:
      - total_frames (int)
      - frame_rate (float)
      - get_frame(frame_number: int) -> QImage
    """
    def __init__(self, video_path: str):
        self.video_path = video_path
        # Suppose you have a C++ class `CppRenderer` exposed via pybind11
        self._cpp = CppRenderer(video_path)
        self.total_frames = self._cpp.get_total_frames()
        self.frame_rate = self._cpp.get_frame_rate()

    @classmethod
    def blank(cls, duration_frames: int = 1000) -> "PlayerModel":
        # Return a PlayerModel that only generates black frames of fixed size
        pm = cls.__new__(cls)
        pm.video_path = None
        pm.total_frames = duration_frames
        pm.frame_rate = 24
        pm._cpp = None
        return pm

    def get_frame(self, frame_number: int) -> QImage:
        if self._cpp:
            buf, w, h = self._cpp.decode_frame(frame_number)
            # buf is a bytes/bytearray in RGB24 or ARGB32 format
            return QImage(buf, w, h, QImage.Format_RGB888)
        else:
            # Return a solid black QImage placeholder
            img = QImage(640, 360, QImage.Format_RGB888)
            img.fill(0x000000)
            return img
