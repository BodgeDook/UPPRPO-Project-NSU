import subprocess
import logging
from pathlib import Path
from platformdirs import user_cache_dir
from typing import Optional, Tuple

__all__ = ["render_video", "RenderError", "get_cache_dir"]

# ── Logging setup ─────────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # or INFO in prod
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
logger.addHandler(handler)


# ── Exceptions ────────────────────────────────────────────────────────────────
class RenderError(Exception):
    """Raised when the render subprocess exits with an error."""


# ── Cache directory ───────────────────────────────────────────────────────────
def get_cache_dir(app_name: str = "uMovie") -> Path:
    """
    Returns a per-user cache directory, e.g.
      - macOS: ~/Library/Caches/uMovie
      - Linux: ~/.cache/uMovie
      - Windows: %LOCALAPPDATA%\\uMovie\\Cache
    """
    cache_dir = Path(user_cache_dir(app_name, appauthor=False))
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


# ── Main wrapper function ─────────────────────────────────────────────────────
def render_video(
    input_path: str,
    output_path: str,
    codec: str,
    resolution: str,
    filters: Optional[str] = None,
    cache_dir: Optional[Path] = None,
    timeout: Optional[float] = None,
) -> Tuple[str, str]:
    """
    Calls the `render` executable with the provided arguments.

    Args:
        input_path:   path to the input video (e.g. "in.mp4")
        output_path:  path to write the output (e.g. "out.mp4")
        codec:        codec name (e.g. "H.264")
        resolution:   resolution string (e.g. "1920x1080")
        filters:      optional FFmpeg filter string
        cache_dir:    where to store any temp files; defaults to user cache
        timeout:      seconds to wait before killing the process

    Returns:
        (stdout, stderr) from the `render` process.

    Raises:
        RenderError if the process exits with non-zero code.
    """
    # Determine cache directory
    cache = cache_dir or get_cache_dir()
    logger.debug(f"Using cache directory: {cache}")

    # Build command
    cmd = [
        "./render",
        "-input",  input_path,
        "-output", output_path,
        "-codec",  codec,
        "-res",    resolution,
    ]
    if filters:
        # if your CLI supports something like "-filter", adjust as needed
        cmd += ["-filter", filters]

    logger.info(f"Running command: {' '.join(cmd)}")

    try:
        proc = subprocess.run(
            cmd,
            cwd=cache,              # in case you want to drop temp files here
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as e:
        logger.error(f"Render timed out after {timeout}s")
        raise RenderError(f"Timeout after {timeout} seconds") from e

    # Log stdout/stderr
    if proc.stdout:
        logger.debug("Render stdout:\n" + proc.stdout)
    if proc.stderr:
        logger.warning("Render stderr:\n" + proc.stderr)

    if proc.returncode != 0:
        msg = f"Render failed (exit code {proc.returncode})"
        logger.error(msg)
        raise RenderError(msg + "\n" + proc.stderr.strip())

    logger.info("Render completed successfully")
    return proc.stdout, proc.stderr
