"""Injectable model and capability context for LLM prompts.

Generates formatted text blocks describing all available models and
capabilities with costs, strengths, weaknesses, and usage guidance.
Used by creative_direction, blueprint, and quality_gate prompts.
"""

from agent.capabilities.registry import (
    get_all_capabilities_for_llm,
    get_all_model_cards_for_llm,
    MODEL_CARDS,
    CAPABILITY_REGISTRY,
)


def get_model_cards_context() -> str:
    """Return formatted model cards for injection into LLM prompts.

    Includes all models with costs, capabilities, strengths, weaknesses,
    and best-for descriptions.
    """
    lines = ["## Available Models\n"]

    # Group by type
    video_models = {k: v for k, v in MODEL_CARDS.items() if v["type"] == "video"}
    image_models = {k: v for k, v in MODEL_CARDS.items() if v["type"] == "image"}

    lines.append("### Video Generation Models\n")
    for model_id, m in video_models.items():
        dur = m.get("duration_range", "N/A")
        lines.append(f"**{m['name']}** (id: `{model_id}`)")
        lines.append(f"  - Cost: ${m['cost_per_unit']:.2f}/video, Duration: {dur}")
        lines.append(f"  - Strengths: {', '.join(m['strengths'])}")
        lines.append(f"  - Weaknesses: {', '.join(m['weaknesses'])}")
        lines.append(f"  - Best for: {m['best_for']}")
        lines.append("")

    lines.append("### Image Generation Models\n")
    for model_id, m in image_models.items():
        lines.append(f"**{m['name']}** (id: `{model_id}`)")
        lines.append(f"  - Cost: ${m['cost_per_unit']:.2f}/image")
        lines.append(f"  - Strengths: {', '.join(m['strengths'])}")
        lines.append(f"  - Weaknesses: {', '.join(m['weaknesses'])}")
        lines.append(f"  - Best for: {m['best_for']}")
        lines.append("")

    # Key decision guidance
    lines.append("### Model Selection Guidance\n")
    lines.append("- **Character consistency needed** → kling_ref (ONLY model with face reference)")
    lines.append("- **Best video quality** → seedance-1.5 (smooth motion, cinematic)")
    lines.append("- **Best value** → veo3.1 ($0.10/video, good quality)")
    lines.append("- **Complex multi-subject** → kling-2.6 or kling-3.0")
    lines.append("- **Motion graphics** → veo3.1 (first/last frame support)")
    lines.append("- **Photorealistic images** → seedream-4.5")
    lines.append("- **Stylized art / fast iteration** → nano_banana_pro")
    lines.append("- **Subject preservation** → flux_dev_i2i (image-to-image)")

    return "\n".join(lines)


def get_capability_context() -> str:
    """Return formatted capability list for injection into LLM prompts.

    Includes all available capabilities with descriptions and output types.
    """
    lines = ["## Available Capabilities\n"]
    lines.append("The production plan can use ANY of these capabilities:\n")

    by_category: dict[str, list] = {}
    for cap_id, cap in CAPABILITY_REGISTRY.items():
        cat = cap["category"]
        by_category.setdefault(cat, []).append((cap_id, cap))

    for category, items in by_category.items():
        lines.append(f"### {category.title()}\n")
        for cap_id, cap in items:
            models = ", ".join(cap["models"]) if cap["models"] else "built-in"
            lines.append(
                f"- `{cap_id}`: {cap['description']} "
                f"(models: {models}, output: {cap['output_type']})"
            )
        lines.append("")

    lines.append("### Production Plan Format\n")
    lines.append("Each step in the production plan is a JSON object:")
    lines.append('```json')
    lines.append('{')
    lines.append('  "step": 1,')
    lines.append('  "capability": "image_gen",')
    lines.append('  "model": "seedream-4.5",')
    lines.append('  "params": {"prompt": "...", "aspect_ratio": "16:9"},')
    lines.append('  "description": "Generate hero image for scene 1",')
    lines.append('  "estimated_cost": 0.04')
    lines.append('}')
    lines.append('```')

    return "\n".join(lines)


def get_full_context() -> str:
    """Return the complete model + capability context for the brain prompt."""
    return f"{get_model_cards_context()}\n\n{get_capability_context()}"
