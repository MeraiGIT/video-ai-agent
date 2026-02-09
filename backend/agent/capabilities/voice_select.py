"""Voice selection capability — search ElevenLabs voice library."""

import logging

logger = logging.getLogger(__name__)


def execute(params: dict, state: dict, ctx: dict) -> dict:
    """Search for a voice matching criteria.

    params:
        gender: str — "male" or "female"
        age: str — "young", "middle_aged", "old"
        accent: str — optional accent filter
        description: str — free-text voice description
    """
    description = params.get("description", "")
    gender = params.get("gender", "")
    age = params.get("age", "")

    # Build search query
    query_parts = []
    if description:
        query_parts.append(description)
    if gender:
        query_parts.append(gender)
    if age:
        query_parts.append(age)
    query = " ".join(query_parts) or "professional narrator"

    try:
        from services.elevenlabs_service import search_voices
        voices = search_voices(query)
        if voices:
            voice = voices[0]
            return {
                "voice_id": voice.get("voice_id", ""),
                "name": voice.get("name", ""),
                "model": "elevenlabs",
                "cost": 0.0,
            }
    except (ImportError, AttributeError):
        logger.warning("Voice search not available, using default voice")

    # Fallback: use default voice
    return {
        "voice_id": "",
        "name": "default",
        "model": "elevenlabs",
        "cost": 0.0,
    }
