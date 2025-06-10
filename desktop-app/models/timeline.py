from typing import List, Optional
from PyQt5.QtCore import QObject, pyqtSignal
from .track import Track
from .playhead import Playhead
from .clip import Clip

# add these two methods inside Clip for (de)serialization:
# @staticmethod
# def from_dict(d: Dict[str,int]) -> "Clip": return Clip(d["asset_path"], d["in_frame"], d["out_frame"], d["timeline_start_frame"])
# def to_dict(self) -> Dict[str,int]: return {"asset_path": self.asset_path, "in_frame": self.in_frame, "out_frame": self.out_frame, "timeline_start_frame": self.timeline_start_frame}

class TimelineModel(QObject):
    """
    Owns all tracks, plus a playhead.
    Emits timelineChanged when clips/tracks mutate.
    """
    timelineChanged = pyqtSignal()
    playheadMoved = pyqtSignal(int)  # current frame

    def __init__(self, fps: float = 30.0, num_tracks: int = 1):
        super().__init__()
        self.fps = fps
        self.tracks: List[Track] = [Track(f"Track {i+1}") for i in range(num_tracks)]
        self.playhead = Playhead(fps=self.fps)
        self.playhead.positionChanged.connect(self._on_playhead_moved)

    def _on_playhead_moved(self, frame: int):
        self.playheadMoved.emit(frame)

    def add_clip(self, clip: Clip, track_index: int = 0):
        self.tracks[track_index].add_clip(clip)
        self.timelineChanged.emit()

    def get_clip_at(self, frame: int, track_index: int = 0) -> Optional[Clip]:
        return self.tracks[track_index].clip_at(frame)

    def play(self):
        self.playhead.play()

    def stop(self):
        self.playhead.stop()

    def seek(self, frame: int):
        self.playhead.seek(frame)