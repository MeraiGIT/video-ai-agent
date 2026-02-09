"""First/last frame capability — generates keyframe pairs for motion graphics.

Uses Nano Banana Pro to generate start and end frame images,
which are then passed to video gen models (Veo 3.1) that support
first/last frame input for smooth motion graphics transitions.
"""

import logging

logger = logging.getLogger(__name__)


def execute(params: dict, state: dict, ctx: dict) -> dict:
    """Generate first and last keyframe images.

    params:
        first_frame_prompt: str — description of the start frame
        last_frame_prompt: str — description of the end frame
        style: str — optional shared style description
    """
    first_prompt = params.get("first_frame_prompt", "")
    last_prompt = params.get("last_frame_prompt", "")
    style = params.get("style", "")

    if not first_prompt or not last_prompt:
        raise ValueError("Both first_frame_prompt and last_frame_prompt required")

    if style:
        first_prompt = f"{first_prompt}, {style}"
        last_prompt = f"{last_prompt}, {style}"

    job_id = state.get("job_id", "unknown")

    from services.nanana_service import generate_image

    # Generate both frames
    first_result = generate_image(
        prompt=first_prompt, job_id=job_id, filename="first_frame.png"
    )
    last_result = generate_image(
        prompt=last_prompt, job_id=job_id, filename="last_frame.png"
    )

    return {
        "first_frame_url": first_result["url"],
        "last_frame_url": last_result["url"],
        "model": "nano_banana_pro",
        "cost": 0.06,  # 2 images
    }
