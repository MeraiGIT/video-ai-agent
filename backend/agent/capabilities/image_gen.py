"""Image generation capability — wraps fal_service + nanana_service.

Generates images from text prompts using the model specified in params.
Supports Seedream 4.5, FLUX Dev (i2i), and Nano Banana Pro.
"""

import logging

from agent.capabilities.prompt_engineering import format_for_image_model

logger = logging.getLogger(__name__)


def execute(params: dict, state: dict, ctx: dict) -> dict:
    """Generate an image from a text prompt.

    params:
        prompt: str — the image description
        model: str — model_id (seedream-4.5, flux_dev_i2i, nano_banana_pro)
        aspect_ratio: str — optional, e.g. "16:9", "1:1"
        reference_image_url: str — required for flux_dev_i2i
        strength: float — for i2i, 0.0-1.0 (default 0.85)
        negative_prompt: str — optional, for models that support it
    """
    model = params.get("model", "seedream-4.5")
    prompt = params.get("prompt", "")
    job_id = state.get("job_id", "unknown")

    # Format prompt for the specific model
    scene_data = {
        "visual_description": prompt,
        "image_prompt": prompt,
    }
    formatted = format_for_image_model(scene_data, model)

    if model == "nano_banana_pro":
        from services.nanana_service import generate_image
        result = generate_image(
            prompt=formatted,
            job_id=job_id,
            filename=params.get("filename", ""),
        )
        return {
            "url": result["url"],
            "local_path": result.get("local_path", ""),
            "model": model,
            "cost": 0.03,
            "prompt": formatted,
        }

    if model == "flux_dev_i2i":
        from services.fal_service import transform_image
        ref_url = params.get("reference_image_url", "")
        if not ref_url:
            raise ValueError("flux_dev_i2i requires reference_image_url")
        result = transform_image(
            image_url=ref_url,
            prompt=formatted,
            strength=params.get("strength", 0.85),
        )
        url = result["images"][0]["url"]
        return {
            "url": url,
            "local_path": "",
            "model": model,
            "cost": 0.03,
            "prompt": formatted,
        }

    # Default: seedream-4.5
    from services.fal_service import generate_image
    result = generate_image(prompt=formatted)
    url = result["images"][0]["url"]
    return {
        "url": url,
        "local_path": "",
        "model": model,
        "cost": 0.04,
        "prompt": formatted,
    }
