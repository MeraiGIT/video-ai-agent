"""Creative direction prompt — the "brain" of the production studio.

This is the most important prompt in the system. It tells Claude to act as a
senior creative director and generate: creative brief, production plan, and
three budget variants with itemized costs.
"""

from agent.prompts.model_knowledge import get_full_context


CREATIVE_DIRECTION_SYSTEM = (
    "You are a senior creative director at a top-tier AI production studio. "
    "You have deep expertise in video production, graphic design, motion graphics, "
    "audio production, and content strategy. You make creative decisions that "
    "maximize quality within budget constraints. You return ONLY valid JSON."
)


def build_creative_direction_prompt(
    user_request: str,
    content_type: str,
    target_platform: str,
    target_audience: str,
    constraints: dict | None = None,
    research_insights: dict | None = None,
    reference_materials: list[dict] | None = None,
    interview_answers: str = "",
) -> str:
    """Build the creative direction prompt with all available context.

    This prompt produces:
    1. A creative brief (concept, style, pacing, audio)
    2. A production plan (ordered capability steps)
    3. Three budget variants (budget/standard/premium)
    """
    # Inject model and capability knowledge
    knowledge = get_full_context()

    # Build context sections
    constraints_str = ""
    if constraints:
        parts = [f"- {k}: {v}" for k, v in constraints.items() if v is not None]
        if parts:
            constraints_str = "\nConstraints:\n" + "\n".join(parts)

    research_str = ""
    if research_insights:
        summary = research_insights.get("summary", "")
        trends = research_insights.get("trends", [])
        recs = research_insights.get("recommendations", [])
        research_str = f"\nResearch insights: {summary}"
        if trends:
            research_str += f"\nTrends: {', '.join(trends[:5])}"
        if recs:
            research_str += f"\nRecommendations: {', '.join(recs[:5])}"

    refs_str = ""
    if reference_materials:
        parts = []
        for ref in reference_materials:
            parts.append(f"- {ref.get('type', 'file')}: {ref.get('filename', 'unknown')} — {ref.get('key_details', ref.get('analysis', ''))}")
        refs_str = "\nReference materials:\n" + "\n".join(parts)

    interview_str = ""
    if interview_answers:
        interview_str = f"\nUser's additional context: {interview_answers}"

    return f"""Create a complete creative direction for this project.

PROJECT BRIEF:
- Request: {user_request}
- Content type: {content_type}
- Platform: {target_platform}
- Audience: {target_audience}{constraints_str}{research_str}{refs_str}{interview_str}

{knowledge}

FIRST, honestly assess feasibility:
- Can we achieve what the user wants with the available capabilities?
- If something is impossible (e.g., real-time 3D rendering, live action), say so clearly and suggest the closest achievable alternative.
- If achievable with tradeoffs, explain them.

THEN generate the complete creative direction as JSON:
{{
  "feasibility": {{
    "achievable": true/false,
    "notes": "Any feasibility notes or limitations",
    "alternatives": "Suggested alternatives if not fully achievable"
  }},
  "creative_brief": {{
    "concept": "High-level creative concept (2-3 sentences)",
    "visual_style": "Detailed visual style description",
    "tone": "Content tone and mood",
    "pacing": "Pacing and rhythm description",
    "audio_direction": "Music, voiceover, and sound design direction",
    "color_palette": "Primary colors and mood",
    "key_messages": ["Message 1", "Message 2"],
    "reference_notes": "How reference materials inform the direction"
  }},
  "production_plan": [
    {{
      "step": 1,
      "capability": "capability_id from registry",
      "model": "model_id",
      "params": {{}},
      "description": "What this step produces",
      "estimated_cost": 0.00,
      "count": 1
    }}
  ],
  "budget_variants": [
    {{
      "tier": "budget",
      "total_estimate": 0.00,
      "model_selections": {{"capability_id": "model_id"}},
      "cost_breakdown": [
        {{"step": "Description", "model": "model_id", "count": 1, "unit_cost": 0.00, "total": 0.00}}
      ],
      "tradeoffs": "What you give up in this tier"
    }},
    {{
      "tier": "standard",
      "total_estimate": 0.00,
      "model_selections": {{}},
      "cost_breakdown": [],
      "tradeoffs": "Good balance of quality and cost"
    }},
    {{
      "tier": "premium",
      "total_estimate": 0.00,
      "model_selections": {{}},
      "cost_breakdown": [],
      "tradeoffs": "Maximum quality, highest cost"
    }}
  ]
}}

CRITICAL RULES:
1. The production_plan MUST only use capabilities from the registry
2. Each budget variant MUST use different models, not just fewer steps
3. Budget variant costs must be realistic based on model pricing
4. The production plan should be for the STANDARD tier by default
5. For short videos: typically 4-6 scenes with images + videos + voiceover + assembly
6. For graphics: typically image generation + optional text overlay
7. For motion graphics: use first_last_frame (Nano Banana) + video_gen with first/last frame support
8. For character consistency: use face_reference + kling_ref model
9. For video recreation: leverage any analyze_video_reference results in the creative brief
10. Include voiceover only if the content type benefits from narration
11. Always end with assembly/polish steps appropriate to the content type"""
