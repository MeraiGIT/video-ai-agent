"""Face reference capability — Gemini vision extracts character sheet.

Sends a reference image to Gemini 2.5 Pro vision mode to extract
detailed character description for consistent generation across scenes.
"""

import json
import logging

logger = logging.getLogger(__name__)


def execute(params: dict, state: dict, ctx: dict) -> dict:
    """Extract character sheet from a reference image.

    params:
        image_url: str — URL of the reference face/character image
        character_name: str — optional name for the character
    """
    image_url = params.get("image_url", "")
    if not image_url:
        raise ValueError("face_reference requires an image_url")

    character_name = params.get("character_name", "main character")

    prompt = f"""Analyze this reference image of "{character_name}" and extract a detailed character sheet.

Return JSON:
{{
  "character_name": "{character_name}",
  "physical_description": "Detailed physical appearance (hair, eyes, skin, build, etc.)",
  "clothing": "What they're wearing",
  "distinguishing_features": "Any unique features (scars, tattoos, accessories)",
  "style_notes": "Artistic style notes for consistent regeneration",
  "prompt_injection": "A concise description to inject into image/video prompts for consistency"
}}"""

    from services.gemini_service import analyze_image
    response = analyze_image(image_url, prompt)

    try:
        # Parse JSON from response
        text = response.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        sheet = json.loads(text)
    except (json.JSONDecodeError, IndexError):
        sheet = {
            "character_name": character_name,
            "prompt_injection": response[:200],
            "raw_analysis": response,
        }

    return {
        "character_sheet": sheet,
        "model": "gemini-2.5-pro",
        "cost": 0.01,
    }
