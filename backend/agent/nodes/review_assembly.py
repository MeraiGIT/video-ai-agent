"""Review Assembly node — user reviews the assembled output.

Uses interrupt() to show the assembled output and get user approval.
"""

import logging

from langgraph.config import get_stream_writer
from langgraph.types import interrupt

from agent.state import ProductionState
from services.supabase_service import save_project_state

logger = logging.getLogger(__name__)


def run(state: ProductionState) -> dict:
    """Present assembled output to user for approval."""
    writer = get_stream_writer()
    assembled_path = state.get("assembled_path", "")

    content = "**Assembly complete!** Please review the assembled output above."
    if not assembled_path:
        content = "Assembly finished but no output was produced. You can approve to continue or ask me to try again."

    writer({
        "event": "message",
        "data": {"role": "assistant", "content": content},
    })

    response = interrupt({
        "stage": "assembly_review",
        "actions": ["approve", "modify"],
    })

    action = response.get("action", "approve")

    if action == "approve":
        logger.info("Assembly approved")
        writer({
            "event": "message",
            "data": {
                "role": "assistant",
                "content": "Assembly approved! Moving to polish...",
            },
        })
        result = {
            "status": "assembly_approved",
            "progress_messages": ["Assembly approved — moving to polish"],
        }
        project_id = state.get("project_id")
        if project_id:
            save_project_state(project_id, {**dict(state), **result})
        return result

    feedback = response.get("message", "")
    logger.info("Assembly modification requested: %s", feedback[:80])
    writer({
        "event": "message",
        "data": {
            "role": "assistant",
            "content": "Got it, reassembling based on your feedback...",
        },
    })
    return {
        "status": "assembly_needs_revision",
        "progress_messages": [f"Assembly revision: {feedback[:50]}"],
    }
