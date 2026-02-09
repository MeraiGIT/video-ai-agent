"""Review Direction node: user reviews the creative direction."""

import logging

from langgraph.types import interrupt

from agent.state import ProductionState

logger = logging.getLogger(__name__)


def run(state: ProductionState) -> dict:
    logger.info("Review Direction: awaiting user approval")
    response = interrupt({"stage": "direction_review", "actions": ["approve", "modify"]})
    if response["action"] == "approve":
        return {
            "status": "direction_approved",
            "progress_messages": ["Creative direction approved"],
        }
    return {
        "progress_messages": ["Creative direction modification requested"],
    }
