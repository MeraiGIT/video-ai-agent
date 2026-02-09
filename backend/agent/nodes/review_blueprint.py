"""Review Blueprint node: user reviews the execution plan."""

import logging

from langgraph.types import interrupt

from agent.state import ProductionState

logger = logging.getLogger(__name__)


def run(state: ProductionState) -> dict:
    logger.info("Review Blueprint: awaiting user approval")
    response = interrupt({"stage": "blueprint_review", "actions": ["approve", "modify"]})
    if response["action"] == "approve":
        return {
            "status": "blueprint_approved",
            "progress_messages": ["Blueprint approved"],
        }
    return {
        "progress_messages": ["Blueprint modification requested"],
    }
