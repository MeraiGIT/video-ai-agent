"""Text overlay capability — wraps ffmpeg_service.add_text_overlay_to_video."""

import logging

logger = logging.getLogger(__name__)


def execute(params: dict, state: dict, ctx: dict) -> dict:
    """Add animated text overlay to video.

    params:
        video_path: str — input video file
        text: str — text to overlay
        position: str — center, top, bottom, top-left, etc.
        font_size: int — default 48
        font_color: str — default "white"
        start_time: float — when to show (seconds)
        end_time: float — when to hide (seconds, None for whole video)
        fade_in: float — fade-in duration
        fade_out: float — fade-out duration
    """
    video_path = params.get("video_path", "")
    text = params.get("text", "")

    if not video_path or not text:
        raise ValueError("text_overlay requires video_path and text")

    job_id = state.get("job_id", "unknown")

    from services.ffmpeg_service import add_text_overlay_to_video
    path = add_text_overlay_to_video(
        video_path=video_path,
        text=text,
        job_id=job_id,
        position=params.get("position", "center"),
        font_size=params.get("font_size", 48),
        font_color=params.get("font_color", "white"),
        font_name=params.get("font_name", "Arial"),
        start_time=params.get("start_time", 0.0),
        end_time=params.get("end_time"),
        fade_in=params.get("fade_in", 0.5),
        fade_out=params.get("fade_out", 0.5),
    )

    return {
        "path": path,
        "model": "ffmpeg",
        "cost": 0.0,
    }
