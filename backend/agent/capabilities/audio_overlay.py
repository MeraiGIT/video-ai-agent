"""Audio overlay capability — wraps ffmpeg_service.overlay_audio."""

import logging

logger = logging.getLogger(__name__)


def execute(params: dict, state: dict, ctx: dict) -> dict:
    """Overlay an audio track onto a video.

    params:
        video_path: str — input video file
        audio_path: str — audio to overlay
    """
    video_path = params.get("video_path", state.get("assembled_path", ""))
    audio_path = params.get("audio_path", state.get("mixed_audio_path", state.get("voiceover_path", "")))

    if not video_path:
        raise ValueError("No video_path for audio overlay")
    if not audio_path:
        raise ValueError("No audio_path for audio overlay")

    job_id = state.get("job_id", "unknown")

    from services.ffmpeg_service import overlay_audio
    path = overlay_audio(video_path, audio_path, job_id)

    return {
        "path": path,
        "model": "ffmpeg",
        "cost": 0.0,
    }
