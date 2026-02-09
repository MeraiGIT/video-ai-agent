"""Model-specific prompt engineering and formatting.

Converts structured scene data into model-optimized natural language prompts.
Each model has a unique optimal prompt structure, length, and vocabulary.

Copied from v2 and extended with Nano Banana Pro and Kling 3.0.
"""

from typing import Optional


# -- Internal Scene Schema ---------------------------------------------------

SCENE_SCHEMA = {
    "scene_number": "int -- sequential scene index",
    "narration": "str -- voiceover text for this scene",
    "subject": "str -- who/what is in the scene",
    "action": "str -- what is happening",
    "environment": "str -- setting/location",
    "camera": {
        "shot_type": "str -- wide, medium, close-up, etc.",
        "movement": "str -- dolly, pan, static, tracking, etc.",
        "angle": "str -- eye level, low angle, high angle, etc.",
    },
    "lighting": "str -- golden hour, studio, neon, etc.",
    "mood": "str -- energetic, calm, dramatic, etc.",
    "style": "str -- photorealistic, cinematic, artistic, etc.",
    "duration": "float -- seconds",
    "continuity_notes": "str -- what must match previous scene",
    "negative_elements": "list[str] -- what to avoid",
}


# -- Model Best Practices Database ------------------------------------------

MODEL_BEST_PRACTICES: dict[str, dict] = {
    "seedream-4.5": {
        "provider": "fal.ai",
        "type": "image",
        "optimal_length": "30-100 words",
        "structure": "Subject -> Style -> Composition -> Lighting -> Technical",
        "supports_negative": True,
        "tips": [
            "Front-load the subject — first phrase is most influential",
            "Use photographic terms: '85mm lens, f/2.8, shallow depth of field'",
            "Include lighting explicitly — Seedream defaults to flat lighting without guidance",
            "Negative prompt field is separate — use 3-7 specific terms",
            "Avoid abstract concepts — be concrete and visual",
        ],
        "example": (
            "A 30-year-old woman with auburn hair standing in a sunlit cafe, "
            "warm golden hour light streaming through windows, medium close-up shot, "
            "shallow depth of field, 85mm lens, cinematic color grade, soft bokeh background"
        ),
    },
    "veo3.1": {
        "provider": "kie_ai",
        "type": "video",
        "optimal_length": "150-300 characters",
        "duration": "8s (fixed)",
        "structure": "Shot type -> Setting -> Subject -> Action -> Sound",
        "supports_negative": True,
        "tips": [
            "Keep prompts SHORT — 150-300 characters optimal, NOT words",
            "One continuous action per prompt — Veo struggles with scene changes mid-clip",
            "Be specific about camera movement direction and speed",
            "Veo excels at realistic human motion and natural environments",
            "Add ambient sound cues for better results: 'birds chirping', 'city traffic'",
        ],
        "example": (
            "Tracking shot through a busy Tokyo street at night, neon signs reflecting "
            "on wet pavement, a woman in a red coat walking toward camera, city ambiance"
        ),
    },
    "kling-2.6": {
        "provider": "kie_ai",
        "type": "video",
        "optimal_length": "50-200 words",
        "duration": "5 or 10 seconds",
        "structure": "Scene -> Subject -> Motion -> Style",
        "supports_negative": True,
        "supports_emphasis": True,
        "tips": [
            "Use ++double plus++ to emphasize critical elements",
            "Describe motion explicitly: direction, speed, acceleration",
            "Negative prompts work aggressively — use 3-7 items for best results",
            "Handles complex multi-subject scenes better than other models",
            "Specify 'smooth camera movement' to avoid jitter",
        ],
        "example": (
            "A cozy kitchen in morning light. ++A chef in white uniform++ carefully "
            "plates a dish, smooth steady hands arranging garnish with precision. "
            "Camera slowly dollies in. Warm color palette, cinematic depth of field."
        ),
    },
    "seedance-1.5": {
        "provider": "fal.ai",
        "type": "video",
        "optimal_length": "50-150 words",
        "duration": "5 or 10 seconds",
        "structure": "Camera movement -> Subject action -> Environment -> Style",
        "supports_negative": False,
        "tips": [
            "ALWAYS requires an input image — image-to-video only",
            "Best motion quality of all models — emphasize fluid movement",
            "Lead with camera movement for best results",
            "Avoid static descriptions — everything should imply motion",
            "Positive framing only — describe what you want, not what to avoid",
        ],
        "example": (
            "Slow dolly forward through autumn forest, golden leaves gently falling "
            "around the frame, soft morning mist between the trees, a deer pauses "
            "and looks toward camera, cinematic shallow depth of field, warm amber tones"
        ),
    },
    "kling-3.0": {
        "provider": "fal.ai",
        "type": "video",
        "optimal_length": "50-200 words",
        "duration": "5 or 10 seconds",
        "structure": "Scene -> Subject -> Motion -> Style",
        "supports_negative": True,
        "supports_emphasis": True,
        "tips": [
            "Use ++double plus++ to emphasize critical elements",
            "Similar prompt structure to Kling 2.6 but with improved quality",
            "Supports image-to-video mode",
        ],
        "example": (
            "A vibrant marketplace at sunset. ++A street musician++ plays guitar, "
            "fingers dancing across strings. Camera arcs slowly around the performer. "
            "Golden light, cinematic depth of field, warm tones."
        ),
    },
    "flux_dev_i2i": {
        "provider": "fal.ai",
        "type": "image",
        "optimal_length": "30-80 words",
        "structure": "Subject -> Style -> Details",
        "supports_negative": False,
        "tips": [
            "Image-to-image mode — requires a reference image",
            "Good for maintaining character consistency from reference photos",
            "Control strength (0.0-1.0) to balance reference vs prompt",
        ],
        "example": (
            "A professional headshot of the same person, wearing a navy blazer, "
            "soft studio lighting, shallow depth of field"
        ),
    },
    "nano_banana_pro": {
        "provider": "nanana",
        "type": "image",
        "optimal_length": "20-80 words",
        "structure": "Subject -> Style -> Details",
        "supports_negative": False,
        "tips": [
            "Fast generation — ideal for iteration and keyframes",
            "Works well with stylized and artistic prompts",
            "Use for motion graphics first/last frame pairs",
            "Positive framing only",
        ],
        "example": (
            "Bold geometric shapes on a gradient background, minimalist design, "
            "vibrant blue and orange color palette, modern motion graphics style"
        ),
    },
}


