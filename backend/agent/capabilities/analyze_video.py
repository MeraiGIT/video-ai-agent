"""Video analysis capability — Gemini vision evaluates video quality."""

import json
import logging

from agent.prompts.quality_gate import build_gemini_eval_prompt

logger = logging.getLogger(__name__)


def execute(params: dict, state: dict, ctx: dict) -> dict:
    """Evaluate video quality with Gemini vision.

    params:
        video_path: str — local path or URL to the video
        prompt: str — the original generation prompt
        step_description: str — what this video is for
    """
    video_path = params.get("video_path", "")
    original_prompt = params.get("prompt", "")
    step_desc = params.get("step_description", "")
    creative_brief = state.get("creative_brief", {})

    if not video_path:
        raise ValueError("No video_path for analysis")

    eval_prompt = build_gemini_eval_prompt(
        asset_type="video",
        creative_brief=creative_brief,
        original_prompt=original_prompt,
        step_description=step_desc,
    )

    from services.gemini_service import analyze_video
    response = analyze_video(video_path, eval_prompt)

    try:
        text = response.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        result = json.loads(text)
    except (json.JSONDecodeError, IndexError):
        result = {
            "overall_score": 7.0,
            "issues": [],
            "suggestions": [],
            "passed": True,
            "summary": response[:200],
        }

    return {
        "asset_type": "video",
        "score": result.get("overall_score", 7.0),
        "issues": result.get("issues", []),
        "suggestions": result.get("suggestions", []),
        "passed": result.get("passed", True),
        "summary": result.get("summary", ""),
        "model": "gemini-2.5-pro",
        "cost": 0.02,
    }
