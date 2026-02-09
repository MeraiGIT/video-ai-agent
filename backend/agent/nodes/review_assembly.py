"""Review Assembly node: user reviews the assembled output."""

import logging

from langgraph.types import interrupt

from agent.state import ProductionState

logger = logging.getLogger(__name__)


def run(state: ProductionState) -> dict:
    logger.info("Review Assembly: awaiting user approval")
    response = interrupt({"stage": "assembly_review", "actions": ["approve", "modify"]})
    if response["action"] == "approve":
        return {
            "status": "assembly_approved",
            "progress_messages": ["Assembly approved"],
        }
    return {
        "progress_messages": ["Assembly modification requested"],
    }
