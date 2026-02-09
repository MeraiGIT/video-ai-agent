"""Caption burn capability — transcribes then burns captions into video."""

import logging

logger = logging.getLogger(__name__)


def execute(params: dict, state: dict, ctx: dict) -> dict:
    """Transcribe audio and burn captions into video.

    params:
        video_path: str — input video file
        style: str — caption style preset (tiktok, youtube, cinematic, etc.)
        word_by_word: bool — use word-level timing (default True)
    """
    video_path = params.get("video_path", state.get("polished_path", state.get("assembled_path", "")))
    style = params.get("style", state.get("caption_style", "youtube"))
    word_by_word = params.get("word_by_word", True)
    job_id = state.get("job_id", "unknown")

    if not video_path:
        raise ValueError("No video_path for caption burn")

    from services.ffmpeg_service import extract_audio, burn_subtitles

    # Step 1: Extract audio
    audio_path = extract_audio(video_path, job_id)

    # Step 2: Transcribe to SRT
    if word_by_word:
        from services.whisper_service import transcribe_to_word_srt
        srt_path = transcribe_to_word_srt(audio_path, job_id)
    else:
        from services.whisper_service import transcribe_to_srt
        srt_path = transcribe_to_srt(audio_path, job_id)

    # Step 3: Burn subtitles
    captioned_path = burn_subtitles(
        video_path, srt_path, job_id, style_name=style,
    )

    return {
        "path": captioned_path,
        "srt_path": srt_path,
        "model": "faster-whisper + ffmpeg",
        "cost": 0.0,
    }
