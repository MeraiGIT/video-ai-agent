"""Music generation capability — wraps ElevenLabs or similar."""

import logging

logger = logging.getLogger(__name__)


def execute(params: dict, state: dict, ctx: dict) -> dict:
    """Generate background music.

    params:
        prompt: str — music description (style, tempo, mood)
        duration: float — desired duration in seconds
    """
    prompt = params.get("prompt", "")
    if not prompt:
        # Derive from blueprint audio_map
        blueprint = state.get("blueprint", {})
        audio_map = blueprint.get("audio_map", {})
        music = audio_map.get("music", {})
        prompt = music.get("style", "upbeat background music")

    job_id = state.get("job_id", "unknown")

    try:
        from services.elevenlabs_service import generate_sfx
        # Use SFX endpoint for music-like generation
        path = generate_sfx(prompt, job_id, filename="music.mp3")
        return {
            "path": path,
            "model": "elevenlabs",
            "cost": 0.05,
        }
    except (ImportError, AttributeError, Exception) as e:
        logger.warning("Music generation failed: %s — returning empty", e)
        return {
            "path": "",
            "model": "elevenlabs",
            "cost": 0.0,
            "error": str(e),
        }
