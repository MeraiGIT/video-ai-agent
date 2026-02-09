"""Review Blueprint node — user reviews the execution blueprint.

Uses interrupt() to pause for user approval. The user can approve
to proceed to production, or request modifications.
"""

import logging

from langgraph.config import get_stream_writer
from langgraph.types import interrupt

from agent.state import ProductionState

logger = logging.getLogger(__name__)


def run(state: ProductionState) -> dict:
    """Wait for user to approve the execution blueprint."""
    writer = get_stream_writer()

    writer({
        "event": "message",
        "data": {
            "role": "assistant",
            "content": (
                "Please review the blueprint above. "
                "Approve to start production, or let me know what to change."
            ),
        },
    })

    response = interrupt({
        "stage": "blueprint_review",
        "actions": ["approve", "modify"],
    })

    action = response.get("action", "approve")

    if action == "approve":
        logger.info("Blueprint approved, proceeding to production")

        writer({
            "event": "message",
            "data": {
                "role": "assistant",
                "content": "Blueprint approved! Starting production...",
            },
        })

        return {
            "status": "blueprint_approved",
            "current_stage_index": 0,
            "total_cost": 0.0,
            "cost_breakdown": [],
            "quality_results": [],
            "retry_count": 0,
            "progress_messages": ["Blueprint approved — production starting"],
        }

    # User wants modifications
    feedback = response.get("message", "")
    logger.info("Blueprint modification requested: %s", feedback[:80])

    writer({
        "event": "message",
        "data": {
            "role": "assistant",
            "content": "Got it, let me revise the blueprint based on your feedback...",
        },
    })

    return {
        "status": "blueprint_needs_revision",
        "progress_messages": [f"Blueprint revision requested: {feedback[:50]}"],
    }
