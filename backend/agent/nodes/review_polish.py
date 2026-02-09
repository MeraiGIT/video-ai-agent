"""Review Polish node — user reviews the polished output.

Uses interrupt() to show the polished output and get user approval.
"""

import logging

from langgraph.config import get_stream_writer
from langgraph.types import interrupt

from agent.state import ProductionState

logger = logging.getLogger(__name__)


def run(state: ProductionState) -> dict:
    """Present polished output to user for approval."""
    writer = get_stream_writer()
    polished_path = state.get("polished_path", "")

    content = "**Polish complete!** Please review the polished output above."
    if not polished_path:
        content = "Polish finished but no output was produced. You can approve to continue or ask me to try again."

    writer({
        "event": "message",
        "data": {"role": "assistant", "content": content},
    })

    response = interrupt({
        "stage": "polish_review",
        "actions": ["approve", "modify"],
    })

    action = response.get("action", "approve")

    if action == "approve":
        logger.info("Polish approved")
        writer({
            "event": "message",
            "data": {
                "role": "assistant",
                "content": "Polish approved! Preparing final delivery...",
            },
        })
        return {
            "status": "polish_approved",
            "progress_messages": ["Polish approved — moving to delivery"],
        }

    feedback = response.get("message", "")
    logger.info("Polish modification requested: %s", feedback[:80])
    writer({
        "event": "message",
        "data": {
            "role": "assistant",
            "content": "Got it, re-polishing based on your feedback...",
        },
    })
    return {
        "status": "polish_needs_revision",
        "progress_messages": [f"Polish revision: {feedback[:50]}"],
    }
