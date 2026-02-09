"""Video generation capability — wraps video_router.

Routes to the correct provider (fal.ai or Kie AI) based on model.
Handles model-specific duration formats and prompt formatting.
"""

import logging

from agent.capabilities.prompt_engineering import format_for_video_model

logger = logging.getLogger(__name__)


def execute(params: dict, state: dict, ctx: dict) -> dict:
    """Generate a video clip from an image and/or text prompt.

    params:
        prompt: str — the video description
        model: str — model_id
        image_url: str — input image (required for most models)
        duration: float — desired duration in seconds
        reference_images: list[str] — for kling_ref character consistency
        first_frame_url: str — for veo3.1 motion graphics
        last_frame_url: str — for veo3.1 motion graphics
    """
    model = params.get("model", "veo3.1")
    prompt = params.get("prompt", "")
    image_url = params.get("image_url", "")
    duration = params.get("duration", 5)
    job_id = state.get("job_id", "unknown")

    # Format prompt for the specific model
    scene_data = {
        "visual_description": prompt,
        "video_prompt": prompt,
        "camera": params.get("camera", {}),
    }
    formatted = format_for_video_model(scene_data, model)

    from services.video_router import generate_video

    filename = params.get("filename", f"video_{params.get('step', 0)}.mp4")

    # Build extra kwargs for specific models
    kwargs: dict = {}
    if model == "kling_ref" and params.get("reference_images"):
        kwargs["reference_images"] = params["reference_images"]
        kwargs["elements"] = params.get("elements")

    local_path = generate_video(
        model_id=model,
        image_url=image_url,
        prompt=formatted,
        duration=duration,
        job_id=job_id,
        filename=filename,
        **kwargs,
    )

    # Cost lookup from model cards
    from agent.capabilities.registry import MODEL_CARDS
    cost = MODEL_CARDS.get(model, {}).get("cost_per_unit", 0.15)

    return {
        "url": "",
        "local_path": local_path,
        "model": model,
        "cost": cost,
        "duration": duration,
        "prompt": formatted,
    }
