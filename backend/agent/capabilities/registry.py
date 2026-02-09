"""
Capability Registry — maps capability IDs to functions and model knowledge cards.

The LLM uses this registry to decide what the system can do.
The production executor uses it to call the right function.
"""

from __future__ import annotations

from typing import Callable

# Capabilities are registered lazily — we import the actual functions only when called.
# This avoids circular imports and heavy dependency loading at import time.


# === Model Knowledge Cards ===
# Full metadata for each model: cost, strengths, weaknesses, prompt structure.
# Injected into LLM prompts so it can make informed model selections.

MODEL_CARDS: dict[str, dict] = {
    "seedream-4.5": {
        "type": "image",
        "name": "Seedream 4.5",
        "provider": "fal.ai",
        "cost_per_unit": 0.04,
        "unit": "image",
        "strengths": [
            "Excellent photorealism",
            "Strong subject rendering",
            "Good with lighting and composition",
        ],
        "weaknesses": [
            "Defaults to flat lighting without explicit guidance",
            "Struggles with abstract concepts",
        ],
        "best_for": "High-quality photorealistic images, product shots, portraits",
        "prompt_structure": "Subject -> Style -> Composition -> Lighting -> Technical",
        "optimal_length": "30-100 words",
        "supports_negative": True,
        "tips": [
            "Front-load the subject — first phrase is most influential",
            "Use photographic terms: '85mm lens, f/2.8, shallow depth of field'",
            "Include lighting explicitly",
            "Negative prompt field is separate — use 3-7 specific terms",
        ],
    },
    "flux_dev_i2i": {
        "type": "image",
        "name": "FLUX Dev (Image-to-Image)",
        "provider": "fal.ai",
        "cost_per_unit": 0.03,
        "unit": "image",
        "strengths": [
            "Preserves subject appearance from reference image",
            "Good for character consistency with photo references",
        ],
        "weaknesses": [
            "Requires a reference image — cannot generate from text alone",
            "Less creative freedom than text-to-image models",
        ],
        "best_for": "Character consistency, style transfer from reference photos",
        "prompt_structure": "Subject -> Style -> Details",
        "optimal_length": "30-80 words",
        "supports_negative": False,
        "tips": [
            "Use with reference_images for best results",
            "Control strength parameter (0.0-1.0) to balance reference vs prompt",
        ],
    },
    "nano_banana_pro": {
        "type": "image",
        "name": "Nano Banana Pro",
        "provider": "nanana",
        "cost_per_unit": 0.03,
        "unit": "image",
        "strengths": [
            "Fast generation",
            "Good for stylized and artistic content",
            "Excellent for motion graphics keyframes",
        ],
        "weaknesses": [
            "Less photorealistic than Seedream",
        ],
        "best_for": "Motion graphics keyframes, stylized art, fast iteration",
        "prompt_structure": "Subject -> Style -> Details",
        "optimal_length": "20-80 words",
        "supports_negative": False,
        "tips": [
            "Use for first/last frame pairs in motion graphics",
            "Works well with abstract and stylized prompts",
        ],
    },
    "seedance-1.5": {
        "type": "video",
        "name": "Seedance 1.5 Pro",
        "provider": "fal.ai",
        "cost_per_unit": 0.26,
        "unit": "video",
        "duration_range": [4, 12],
        "duration_format": "int",
        "strengths": [
            "Best motion quality among all models",
            "Smooth fluid movement",
            "Excellent camera motion handling",
        ],
        "weaknesses": [
            "Image-to-video only (requires input image)",
            "No negative prompt support",
            "Higher cost than alternatives",
        ],
        "best_for": "High-quality cinematic video, smooth motion, nature scenes",
        "prompt_structure": "Camera movement -> Subject action -> Environment -> Style",
        "optimal_length": "50-150 words",
        "supports_negative": False,
        "tips": [
            "ALWAYS requires an input image",
            "Lead with camera movement for best results",
            "Describe fluid motion — avoid static descriptions",
            "Positive framing only",
        ],
    },
    "veo3.1": {
        "type": "video",
        "name": "Google Veo 3.1 Fast",
        "provider": "kie_ai",
        "cost_per_unit": 0.10,
        "unit": "video",
        "duration_range": [4, 8],
        "duration_format": "Xs",  # "4s", "6s", "8s"
        "strengths": [
            "Best value for quality-to-cost ratio",
            "Excellent realistic human motion",
            "Supports first/last frame for motion graphics",
            "Supports text-to-video (no image required)",
        ],
        "weaknesses": [
            "Fixed 8s max duration",
            "Short prompts only (150-300 chars)",
            "Struggles with scene changes mid-clip",
        ],
        "best_for": "Cost-effective video, realistic motion, motion graphics",
        "prompt_structure": "Shot type -> Setting -> Subject -> Action -> Sound",
        "optimal_length": "150-300 characters",
        "supports_negative": True,
        "supports_first_last_frame": True,
        "tips": [
            "Keep prompts SHORT — 150-300 characters, NOT words",
            "One continuous action per prompt",
            "Add ambient sound cues for better results",
            "Supports first/last frame via imageUrls parameter",
        ],
    },
    "kling-2.6": {
        "type": "video",
        "name": "Kling 2.6",
        "provider": "kie_ai",
        "cost_per_unit": 0.15,
        "unit": "video",
        "duration_range": [5, 10],
        "duration_format": "str_int",
        "strengths": [
            "Handles complex multi-subject scenes",
            "++emphasis++ syntax for key elements",
            "Good negative prompt support",
        ],
        "weaknesses": [
            "Can have jitter without explicit 'smooth camera' instruction",
        ],
        "best_for": "Complex scenes, multi-subject, detailed control",
        "prompt_structure": "Scene -> Subject -> Motion -> Style",
        "optimal_length": "50-200 words",
        "supports_negative": True,
        "supports_emphasis": True,
        "tips": [
            "Use ++double plus++ to emphasize critical elements",
            "Specify 'smooth camera movement' to avoid jitter",
            "Negative prompts work aggressively — use 3-7 items",
        ],
    },
    "kling-3.0": {
        "type": "video",
        "name": "Kling 3.0",
        "provider": "fal.ai",
        "cost_per_unit": 0.20,
        "unit": "video",
        "duration_range": [5, 10],
        "duration_format": "int",
        "strengths": [
            "Improved quality over Kling 2.6",
            "++emphasis++ syntax support",
            "Image-to-video mode",
        ],
        "weaknesses": [
            "Higher cost than Kling 2.6",
        ],
        "best_for": "High-quality video with detailed control",
        "prompt_structure": "Scene -> Subject -> Motion -> Style",
        "optimal_length": "50-200 words",
        "supports_negative": True,
        "supports_emphasis": True,
        "tips": [
            "Similar prompting to Kling 2.6 but with improved quality",
            "Use ++double plus++ for emphasis",
        ],
    },
    "kling_ref": {
        "type": "video",
        "name": "Kling O1 (Character Reference)",
        "provider": "fal.ai",
        "cost_per_unit": 0.56,
        "unit": "video",
        "duration_range": [5, 10],
        "duration_format": "int",
        "strengths": [
            "ONLY model supporting character consistency via reference images",
            "Maintains face/appearance across scenes",
        ],
        "weaknesses": [
            "Most expensive video model",
            "Requires reference images",
        ],
        "best_for": "Videos with consistent characters from reference photos",
        "prompt_structure": "Scene -> Subject -> Motion -> Style",
        "optimal_length": "50-150 words",
        "supports_negative": False,
        "tips": [
            "Pass reference images via image_urls parameter",
            "Use with face_reference capability for best results",
        ],
    },
}


