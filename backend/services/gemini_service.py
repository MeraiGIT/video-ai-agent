"""
Gemini 2.5 Pro service — vision/multimodal analysis.

Uses Gemini to SEE images, WATCH videos, and LISTEN to audio
for quality evaluation in the quality gate.
"""

import logging
import os
from typing import Optional

from config import settings

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    """Lazy-load the Gemini client singleton."""
    global _client
    if _client is None:
        if not settings.GOOGLE_API_KEY:
            raise RuntimeError("GOOGLE_API_KEY not set — Gemini service unavailable")
        from google import genai
        _client = genai.Client(api_key=settings.GOOGLE_API_KEY)
    return _client


MODEL = "gemini-2.5-pro"


def analyze_image(image_url: str, prompt: str) -> str:
    """Send an image to Gemini vision for analysis.

    Args:
        image_url: Public URL or local path to an image.
        prompt: Analysis prompt (e.g., quality evaluation criteria).

    Returns:
        Gemini's text response with the analysis.
    """
    from google.genai import types
    from PIL import Image
    import urllib.request
    import tempfile

    client = _get_client()

    # Download image if URL
    if image_url.startswith(("http://", "https://")):
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        urllib.request.urlretrieve(image_url, tmp.name)
        image = Image.open(tmp.name)
    else:
        image = Image.open(image_url)

    response = client.models.generate_content(
        model=MODEL,
        contents=[image, prompt],
    )
    logger.info("[gemini] Image analysis complete (%d chars)", len(response.text))
    return response.text


def analyze_video(video_path_or_url: str, prompt: str) -> str:
    """Send a video to Gemini vision for analysis.

    Uploads the video via the File API for processing.

    Args:
        video_path_or_url: Local path or URL to a video file.
        prompt: Analysis prompt.

    Returns:
        Gemini's text response.
    """
    from services.ffmpeg_service import download_if_url

    client = _get_client()

    # Ensure local file
    local_path = video_path_or_url
    if video_path_or_url.startswith(("http://", "https://")):
        import tempfile
        import urllib.request
        tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        urllib.request.urlretrieve(video_path_or_url, tmp.name)
        local_path = tmp.name

    # Upload to Gemini File API
    uploaded_file = client.files.upload(file=local_path)
    logger.info("[gemini] Video uploaded for analysis: %s", uploaded_file.name)

    response = client.models.generate_content(
        model=MODEL,
        contents=[uploaded_file, prompt],
    )
    logger.info("[gemini] Video analysis complete (%d chars)", len(response.text))
    return response.text


def analyze_audio(audio_path: str, prompt: str) -> str:
    """Send audio to Gemini for analysis (clarity, pronunciation, pacing).

    Args:
        audio_path: Local path to an audio file.
        prompt: Analysis prompt.

    Returns:
        Gemini's text response.
    """
    from google.genai import types

    client = _get_client()

    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    # Determine MIME type
    ext = os.path.splitext(audio_path)[1].lower()
    mime_map = {".mp3": "audio/mp3", ".wav": "audio/wav", ".m4a": "audio/mp4"}
    mime_type = mime_map.get(ext, "audio/mp3")

    response = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
            prompt,
        ],
    )
    logger.info("[gemini] Audio analysis complete (%d chars)", len(response.text))
    return response.text


def generate_text(prompt: str, system_instruction: str = "") -> str:
    """Simple text generation with Gemini (no multimodal input).

    Useful for tasks where Gemini's reasoning is preferred over Claude.
    """
    client = _get_client()

    config = {}
    if system_instruction:
        from google.genai import types
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
        )

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=config if config else None,
    )
    return response.text
