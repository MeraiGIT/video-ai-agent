"""
fal.ai provider — image generation, image-to-image, video generation,
and reference-to-video (character consistency).
"""

import fal_client
from tenacity import retry, stop_after_attempt, wait_exponential


def _on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in update.logs:
            print(f"  [fal] {log['message']}")


# ---------------------------------------------------------------------------
# Image generation
# ---------------------------------------------------------------------------

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=4, max=60),
)
def generate_image(prompt: str) -> dict:
    """Generate an image with Seedream 4.5 (text-to-image)."""
    result = fal_client.subscribe(
        "fal-ai/bytedance/seedream/v4.5/text-to-image",
        arguments={
            "prompt": prompt,
            "image_size": "landscape_16_9",
            "num_images": 1,
            "enable_safety_checker": False,
        },
        with_logs=True,
        on_queue_update=_on_queue_update,
    )
    return result


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=4, max=60),
)
def transform_image(image_url: str, prompt: str, strength: float = 0.85) -> dict:
    """Transform an existing image using FLUX.1 [dev] image-to-image.

    strength: 0.0 = no change, 1.0 = full transformation.
    0.7-0.85 is recommended to preserve subject while applying changes.
    """
    result = fal_client.subscribe(
        "fal-ai/flux/dev/image-to-image",
        arguments={
            "image_url": image_url,
            "prompt": prompt,
            "strength": strength,
            "num_inference_steps": 40,
            "guidance_scale": 3.5,
            "num_images": 1,
            "enable_safety_checker": False,
            "output_format": "jpeg",
        },
        with_logs=True,
        on_queue_update=_on_queue_update,
    )
    return result


# ---------------------------------------------------------------------------
# Video generation — standard image-to-video (Seedance only on fal)
# ---------------------------------------------------------------------------

def _format_duration_seedance(duration: float) -> int:
    """Seedance accepts integer 4-12."""
    return int(min(max(duration, 4), 12))


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=10, max=120),
)
def generate_video_seedance(
    image_url: str, prompt: str, duration: float
) -> dict:
    """Generate video from image using Seedance 1.5 Pro via fal.ai."""
    result = fal_client.subscribe(
        "fal-ai/bytedance/seedance/v1.5/pro/image-to-video",
        arguments={
            "prompt": prompt,
            "image_url": image_url,
            "duration": _format_duration_seedance(duration),
            "aspect_ratio": "16:9",
            "resolution": "720p",
            "generate_audio": False,
            "enable_safety_checker": False,
        },
        with_logs=True,
        on_queue_update=_on_queue_update,
    )
    return result


# ---------------------------------------------------------------------------
# Video generation — reference-to-video (Kling O1, character consistency)
# ---------------------------------------------------------------------------

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=10, max=120),
)
def generate_reference_video(
    prompt: str,
    image_urls: list[str] | None = None,
    elements: list[dict] | None = None,
    duration: float = 5,
    aspect_ratio: str = "16:9",
) -> dict:
    """Generate video with character/style consistency using Kling O1.

    Use @Image1/@Image2 in prompt to reference image_urls (1-indexed).
    Use @Element1/@Element2 to reference elements (1-indexed).
    Max 7 total references across images + elements.

    elements: list of {"frontal_image_url": str, "reference_image_urls": [str]}
    """
    dur = str(int(min(max(duration, 3), 10)))

    arguments = {
        "prompt": prompt,
        "duration": dur,
        "aspect_ratio": aspect_ratio,
    }

    if image_urls:
        arguments["image_urls"] = image_urls
    if elements:
        arguments["elements"] = elements

    result = fal_client.subscribe(
        "fal-ai/kling-video/o1/reference-to-video",
        arguments=arguments,
        with_logs=True,
        on_queue_update=_on_queue_update,
    )
    return result