# === Capability Registry ===
# Maps capability_id to metadata. The actual function is loaded lazily.

CAPABILITY_REGISTRY: dict[str, dict] = {
    # --- Generation ---
    "image_gen": {
        "description": "Generate images from text prompts",
        "category": "generation",
        "models": ["seedream-4.5", "flux_dev_i2i", "nano_banana_pro"],
        "output_type": "ImageAsset",
        "module": "agent.capabilities.image_gen",
    },
    "video_gen": {
        "description": "Generate video clips from images or text",
        "category": "generation",
        "models": ["seedance-1.5", "veo3.1", "kling-2.6", "kling-3.0", "kling_ref"],
        "output_type": "VideoAsset",
        "module": "agent.capabilities.video_gen",
    },
    "voiceover": {
        "description": "Generate text-to-speech voiceover audio",
        "category": "generation",
        "models": ["elevenlabs"],
        "output_type": "audio_path",
        "module": "agent.capabilities.voiceover",
    },
    "voice_select": {
        "description": "Search and select a voice by criteria (gender, age, tone)",
        "category": "generation",
        "models": ["elevenlabs"],
        "output_type": "voice_id",
        "module": "agent.capabilities.voice_select",
    },
    "music_gen": {
        "description": "Generate background music",
        "category": "generation",
        "models": ["elevenlabs"],
        "output_type": "audio_path",
        "module": "agent.capabilities.music_gen",
    },
    "sfx_gen": {
        "description": "Generate sound effects",
        "category": "generation",
        "models": ["elevenlabs"],
        "output_type": "audio_path",
        "module": "agent.capabilities.sfx_gen",
    },
    "face_reference": {
        "description": "Extract character sheet from reference image for consistency",
        "category": "generation",
        "models": ["gemini-2.5-pro"],
        "output_type": "character_sheet",
        "module": "agent.capabilities.face_reference",
    },
    "first_last_frame": {
        "description": "Generate first and last keyframe images for motion graphics",
        "category": "generation",
        "models": ["nano_banana_pro"],
        "output_type": "frame_pair",
        "module": "agent.capabilities.first_last_frame",
    },
    # --- Processing ---
    "audio_mix": {
        "description": "Mix multiple audio tracks with volume and fade control",
        "category": "processing",
        "models": [],
        "output_type": "audio_path",
        "module": "agent.capabilities.audio_mix",
    },
    "video_concat": {
        "description": "Concatenate video clips with optional transitions",
        "category": "processing",
        "models": [],
        "output_type": "video_path",
        "module": "agent.capabilities.video_concat",
    },
    "audio_overlay": {
        "description": "Overlay audio track onto video",
        "category": "processing",
        "models": [],
        "output_type": "video_path",
        "module": "agent.capabilities.audio_overlay",
    },
    "caption_burn": {
        "description": "Transcribe audio and burn captions into video",
        "category": "processing",
        "models": [],
        "output_type": "video_path",
        "module": "agent.capabilities.caption_burn",
    },
    "text_overlay": {
        "description": "Add animated text overlays to video",
        "category": "processing",
        "models": [],
        "output_type": "video_path",
        "module": "agent.capabilities.text_overlay",
    },
    "image_composite": {
        "description": "Composite multiple image layers (graphic design)",
        "category": "processing",
        "models": [],
        "output_type": "image_path",
        "module": "agent.capabilities.image_composite",
    },
    "transcribe": {
        "description": "Transcribe audio to SRT subtitles",
        "category": "processing",
        "models": ["faster-whisper"],
        "output_type": "srt_path",
        "module": "agent.capabilities.transcribe",
    },
    # --- Analysis ---
    "analyze_image": {
        "description": "Gemini vision evaluates image quality against creative brief",
        "category": "analysis",
        "models": ["gemini-2.5-pro"],
        "output_type": "QualityResult",
        "module": "agent.capabilities.analyze_image",
    },
    "analyze_video": {
        "description": "Gemini vision evaluates video quality (motion, coherence, subject)",
        "category": "analysis",
        "models": ["gemini-2.5-pro"],
        "output_type": "QualityResult",
        "module": "agent.capabilities.analyze_video",
    },
    "analyze_audio": {
        "description": "Gemini evaluates audio quality (clarity, pronunciation, pacing)",
        "category": "analysis",
        "models": ["gemini-2.5-pro"],
        "output_type": "QualityResult",
        "module": "agent.capabilities.analyze_audio",
    },
    "analyze_video_reference": {
        "description": "Gemini vision analyzes an existing video for recreation/inspiration",
        "category": "analysis",
        "models": ["gemini-2.5-pro"],
        "output_type": "video_analysis",
        "module": "agent.capabilities.analyze_video_reference",
    },
    "web_search": {
        "description": "Search the web for trends, references, and best practices",
        "category": "analysis",
        "models": ["tavily"],
        "output_type": "search_results",
        "module": "agent.capabilities.web_search",
    },
}