# -- Cinematography Vocabulary -----------------------------------------------

CAMERA_MOVEMENTS = [
    "dolly in", "dolly out", "pan left", "pan right", "tilt up", "tilt down",
    "tracking shot", "crane shot", "arc shot", "steadicam", "handheld",
    "aerial/drone", "push-in", "pull-back", "static",
]

CAMERA_ANGLES = [
    "low angle", "high angle", "bird's eye", "Dutch angle", "eye level",
    "over-the-shoulder", "worm's eye",
]

SHOT_TYPES = [
    "extreme close-up", "close-up", "medium close-up", "medium shot",
    "medium wide", "wide shot", "extreme wide", "establishing shot",
]

LIGHTING_TERMS = {
    "natural": [
        "golden hour", "blue hour", "overcast", "harsh midday", "dappled light",
    ],
    "studio": [
        "Rembrandt lighting", "butterfly lighting", "split lighting",
        "rim light", "backlit", "three-point lighting",
    ],
    "atmospheric": [
        "volumetric light", "god rays", "neon glow", "candlelight", "firelight",
    ],
    "technical": [
        "high key", "low key", "chiaroscuro", "silhouette",
    ],
}

DEFAULT_NEGATIVE_PROMPTS = {
    "image": ["blurry", "low quality", "distorted face", "watermark", "text overlay", "deformed hands"],
    "video": ["static camera", "frozen motion", "jittery", "morphing", "flickering", "low quality"],
}


# -- Formatting Functions ----------------------------------------------------

