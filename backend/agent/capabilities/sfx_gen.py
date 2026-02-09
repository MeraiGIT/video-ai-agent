"""Sound effects generation capability — wraps ElevenLabs SFX."""

import logging

logger = logging.getLogger(__name__)


def execute(params: dict, state: dict, ctx: dict) -> dict:
    """Generate a sound effect.

    params:
        prompt: str — SFX description (e.g., "whoosh", "explosion", "rain")
        duration: float — optional desired duration
    """
    prompt = params.get("prompt", "")
    if not prompt:
        raise ValueError("No prompt for SFX generation")

    job_id = state.get("job_id", "unknown")
    filename = params.get("filename", "sfx.mp3")

    try:
        from services.elevenlabs_service import generate_sfx
        path = generate_sfx(prompt, job_id, filename=filename)
        return {
            "path": path,
            "model": "elevenlabs",
            "cost": 0.02,
        }
    except (ImportError, AttributeError, Exception) as e:
        logger.warning("SFX generation failed: %s", e)
        return {
            "path": "",
            "model": "elevenlabs",
            "cost": 0.0,
            "error": str(e),
        }
