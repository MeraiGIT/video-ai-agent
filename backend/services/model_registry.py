"""
Model registry — single source of truth for all video and image models.

Each model entry defines its provider, endpoint, capabilities, duration limits,
cost, strengths, weaknesses, and prompting guidance. Used by video_router.py
for dispatch and by the capability registry for LLM context injection.
"""

VIDEO_MODELS = {
    "seedance": {
        "name": "Seedance 1.5 Pro",
        "provider": "fal",
        "endpoint": "fal-ai/bytedance/seedance/v1.5/pro/image-to-video",
        "supports": ["image-to-video"],
        "duration_range": [4, 12],
        "duration_format": "int",
        "cost_per_scene": 0.26,
        "strengths": ["Best motion quality", "Smooth fluid movement", "Great camera handling"],
        "weaknesses": ["Image-to-video only", "No negative prompts", "Higher cost"],
        "best_for": "Cinematic video with smooth motion",
    },
    "veo": {
        "name": "Google Veo 3.1 Fast",
        "provider": "kie",
        "endpoint": "veo3",
        "supports": ["image-to-video", "text-to-video", "first-last-frame"],
        "duration_range": [4, 8],
        "duration_format": "Xs",  # "4s", "6s", "8s"
        "cost_per_scene": 0.10,
        "strengths": ["Best value", "Realistic human motion", "First/last frame support"],
        "weaknesses": ["8s max", "Short prompts only (150-300 chars)"],
        "best_for": "Cost-effective video, motion graphics",
    },
    "kling": {
        "name": "Kling 2.6",
        "provider": "kie",
        "endpoint": "kling-2.6",
        "supports": ["image-to-video"],
        "duration_range": [5, 10],
        "duration_format": "str_int",
        "cost_per_scene": 0.15,
        "strengths": ["Complex multi-subject scenes", "++emphasis++ syntax", "Good negatives"],
        "weaknesses": ["Can have jitter without 'smooth camera' instruction"],
        "best_for": "Complex scenes with multiple subjects",
    },
    "kling_ref": {
        "name": "Kling O1 (Character Reference)",
        "provider": "fal",
        "endpoint": "fal-ai/kling-video/o1/reference-to-video",
        "supports": ["reference-to-video", "character-consistency"],
        "duration_range": [5, 10],
        "duration_format": "int",
        "cost_per_scene": 0.56,
        "strengths": ["ONLY model with character consistency", "Face preservation"],
        "weaknesses": ["Most expensive", "Requires reference images"],
        "best_for": "Videos with consistent characters from photos",
    },
}

IMAGE_MODELS = {
    "seedream": {
        "name": "Seedream 4.5",
        "provider": "fal",
        "endpoint": "fal-ai/bytedance/seedream/v4.5/text-to-image",
        "supports": ["text-to-image"],
        "cost": 0.04,
        "strengths": ["Excellent photorealism", "Strong subject rendering"],
        "weaknesses": ["Flat lighting without explicit guidance"],
        "best_for": "Photorealistic images, product shots, portraits",
    },
    "flux_dev_i2i": {
        "name": "FLUX Dev (Image-to-Image)",
        "provider": "fal",
        "endpoint": "fal-ai/flux/dev/image-to-image",
        "supports": ["image-to-image"],
        "cost": 0.03,
        "strengths": ["Preserves subject from reference", "Character consistency"],
        "weaknesses": ["Requires reference image", "Less creative freedom"],
        "best_for": "Character consistency, style transfer",
    },
    "nano_banana_pro": {
        "name": "Nano Banana Pro",
        "provider": "nanana",
        "endpoint": "nanana-api",
        "supports": ["text-to-image"],
        "cost": 0.03,
        "strengths": ["Fast generation", "Good for stylized content", "Motion graphics keyframes"],
        "weaknesses": ["Less photorealistic than Seedream"],
        "best_for": "Motion graphics keyframes, stylized art, fast iteration",
    },
}


def get_video_model(model_id: str) -> dict:
    """Get a video model config by ID. Raises KeyError if not found."""
    return VIDEO_MODELS[model_id]


def get_image_model(model_id: str) -> dict:
    """Get an image model config by ID."""
    return IMAGE_MODELS[model_id]


def get_models_for_capability(capability: str) -> list[dict]:
    """Return all models (video + image) supporting a given capability."""
    results = []
    for model_id, model in VIDEO_MODELS.items():
        if capability in model["supports"]:
            results.append({"id": model_id, **model})
    for model_id, model in IMAGE_MODELS.items():
        if capability in model["supports"]:
            results.append({"id": model_id, **model})
    return results


def get_model_description_for_llm() -> str:
    """Return a formatted string describing all models for use in Claude prompts."""
    lines = ["Available video generation models:\n"]
    for model_id, m in VIDEO_MODELS.items():
        caps = ", ".join(m["supports"])
        dur = f"{m['duration_range'][0]}-{m['duration_range'][1]}s"
        lines.append(
            f"- **{m['name']}** (id: `{model_id}`): "
            f"Provider: {m['provider']}, Capabilities: [{caps}], "
            f"Duration: {dur}, Cost: ~${m['cost_per_scene']:.2f}/scene"
        )
        lines.append(f"  Best for: {m['best_for']}")

    lines.append("\nAvailable image generation models:\n")
    for model_id, m in IMAGE_MODELS.items():
        caps = ", ".join(m["supports"])
        lines.append(
            f"- **{m['name']}** (id: `{model_id}`): "
            f"Capabilities: [{caps}], Cost: ~${m['cost']:.2f}/image"
        )
        lines.append(f"  Best for: {m['best_for']}")

    lines.append(
        "\nKey notes:"
        "\n- Kling O1 is the ONLY model supporting character consistency via reference images."
        "\n- FLUX Dev image-to-image preserves subject appearance from reference photos."
        "\n- Veo 3.1 supports first/last frame for motion graphics."
        "\n- Nano Banana Pro is fastest for stylized content and keyframes."
        "\n- For standard video: Veo 3.1 = best value, Seedance 1.5 = highest quality."
    )
    return "\n".join(lines)
