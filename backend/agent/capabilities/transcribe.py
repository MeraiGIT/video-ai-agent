"""Transcription capability — wraps whisper_service."""

import logging

logger = logging.getLogger(__name__)


def execute(params: dict, state: dict, ctx: dict) -> dict:
    """Transcribe audio to SRT subtitles.

    params:
        audio_path: str — input audio file
        word_level: bool — word-by-word timestamps (default True)
    """
    audio_path = params.get("audio_path", state.get("voiceover_path", ""))
    word_level = params.get("word_level", True)

    if not audio_path:
        raise ValueError("No audio_path for transcription")

    job_id = state.get("job_id", "unknown")

    if word_level:
        from services.whisper_service import transcribe_to_word_srt
        srt_path = transcribe_to_word_srt(audio_path, job_id)
    else:
        from services.whisper_service import transcribe_to_srt
        srt_path = transcribe_to_srt(audio_path, job_id)

    return {
        "path": srt_path,
        "model": "faster-whisper",
        "cost": 0.0,
    }
