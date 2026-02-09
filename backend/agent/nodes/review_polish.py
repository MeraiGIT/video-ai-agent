"""Review Polish node: user reviews the polished output."""

import logging

from langgraph.types import interrupt

from agent.state import ProductionState

logger = logging.getLogger(__name__)


def run(state: ProductionState) -> dict:
    logger.info("Review Polish: awaiting user approval")
    response = interrupt({"stage": "polish_review", "actions": ["approve", "modify"]})
    if response["action"] == "approve":
        return {
            "status": "polish_approved",
            "progress_messages": ["Polish approved"],
        }
    return {
        "progress_messages": ["Polish modification requested"],
    }
