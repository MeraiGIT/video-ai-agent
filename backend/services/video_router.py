"""
Video routing layer — routes generation requests to the correct provider
based on the model registry.
"""

import logging
from services.model_registry import get_video_model
from services import fal_service, kie_service
from utils.file_manager import download_file

logger = logging.getLogger(__name__)


def generate_video(
    model_id: str,
    image_url: str,
    prompt: str,
    duration: float,
    job_id: str,
    filename: str,
    reference_images: list[str] | None = None,
    elements: list[dict] | None = None,
) -> str:
    """Generate a video and download it to workspace. Returns local path.

    Routes to the correct provider (fal.ai or Kie AI) based on model_id.
    For character-consistent generation (kling_ref), pass reference_images/elements.
    """
    model = get_video_model(model_id)
    provider = model["provider"]

    logger.info(f"[router] Generating video: model={model_id}, provider={provider}")

    if model_id == "kling_ref":
        # Character consistency via Kling O1 reference-to-video
        result = fal_service.generate_reference_video(
            prompt=prompt,
            image_urls=reference_images or ([image_url] if image_url else None),
            elements=elements,
            duration=duration,
            aspect_ratio="16:9",
        )
        video_url = result["video"]["url"]

    elif provider == "fal":
        # Seedance on fal.ai
        result = fal_service.generate_video_seedance(
            image_url=image_url,
            prompt=prompt,
            duration=duration,
        )
        video_url = result["video"]["url"]

    elif provider == "kie":
        if model_id == "veo":
            result = kie_service.generate_video_veo3(
                prompt=prompt,
                image_url=image_url,
                aspect_ratio="16:9",
                model="veo3_fast",
            )
        elif model_id == "kling":
            result = kie_service.generate_video_kling(
                prompt=prompt,
                image_url=image_url,
                duration=duration,
                aspect_ratio="16:9",
            )
        else:
            raise ValueError(f"Unknown Kie AI model: {model_id}")
        video_url = result["video"]["url"]

    else:
        raise ValueError(f"Unknown provider '{provider}' for model '{model_id}'")

    # Download to workspace
    local_path = download_file(video_url, job_id, filename)
    logger.info(f"[router] Video saved: {local_path}")
    return local_path


def generate_image_for_scene(
    prompt: str,
    job_id: str,
    filename: str,
    reference_image_url: str | None = None,
    strength: float = 0.85,
) -> tuple[str, str]:
    """Generate a scene image. Returns (image_url, local_path).

    If reference_image_url is provided, uses FLUX dev image-to-image
    to preserve the subject while adapting to the scene prompt.
    Otherwise uses Seedream 4.5 text-to-image.
    """
    if reference_image_url:
        logger.info("[router] Using FLUX dev image-to-image with reference")
        result = fal_service.transform_image(
            image_url=reference_image_url,
            prompt=prompt,
            strength=strength,
        )
    else:
        result = fal_service.generate_image(prompt)

    image_url = result["images"][0]["url"]
    local_path = download_file(image_url, job_id, filename)
    return image_url, local_path
