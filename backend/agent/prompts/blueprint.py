"""Blueprint generation prompt — transforms creative direction into execution specs.

Takes the creative brief, approved production plan, and model knowledge cards
to generate a freeform detailed blueprint that the production executor follows.
The blueprint structure is NOT fixed — the LLM decides what's needed.
"""

from agent.prompts.model_knowledge import get_model_cards_context


BLUEPRINT_SYSTEM = (
    "You are a senior technical director at an AI production studio. "
    "You translate creative briefs into precise, actionable execution blueprints. "
    "Your blueprints are detailed enough that a production team (or automated system) "
    "can execute each step without further clarification. You return ONLY valid JSON."
)


def build_blueprint_prompt(
    creative_brief: dict,
    production_plan: list[dict],
    content_type: str,
    user_request: str,
    constraints: dict | None = None,
    research_insights: dict | None = None,
    reference_materials: list[dict] | None = None,
) -> str:
    """Build the blueprint generation prompt.

    The LLM generates whatever structure the project needs — scripts,
    storyboards, audio maps, layout specs, typography, etc. Nothing is
    hardcoded per content type.
    """
    import json

    model_context = get_model_cards_context()

    brief_str = json.dumps(creative_brief, indent=2)
    plan_str = json.dumps(production_plan, indent=2)

    constraints_str = ""
    if constraints:
        parts = [f"- {k}: {v}" for k, v in constraints.items() if v is not None]
        if parts:
            constraints_str = "\nConstraints:\n" + "\n".join(parts)

    refs_str = ""
    if reference_materials:
        parts = []
        for ref in reference_materials:
            parts.append(
                f"- {ref.get('type', 'file')}: {ref.get('filename', 'unknown')} "
                f"— {ref.get('analysis', ref.get('key_details', ''))}"
            )
        refs_str = "\nReference materials:\n" + "\n".join(parts)

    research_str = ""
    if research_insights:
        summary = research_insights.get("summary", "")
        if summary:
            research_str = f"\nResearch context: {summary}"

    return f"""Generate a detailed execution blueprint for this project.

CREATIVE BRIEF:
{brief_str}

APPROVED PRODUCTION PLAN (execute these steps in order):
{plan_str}

PROJECT CONTEXT:
- Content type: {content_type}
- Original request: {user_request}{constraints_str}{refs_str}{research_str}

{model_context}

Generate a blueprint JSON object with whatever sections this project needs.
The blueprint should contain ALL the detail needed to execute each production step.

GUIDELINES:
1. For each production step that generates content, include the EXACT prompt to use
2. Prompts must be model-specific — use the model knowledge cards above for formatting
3. For video content: include script, scene-by-scene storyboard with visual descriptions,
   camera directions, audio cues, and timing
4. For graphic content: include layout specifications, element placement, typography, colors
5. For audio content: include script, voice direction, music cues, mixing notes
6. For motion graphics: include keyframe descriptions, transition specs, timing
7. For ANY content type: generate whatever detailed specs are needed — don't limit yourself
8. Include an audio_map if the project has voiceover, music, or SFX
9. Scene/element prompts should be vivid, specific, and styled per the creative brief
10. Total durations and counts must match the production plan

Return a JSON object. Example structure (adapt freely):
{{
  "title": "Project title",
  "summary": "Brief execution summary",
  "scenes": [
    {{
      "scene_number": 1,
      "narration": "Script text for this scene",
      "visual_description": "What the viewer sees",
      "image_prompt": "Exact prompt for image generation (model-specific)",
      "video_prompt": "Exact prompt for video generation (model-specific)",
      "camera": {{"shot_type": "wide", "movement": "slow pan right", "angle": "eye level"}},
      "duration": 5.0,
      "transition": "fade",
      "text_overlay": "Optional on-screen text",
      "sfx_cue": "Optional sound effect"
    }}
  ],
  "audio_map": {{
    "voiceover": {{"full_script": "...", "voice_direction": "warm, conversational"}},
    "music": {{"style": "upbeat corporate", "tempo": "120bpm"}},
    "sfx": [{{"cue": "whoosh", "timestamp": 3.0}}]
  }},
  "style_guide": {{
    "color_palette": ["#hex1", "#hex2"],
    "typography": {{"heading_font": "...", "body_font": "..."}},
    "visual_consistency": "Notes on maintaining visual coherence"
  }}
}}

Adapt the structure to match this specific project. Not all sections are needed for
every project type — include only what's relevant."""
