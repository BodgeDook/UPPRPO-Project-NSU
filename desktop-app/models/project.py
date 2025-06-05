# models/project.py (outline)
import json
from models.render import PlayerModel
from models.timeline import TimelineModel

class Project:
    def __init__(self, timeline: TimelineModel, player: PlayerModel, path: str = None):
        self.timeline = timeline
        self.player = player
        self.file_path = path  # None for “untitled”

    @classmethod
    def load_from_file(cls, path: str) -> "Project":
        data = json.load(open(path, "r"))
        tl_model = TimelineModel.from_dict(data["timeline"])
        player = PlayerModel(data["video_path"])
        proj = cls(tl_model, player, path)
        return proj

    @classmethod
    def create_new(cls, default_frames=1000) -> "Project":
        tl_model = TimelineModel(duration_frames=default_frames)
        player = PlayerModel.blank(default_frames)
        return cls(tl_model, player)

    def save_to_file(self, path: str):
        payload = {
            "timeline": self.timeline.to_dict(),
            "video_path": self.player.video_path,
            # include any other project metadata here
        }
        json.dump(payload, open(path, "w"), indent=2)
        self.file_path = path
