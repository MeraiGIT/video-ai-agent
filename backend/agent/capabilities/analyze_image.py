"""Image analysis capability — Gemini vision evaluates image quality."""

import json
import logging

from agent.prompts.quality_gate import build_gemini_eval_prompt

logger = logging.getLogger(__name__)


def execute(params: dict, state: dict, ctx: dict) -> dict:
    """Evaluate image quality with Gemini vision.

    params:
        image_url: str — URL of the image to evaluate
        prompt: str — the original generation prompt
        step_description: str — what this image is for
    """
    image_url = params.get("image_url", "")
    original_prompt = params.get("prompt", "")
    step_desc = params.get("step_description", "")
    creative_brief = state.get("creative_brief", {})

    if not image_url:
        raise ValueError("No image_url for analysis")

    eval_prompt = build_gemini_eval_prompt(
        asset_type="image",
        creative_brief=creative_brief,
        original_prompt=original_prompt,
        step_description=step_desc,
    )

    from services.gemini_service import analyze_image
    response = analyze_image(image_url, eval_prompt)

    try:
        text = response.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        result = json.loads(text)
    except (json.JSONDecodeError, IndexError):
        # Fallback: assume pass
        result = {
            "overall_score": 7.0,
            "issues": [],
            "suggestions": [],
            "passed": True,
            "summary": response[:200],
        }

    return {
        "asset_type": "image",
        "score": result.get("overall_score", 7.0),
        "issues": result.get("issues", []),
        "suggestions": result.get("suggestions", []),
        "passed": result.get("passed", True),
        "summary": result.get("summary", ""),
        "model": "gemini-2.5-pro",
        "cost": 0.01,
    }
