# models/timeline_model.py
from PyQt5.QtCore import QObject, pyqtSignal

class TimelineModel(QObject):
    dataChanged = pyqtSignal()

    def __init__(self, duration_frames=0):
        super().__init__()
        self.total_frames = duration_frames
        self.clips = []  # Each clip is a dict { "id": int, "start_frame": int, "end_frame": int, "source_path": str }
        self.current_tool = "Select"
        self.playhead = 0
        self._next_clip_id = 1

        # Optionally, initialize with a blank “track placeholder” or no clips.
        # self.clips.append({ "id": 0, "start_frame": 0, "end_frame": duration_frames, "source_path": None })

    @classmethod
    def from_dict(cls, data: dict) -> "TimelineModel":
        model = cls(duration_frames=data["total_frames"])
        model.clips = data["clips"]
        model._next_clip_id = max(c["id"] for c in model.clips) + 1 if model.clips else 1
        return model

    def to_dict(self) -> dict:
        return {
            "total_frames": self.total_frames,
            "clips": self.clips
        }

    def get_clips(self):
        return self.clips

    def set_playhead(self, frame: int):
        self.playhead = frame
        self.dataChanged.emit()

    def set_current_tool(self, tool_name: str):
        self.current_tool = tool_name
        # If your timeline drawing changes based on tool (e.g. highlight edges in Cut mode),
        # you may want to .dataChanged.emit() here as well.

    def split_clip(self, clip_id: int, at_frame: int):
        """
        Find the clip with clip_id, split it into two new clips around at_frame.
        Remove the old clip, insert the two new ones, emit dataChanged.
        """
        for idx, clip in enumerate(self.clips):
            if clip["id"] == clip_id:
                start, end = clip["start_frame"], clip["end_frame"]
                if start < at_frame < end:
                    left = { "id": self._next_clip_id, "start_frame": start, "end_frame": at_frame, "source_path": clip["source_path"] }
                    self._next_clip_id += 1
                    right = { "id": self._next_clip_id, "start_frame": at_frame + 1, "end_frame": end, "source_path": clip["source_path"] }
                    self._next_clip_id += 1
                    # Replace the old clip with the two new ones
                    self.clips.pop(idx)
                    self.clips.insert(idx, left)
                    self.clips.insert(idx + 1, right)
                    self.dataChanged.emit()
                break

    def save_to_file(self, path: str):
        # For simplicity, just call Project.save_to_file() or replicate this logic here.
        pass
