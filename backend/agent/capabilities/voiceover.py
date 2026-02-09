"""Voiceover capability — wraps elevenlabs_service TTS."""

import logging

logger = logging.getLogger(__name__)


def execute(params: dict, state: dict, ctx: dict) -> dict:
    """Generate text-to-speech voiceover.

    params:
        text: str — script text to convert to speech
        voice_id: str — optional ElevenLabs voice ID
    """
    text = params.get("text", "")
    if not text:
        # Try to get script from state or blueprint
        text = state.get("script", "")
        if not text:
            blueprint = state.get("blueprint", {})
            audio_map = blueprint.get("audio_map", {})
            vo = audio_map.get("voiceover", {})
            text = vo.get("full_script", "")
    if not text:
        raise ValueError("No text provided for voiceover")

    job_id = state.get("job_id", "unknown")

    from services.elevenlabs_service import generate_tts
    path = generate_tts(text, job_id)

    return {
        "path": path,
        "model": "elevenlabs",
        "cost": 0.03,
        "duration": None,  # Unknown until file is analyzed
    }