# === Helper Functions ===


def get_capability(capability_id: str) -> dict:
    """Get capability metadata by ID. Raises KeyError if not found."""
    return CAPABILITY_REGISTRY[capability_id]


def get_capability_function(capability_id: str) -> Callable:
    """Lazily import and return the execute function for a capability."""
    import importlib

    cap = CAPABILITY_REGISTRY[capability_id]
    module = importlib.import_module(cap["module"])
    return module.execute


def get_model_card(model_id: str) -> dict:
    """Get full model knowledge card. Raises KeyError if not found."""
    return MODEL_CARDS[model_id]


def get_models_by_type(model_type: str) -> list[dict]:
    """Get all models of a given type ('image' or 'video')."""
    return [
        {"id": mid, **card}
        for mid, card in MODEL_CARDS.items()
        if card["type"] == model_type
    ]


def get_all_capabilities_for_llm() -> str:
    """Format all capabilities as text for injection into LLM prompts."""
    lines = ["Available capabilities:\n"]

    for category in ["generation", "processing", "analysis"]:
        lines.append(f"\n### {category.title()}")
        for cap_id, cap in CAPABILITY_REGISTRY.items():
            if cap["category"] == category:
                models_str = ", ".join(cap["models"]) if cap["models"] else "local"
                lines.append(
                    f"- `{cap_id}`: {cap['description']} (models: {models_str})"
                )

    return "\n".join(lines)


def get_all_model_cards_for_llm() -> str:
    """Format all model cards as text for injection into LLM prompts."""
    lines = ["Available models:\n"]

    for model_type in ["image", "video"]:
        lines.append(f"\n### {model_type.title()} Models")
        for mid, card in MODEL_CARDS.items():
            if card["type"] != model_type:
                continue
            lines.append(f"\n**{card['name']}** (id: `{mid}`)")
            lines.append(f"  Provider: {card['provider']}")
            lines.append(f"  Cost: ${card['cost_per_unit']:.2f}/{card['unit']}")
            if "duration_range" in card:
                dr = card["duration_range"]
                lines.append(f"  Duration: {dr[0]}-{dr[1]}s")
            lines.append(f"  Best for: {card['best_for']}")
            lines.append(f"  Strengths: {', '.join(card['strengths'])}")
            lines.append(f"  Weaknesses: {', '.join(card['weaknesses'])}")

    return "\n".join(lines)
