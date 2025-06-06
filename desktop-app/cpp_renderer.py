# desktop-app/cpp_renderer.py

class CppRenderer:
    def __init__(self, video_path: str):
        # Just record the path; do nothing else
        self.video_path = video_path
        self._total_frames = 1000
        self._frame_rate = 24.0
        self._width = 640
        self._height = 360

    def get_total_frames(self) -> int:
        # Return a dummy total‐frames count
        return self._total_frames

    def get_frame_rate(self) -> float:
        # Return a dummy frame rate
        return self._frame_rate

    def decode_frame(self, frame_number: int):
        """
        Return a black (all‐zero) RGB24 buffer of size width×height, plus width and height.
        """
        # Make sure frame_number is in range, but it doesn't really matter here
        # We just return the same black image every time.
        w, h = self._width, self._height
        buf = bytes([0] * (w * h * 3))
        return buf, w, h