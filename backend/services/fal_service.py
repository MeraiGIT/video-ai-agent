import fal_client
from tenacity import retry, stop_after_attempt, wait_exponential

VIDEO_MODEL_ENDPOINTS = {
    "seedance": "fal-ai/bytedance/seedance/v1.5/pro/image-to-video",
    "veo": "fal-ai/veo3.1/image-to-video",
    "kling": "fal-ai/kling-video/o3/standard/image-to-video",
}


def _on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in update.logs:
            print(f"  [fal] {log['message']}")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=4, max=60),
)
def generate_image(prompt: str) -> dict:
    """Generate an image with Seedream 4.5 via fal.ai."""
    result = fal_client.subscribe(
        "fal-ai/bytedance/seedream/v4.5/text-to-image",
        arguments={
            "prompt": prompt,
            "image_size": "landscape_16_9",
            "num_images": 1,
            "enable_safety_checker": True,
        },
        with_logs=True,
        on_queue_update=_on_queue_update,
    )
    return result


def _format_duration(model: str, duration: float) -> str | int:
    """Format duration for the specific video model's API."""
    if model == "veo":
        # Veo accepts "4s", "6s", "8s"
        seconds = int(min(max(duration, 4), 8))
        # Snap to closest valid value
        valid = [4, 6, 8]
        closest = min(valid, key=lambda x: abs(x - seconds))
        return f"{closest}s"
    elif model == "seedance":
        # Seedance accepts integer 4-12
        return int(min(max(duration, 4), 12))
    elif model == "kling":
        # Kling O3 accepts 3-15 seconds as string
        return str(int(min(max(duration, 3), 15)))
    return str(int(duration))


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=10, max=120),
)
def generate_video(
    model: str, image_url: str, prompt: str, duration: float
) -> dict:
    """Generate video from image using the selected model via fal.ai."""
    endpoint = VIDEO_MODEL_ENDPOINTS[model]

    arguments = {
        "prompt": prompt,
        "image_url": image_url,
        "duration": _format_duration(model, duration),
        "generate_audio": False,  # We use our own voiceover
    }

    # Model-specific parameters
    if model == "veo":
        arguments["aspect_ratio"] = "16:9"
        arguments["resolution"] = "720p"
    elif model == "seedance":
        arguments["aspect_ratio"] = "16:9"
        arguments["resolution"] = "720p"
    elif model == "kling":
        arguments["aspect_ratio"] = "16:9"

    result = fal_client.subscribe(
        endpoint,
        arguments=arguments,
        with_logs=True,
        on_queue_update=_on_queue_update,
    )
    return result
