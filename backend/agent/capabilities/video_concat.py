"""Video concatenation capability — wraps ffmpeg_service."""

import logging

logger = logging.getLogger(__name__)


def execute(params: dict, state: dict, ctx: dict) -> dict:
    """Concatenate video clips with optional transitions.

    params:
        video_paths: list[str] — ordered list of video file paths
        transition: str — "cut", "fade", "dissolve", "wipeleft", etc.
        transition_duration: float — seconds (default 0.5)
    """
    video_paths = params.get("video_paths", [])
    if not video_paths:
        # Auto-collect from state
        videos = state.get("videos", [])
        video_paths = [v["local_path"] for v in videos if v.get("local_path")]

    if not video_paths:
        raise ValueError("No video paths to concatenate")

    transition = params.get("transition", "cut")
    transition_duration = params.get("transition_duration", 0.5)
    job_id = state.get("job_id", "unknown")

    from services.ffmpeg_service import concat_videos, concat_videos_with_transitions

    if transition == "cut":
        path = concat_videos(video_paths, job_id)
    else:
        path = concat_videos_with_transitions(
            video_paths, job_id,
            transition=transition,
            transition_duration=transition_duration,
        )

    return {
        "path": path,
        "model": "ffmpeg",
        "cost": 0.0,
    }
