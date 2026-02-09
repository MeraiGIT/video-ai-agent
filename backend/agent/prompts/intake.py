"""Intake classification prompt — classifies any creative request."""

from agent.capabilities.registry import get_all_capabilities_for_llm


INTAKE_SYSTEM = (
    "You are the intake director for an AI Production Studio. "
    "You classify creative requests, identify what kind of content is being asked for, "
    "and determine what information is needed to produce the best result. "
    "You return ONLY valid JSON."
)


def build_intake_prompt(
    user_request: str,
    file_analyses: list[dict] | None = None,
) -> str:
    """Build the intake classification prompt.

    Args:
        user_request: The raw user request text.
        file_analyses: List of {filename, type, analysis} dicts from Gemini vision.

    Returns:
        Formatted prompt string for Claude.
    """
    capabilities = get_all_capabilities_for_llm()

    files_section = ""
    if file_analyses:
        parts = []
        for f in file_analyses:
            parts.append(
                f"- **{f['filename']}** ({f['type']}): {f.get('analysis', 'No analysis')}"
            )
        files_section = (
            "\n\nUPLOADED FILES (analyzed by Gemini vision):\n"
            + "\n".join(parts)
        )

    return f"""Classify this creative request and extract structured project details.

USER REQUEST:
{user_request}{files_section}

SYSTEM CAPABILITIES:
{capabilities}

Analyze the request and return ONLY this JSON:
{{
  "content_type": "short_video | long_video | graphic | motion_graphic | audio | presentation | other",
  "target_platform": "tiktok | youtube | instagram | linkedin | twitter | custom | unspecified",
  "target_audience": "Description of the target audience, or 'general' if not specified",
  "constraints": {{
    "duration": null or estimated seconds,
    "aspect_ratio": "16:9 | 9:16 | 1:1 | 4:5 | null",
    "style": "Inferred visual style or null",
    "tone": "Inferred tone (professional, casual, energetic, etc.) or null"
  }},
  "reference_materials": [
    {{"type": "image|video|audio|document", "filename": "...", "key_details": "..."}}
  ],
  "project_name": "Short catchy name for this project (2-5 words, Title Case)",
  "summary": "1-2 sentence summary of what the user wants, in your words",
  "needs_interview": true/false,
  "interview_reason": "Why follow-up questions would help, or empty string if not needed",
  "needs_research": true/false,
  "research_reason": "Why web research would help (trends, references, specs), or empty string"
}}

CLASSIFICATION GUIDELINES:
- short_video: Under 2 minutes, single topic (TikTok, Reels, Shorts)
- long_video: Over 2 minutes, multi-section (YouTube, documentary, tutorial)
- graphic: Static image(s) — poster, thumbnail, social media post, infographic
- motion_graphic: Animated graphics — logo animation, text animation, kinetic typography
- audio: Podcast, voiceover, music track, sound design
- presentation: Slide deck, pitch deck, educational slides
- other: Anything that doesn't fit above categories

Set needs_interview=false if:
- The request is very specific and complete
- The user said something like "just make it" or "surprise me"
- There's enough context to produce great output

Set needs_interview=true if:
- Key details are missing (audience, style, tone)
- Ambiguous requirements that could go multiple ways
- The request would benefit significantly from clarification"""
