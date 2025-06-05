# desktop-app/models/project.py

import json
import os
import shutil
import uuid

from PyQt5.QtCore import QStandardPaths
from .timeline import TimelineModel
from .render import PlayerModel  # your existing C++/FFmpeg wrapper


class Project:
    """
    Represents a single video‐editing project. 
    On disk, each project lives in a folder with:
      ├─ project.json
      ├─ assets/
      └─ cache/
    """

    def __init__(self, project_dir, timeline_model, player_model, metadata=None):
        self.project_dir = project_dir
        self.assets_dir = os.path.join(project_dir, "assets")
        self.cache_dir = os.path.join(project_dir, "cache")
        self.json_path = os.path.join(project_dir, "project.json")
        self.timeline_model = timeline_model
        self.player = player_model
        self.metadata = metadata or {}

    @classmethod
    def create_new(cls, base_dir):
        """
        Create a brand‐new project under base_dir. 
        `base_dir` is assumed to be an existing directory (e.g. uMovie/desktop-app/dev-cache/NewProjectXYZ).
        """
        # Ensure the base directory exists
        os.makedirs(base_dir, exist_ok=True)

        # Inside it, create subfolders: assets/ and cache/
        assets_dir = os.path.join(base_dir, "assets")
        cache_dir = os.path.join(base_dir, "cache")
        os.makedirs(assets_dir, exist_ok=True)
        os.makedirs(cache_dir, exist_ok=True)

        # Instantiate an empty TimelineModel (0 frames initially)
        timeline_model = TimelineModel(duration_frames=0)

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
    def load_from_file(cls, json_path):
        """
        Load a project JSON from disk. 
        `json_path` should be something like /.../myProject/project.json.
        """
        project_dir = os.path.dirname(json_path)
        with open(json_path, "r") as f:
            data = json.load(f)

        # Recreate the TimelineModel from stored clip data
        timeline_model = TimelineModel.from_dict(data["timeline_model"])

        # If at least one asset exists, point the PlayerModel to it (for preview)
        if data.get("clips"):
            first_clip = data["clips"][0]
            asset_rel = first_clip["asset_rel_path"]  # e.g. "assets/video1.mp4"
            asset_abs = os.path.join(project_dir, asset_rel)
            player_model = PlayerModel(asset_abs)
        else:
            player_model = PlayerModel.blank()

        project = cls(
            project_dir,
            timeline_model,
            player_model,
            metadata=data.get("metadata", {}),
        )
        return project

    def save(self):
        """
        Serialize project to project.json, including:
          - metadata
          - timeline_model.to_dict()
          - clips list with relative paths for assets
        """
        data = {
            "metadata": self.metadata,
            "timeline_model": self.timeline_model.to_dict(),
            # We'll store a flat list of clips with their asset paths:
            "clips": [],
        }

        for clip in self.timeline_model.get_clips():
            data["clips"].append(
                {
                    "id": clip["id"],
                    "start_frame": clip["start_frame"],
                    "end_frame": clip["end_frame"],
                    "asset_rel_path": clip["asset_rel_path"],
                }
            )

        with open(self.json_path, "w") as f:
            json.dump(data, f, indent=2)

    def add_asset(self, source_file_path):
        """
        Copy the given video file into assets_dir, and register it as a new clip in the timeline.
        Returns the new clip dict.
        """
        # 1) Determine a unique filename under assets/
        filename = os.path.basename(source_file_path)
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        dest_path = os.path.join(self.assets_dir, unique_name)

        # 2) Copy the file
        shutil.copy2(source_file_path, dest_path)

        # 3) Ask the PlayerModel to open this newly copied asset so we can get its frame count
        new_player = PlayerModel(dest_path)
        total_frames = new_player.total_frames

        # 4) Register a new clip in the timeline model
        clip_id = self.timeline_model.next_clip_id()
        clip_dict = {
            "id": clip_id,
            "start_frame": 0,
            "end_frame": total_frames - 1,
            # We store the RELATIVE path so project can be moved and still load
            "asset_rel_path": os.path.relpath(dest_path, self.project_dir),
        }
        self.timeline_model.add_clip_dict(clip_dict)

        # 5) Now that we have a real asset, switch our “player” to preview that clip
        self.player = new_player

        # 6) Possibly update the timeline length to match this new clip if it’s longer
        self.timeline_model.total_frames = max(self.timeline_model.total_frames, total_frames)

        # 7) Persist the project
        self.save()

        return clip_dict
