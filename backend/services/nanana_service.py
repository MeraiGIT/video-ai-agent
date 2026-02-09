"""
Nanana AI service — Nano Banana Pro image generation.

Used for fast stylized image generation, especially for
motion graphics keyframes (first/last frame pairs).
"""

import logging
import os
import time
import urllib.request
from config import settings
from utils.file_manager import get_job_path

logger = logging.getLogger(__name__)


def generate_image(prompt: str, job_id: str, filename: str = "") -> dict:
    """Generate an image using Nano Banana Pro via Nanana AI API.

    Args:
        prompt: Image generation prompt.
        job_id: Workspace job ID for saving the file.
        filename: Optional output filename.

    Returns:
        {"url": str, "local_path": str}
    """
    if not settings.NANANA_API_KEY:
        raise RuntimeError("NANANA_API_KEY not set — Nanana service unavailable")

    import requests

    logger.info("[nanana] Generating image: %s", prompt[:80])

    response = requests.post(
        "https://api.nanana.ai/v1/images/generations",
        headers={
            "Authorization": f"Bearer {settings.NANANA_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "prompt": prompt,
            "model": "nano-banana-pro",
            "n": 1,
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()

    image_url = data["data"][0]["url"]
    logger.info("[nanana] Image generated: %s", image_url[:80])

    # Download to workspace
    if not filename:
        filename = f"nanana_{int(time.time())}.png"
    local_path = get_job_path(job_id, filename)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    urllib.request.urlretrieve(image_url, local_path)

    return {"url": image_url, "local_path": local_path}
