from .clip import Clip
from typing import List, Optional

class Track:
    """
    Holds exactly one list of Clip instances.
    """
    def __init__(self, name: str = "Default"):
        self.name = name
        self.clips: List[Clip] = []

    def add_clip(self, clip: Clip) -> None:
        self.clips.append(clip)
        # TODO: sort by timeline_start_frame if you want auto-order

    def clip_at(self, frame: int) -> Optional[Clip]:
        """
        Return the clip playing at `frame`, or None.
        """
        for clip in self.clips:
            if clip.contains_frame(frame):
                return clip
        return None