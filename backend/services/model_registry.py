"""
Model registry — single source of truth for all video and image models.

Each model entry defines its provider, endpoint, capabilities, duration limits,
and cost. Helper functions let other modules query models by capability and
generate descriptions for Claude prompts.
"""

VIDEO_MODELS = {
    "seedance": {
        "name": "Seedance 1.5 Pro",
        "provider": "fal",
        "endpoint": "fal-ai/bytedance/seedance/v1.5/pro/image-to-video",
        "supports": ["image-to-video"],
        "duration_range": [4, 12],
        "duration_format": "int",  # plain integer seconds
        "cost_per_scene": 0.26,
    },
    "veo": {
        "name": "Google Veo 3.1 Fast",
        "provider": "kie",
        "endpoint": "veo3",  # Kie uses model name in request body
        "supports": ["image-to-video", "text-to-video"],
        "duration_range": [4, 8],
        "duration_format": "Xs",  # "4s", "6s", "8s"
        "cost_per_scene": 0.10,
    },
    "kling": {
        "name": "Kling 2.6",
        "provider": "kie",
        "endpoint": "kling-2.6",  # Kie task type
        "supports": ["image-to-video"],
        "duration_range": [5, 10],
        "duration_format": "str_int",  # "5", "10"
        "cost_per_scene": 0.15,
    },
    "kling_ref": {
        "name": "Kling O1 (Character Reference)",
        "provider": "fal",
        "endpoint": "fal-ai/kling-video/o1/reference-to-video",
        "supports": ["reference-to-video", "character-consistency"],
        "duration_range": [5, 10],
        "duration_format": "int",
        "cost_per_scene": 0.56,
    },
}

IMAGE_MODELS = {
    "seedream": {
        "name": "Seedream 4.5",
        "provider": "fal",
        "endpoint": "fal-ai/bytedance/seedream/v4.5/text-to-image",
        "supports": ["text-to-image"],
        "cost": 0.04,
    },
    "flux_dev_i2i": {
        "name": "FLUX Dev (Image-to-Image)",
        "provider": "fal",
        "endpoint": "fal-ai/flux/dev/image-to-image",
        "supports": ["image-to-image"],
        "cost": 0.03,
    },
}


def get_video_model(model_id: str) -> dict:
    """Get a video model config by ID. Raises KeyError if not found."""
    return VIDEO_MODELS[model_id]


def get_image_model(model_id: str) -> dict:
    """Get an image model config by ID."""
    return IMAGE_MODELS[model_id]


def get_models_for_capability(capability: str) -> list[dict]:
    """Return all video models supporting a given capability."""
    results = []
    for model_id, model in VIDEO_MODELS.items():
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

    lines.append("\nAvailable image generation models:\n")
    for model_id, m in IMAGE_MODELS.items():
        caps = ", ".join(m["supports"])
        lines.append(
            f"- **{m['name']}** (id: `{model_id}`): "
            f"Capabilities: [{caps}], Cost: ~${m['cost']:.2f}/image"
        )

    lines.append(
        "\nNotes:"
        "\n- Kling O1 (Character Reference) is the ONLY model supporting character "
        "consistency via reference images. Use it when the user provides photos of "
        "a person/pet/character and wants them to appear consistently across scenes."
        "\n- FLUX Dev image-to-image can transform user-uploaded photos into scene "
        "images while preserving the subject's appearance."
        "\n- For standard video generation without character references, Veo 3.1 Fast "
        "offers the best value. Seedance 1.5 Pro is the highest quality."
    )
    return "\n".join(lines)
