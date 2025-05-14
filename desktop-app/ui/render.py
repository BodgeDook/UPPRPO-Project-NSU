from pathlib import Path
from render_wrapper import render_video, RenderError

def on_start_render():
    try:
        stdout, stderr = render_video(
            input_path="in.mp4",
            output_path="out.mp4",
            codec="H.264",
            resolution="1280x720",
            filters="scale=1280:720",
            # timeout=300,  # optional
        )
        # update UI: done!
    except RenderError as e:
        # show error dialog: e
        print("Rendering failed:", e)
