"""Creative Direction node — the "brain" call.

Generates creative brief, production plan, and budget variants.
This is the most important Claude call in the entire pipeline.
"""

import json
import logging

from langgraph.config import get_stream_writer

from agent.state import ProductionState
from agent.prompts.creative_direction import (
    CREATIVE_DIRECTION_SYSTEM,
    build_creative_direction_prompt,
)
from services.claude_service import client, MODEL

logger = logging.getLogger(__name__)


def run(state: ProductionState) -> dict:
    """Generate creative brief, production plan, and budget variants."""
    writer = get_stream_writer()

    writer({
        "event": "progress",
        "data": {"stage": "creative_direction", "message": "Crafting creative direction..."},
    })

    # Build the brain prompt with all available context
    prompt = build_creative_direction_prompt(
        user_request=state.get("user_request", ""),
        content_type=state.get("content_type", "short_video"),
        target_platform=state.get("target_platform", "unspecified"),
        target_audience=state.get("target_audience", "general"),
        constraints=state.get("constraints"),
        research_insights=state.get("research_insights"),
        reference_materials=state.get("reference_materials"),
        interview_answers=state.get("interview_answers", ""),
    )

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=CREATIVE_DIRECTION_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        direction = json.loads(text)
    except Exception as e:
        logger.error("Creative direction generation failed: %s", e)
        writer({
            "event": "message",
            "data": {
                "role": "assistant",
                "content": f"I encountered an issue generating the creative direction. Let me try a simpler approach. Error: {str(e)[:100]}",
            },
        })
        # Fallback minimal direction
        direction = {
            "feasibility": {"achievable": True, "notes": "Using fallback direction"},
            "creative_brief": {
                "concept": f"Create a {state.get('content_type', 'video')} about: {state.get('user_request', '')[:100]}",
                "visual_style": "Clean, modern, professional",
                "tone": "Engaging and informative",
                "pacing": "Medium pace",
                "audio_direction": "Background music, voiceover narration",
                "color_palette": "Blues and whites",
                "key_messages": [state.get("user_request", "")[:100]],
                "reference_notes": "",
            },
            "production_plan": [],
            "budget_variants": [],
        }

    creative_brief = direction.get("creative_brief", {})
    production_plan = direction.get("production_plan", [])
    budget_variants = direction.get("budget_variants", [])
    feasibility = direction.get("feasibility", {})

    # Show creative brief to user
    concept = creative_brief.get("concept", "")
    style = creative_brief.get("visual_style", "")
    tone = creative_brief.get("tone", "")

    brief_msg = f"**Creative Direction:**\n\n**Concept:** {concept}"
    if style:
        brief_msg += f"\n**Visual Style:** {style}"
    if tone:
        brief_msg += f"\n**Tone:** {tone}"

    # Feasibility notes
    if feasibility.get("notes") and not feasibility.get("achievable", True):
        brief_msg += f"\n\n**Note:** {feasibility['notes']}"
        if feasibility.get("alternatives"):
            brief_msg += f"\n**Alternative:** {feasibility['alternatives']}"

    writer({
        "event": "message",
        "data": {"role": "assistant", "content": brief_msg},
    })

    # Emit creative brief as artifact
    writer({
        "event": "artifact",
        "data": {"type": "creative_brief", "brief": creative_brief},
    })

    # Emit budget variants as artifact
    if budget_variants:
        writer({
            "event": "artifact",
            "data": {"type": "budget_variants", "variants": budget_variants},
        })

        # Show budget summary
        budget_msg = "**Budget Options:**\n"
        for v in budget_variants:
            tier = v.get("tier", "unknown")
            total = v.get("total_estimate", 0)
            tradeoffs = v.get("tradeoffs", "")
            budget_msg += f"\n- **{tier.title()}**: ~${total:.2f} — {tradeoffs}"

        writer({
            "event": "message",
            "data": {"role": "assistant", "content": budget_msg},
        })

    return {
        "creative_brief": creative_brief,
        "production_plan": production_plan,
        "budget_variants": budget_variants,
        "status": "direction_generated",
        "progress_messages": [
            f"Creative direction: {len(production_plan)} steps, {len(budget_variants)} budget options"
        ],
    }
