import json
import os
import shutil
import uuid
from typing import Any, Dict

from PyQt5.QtCore import QStandardPaths

from .timeline import TimelineModel
from .render import PlayerModel

class Project:
    JSON_FILENAME = "project.json"

    def __init__(
        self,
        project_dir: str,
        timeline_model: TimelineModel,
        player: PlayerModel,
        metadata: Dict[str, Any] = None,
    ):
        self.project_dir = project_dir
        self.assets_dir = os.path.join(project_dir, "assets")
        self.cache_dir = os.path.join(project_dir, "cache")
        self.json_path = os.path.join(project_dir, self.JSON_FILENAME)

        # ensure folder structure
        os.makedirs(self.assets_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)

        self.timeline_model = timeline_model
        self.player = player
        self.metadata = metadata or {}

    # @classmethod
    # def create_new(cls, project_dir: str, fps: float = 30.0, num_tracks: int = 1):
    #     """
    #     Initialize a fresh project at project_dir.
    #     """
    #     timeline_model = TimelineModel(fps=fps, num_tracks=num_tracks)
    #     # player = PlayerModel()
    #     metadata = {
    #         "id": str(uuid.uuid4()),
    #         "name": os.path.basename(project_dir),
    #         "fps": fps,
    #     }
    #     proj = cls(project_dir, timeline_model, metadata) #cls(project_dir, timeline_model, player, metadata)
    #     proj.save()
    #     return proj

    @classmethod
    def create_new(cls, base_dir, fps: float = 30.0, num_tracks: int = 1):
        """
        Create a brand-new project under base_dir. 
        `base_dir` is assumed to be an existing directory (e.g. uMovie/desktop-app/dev-cache/NewProjectXYZ).
        """
        # Ensure the base directory exists
        os.makedirs(base_dir, exist_ok=True)

        # Inside it, create subfolders: assets/ and cache/
        assets_dir = os.path.join(base_dir, "assets")
        cache_dir = os.path.join(base_dir, "cache")
        os.makedirs(assets_dir, exist_ok=True)
        os.makedirs(cache_dir, exist_ok=True)

        timeline_model = TimelineModel(fps=fps, num_tracks=num_tracks)

        # Instantiate a “blank” player that can produce black frames until we import something
        player_model = PlayerModel.blank()

        # Metadata can include creation timestamp, UUID, etc.
        metadata = {
            "id": str(uuid.uuid4()),
            "created_at": int(os.path.getmtime(base_dir)),
            "name": os.path.basename(base_dir),
        }

        project = cls(base_dir, timeline_model, player_model, metadata=metadata)
        project.save()  # write initial project.json
        return project


    @classmethod
    def load_from_file(cls, path: str):
        """
        Load an existing project, given either:
          - path == folder containing project.json
          - path == full path to project.json
        """
        # determine whether user gave us the JSON file or the folder
        if os.path.isdir(path):
            project_dir = path
            json_path = os.path.join(path, cls.JSON_FILENAME)
        else:
            json_path = path
            project_dir = os.path.dirname(path)

        # read JSON
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # rebuild metadata & timeline_model
        meta = data.get("metadata", {})
        fps = meta.get("fps", 30.0)
        tracks_data = data.get("tracks", [])
        timeline_model = TimelineModel(fps=fps, num_tracks=len(tracks_data))
        for idx, track_dict in enumerate(tracks_data):
            for clip_dict in track_dict.get("clips", []):
                clip = TimelineModel.Clip.from_dict(clip_dict)
                timeline_model.add_clip(clip, track_index=idx)

        # player = PlayerModel()
        # return cls(project_dir, timeline_model, player, meta)
        return cls(project_dir, timeline_model, meta)

    def save(self):
        """
        Serialize metadata, tracks, and clips to project.json.
        """
        export = {
            "metadata": self.metadata,
            "tracks": [
                {"clips": [clip.to_dict() for clip in track.clips]}
                for track in self.timeline_model.tracks
            ],
        }
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(export, f, indent=2)

    def delete(self):
        """
        Remove the entire project folder from disk.
        """
        shutil.rmtree(self.project_dir)