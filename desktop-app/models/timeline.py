# desktop-app/models/timeline_model.py

from PyQt5.QtCore import QObject, pyqtSignal


class TimelineModel(QObject):
    """
    Holds clip data, playhead, and current tool. 
    Provides methods to add new clips and serialize/deserialize.
    """

    dataChanged = pyqtSignal()

    def __init__(self, duration_frames=0):
        super().__init__()
        self.total_frames = duration_frames
        self.clips = []  # list of dicts: {id, start_frame, end_frame, asset_rel_path}
        self.current_tool = "Select"
        self.playhead = 0
        self._next_id = 1

    @classmethod
    def from_dict(cls, data):
        """
        Recreate a TimelineModel from a dictionary (as saved in project.json).
        """
        obj = cls(duration_frames=data.get("total_frames", 0))
        obj.clips = data.get("clips", [])
        obj.playhead = data.get("playhead", 0)
        obj.current_tool = data.get("current_tool", "Select")

        # Determine next ID from existing clips
        existing_ids = [clip["id"] for clip in obj.clips]
        obj._next_id = max(existing_ids, default=0) + 1
        return obj

    def to_dict(self):
        """
        Serialize model state for saving in project.json.
        """
        return {
            "total_frames": self.total_frames,
            "clips": self.clips,
            "playhead": self.playhead,
            "current_tool": self.current_tool,
        }

    def next_clip_id(self):
        _id = self._next_id
        self._next_id += 1
        return _id

    def get_clips(self):
        return self.clips

    def add_clip_dict(self, clip_dict):
        """
        Add a new clip entry (with keys 'id', 'start_frame', 'end_frame', 'asset_rel_path').
        """
        self.clips.append(clip_dict)
        # If this clip extends beyond total_frames, update total_frames
        if clip_dict["end_frame"] + 1 > self.total_frames:
            self.total_frames = clip_dict["end_frame"] + 1

        self.dataChanged.emit()

    def split_clip(self, clip_id, at_frame):
        # (unchanged) split logic goes here if you have it
        self.dataChanged.emit()

    def set_playhead(self, frame_number):
        self.playhead = frame_number
        self.dataChanged.emit()

    def set_current_tool(self, tool_name):
        self.current_tool = tool_name
        self.dataChanged.emit()

    def save_to_file(self, path):
        # You probably won’t call this directly, since Project.save() handles it.
        pass