def format_for_image_model(
    scene: dict,
    model: str = "seedream-4.5",
    character_sheets: list[dict] | None = None,
) -> dict:
    """Format a scene into a model-optimized image prompt.

    Returns:
        {"prompt": str, "negative_prompt": str | None}
    """
    subject = scene.get("subject", scene.get("visual_description", ""))
    if character_sheets:
        for char in character_sheets:
            char_id = char.get("character_id", "")
            if char_id and char_id in subject.lower():
                subject = char["locked_tokens"]
                break

    if model == "seedream-4.5":
        parts = [
            subject,
            scene.get("action", ""),
            f"in {scene['environment']}" if scene.get("environment") else "",
            f"{scene['camera']['shot_type']} shot" if scene.get("camera", {}).get("shot_type") else "",
            scene.get("lighting", ""),
            scene.get("style", "cinematic, photorealistic"),
        ]
        prompt = ", ".join(p for p in parts if p)
        negative = ", ".join(
            scene.get("negative_elements", DEFAULT_NEGATIVE_PROMPTS["image"])
        )
        return {"prompt": prompt, "negative_prompt": negative}

    elif model == "flux_dev_i2i":
        parts = [
            subject,
            scene.get("action", ""),
            scene.get("style", "photorealistic"),
            scene.get("lighting", ""),
        ]
        prompt = ", ".join(p for p in parts if p)
        return {"prompt": prompt, "negative_prompt": None}

    elif model == "nano_banana_pro":
        parts = [
            subject,
            scene.get("action", ""),
            scene.get("style", "vibrant, modern"),
            scene.get("lighting", ""),
        ]
        prompt = ", ".join(p for p in parts if p)
        return {"prompt": prompt, "negative_prompt": None}

    # Fallback
    prompt = f"{subject} {scene.get('action', '')}".strip()
    if scene.get("environment"):
        prompt += f" in {scene['environment']}"
    return {"prompt": prompt, "negative_prompt": None}


def format_for_video_model(
    scene: dict,
    model: str = "veo3.1",
    character_sheets: list[dict] | None = None,
) -> dict:
    """Format a scene into a model-optimized video prompt.

    Returns:
        {"prompt": str, "negative_prompt": str | None}
    """
    subject = scene.get("subject", scene.get("visual_description", ""))
    if character_sheets:
        for char in character_sheets:
            char_id = char.get("character_id", "")
            if char_id and char_id in subject.lower():
                subject = char["locked_tokens"]
                break

    camera = scene.get("camera", {})
    camera_desc = f"{camera.get('movement', 'static')} {camera.get('shot_type', 'medium')} shot"
    if camera.get("angle") and camera["angle"] != "eye level":
        camera_desc += f", {camera['angle']}"

    if model == "veo3.1":
        prompt = f"{camera_desc}, {subject} {scene.get('action', '')}"
        if scene.get("environment"):
            prompt += f", {scene['environment']}"
        if scene.get("mood"):
            prompt += f", {scene['mood']} atmosphere"
        if len(prompt) > 300:
            prompt = prompt[:297] + "..."
        return {"prompt": prompt, "negative_prompt": None}

    elif model in ("kling-2.6", "kling-3.0"):
        parts = [
            scene.get("environment", ""),
            f"++{subject}++ {scene.get('action', '')}",
            f"Camera: {camera_desc}",
            scene.get("style", "cinematic"),
        ]
        prompt = ". ".join(p for p in parts if p) + "."
        negatives = scene.get("negative_elements", DEFAULT_NEGATIVE_PROMPTS["video"])
        return {"prompt": prompt, "negative_prompt": ", ".join(negatives)}

    elif model == "seedance-1.5":
        parts = [
            camera_desc,
            f"{subject} {scene.get('action', '')}",
            scene.get("environment", ""),
            scene.get("style", "cinematic, smooth motion"),
        ]
        prompt = ", ".join(p for p in parts if p)
        return {"prompt": prompt, "negative_prompt": None}

    # Fallback
    return {
        "prompt": f"{subject} {scene.get('action', '')}",
        "negative_prompt": None,
    }


def get_best_practices(model: str) -> dict:
    """Get the full best practices guide for a specific model."""
    return MODEL_BEST_PRACTICES.get(model, {"error": f"Unknown model: {model}"})


def get_all_model_names() -> dict:
    """Return categorized model names for quick reference."""
    return {
        "image_models": [k for k, v in MODEL_BEST_PRACTICES.items() if v["type"] == "image"],
        "video_models": [k for k, v in MODEL_BEST_PRACTICES.items() if v["type"] == "video"],
    }


def get_all_best_practices_summary() -> str:
    """Get a formatted summary of all model best practices for the system prompt."""
    lines = []
    for model_id, practices in MODEL_BEST_PRACTICES.items():
        lines.append(f"### {model_id} ({practices['provider']})")
        lines.append(f"- Type: {practices['type']}")
        lines.append(f"- Optimal length: {practices['optimal_length']}")
        lines.append(f"- Structure: {practices['structure']}")
        if practices.get("duration"):
            lines.append(f"- Duration: {practices['duration']}")
        lines.append(f"- Supports negative: {practices.get('supports_negative', False)}")
        lines.append("")
    return "\n".join(lines)
