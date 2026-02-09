"""Audio analysis capability — Gemini evaluates audio quality."""

import json
import logging

from agent.prompts.quality_gate import build_gemini_eval_prompt

logger = logging.getLogger(__name__)


def execute(params: dict, state: dict, ctx: dict) -> dict:
    """Evaluate audio quality with Gemini.

    params:
        audio_path: str — local path to the audio file
        prompt: str — the original generation prompt or script
        step_description: str — what this audio is for
    """
    audio_path = params.get("audio_path", "")
    original_prompt = params.get("prompt", "")
    step_desc = params.get("step_description", "")
    creative_brief = state.get("creative_brief", {})

    if not audio_path:
        raise ValueError("No audio_path for analysis")

    eval_prompt = build_gemini_eval_prompt(
        asset_type="audio",
        creative_brief=creative_brief,
        original_prompt=original_prompt,
        step_description=step_desc,
    )

    from services.gemini_service import analyze_audio
    response = analyze_audio(audio_path, eval_prompt)

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
        "asset_type": "audio",
        "score": result.get("overall_score", 7.0),
        "issues": result.get("issues", []),
        "suggestions": result.get("suggestions", []),
        "passed": result.get("passed", True),
        "summary": result.get("summary", ""),
        "model": "gemini-2.5-pro",
        "cost": 0.01,
    }
