"""Video reference analysis — Gemini vision deconstructs existing videos.

Used for "recreate this video" or "make something like this" requests.
Gemini watches the video and extracts detailed production information
that feeds into creative direction and blueprint generation.
"""

import json
import logging

logger = logging.getLogger(__name__)


def execute(params: dict, state: dict, ctx: dict) -> dict:
    """Analyze an existing video for recreation/inspiration.

    params:
        video_url: str — URL of the reference video
        analysis_focus: str — what to focus on (general, style, structure, all)
    """
    video_url = params.get("video_url", "")
    focus = params.get("analysis_focus", "all")

    if not video_url:
        raise ValueError("No video_url for reference analysis")

    prompt = f"""Analyze this reference video in detail for recreation purposes.
Focus: {focus}

Return a JSON analysis:
{{
  "overview": "Brief description of the video",
  "duration_estimate": "Estimated total duration",
  "scenes": [
    {{
      "timestamp": "0:00-0:05",
      "description": "What happens visually",
      "camera": "Camera angle/movement",
      "transition_from_previous": "cut/fade/dissolve",
      "text_overlays": "Any on-screen text",
      "audio_cue": "Music/voice/SFX description"
    }}
  ],
  "visual_style": {{
    "color_palette": "Dominant colors and mood",
    "lighting": "Lighting style",
    "aesthetic": "Overall visual aesthetic"
  }},
  "pacing": "Fast/medium/slow, rhythm description",
  "audio_analysis": {{
    "music_style": "Background music description",
    "voiceover": "Yes/no, tone if present",
    "sfx": "Notable sound effects"
  }},
  "production_notes": "Key techniques used, what makes it effective"
}}"""

    from services.gemini_service import analyze_video
    response = analyze_video(video_url, prompt)

    try:
        text = response.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        analysis = json.loads(text)
    except (json.JSONDecodeError, IndexError):
        analysis = {
            "overview": response[:300],
            "raw_analysis": response,
        }

    return {
        "analysis": analysis,
        "model": "gemini-2.5-pro",
        "cost": 0.03,
    }
