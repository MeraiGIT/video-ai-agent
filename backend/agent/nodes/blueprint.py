"""Blueprint node — generates the detailed execution blueprint.

Takes the approved creative brief and production plan, calls Claude to
generate a freeform blueprint with all execution details. The blueprint
structure varies by project type — the LLM decides what's needed.
"""

import json
import logging

from langgraph.config import get_stream_writer

from agent.state import ProductionState
from agent.prompts.blueprint import BLUEPRINT_SYSTEM, build_blueprint_prompt
from services.claude_service import client, MODEL

logger = logging.getLogger(__name__)


def run(state: ProductionState) -> dict:
    """Generate a detailed execution blueprint from the creative direction."""
    writer = get_stream_writer()

    writer({
        "event": "progress",
        "data": {"stage": "blueprint", "message": "Generating execution blueprint..."},
    })

    creative_brief = state.get("creative_brief", {})
    production_plan = state.get("production_plan", [])

    prompt = build_blueprint_prompt(
        creative_brief=creative_brief,
        production_plan=production_plan,
        content_type=state.get("content_type", "short_video"),
        user_request=state.get("user_request", ""),
        constraints=state.get("constraints"),
        research_insights=state.get("research_insights"),
        reference_materials=state.get("reference_materials"),
    )

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=BLUEPRINT_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        blueprint = json.loads(text)
    except Exception as e:
        logger.error("Blueprint generation failed: %s", e)
        writer({
            "event": "message",
            "data": {
                "role": "assistant",
                "content": (
                    "I had trouble generating the detailed blueprint. "
                    "Using the production plan directly as the execution guide."
                ),
            },
        })
        # Fallback: use production plan as minimal blueprint
        blueprint = {
            "title": state.get("user_request", "Untitled project")[:80],
            "summary": "Auto-generated from production plan",
            "steps": production_plan,
        }

    # Emit blueprint artifact for frontend
    writer({
        "event": "artifact",
        "data": {"type": "blueprint", "blueprint": blueprint},
    })

    # Show summary to user
    title = blueprint.get("title", "Blueprint")
    summary = blueprint.get("summary", "")
    scene_count = len(blueprint.get("scenes", []))
    step_count = len(production_plan)

    msg_parts = [f"**Blueprint: {title}**"]
    if summary:
        msg_parts.append(summary)
    if scene_count:
        msg_parts.append(f"{scene_count} scenes planned")
    msg_parts.append(f"{step_count} production steps ready")

    writer({
        "event": "message",
        "data": {"role": "assistant", "content": "\n\n".join(msg_parts)},
    })

    return {
        "blueprint": blueprint,
        "status": "blueprint_generated",
        "progress_messages": [
            f"Blueprint: {title} ({step_count} steps, {scene_count} scenes)"
        ],
    }
