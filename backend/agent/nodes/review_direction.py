"""Review Direction node — user approves creative direction + selects budget.

Uses interrupt() to pause for user approval. The user can:
- Approve (with budget tier selection)
- Modify (send feedback to revise the direction)
"""

import logging

from langgraph.config import get_stream_writer
from langgraph.types import interrupt

from agent.state import ProductionState
from services.supabase_service import save_project_state

logger = logging.getLogger(__name__)


def run(state: ProductionState) -> dict:
    """Wait for user to approve creative direction and select budget tier."""
    writer = get_stream_writer()

    writer({
        "event": "message",
        "data": {
            "role": "assistant",
            "content": (
                "Please review the creative direction and budget options above. "
                "You can approve with a budget selection, or ask me to modify anything."
            ),
        },
    })

    response = interrupt({
        "stage": "direction_review",
        "actions": ["approve", "modify"],
    })

    action = response.get("action", "approve")

    # Handle budget selection sent via modify path (e.g., "approve:budget")
    message = response.get("message", "")
    if action == "modify" and message.startswith("approve:"):
        action = "approve"
        tier_from_message = message.split(":", 1)[1].strip()
        if tier_from_message:
            response = {**response, "selected_tier": tier_from_message}

    if action == "approve":
        # Extract selected budget tier — check multiple field names for flexibility
        selected_tier = (
            response.get("selected_tier")
            or response.get("selected_variant")
            or response.get("tier")
            or "standard"
        )
        logger.info("Direction approved with %s tier", selected_tier)

        # Apply selected variant's model selections to production plan
        budget_variants = state.get("budget_variants", [])
        selected_variant = None
        for v in budget_variants:
            if v.get("tier") == selected_tier:
                selected_variant = v
                break

        result: dict = {
            "selected_variant": selected_tier,
            "status": "direction_approved",
            "progress_messages": [f"Direction approved ({selected_tier} tier)"],
        }

        # Update production plan with selected variant's model choices
        if selected_variant and selected_variant.get("model_selections"):
            production_plan = list(state.get("production_plan", []))
            model_map = selected_variant["model_selections"]
            for step in production_plan:
                cap = step.get("capability", "")
                if cap in model_map:
                    step["model"] = model_map[cap]
            result["production_plan"] = production_plan

        # Set budget limit
        if selected_variant:
            result["budget_limit"] = selected_variant.get("total_estimate", 0) * 1.2

        writer({
            "event": "message",
            "data": {
                "role": "assistant",
                "content": f"Creative direction approved with **{selected_tier}** budget. Moving to blueprint...",
            },
        })

        # Auto-save to Supabase at this phase boundary
        project_id = state.get("project_id")
        if project_id:
            save_project_state(project_id, {**dict(state), **result})

        return result

    # User wants modifications
    feedback = response.get("message", "")
    logger.info("Direction modification requested: %s", feedback[:80])

    writer({
        "event": "message",
        "data": {
            "role": "assistant",
            "content": "Got it, let me revise the creative direction based on your feedback...",
        },
    })

    return {
        "status": "direction_needs_revision",
        "progress_messages": [f"Direction revision requested: {feedback[:50]}"],
    }
