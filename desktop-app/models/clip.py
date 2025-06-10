class Clip:
    """
    Represents one segment on a track.
    """
    def __init__(self,
                 asset_path: str,
                 in_frame: int,
                 out_frame: int,
                 timeline_start_frame: int):
        self.asset_path = asset_path
        self.in_frame = in_frame
        self.out_frame = out_frame
        self.timeline_start_frame = timeline_start_frame

    @property
    def duration(self) -> int:
        return self.out_frame - self.in_frame

    def contains_frame(self, frame: int) -> bool:
        """
        Does this clip cover `frame` on the timeline?
        """
        return (self.timeline_start_frame <= frame <
                self.timeline_start_frame + self.duration)