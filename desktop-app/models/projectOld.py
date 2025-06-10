# desktop-app/models/project.py

import json
import os
import shutil
import uuid

from PyQt5.QtCore import QStandardPaths
from .timeline import TimelineModel
from .render import PlayerModel  # your existing C++/FFmpeg wrapper

# bump this whenever you make a breaking change to project.json format
SCHEMA_VERSION = 1

class Project:
    """
    Represents a single video-editing project. 
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

        # 1) Check schema version (in the future you could migrate here)
        file_version = data.get("schema_version", 0)
        if file_version != SCHEMA_VERSION:
            # TODO: run migration routines if file_version < SCHEMA_VERSION
            pass

        # Recreate the TimelineModel from stored clip data
        timeline_model = TimelineModel.from_dict(data["timeline_model"])

        # # 3) Bind a player to the first clip, or blank
        # clips = data.get("clips", [])
        # if clips:
        #     first_path = os.path.join(project_dir, clips[0]["asset_rel_path"])
        #     player = PlayerModel(first_path)
        # else:
        #     player = PlayerModel.blank()
        # proj = cls(project_dir, timeline_model, player, metadata=data.get("metadata", {}))
        # return proj
    
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
          - schema_version
          - metadata
          - timeline_model.to_dict()
          - clips list with relative paths for assets
        """
        data = {
            "schema_version": SCHEMA_VERSION,
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
    
    def list_assets(self):
        """
        Return a list of all asset paths (relative to project_dir) in assets/.
        """
        rels = []
        for fname in os.listdir(self.assets_dir):
            absf = os.path.join(self.assets_dir, fname)
            if os.path.isfile(absf):
                rels.append(os.path.relpath(absf, self.project_dir))
        return rels

    def add_clip_from_asset(self, asset_rel_path, start_frame):
        """
        Insert a clip (referencing an existing asset) at start_frame.
        Simple overlap resolution: any existing clip that overlaps
        is bumped forward so ranges don’t collide.
        """
        # 1) Load its length via PlayerModel
        abs_path = os.path.join(self.project_dir, asset_rel_path)
        new_player = PlayerModel(abs_path)
        length = new_player.total_frames
        new_start = start_frame
        new_end = new_start + length - 1

        # 2) Nudge any overlapping existing clips
        for clip in self.timeline_model.get_clips():
            cs, ce = clip["start_frame"], clip["end_frame"]
            # overlap if cs ≤ new_end AND ce ≥ new_start
            if not (ce < new_start or cs > new_end):
                shift = (new_end + 1) - cs
                clip["start_frame"] += shift
                clip["end_frame"]   += shift
        # emit so timeline repaints the nudged clips
        self.timeline_model.dataChanged.emit()

        # 3) Build the new clip dict
        cid = self.timeline_model.next_clip_id()
        clip_dict = {
            "id": cid,
            "start_frame": new_start,
            "end_frame": new_end,
            "asset_rel_path": asset_rel_path,
        }
        # 4) Insert into timeline
        self.timeline_model.add_clip_dict(clip_dict)

        # 5) Switch preview to this asset
        self.player = new_player
        # 6) Update overall timeline length (if needed)
        self.timeline_model.total_frames = max(
            self.timeline_model.total_frames, new_end + 1
        )
        # 7) Persist
        self.save()
        return clip_dict
    
    def get_clip_at_frame(self, frame_number: int):
        """
        Return the clip dict whose [start_frame, end_frame] covers
        frame_number, or None if there’s no clip there.
        """
        for clip in self.timeline_model.get_clips():
            if clip["start_frame"] <= frame_number <= clip["end_frame"]:
                return clip
        return None
    
    # ------------------------------------------------------------------
    # NEW: Given a global frame index, tell the UI which file+position
    #      to show.  Returns (absolute_path, position_ms) or None.
    # ------------------------------------------------------------------
    # def source_at_frame(self, frame: int) -> Tuple[str, int]:
    #     """
    #     Look up the clip that covers `frame` and translate the global frame
    #     into a timestamp **inside that clip**.

    #     Returns:
    #         (absolute_file_path, position_ms) if a clip exists there,
    #         or None if the play-head is on an empty gap.
    #     """
    #     clip = self.timeline_model.get_clip_at_frame(frame)
    #     if clip is None:
    #         return None

    #     # absolute file path
    #     abs_path = os.path.join(self.project_dir, clip["asset_rel_path"])

    #     # convert global frame → local position in ms
    #     local_frame = frame - clip["start_frame"]
    #     fps         = clip.get("fps", 30.0)          # sensible fallback
    #     pos_ms      = int(local_frame / fps * 1000)

    #     return abs_path, pos_ms
